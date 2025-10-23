from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsletterRequest(BaseModel):
    """Schema to create a newsletter generation request."""
    newsletter_topic: str = Field(..., example="Inflación en Brasil y su impacto en las pequeñas empresas")
    query: Optional[str] = Field(None, example="Taxa de água e esgoto no cálculo do IPCA")
    language: Optional[str] = Field(default="es-CL", example="es-CL")

class NewsletterResponse(BaseModel):
    """Response schema for newsletter generation"""
    html_content: str = Field(..., description="Generated HTML content")

class NewsletterSaveRequest(BaseModel):
    """Schema to save a new newsletter."""
    topic: str = Field(..., example="Newsletter Topic")
    html_content: Optional[str] = Field(None, example="<html>Content</html>")
class NewsletterUpdateRequest(BaseModel):
    """Schema to update an existing newsletter."""
    html_content: Optional[str] = Field(None, example="<html>...</html>")

class NewsletterListItem(BaseModel):
    """Schema for newsletter list items"""
    id: int = Field(..., description="Newsletter ID")
    topic: str = Field(..., description="Newsletter topic")
    created_on: datetime = Field(..., description="Creation timestamp")

class NewsletterListResponse(BaseModel):
    """Response schema for newsletter list"""
    newsletters: List[NewsletterListItem] = Field(..., description="List of newsletters")

class NewsletterDetailResponse(BaseModel):
    """Response schema for newsletter details"""
    id: int = Field(..., description="Newsletter ID")
    topic: str = Field(..., description="Newsletter topic")
    html_content: str = Field(..., description="Newsletter HTML content")
    created_on: datetime = Field(..., description="Creation timestamp")