"""
Tools for analyzing database schemas and creating structured data configurations.

This module provides CrewAI-compatible tools for:
    - Analyzing table schemas from PostgreSQL databases
    - Sampling data from tables to understand structure
    - Appending configurations to structured_data.yaml files
"""

import os
import json
import yaml
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from ...database.connection import db, DatabaseConnection


class GetTableSchemaArgs(BaseModel):
    """Arguments for getting table schema information."""

    table_name: str = Field(..., description="The name of the table to analyze.")


class GetTableSchemaTool(BaseTool):
    """Tool to get table schema information from PostgreSQL."""

    name: str = "get_table_schema"
    description: str = (
        "Retrieves schema information for a table including column names, "
        "data types, nullable status, and defaults. Returns JSON with schema details."
    )
    args_schema: Type[BaseModel] = GetTableSchemaArgs

    def _run(
        self, table_name: str, db_connection: DatabaseConnection = db
    ) -> str:
        try:
            if not db_connection.table_exists(table_name):
                return json.dumps({"error": f"Table '{table_name}' does not exist."})

            schema = db_connection.get_table_schema(table_name)
            
            # Also get sample row count
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            count_result = db_connection.execute_query(count_query)
            total_rows = count_result[0]['total'] if count_result else 0

            result = {
                "table_name": table_name,
                "total_rows": total_rows,
                "columns": [dict(col) for col in schema]
            }
            
            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})


class SampleTableDataArgs(BaseModel):
    """Arguments for sampling table data."""

    table_name: str = Field(..., description="The name of the table to sample.")
    limit: int = Field(
        default=5, 
        description="Number of sample rows to retrieve (default: 5)."
    )


class SampleTableDataTool(BaseTool):
    """Tool to retrieve sample data from a table."""

    name: str = "sample_table_data"
    description: str = (
        "Retrieves sample rows from a table to understand the data structure "
        "and values. Returns JSON array with sample rows."
    )
    args_schema: Type[BaseModel] = SampleTableDataArgs

    def _run(
        self, 
        table_name: str, 
        limit: int = 5,
        db_connection: DatabaseConnection = db
    ) -> str:
        try:
            if not db_connection.table_exists(table_name):
                return json.dumps({"error": f"Table '{table_name}' does not exist."})

            # Get sample data with limit
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            results = db_connection.execute_query(query)
            
            return json.dumps([dict(row) for row in results], indent=2, default=str)

        except Exception as e:
            return json.dumps({"error": str(e)})


class GetTableNamesArgs(BaseModel):
    """Arguments for getting all table names from database."""

    schema_name: str = Field(
        default="public",
        description="Database schema name (default: public)."
    )


class GetTableNamesTool(BaseTool):
    """Tool to list all tables in the database."""

    name: str = "get_table_names"
    description: str = (
        "Lists all table names in the specified database schema. "
        "Useful for discovering available tables."
    )
    args_schema: Type[BaseModel] = GetTableNamesArgs

    def _run(
        self, 
        schema_name: str = "public",
        db_connection: DatabaseConnection = db
    ) -> str:
        try:
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """
            results = db_connection.execute_query(query, (schema_name,))
            
            table_names = [row['table_name'] for row in results]
            
            return json.dumps({
                "schema": schema_name,
                "tables": table_names,
                "count": len(table_names)
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})


class AppendToYAMLArgs(BaseModel):
    """Arguments for appending configuration to YAML file."""

    table_name: str = Field(..., description="The table name key for the configuration.")
    config: str = Field(
        ..., 
        description="JSON string containing the configuration to append (with keys: description, fields, task, validations, visualization)."
    )
    yaml_file: str = Field(
        default="src/config/newsletter_v1/structured_data.yaml",
        description="Path to the YAML file to append to."
    )


class AppendToYAMLTool(BaseTool):
    """Tool to append table configuration to structured_data.yaml file."""

    name: str = "append_to_yaml"
    description: str = (
        "Appends a new table configuration to the structured_data.yaml file. "
        "The config should include: description, fields, task, validations, and visualization."
    )
    args_schema: Type[BaseModel] = AppendToYAMLArgs

    def _run(
        self, 
        table_name: str,
        config: str,
        yaml_file: str = "src/config/newsletter_v1/structured_data.yaml"
    ) -> str:
        try:
            # Parse the config JSON
            try:
                config_dict = json.loads(config)
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON config - {str(e)}"

            # Validate required keys
            required_keys = ["description", "fields", "task", "validations", "visualization"]
            missing_keys = [k for k in required_keys if k not in config_dict]
            if missing_keys:
                return f"Error: Missing required keys in config: {missing_keys}"

            # Read existing YAML or create empty dict
            if os.path.exists(yaml_file):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            else:
                existing_data = {}

            # Check if table already exists
            if table_name in existing_data:
                return f"Warning: Table '{table_name}' already exists in {yaml_file}. Configuration not appended."

            # Add new table configuration
            existing_data[table_name] = config_dict

            # Write back to YAML file
            os.makedirs(os.path.dirname(yaml_file), exist_ok=True)
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            return f"Successfully appended configuration for table '{table_name}' to {yaml_file}"

        except Exception as e:
            return f"Error appending to YAML: {str(e)}"

