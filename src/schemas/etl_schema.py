"""ETL Schema definitions for structured and unstructured data processing"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Enums
# ============================================================================

class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some succeeded, some failed


# ============================================================================
# Structured Data Models (IBGE)
# ============================================================================

class IBGEDataSource(BaseModel):
    """Model for IBGE data source"""
    url: str = Field(
        ...,
        example="http://api.sidra.ibge.gov.br/values/t/1419/n1/all/v/all/p/all?formato=json"
    )
    table_name: str = Field(..., example="ipca")


class IBGEDataSourceList(BaseModel):
    """Model for list of IBGE data sources"""
    data_sources: List[IBGEDataSource] = Field(
        ...,
        min_items=1,
        description="List of IBGE data sources to process"
    )


class ETLResponse(BaseModel):
    """Response model for ETL operations"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    table_name: str = Field(..., description="Name of the processed table")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details"
    )


class ETLJobItem(BaseModel):
    """Individual job item for a single data source"""
    job_id: str = Field(..., description="Unique job identifier")
    table_name: str = Field(..., description="Table name being processed")
    url: str = Field(..., description="Data source URL")
    status: JobStatus = Field(..., description="Current job status")


class ETLJobResponse(BaseModel):
    """Response model for ETL job creation"""
    message: str = Field(..., description="Response message")
    total: int = Field(..., description="Total number of jobs created")
    jobs: List[ETLJobItem] = Field(
        ...,
        description="List of individual job items with their job IDs"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")


class ETLJobStatusResponse(BaseModel):
    """Response model for individual ETL job status"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    table_name: str = Field(..., description="Table name being processed")
    url: str = Field(..., description="Data source URL")
    result: Optional[ETLResponse] = Field(
        None,
        description="Processing result if completed"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(
        None,
        description="Job completion timestamp"
    )


class DataSourceDeleteResponse(BaseModel):
    """Response schema for data source deletion"""
    success: bool = Field(..., description="Deletion success status")
    message: str = Field(..., description="Response message")


# ============================================================================
# Unstructured Data Models (PDF)
# ============================================================================

class PDFItem(BaseModel):
    """Model for a single PDF item to be uploaded"""
    url: HttpUrl
    filename: Optional[str] = None


class PDFBatchRequest(BaseModel):
    """Request model for batch PDF upload"""
    items: List[PDFItem]


class PDFJobStatusResponse(BaseModel):
    """Response model for PDF job status"""
    job_id: str
    status: str
    detail: Optional[str] = None
