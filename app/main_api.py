from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.services import process_lead_generation
from typing import Optional

app = FastAPI(title="Lead Gen API", description="API para automação de coleta de leads (n8n/Make)")

class ScrapeRequest(BaseModel):
    query: str
    limit: int = 10
    segment: str
    no_enrich: bool = False
    deep_enrich: bool = False

@app.get("/")
def read_root():
    return {"status": "online", "service": "Lead Intelligence Platform"}

@app.post("/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Triggers a scraping job in the background.
    Returns immediately so n8n doesn't timeout.
    """
    # Run in background because scraping takes time
    background_tasks.add_task(
        process_lead_generation, 
        request.query, 
        request.limit, 
        request.segment, 
        request.no_enrich, 
        request.deep_enrich
    )
    
    return {
        "status": "accepted", 
        "message": f"Scraping started for '{request.query}'",
        "job_details": request.dict()
    }
