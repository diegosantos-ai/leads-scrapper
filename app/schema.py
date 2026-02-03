from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    
    # Enrichment Fields
    sector = Column(String, nullable=True)
    employees_estimate = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    
    # Organization
    segment = Column(String, index=True, nullable=True) # e.g. "Padaria", "Marketing"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    enrichment_data = Column(JSON, nullable=True) # Store raw AI response
