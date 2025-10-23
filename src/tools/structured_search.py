"""
Tools for storing and retrieving structured SQL queries and their results.

This module provides CrewAI-compatible tools for:
    - Storing SQL queries as JSON files for reproducibility and auditability
    - Saving and loading structured data results from database queries
    - Supporting agent workflows that require persistent query and result storage

All tools are designed for integration with agent-based pipelines and support
customizable output locations and file naming.
"""

import os
import json
import re

from typing import Type
from pydantic import BaseModel, Field, field_validator
from crewai.tools import BaseTool
from ..database.connection import db, DatabaseConnection


class StoreQueryArgs(BaseModel):
    """Arguments for storing an SQL query in a JSON file."""

    query: str = Field(..., description="The SQL query to store.")
    name: str = Field(
        ..., description="The name for the query file (without extension)."
    )
    folder: str = Field(
        default="output/structured_data/queries",
        description="Folder to store the query JSON file.",
    )


class StoreQueryTool(BaseTool):
    """Tool to store an SQL query in a JSON file."""

    name: str = "store_query"
    description: str = (
        "Stores an SQL query in a JSON file with a 'valid' field and a 'query' field."
    )
    args_schema: Type[BaseModel] = StoreQueryArgs

    def _run(
        self, query: str, name: str, folder: str = "output/structured_data/queries"
    ) -> str:
        os.makedirs(folder, exist_ok=True)

        # returns the valid field empty for later validation
        data = {"table_name": name, "query": query}
        file_path = os.path.join(folder, f"{name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file_path


class QueryDatabaseArgs(BaseModel, arbitrary_types_allowed=True):
    """Arguments for querying the database"""

    query: str = Field(..., description="SQL query to execute on the database")
    table_name: str = Field(..., description="Name of the table to query")

    @field_validator("table_name")
    @classmethod
    def safe_table_name(cls, table_name: str):
        """
        Validate the table name to prevent SQL injection by ensuring it exists in the database.
        """
        if not table_name or not db.table_exists(table_name):
            raise ValueError("Invalid or non-existent table name.")

        return table_name

    @field_validator("query")
    @classmethod
    def safe_query(cls, query: str):
        """
        Validate the SQL query to prevent SQL injection.
        Only allow SELECT statements and reject dangerous keywords.
        """
        # Remove leading/trailing whitespace
        q = query.strip()
        # Only allow SELECT statements
        if not q.lower().startswith("select"):
            raise ValueError("Only SELECT statements are allowed.")
        # Disallow dangerous SQL keywords
        forbidden = [
            r"\binsert\b",
            r"\bupdate\b",
            r"\bdelete\b",
            r"\bdrop\b",
            r"\balter\b",
            r"\btruncate\b",
            r"\bcreate\b",
            r"\bgrant\b",
            r"\brevoke\b",
        ]
        for pattern in forbidden:
            if re.search(pattern, q, re.IGNORECASE):
                raise ValueError("Query contains forbidden SQL keywords.")
        return q


class ExecuteQueryTool(BaseTool):
    """Tool to execute a SQL query and return the results as JSON."""

    name: str = "execute_query"
    description: str = "Executes a SQL query and returns the results as JSON."
    args_schema: Type[BaseModel] = QueryDatabaseArgs

    def _run(
        self,
        query: str,
        table_name: str,
        db_connection: DatabaseConnection = db,
    ) -> str:
        if not db_connection.table_exists(table_name):
            raise ValueError("Table does not exist.")
        try:
            results = db_connection.execute_query(query)
            return json.dumps(results)

        except Exception as e:
            return json.dumps({"error": str(e)})


class StructuredDataStoreArgs(BaseModel):
    """Arguments for storing structured data from a query in a JSON file."""

    table_name: str = Field(..., description="The name of the table to query.")
    query: str = Field(..., description="The SQL query to execute.")
    folder: str = Field(
        default="output/structured_data/data",
        description="Folder to store the result JSON file.",
    )


class StructuredDataStoreTool(BaseTool):
    """Tool to store structured data in a JSON file after executing a query."""

    name: str = "structured_data_store"
    description: str = "Executes a query and stores the result as a JSON file."
    args_schema: Type[BaseModel] = StructuredDataStoreArgs

    def _run(self, **kwargs) -> str:
        table_name = kwargs.get("table_name")
        query = kwargs.get("query")
        folder = kwargs.get("folder", "output/structured_data/data")
        os.makedirs(folder, exist_ok=True)
        # Execute the query using the db connection
        if not db.table_exists(table_name):  # type: ignore
            raise ValueError(f"Table {table_name} does not exist.")
        try:
            results = db.execute_query(query)  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e

        # Store the results as a JSON file
        file_path = os.path.join(folder, f"{table_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        return file_path
