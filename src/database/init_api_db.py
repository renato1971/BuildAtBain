import logging
from .connection import db

logger = logging.getLogger(__name__)

def create_newsletters_table():
    """Create newsletters table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS newsletters (
        id SERIAL PRIMARY KEY,
        topic TEXT NOT NULL,
        final_html TEXT,
        created_on TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_newsletters_created_on ON newsletters(created_on DESC);
    CREATE INDEX IF NOT EXISTS idx_newsletters_topic ON newsletters(topic);
    """
    
    try:
        db.execute_script(create_table_sql)
        logger.info("Newsletter table created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating newsletter table: {str(e)}")
        raise

def initialize_database():
    """Initialize all database tables."""
    try:
        logger.info("Starting database initialization...")
        
        # Check if table already exists
        if db.table_exists('newsletters'):
            logger.info("Newsletter table already exists")
        else:
            create_newsletters_table()
            logger.info("Newsletter table created")
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    initialize_database()