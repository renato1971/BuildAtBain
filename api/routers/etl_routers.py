"""ETL API Routers for data ingestion and processing.

This module provides FastAPI routers for:
1. Structured data (IBGE) ETL operations
2. Unstructured data (PDF) ETL operations
"""

import logging
import re
import shutil
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Tuple

import requests
import yaml
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from api.logger import get_logger
from src.schemas.etl_schema import (
    DataSourceDeleteResponse,
    ETLJobResponse,
    ETLJobStatusResponse,
    ETLResponse,
    IBGEDataSource,
    IBGEDataSourceList,
    JobStatus,
    PDFBatchRequest,
    PDFItem,
    PDFJobStatusResponse,
)
from src.services.etl_service.structured_data import (
    delete_table,
    run_crew_pipeline,
    run_etl_pipeline,
)
from src.services.etl_service.unstructured_data import PDFToWeaviate

# Initialize logger and router
logger = get_logger(__name__)
router = APIRouter(prefix="/etl", tags=["ETL"])

# Load environment variables
load_dotenv(project_root / ".env", override=True)

# ============================================================================
# Configuration and Global State
# ============================================================================

# Path to data_apis.yaml
DATA_APIS_CONFIG = project_root / "data" / "config" / "data_apis.yaml"

# Directories for PDF processing
RAW_DIR = project_root / "data" / "raw"
PROCESSED_DIR = project_root / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job tracking
jobs_store: Dict[str, Dict[str, Any]] = {}
_processing_jobs: Dict[str, str] = {}
_job_details: Dict[str, str | None] = {}

# ETL lock for preventing concurrent PDF ETL runs
_etl_lock = Lock()
_etl_active = False


# ============================================================================
# Utility Functions - Structured Data
# ============================================================================

def _process_table_name(table_name: str) -> Tuple[str, bool]:
    original = table_name
    
    # Convert to lowercase and replace spaces/hyphens with underscores
    sanitized = table_name.lower().replace(" ", "_").replace("-", "_")
    
    # Remove any characters that are not alphanumeric or underscore
    sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
    
    # Collapse multiple underscores into one
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it starts with a letter or underscore (not a number)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"table_{sanitized}"
    
    # If empty after sanitization, use a default name
    if not sanitized:
        sanitized = "table_unnamed"
    
    was_changed = (original != sanitized)
    
    if was_changed:
        logger.warning(f"Table name sanitized: '{original}' → '{sanitized}'")
    
    return sanitized, was_changed


def _append_to_data_apis_yaml(url: str, table_name: str) -> bool:
    """Append new data source to data_apis.yaml"""
    try:
        # Read existing YAML
        if DATA_APIS_CONFIG.exists():
            with open(DATA_APIS_CONFIG, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        
        # Check if table already exists
        if table_name in data:
            logger.warning(f"Table '{table_name}' already exists in data_apis.yaml - updating URL")
        
        # Add/update the entry
        data[table_name] = {
            'url': url,
            'table_name': table_name
        }
        
        # Write back to YAML
        with open(DATA_APIS_CONFIG, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        logger.info(f"Successfully added/updated '{table_name}' in data_apis.yaml")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update data_apis.yaml: {str(e)}")
        raise


# ============================================================================
# Background Tasks - Structured Data
# ============================================================================

def process_single_data_source(job_id: str, data_source: IBGEDataSource) -> None:
    """
    Background task to process a single data source and update its job status.
    
    Args:
        job_id: Unique job identifier for this data source
        data_source: IBGE data source to process
    """
    try:
        # Update job status to PROCESSING
        jobs_store[job_id]["status"] = JobStatus.PROCESSING
        jobs_store[job_id]["updated_at"] = datetime.now()
        
        logger.info(f"[Job {job_id}] Starting processing of '{data_source.table_name}'")
        
        # Step 1: Add to data_apis.yaml
        _append_to_data_apis_yaml(data_source.url, data_source.table_name)
        
        # Step 2: Run ETL pipeline for this specific source
        try:
            logger.info(f"[Job {job_id}] Starting structured data pipeline for '{data_source.table_name}'")
            success = run_etl_pipeline()
        except Exception as e:
            logger.error(f"[Job {job_id}] Failed to start structured data pipeline for '{data_source.table_name}': {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start structured data pipeline for '{data_source.table_name}': {str(e)}"
            )
        try:
            logger.info(f"[Job {job_id}] Starting crew pipeline for '{data_source.table_name}'")
            success = run_crew_pipeline(data_source.table_name)
        except Exception as e:
            logger.error(f"[Job {job_id}] Failed to start crew pipeline for '{data_source.table_name}': {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start crew pipeline for '{data_source.table_name}': {str(e)}"
            )
            
        if success:
            result = ETLResponse(
                success=True,
                message=f"Successfully processed data source '{data_source.table_name}'",
                table_name=data_source.table_name,
                details={
                    "config_file": "data/config/data_apis.yaml",
                    "structured_data_config": "src/config/newsletter_v1/structured_data.yaml",
                    "quality_report": "data/config/structured_data_report.yaml",
                    "status": "Data downloaded, loaded, and analyzed"
                }
            )
            jobs_store[job_id]["status"] = JobStatus.COMPLETED
            jobs_store[job_id]["message"] = f"Successfully processed '{data_source.table_name}'"
            logger.info(f"[Job {job_id}] Successfully processed: {data_source.table_name}")
        else:
            result = ETLResponse(
                success=False,
                message=f"Failed to process data source '{data_source.table_name}'",
                table_name=data_source.table_name,
                details={"error": "ETL pipeline failed"}
            )
            jobs_store[job_id]["status"] = JobStatus.FAILED
            jobs_store[job_id]["message"] = f"Failed to process '{data_source.table_name}'"
            logger.error(f"[Job {job_id}] Failed to process: {data_source.table_name}")
        
        # Store result
        jobs_store[job_id]["result"] = result
        
    except Exception as e:
        error_msg = str(e)
        result = ETLResponse(
            success=False,
            message=f"Error processing '{data_source.table_name}': {error_msg}",
            table_name=data_source.table_name,
            details={"error": error_msg}
        )
        jobs_store[job_id]["status"] = JobStatus.FAILED
        jobs_store[job_id]["message"] = f"Error: {error_msg}"
        jobs_store[job_id]["result"] = result
        logger.error(f"[Job {job_id}] Exception processing {data_source.table_name}: {error_msg}")
    
    finally:
        # Update final timestamps
        jobs_store[job_id]["completed_at"] = datetime.now()
        jobs_store[job_id]["updated_at"] = datetime.now()
        logger.info(f"[Job {job_id}] Processing completed - Status: {jobs_store[job_id]['status']}")


# ============================================================================
# API Endpoints - Structured Data (IBGE)
# ============================================================================

@router.post("/upload_data_ibge", response_model=ETLJobResponse)
async def upload_data_ibge(
    data_source_list: IBGEDataSourceList,
    background_tasks: BackgroundTasks
) -> ETLJobResponse:
    """
    Upload multiple IBGE data sources and trigger ETL pipeline in background.
    
    This endpoint:
    1. Accepts a list of URLs and table names
    2. Creates a unique job ID for EACH data source
    3. Adds each to data_apis.yaml in the background
    4. Triggers the ETL pipeline for each to download and process the data
    5. Runs the ETL Crew to analyze tables and generate configurations
    6. Returns list of job IDs for tracking each individual data source
    
    Args:
        data_source_list: List of IBGE data sources with URLs and table names
        background_tasks: FastAPI background tasks
    
    Returns:
        List of job IDs (one per data source) for tracking
    """
    try:
        data_sources = data_source_list.data_sources
        created_at = datetime.now()
        job_items = []
        
        logger.info(f"Creating {len(data_sources)} individual jobs for data sources")
        
        # Create a job for each data source
        for data_source in data_sources:
            # Sanitize table name
            sanitized_table_name, _ = _process_table_name(data_source.table_name)
            
            # Generate unique job ID for this data source
            job_id = str(uuid.uuid4())
            
            # Initialize job in store
            jobs_store[job_id] = {
                "job_id": job_id,
                "status": JobStatus.PENDING,
                "message": f"Job created for '{sanitized_table_name}'",
                "table_name": sanitized_table_name,
                "url": data_source.url,
                "result": None,
                "created_at": created_at,
                "updated_at": created_at,
                "completed_at": None
            }
            
            # Add job item to response
            job_items.append({
                "job_id": job_id,
                "table_name": sanitized_table_name,
                "url": data_source.url,
                "status": JobStatus.PENDING
            })
            
            # Update data source with sanitized name for processing
            data_source.table_name = sanitized_table_name
            
            background_tasks.add_task(process_single_data_source, job_id, data_source)
            
            logger.info(f"[Job {job_id}] Created for table '{data_source.table_name}'")

        return ETLJobResponse(
            message=f"Created {len(data_sources)} jobs for processing",
            total=len(data_sources),
            jobs=job_items,
            created_at=created_at
        )
            
    except Exception as e:
        logger.error(f"Unexpected error in upload_data_ibge: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/ibge-job-status/{job_id}", response_model=ETLJobStatusResponse)
async def get_job_status(job_id: str) -> ETLJobStatusResponse:
    """
    Check the status of an individual ETL job.
    
    Args:
        job_id: Unique job identifier for a specific data source
    
    Returns:
        Current job status with results if completed
    """
    try:
        # Check if job exists
        if job_id not in jobs_store:
            raise HTTPException(
                status_code=404,
                detail=f"Job '{job_id}' not found"
            )
        
        job = jobs_store[job_id]
        
        # Convert enum to string value for API response
        status_value = job["status"].value if hasattr(job["status"], 'value') else str(job["status"])
        
        # Return job status
        return ETLJobStatusResponse(
            job_id=job["job_id"],
            status=status_value,  # Ensure this is a string
            message=job["message"],
            table_name=job["table_name"],
            url=job["url"],
            result=job.get("result"),
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            completed_at=job["completed_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.delete("/data_sources/{table_name}", response_model=DataSourceDeleteResponse)
async def delete_data_source(table_name: str) -> DataSourceDeleteResponse:
    """
    Remove a data source from data_apis.yaml.
    
    Args:
        table_name: Name of the table to remove
    
    Returns:
        Success message
    """

    if not DATA_APIS_CONFIG.exists():
        raise HTTPException(
            status_code=404,
            detail="data_apis.yaml not found"
        )

    try:
        with open(DATA_APIS_CONFIG, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to read data sources: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read data sources: {str(e)}"
        )
    try:
        if table_name not in data:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found in data sources"
            )
        
        # Remove the entry from data_apis.yaml
        del data[table_name]
        
        # Write back
        with open(DATA_APIS_CONFIG, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        logger.info(f"Table {table_name} removed from data_apis.yaml")

    except Exception as e:
        logger.error(f"Failed to delete table {table_name} from data_apis.yaml: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete table {table_name} from data_apis.yaml: {str(e)}"
        )
    # Remove the table from the database
    try:
        success = delete_table(table_name)
        
        if success:
            return DataSourceDeleteResponse(
                success=True,
                message=f"Data source '{table_name}' removed successfully"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "ETL pipeline failed",
                    "error": "Check server logs for detailed error information"
                }
            )
    
    except Exception as e:
        logger.error(f"Failed to delete data source: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete data source: {str(e)}"
        )


# ============================================================================
# Utility Functions - Unstructured Data (PDF)
# ============================================================================

def _download_pdfs(items: list[PDFItem], job_id: str):
    """Download PDFs from provided URLs to the raw directory"""
    try:
        _processing_jobs[job_id] = "downloading"
        saved = []
        for i, item in enumerate(items, start=1):
            resp = requests.get(str(item.url), timeout=90)
            if resp.status_code != 200:
                raise RuntimeError(f"Falha download {item.url}: HTTP {resp.status_code}")
            ct = resp.headers.get("Content-Type", "")
            base_name = item.filename or f"pdf_{i}_{job_id}.pdf"
            if not base_name.lower().endswith(".pdf"):
                base_name += ".pdf"
            if "pdf" not in ct.lower() and not base_name.lower().endswith(".pdf"):
                raise RuntimeError(f"Content-Type inesperado: {ct} para {item.url}")
            safe_name = "".join(c for c in base_name if c.isalnum() or c in ("-", "_", ".", " ")).strip()
            target = RAW_DIR / safe_name
            with open(target, "wb") as f:
                f.write(resp.content)
            logger.info(f"[{job_id}] PDF salvo: {target.name}")
            saved.append(safe_name)
        _processing_jobs[job_id] = "saved"
        _job_details[job_id] = f"{len(saved)} PDFs salvos em data/raw"
    except Exception as e:
        logger.error(f"Falha no upload batch {job_id}: {e}")
        _processing_jobs[job_id] = "error"
        _job_details[job_id] = str(e)


# ============================================================================
# Background Tasks - Unstructured Data (PDF)
# ============================================================================

def _run_etl(job_id: str):
    """Run ETL pipeline to ingest PDFs from raw directory into Weaviate"""
    global _etl_active
    try:
        _processing_jobs[job_id] = "ingesting"
        etl = PDFToWeaviate()
        try:
            etl.run(RAW_DIR)
        finally:
            etl.close()
        for pdf in RAW_DIR.glob("*.pdf"):
            shutil.move(str(pdf), PROCESSED_DIR / pdf.name)
        _processing_jobs[job_id] = "done"
        _job_details[job_id] = "ETL concluído e PDFs movidos para data/processed"
    except Exception as e:
        logger.error(f"Falha no run {job_id}: {e}")
        _processing_jobs[job_id] = "error"
        _job_details[job_id] = str(e)
    finally:
        with _etl_lock:
            _etl_active = False


# ============================================================================
# API Endpoints - Unstructured Data (PDF)
# ============================================================================

@router.post("/pdf-upload", response_model=PDFJobStatusResponse)
def upload_pdfs(
    payload: PDFBatchRequest,
    background_tasks: BackgroundTasks
) -> PDFJobStatusResponse:
    """
    Upload PDFs from provided URLs to the raw directory.
    
    Args:
        payload: Batch request containing list of PDF items with URLs
        background_tasks: FastAPI background tasks
    
    Returns:
        Job status response with job ID for tracking
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="Lista vazia")
    
    job_id = f"upload_{int(time.time())}"
    _processing_jobs[job_id] = "queued"
    _job_details[job_id] = None
    
    background_tasks.add_task(_download_pdfs, payload.items, job_id)
    
    return PDFJobStatusResponse(job_id=job_id, status="queued", detail=None)


@router.post("/run", response_model=PDFJobStatusResponse)
def run_etl(background_tasks: BackgroundTasks) -> PDFJobStatusResponse:
    """
    Run ETL pipeline to process PDFs from raw directory into Weaviate.
    
    This endpoint:
    1. Checks if there are PDFs in the raw directory
    2. Ensures no other ETL process is running
    3. Ingests PDFs into Weaviate
    4. Moves processed PDFs to the processed directory
    
    Args:
        background_tasks: FastAPI background tasks
    
    Returns:
        Job status response with job ID for tracking
    """
    if not any(RAW_DIR.glob("*.pdf")):
        raise HTTPException(status_code=400, detail="Nenhum PDF em data/raw")
    
    with _etl_lock:
        global _etl_active
        if _etl_active:
            raise HTTPException(
                status_code=409,
                detail="Já existe um ETL em execução"
            )
        _etl_active = True
    
    job_id = f"run_{int(time.time())}"
    _processing_jobs[job_id] = "queued"
    _job_details[job_id] = None
    
    background_tasks.add_task(_run_etl, job_id)
    
    return PDFJobStatusResponse(job_id=job_id, status="queued", detail=None)


@router.get("/pdf-job-status/{job_id}", response_model=PDFJobStatusResponse)
def pdf_job_status(job_id: str) -> PDFJobStatusResponse:
    """
    Check the status of a PDF processing job.
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Current job status and details
    """
    status = _processing_jobs.get(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    return PDFJobStatusResponse(
        job_id=job_id,
        status=status,
        detail=_job_details.get(job_id)
    )
