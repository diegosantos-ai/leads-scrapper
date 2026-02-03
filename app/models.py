from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import Optional, List

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

    # Firmographic Data (Phase 3)
    cnpj: Optional[str] = None
    capital_social: Optional[str] = None
    socios: Optional[List[str]] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
