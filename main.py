import asyncio
import argparse
import pandas as pd
from app.scraper import GoogleMapsScraper
from app.enrichment import LeadEnricher
from dotenv import load_dotenv

load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Lead Intelligence Platform - MVP Concierge")
    parser.add_argument("--query", type=str, required=True, help="Search query (e.g. 'Energia Solar SP')")
    parser.add_argument("--limit", type=int, default=5, help="Number of leads to scrape")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.add_argument("--no-enrich", action="store_true", help="Skip AI enrichment")
    
    args = parser.parse_args()
    
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
    
    # 3. Export
    print("Step 3: Exporting to CSV...")
    df = pd.DataFrame([lead.model_dump() for lead in leads])
    filename = f"leads_{args.query.replace(' ', '_')}.csv"
    df.to_csv(filename, index=False)
    print(f"🎉 Done! Saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
