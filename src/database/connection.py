import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
import os
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import json
import logging
from dotenv import load_dotenv

# Load .env file but don't override existing environment variables
# This allows Docker environment variables to take precedence
load_dotenv(".env", override=False)
os.getenv("POSTGRES_PASSWORD")

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """PostgreSQL database connection manager with connection pooling"""
    
    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            db_config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': os.getenv('POSTGRES_PORT', 5432),
                'database': os.getenv('POSTGRES_DB', 'newsletter_db'),
                'user': os.getenv('POSTGRES_USER', 'bain'),
                'password': os.getenv('POSTGRES_PASSWORD', 'bain')
            }
            
            self.connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **db_config
            )
            
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE command and return affected rows"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(command, params)
                conn.commit()
                return cursor.rowcount
    
    def execute_script(self, script: str) -> None:
        """Execute SQL script (multiple statements)"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(script)
                conn.commit()
                logger.info("SQL script executed successfully")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
        """
        result = self.execute_query(query, (table_name,))
        return result[0]['exists'] if result else False
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
        """
        return self.execute_query(query, (table_name,))
    
    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]]) -> int:
        """Bulk insert data using execute_values for better performance"""
        if not data:
            return 0
        
        columns = list(data[0].keys())
        values = [[row[col] for col in columns] for row in data]
        
        # Create columns string
        columns_str = ','.join(columns)
        
        # For execute_values, we need a template with VALUES %s
        insert_query = f"""
        INSERT INTO {table_name} ({columns_str}) 
        VALUES %s
        ON CONFLICT DO NOTHING
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                psycopg2.extras.execute_values(
                    cursor, insert_query, values, template=None, page_size=1000
                )
                conn.commit()
                affected_rows = cursor.rowcount
                logger.info(f"Inserted {affected_rows} rows into {table_name}")
                return affected_rows
    
    def close_pool(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

# Global database instance
db = DatabaseConnection()