from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import Optional

class Lead(BaseModel):
    """
    Represents a business lead scraped from Google Maps or other sources.
    Includes basic verification and enrichment fields.
    """
    name: str
    address: Optional[str] = None
    website: Optional[str] = None  # Kept as str to avoid strict validation errors during scraping
    phone: Optional[str] = None
    source_url: Optional[str] = None
    
    # Enrichment Fields (filled later by AI)
    sector: Optional[str] = None
    employees_estimate: Optional[str] = None
    business_type: Optional[str] = Field(None, description="B2B or B2C")
    
    class Config:
        from_attributes = True
