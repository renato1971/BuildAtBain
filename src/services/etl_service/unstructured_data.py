#!/usr/bin/env python3
"""
Simple PDF to Weaviate ETL
Reads PDFs, converts pages to images, summarizes with OpenAI, stores in Weaviate
"""
from pathlib import Path
import os, sys, logging, base64, urllib.parse

#import fitz
import pymupdf as fitz
from openai import OpenAI
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))
load_dotenv(project_root / ".env", override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _connect_weaviate():
    # To run script locally with uv run use WEAVIATE_URL=http://localhost:8080 in .env
    # To run with docker compose use WEAVIATE_URL=http://weaviate:8080 in .env
    url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    logger.info(f"Usando WEAVIATE_URL={url}")
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    secure = parsed.scheme == "https"
    try:
        client = weaviate.connect_to_custom(
            http_host=host,
            http_port=port,
            http_secure=secure,
            grpc_host=host,
            grpc_port=50051,
            grpc_secure=secure
        )
        # Simple readiness check
        client.collections.list_all()  # triggers a request
        return client
    except Exception as e:
        raise RuntimeError(f"Connection to Weaviate failed. Details: {e}. (Host={host} Port={port} Secure={secure})")

class PDFToWeaviate:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY não definido; resumo será pulado.")
        self.openai_client = OpenAI(api_key=api_key) if api_key else None
        self.weaviate_client = _connect_weaviate()
        self.setup_schema()

    def setup_schema(self):
        """Create or update Weaviate schema"""
        try:
            if self.weaviate_client.collections.exists("PDFDocument"):
                logger.info("PDFDocument collection already exists")
                return
            self.weaviate_client.collections.create(
                name="PDFDocument",
                properties=[
                    Property(name="filename", data_type=DataType.TEXT),
                    Property(name="page_number", data_type=DataType.INT),
                    Property(name="text_content", data_type=DataType.TEXT),
                    Property(name="summary", data_type=DataType.TEXT),
                    Property(name="file_path", data_type=DataType.TEXT),
                    Property(name="total_pages", data_type=DataType.INT),
                ],
                vectorizer_config=Configure.Vectorizer.none()
            )
            logger.info("Created PDFDocument collection")
        except Exception as e:
            logger.error(f"Error setting up schema: {e}")
            raise

    def pdf_page_to_image(self, page) -> bytes:
        """Convert PDF page to PNG image bytes"""
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        return pix.tobytes("png")

    def summarize_page_with_openai(self, image_bytes: bytes, text_content: str) -> str:
        if not self.openai_client:
            return "Is not possible to summarize, missing OPEN API key."
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Summarize this PDF page in Portuguese. Focus on key information, data, charts, and tables. Text extracted: {text_content[:500]}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating summary: {str(e)}"

    def process_pdf(self, pdf_path: Path):
        """Process a single PDF file and save pages incrementally"""
        logger.info(f"Processing: {pdf_path.name}")

        doc = fitz.open(pdf_path)
        collection = self.weaviate_client.collections.get("PDFDocument")
        total_pages = len(doc)

        for page_num in range(total_pages):
            page = doc[page_num]
            text_content = page.get_text()
            image_bytes = self.pdf_page_to_image(page)
            summary = self.summarize_page_with_openai(image_bytes, text_content)

            page_data = {
                "filename": pdf_path.name,
                "page_number": page_num + 1,
                "text_content": text_content,
                "summary": summary,
                "file_path": str(pdf_path),
                "total_pages": total_pages
            }

            collection.data.insert(properties=page_data)
            logger.info(f"  ✓ Page {page_num + 1}/{total_pages} saved")

        doc.close()
        logger.info(f"Completed {pdf_path.name}: {total_pages} pages")

    def run(self, pdf_dir: Path):
        """Main ETL process"""
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return

        logger.info(f"Found {len(pdf_files)} PDF files")

        for pdf_file in pdf_files:
            try:
                self.process_pdf(pdf_file)
            except Exception as e:
                logger.error(f"✗ Failed {pdf_file.name}: {e}")

        logger.info("PDF processing complete!")

    def close(self):
        """Close connections"""
        self.weaviate_client.close()

def main(raw_dir: Path | None = None):
    
    if raw_dir is None:
        env_dir = os.getenv("RAW_DATA_DIR")
        if env_dir:
            raw_dir = Path(env_dir).expanduser().resolve()
        else:
            raw_dir = project_root / "data" / "raw"

    logger.info("=" * 50)
    logger.info("PDF TO WEAVIATE ETL")
    logger.info(f"Raw data directory: {raw_dir}")
    logger.info("=" * 50)

    if not raw_dir.exists() or not raw_dir.is_dir():
        logger.error(f"Raw data directory does not exist or is not a directory: {raw_dir}")
        return
    
    if not any(raw_dir.glob("*.pdf")):
        logger.warning(f"No PDF files found in the directory: {raw_dir}")
        return

    etl = PDFToWeaviate()
    try:
        etl.run(raw_dir)
    finally:
        etl.close()

    logger.info("=" * 50)
    logger.info("ETL COMPLETE")
    logger.info("=" * 50)

if __name__ == "__main__":
    cli_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    main(cli_dir)