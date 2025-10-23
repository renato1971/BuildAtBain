#!/usr/bin/env python3
"""
Fixed ETL Pipeline Orchestrator
Executes a simplified ETL process that actually completes
"""

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Setup paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.utils.etl_utils import download_all_datasets, transform_json_for_db
from src.database.connection import db
from src.database.schema_generator import schema_generator
from src.agents.etl_crew import ETLCrew

# Load environment variables (don't override Docker environment variables)
load_dotenv(project_root / ".env", override=False)

# Simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_structured_data_pipeline():
    """Run a simplified version that actually works"""
    try:
        logger.info("Starting Simplified ETL Process")
        
        # Step 0: Download data
        logger.info("Downloading datasets from IBGE API...")
        download_result = download_all_datasets()
        logger.info(download_result)

        # Step 1: Check raw data
        raw_dir = project_root / "data/raw"
        json_files = list(raw_dir.glob("*.json"))

        if not json_files:
            logger.error("No JSON files found in data/raw/")
            return False
        
        logger.info(f"Found {len(json_files)} data files")
        
        # Step 2: Generate and create schemas
        logger.info("Creating database schemas...")
        schemas = schema_generator.generate_all_schemas(str(raw_dir))
        
        for table_name, sql in schemas.items():
            try:
                db.execute_command(f'DROP TABLE IF EXISTS {table_name} CASCADE;')
                db.execute_script(sql)
                logger.info(f"Created table: {table_name}")
            except Exception as e:
                logger.error(f"Failed to create table {table_name}: {e}")
                return False
        
        # Step 3: Load data
        logger.info("Loading data into database...")
        total_loaded = 0
        
        for json_file in json_files:
            table_name = json_file.stem
            
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Transform data
                transformed = transform_json_for_db(data, table_name)
                
                if transformed and db.table_exists(table_name):
                    rows_inserted = db.bulk_insert(table_name, transformed)
                    total_loaded += rows_inserted
                    logger.info(f"Loaded {rows_inserted} rows into {table_name}")
                
            except Exception as e:
                logger.error(f"Failed to load {table_name}: {e}")
        
        # Step 4: Verify
        logger.info("Verifying results...")
        tables = db.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        for table in tables:
            table_name = table['table_name']
            count = db.execute_query(f'SELECT COUNT(*) as count FROM {table_name};')[0]['count']
            logger.info(f"Table {table_name}: {count} rows")

        # Step 5: Copy data from raw to processed
        logger.info("Copying data from raw to processed...")
        processed_dir = project_root / "data/processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        for json_file in json_files:
            table_name = json_file.stem
            processed_file = processed_dir / f"{table_name}.json"
            
            # Read from raw and write to processed
            with open(json_file, 'r', encoding='utf-8') as source:
                content = source.read()
            
            with open(processed_file, 'w', encoding='utf-8') as dest:
                dest.write(content)
            
            logger.info(f"Copied {json_file.name} to processed/{table_name}.json")
        
        if total_loaded > 0:
            logger.info(f"ETL completed successfully! Total rows: {total_loaded}")
            return True
        else:
            logger.error("No data was loaded")
            return False
            
    except Exception as e:
        logger.error(f"ETL failed: {e}")
        return False

def run_etl_crew_analysis(table_name: str = None):
    """Run ETL Crew to analyze tables and generate configurations"""
    try:
        logger.info("\n" + "="*50)
        logger.info("Starting ETL Crew analysis")
        logger.info("="*50)
        
        # Initialize the ETL crew
        logger.info("Initializing ETL Crew...")
        etl_crew = ETLCrew()
        
        # Set inputs for automatic discovery and batch analysis
        inputs = {
            'table_list': [table_name] if table_name else [],  # Empty = auto-discover all tables
            'config_template_path': 'src/templates/etl/structured_data_template.yaml',
            'output_yaml_path': 'src/config/newsletter_v1/structured_data.yaml',
            'quality_report': 'data/config/structured_data_report.yaml'
        }
        
        logger.info("Running table analysis and quality assurance...")
        
        # Run the crew (batch analysis + quality assurance)
        try:
            _ = etl_crew.crew().kickoff(inputs=inputs)

        except Exception as e:
            logger.error(f"ETL Crew analysis failed: {str(e)}")
            logger.error("Configuration generation incomplete, but data is loaded.")
            return False
        return True
        
    except Exception as e:
        logger.error(f"ETL Crew analysis failed: {str(e)}")
        logger.error("Configuration generation incomplete, but data is loaded.")
        return False


def run_etl_pipeline():
    """Main ETL pipeline execution - can be called directly from API"""
    try:
        logger.info("="*50)
        logger.info("STARTING ETL PIPELINE")
        logger.info("="*50)
        
        # Step 1: Download and load data
        success = run_structured_data_pipeline()
            
        if success:
            logger.info("✅ Data download and loading completed successfully!")
            
            # Step 2: Run ETL Crew to analyze tables
            logger.info("\n" + "="*50)
            logger.info("PHASE 2: TABLE ANALYSIS & CONFIGURATION")
            logger.info("="*50)

            return True

        else:
            logger.error("ETL Pipeline failed - Data loading unsuccessful")
            return False
            
    except Exception as e:
        logger.error(f"ETL Pipeline execution failed: {str(e)}")
        return False

def run_crew_pipeline(table_name: str = None):
    """Run ETL Crew to analyze tables and generate configurations"""
    try:
        logger.info("\n" + "="*50)
        logger.info("Starting ETL Crew analysis")
        logger.info("="*50)

        crew_success = run_etl_crew_analysis(table_name)
            
        if crew_success:
            logger.info("✅ Table analysis and configuration completed successfully!")
            return True
        else:
            logger.warning("\n⚠️  Data loaded but configuration generation had issues")
            logger.info("Data is available in the database and can be used.")
        
            return False
        
    except Exception as e:
        logger.error(f"ETL Crew analysis failed: {str(e)}")
        return False

def delete_table(table_name: str):
    """Delete a table from the database"""
    try:
        db.execute_command(f'DROP TABLE IF EXISTS {table_name} CASCADE;')
        logger.info(f"Table {table_name} deleted successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to delete table {table_name}: {str(e)}")
        return False

def main():
    """CLI entry point - calls run_etl_pipeline()"""
    return run_etl_pipeline()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("ETL Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"ETL Pipeline failed with error: {str(e)}")
        sys.exit(1)