from typing import List, Optional
import logging
from src.database.connection import db

logger = logging.getLogger(__name__)

class NewsletterService:
    
    @staticmethod
    def save_newsletter(topic: str, html_content: str) -> int:
        """Save a new newsletter and return its ID."""
        query = """
        INSERT INTO newsletters (topic, final_html) 
        VALUES (%s, %s) 
        RETURNING id
        """
        try:
            from src.database.connection import db
            with db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (topic, html_content))
                    newsletter_id = cursor.fetchone()[0]  # fetch RETURNING id
                    conn.commit()
            logger.info(f"Newsletter saved successfully with ID: {newsletter_id}")
            return newsletter_id
        except Exception as e:
            logger.error(f"Error saving newsletter: {str(e)}")
            raise
    
    @staticmethod
    def get_newsletter_by_id(newsletter_id: int) -> Optional[dict]:
        """Get newsletter by ID."""
        query = """
        SELECT id, topic, final_html, created_on 
        FROM newsletters 
        WHERE id = %s
        """
        try:
            result = db.execute_query(query, (newsletter_id,))
            if result:
                logger.info(f"Newsletter {newsletter_id} retrieved successfully")
                return result[0]
            else:
                logger.warning(f"Newsletter {newsletter_id} not found")
                return None
        except Exception as e:
            logger.error(f"Error getting newsletter {newsletter_id}: {str(e)}")
            raise
    
    @staticmethod
    def update_newsletter(newsletter_id: int, html_content: str) -> bool:
        """Update newsletter HTML content."""
        query = """
        UPDATE newsletters 
        SET final_html = %s 
        WHERE id = %s
        """
        try:
            affected_rows = db.execute_command(query, (html_content, newsletter_id))
            success = affected_rows > 0
            if success:
                logger.info(f"Newsletter {newsletter_id} updated successfully")
            else:
                logger.warning(f"Newsletter {newsletter_id} not found for update")
            return success
        except Exception as e:
            logger.error(f"Error updating newsletter {newsletter_id}: {str(e)}")
            raise
    
    @staticmethod
    def list_newsletters() -> List[dict]:
        """List all newsletters."""
        query = """
        SELECT id, topic, created_on 
        FROM newsletters 
        ORDER BY created_on DESC
        """
        try:
            result = db.execute_query(query)
            logger.info(f"Retrieved {len(result)} newsletters")
            return result
        except Exception as e:
            logger.error(f"Error listing newsletters: {str(e)}")
            raise
    
    @staticmethod
    def delete_newsletter(newsletter_id: int) -> bool:
        """Delete newsletter by ID."""
        query = "DELETE FROM newsletters WHERE id = %s"
        try:
            affected_rows = db.execute_command(query, (newsletter_id,))
            success = affected_rows > 0
            if success:
                logger.info(f"Newsletter {newsletter_id} deleted successfully")
            else:
                logger.warning(f"Newsletter {newsletter_id} not found for deletion")
            return success
        except Exception as e:
            logger.error(f"Error deleting newsletter {newsletter_id}: {str(e)}")
            raise