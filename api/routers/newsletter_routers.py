from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import sys
from pathlib import Path
from io import BytesIO
import re
from weasyprint import HTML
from src.schemas.newsletter_schema import (
    NewsletterRequest, 
    NewsletterResponse, 
    NewsletterSaveRequest,
    NewsletterUpdateRequest,
    NewsletterListResponse,
    NewsletterDetailResponse,
    NewsletterListItem
)
import base64, mimetypes

# Add the project root to the sys.path to allow imports from 'src'
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from api.logger import get_logger, log_error
from src.agents.newsletter_crew_v1.crew import NewsletterCrew
from src.utils.make_output_folders import create_output_folders
from src.services.newsletter_service import NewsletterService

# Initialize logger
logger = get_logger(__name__)

router = APIRouter(
    prefix="/newsletter",
    tags=["Newsletter"],
)

@router.post("/generate", response_model=NewsletterResponse)
def generate_newsletter(request: NewsletterRequest):
    """
    Initiate the newsletter generation process with the given topic, query, and language.
    """
    try:
        crew = NewsletterCrew().crew()

        api_output_folder = Path(__file__).resolve().parents[2] / "output"
        
        # Ensure output folder exists with proper permissions
        try:
            api_output_folder.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = api_output_folder / ".test_write"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Cannot access output folder: {str(e)}"
            )
        
        create_output_folders(api_output_folder)

        result = crew.kickoff(
            inputs={
                "newsletter_topic": request.newsletter_topic,
                "output_folder": str(api_output_folder),
                "query": request.query,
                "language": request.language,
            }
        )

        # Fix image paths for API endpoint (using full backend URL)
        html_content_api = str(result).replace(
            'src="/output/',
            'src="http://localhost:8000/newsletter/assets/'
        ).replace(
            'src="output/',
            'src="http://localhost:8000/newsletter/assets/'
        )
        
        # Fix image paths for local file viewing (relative paths without leading slash)
        html_content_local = str(result).replace(
            'src="/output/',
            'src="'
        ).replace(
            'src="output/',
            'src="'
        )
        output_html_path = api_output_folder / "newsletter.html" 
        output_html_path.write_text(html_content_local, encoding="utf-8")

        return {"html_content": html_content_api}

    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context="Newsletter generation failed")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/assets/{file_path:path}")
def get_asset(file_path: str):
    """Serve static assets (images, charts, etc.) from output folder."""
    api_output_folder = Path(__file__).resolve().parents[2] / "output"
    asset_path = api_output_folder / file_path
    
    if not asset_path.exists() or not asset_path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return FileResponse(asset_path)

@router.post("/save")
def save_newsletter(request: NewsletterSaveRequest):
    """Save newsletter content to database."""
    try:
        newsletter_id = NewsletterService.save_newsletter(
            topic=request.topic,
            html_content=request.html_content
        )
        return {"id": newsletter_id, "message": "Newsletter saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving newsletter: {str(e)}")

@router.get("/list", response_model=NewsletterListResponse)
def list_newsletters():
    """List all newsletters."""
    try:
        newsletters_data = NewsletterService.list_newsletters()
        newsletters = [
            NewsletterListItem(
                id=item['id'],
                topic=item['topic'],
                created_on=item['created_on']
            ) for item in newsletters_data
        ]
        return {"newsletters": newsletters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing newsletters: {str(e)}")

@router.get("/{newsletter_id}", response_model=NewsletterDetailResponse)
def get_newsletter(newsletter_id: int):
    """Get newsletter by ID."""
    try:
        newsletter = NewsletterService.get_newsletter_by_id(newsletter_id)
        if not newsletter:
            raise HTTPException(status_code=404, detail="Newsletter not found")
        
        return NewsletterDetailResponse(
            id=newsletter['id'],
            topic=newsletter['topic'],
            html_content=newsletter['final_html'],
            created_on=newsletter['created_on']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting newsletter: {str(e)}")

@router.put("/{newsletter_id}")
def update_newsletter(newsletter_id: int, request: NewsletterUpdateRequest):
    """Update newsletter content."""
    try:
        success = NewsletterService.update_newsletter(newsletter_id, request.html_content)
        if not success:
            raise HTTPException(status_code=404, detail="Newsletter not found")
        
        return {"message": "Newsletter updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating newsletter: {str(e)}")

@router.get("/{newsletter_id}/export-pdf")
async def export_newsletter_pdf(newsletter_id: int):
    """Export newsletter as PDF using WeasyPrint."""
    logger.info(f"Starting PDF export for newsletter {newsletter_id}")
    
    try:
        # Fetch newsletter from database
        newsletter = NewsletterService.get_newsletter_by_id(newsletter_id)
        if not newsletter:
            logger.warning(f"Newsletter {newsletter_id} not found")
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "Newsletter Not Found",
                    "message": f"Newsletter with ID {newsletter_id} does not exist",
                    "newsletter_id": newsletter_id
                }
            )
        
        # Get HTML content
        html_content = newsletter.get('final_html')
        if not html_content:
            logger.error(f"Newsletter {newsletter_id} has no HTML content")
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "No HTML Content",
                    "message": "Newsletter exists but has no HTML content to export",
                    "newsletter_id": newsletter_id
                }
            )
    
        # Replace image URLs so WeasyPrint can access them using relative paths + base_url
        output_folder = Path("/app/output")
        prefix = "http://localhost:8000/newsletter/assets/"
        html_for_pdf = html_content

        def normalize_src(match):
            src = match.group(1)
            if src.startswith(prefix):
                rel = src[len(prefix):]  # strip prefix -> relative path
                return f'src="{rel}"'
            return f'src="{src}"'

        html_for_pdf = re.sub(r'src="([^"]+)"', normalize_src, html_for_pdf)

        # Collect image sources
        img_sources = re.findall(r'<img[^>]+src="([^"]+)"', html_for_pdf)
        missing = []
        for src in img_sources:
            if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
                continue
            img_path = (output_folder / src).resolve()
            if img_path.exists():
                try:
                    size = img_path.stat().st_size
                    logger.info(f"Image OK: {src} (bytes={size})")
                except Exception:
                    logger.info(f"Image OK (size unknown): {src}")
            else:
                logger.warning(f"Image missing: {src}")
                missing.append(src)

        # Fallback: embed missing images (if they actually appear later after generation delay)
        def embed_local(match):
            src = match.group(1)
            if src in missing:
                p = (output_folder / src).resolve()
                if p.exists():
                    mime, _ = mimetypes.guess_type(str(p))
                    if not mime:
                        mime = "application/octet-stream"
                    try:
                        b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
                        logger.info(f"Embedding image as data URI: {src}")
                        return f'src="data:{mime};base64,{b64}"'
                    except Exception as e:
                        logger.error(f"Failed embedding {src}: {e}")
            return match.group(0)

        if missing:
            html_for_pdf = re.sub(r'src="([^"]+)"', embed_local, html_for_pdf)

        logger.info(f"Final HTML (first 800 chars): {html_for_pdf[:800]}")
        # Create filename
        safe_topic = "".join(c for c in newsletter['topic'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"newsletter_{newsletter_id}_{safe_topic[:50]}.pdf"
        
        # Generate PDF using WeasyPrint
        logger.info(f"Generating PDF for newsletter {newsletter_id}")
        
        try:
            # Create PDF in memory
            pdf_buffer = BytesIO()
            HTML(string=html_for_pdf, base_url=str(output_folder)).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            logger.info(f"✓ Successfully generated PDF for newsletter {newsletter_id}")
            
            # Return PDF as streaming response
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Newsletter-ID": str(newsletter_id)
                }
            )
            
        except Exception as pdf_error:
            logger.error(f"PDF generation failed: {str(pdf_error)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "PDF Generation Failed",
                    "message": "Failed to convert HTML to PDF",
                    "newsletter_id": newsletter_id,
                    "error_details": str(pdf_error)
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context=f"Unexpected error exporting newsletter {newsletter_id} to PDF")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PDF Export Failed",
                "message": "An unexpected error occurred while exporting the newsletter to PDF",
                "newsletter_id": newsletter_id,
                "error_details": str(e)
            }
        )

@router.delete("/{newsletter_id}")
def delete_newsletter(newsletter_id: int):
    """Delete newsletter by ID."""
    try:
        success = NewsletterService.delete_newsletter(newsletter_id)
        if not success:
            raise HTTPException(status_code=404, detail="Newsletter not found")
        
        return {"message": "Newsletter deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting newsletter: {str(e)}")