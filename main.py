import asyncio
import argparse
import pandas as pd
from app.scraper import GoogleMapsScraper
from app.enrichment import LeadEnricher
from app.database import engine, SessionLocal, Base
from app.schema import LeadModel
from dotenv import load_dotenv

load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Lead Intelligence Platform - MVP Concierge")
    parser.add_argument("--query", type=str, required=True, help="Search query (e.g. 'Energia Solar SP')")
    parser.add_argument("--limit", type=int, default=5, help="Number of leads to scrape")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.add_argument("--no-enrich", action="store_true", help="Skip AI enrichment")
    parser.add_argument("--segment", type=str, help="Business segment for database organization (e.g. 'Padaria')")
    
    args = parser.parse_args()
    
    # 0. Setup DB
    if args.segment:
        print("🔌 Connecting to Database...")
        # In production use migrations (Alembic). For MVP, create tables if not exist.
        Base.metadata.create_all(bind=engine)
    
    print(f"🚀 Starting Lead Generation for: '{args.query}' (Limit: {args.limit})")
    
    # 1. Scrape
    scraper = GoogleMapsScraper(headless=args.headless)
    print("Step 1: Scraping Google Maps...")
    leads = await scraper.scrape(args.query, args.limit)
    print(f"✅ Scraped {len(leads)} raw leads.")
    
    # 2. Enrich
    if not args.no_enrich:
        print("Step 2: Enriching with AI...")
        enricher = LeadEnricher()
        if enricher.llm:
            for lead in leads:
                await enricher.enrich(lead)
        else:
            print("⚠️ Skipping enrichment (No API Key found)")
    
    # 3. Export & Save
    print("Step 3: Exporting...")
    
    # Save to CSV
    df = pd.DataFrame([lead.model_dump() for lead in leads])
    filename = f"leads_{args.query.replace(' ', '_')}.csv"
    df.to_csv(filename, index=False)
    print(f"🎉 Saved CSV to {filename}")
    
    # Save to DB
    if args.segment:
        print(f"💾 Saving to Database (Segment: {args.segment})...")
        db = SessionLocal()
        try:
            for lead in leads:
                db_lead = LeadModel(
                    name=lead.name,
                    address=lead.address,
                    website=lead.website,
                    phone=lead.phone,
                    source_url=lead.source_url,
                    sector=lead.sector,
                    employees_estimate=lead.employees_estimate,
                    business_type=lead.business_type,
                    segment=args.segment
                )
                db.add(db_lead)
            db.commit()
            print("✅ Data persisted to AWS Database!")
        except Exception as e:
            print(f"❌ Database Error: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(main())
