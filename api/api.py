from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import time
from pathlib import Path
import uvicorn

# Add the project root to the sys.path to allow imports from 'src'
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from api.logger import get_logger, log_startup, log_shutdown
from api.routers.newsletter_routers import router as newsletter_router
from api.routers.etl_routers import router as etl_router
from src.database.init_api_db import initialize_database

# Initialize logger
logger = get_logger(__name__)

def wait_for_database(max_retries=30, delay=2):
    """Wait for database to be ready with retries."""
    from src.database.connection import db
    logger.info("Waiting for database to be ready...")
    for attempt in range(max_retries):
        try:
            # Test database connection
            result = db.execute_query("SELECT 1")
            if result:
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error("Database not available after maximum retries")
                raise Exception("Database connection failed")
    
    return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    try:
        log_startup("AIS Masterclass Newsletter API", "1.0.0", 8000)
        
        # Wait for database to be ready
        wait_for_database()
        
        # Initialize database tables
        initialize_database()
        
        logger.info("✓ API started successfully and ready to accept requests")
    except Exception as e:
        logger.error(f"✗ Failed to start API: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    log_shutdown("AIS Masterclass Newsletter API")

app = FastAPI(
    title="AIS Masterclass Newsletter API",
    description="API for generating and managing newsletters",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(newsletter_router)
app.include_router(etl_router)

@app.get("/")
def read_root():
    return {"message": "AIS Masterclass Newsletter API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "newsletter-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=True)