import asyncio
import argparse
import os
import pandas as pd
from playwright.async_api import async_playwright
from app.scraper import GoogleMapsScraper
from app.enrichment import LeadEnricher
from app.scrapers.cnpj import CNPJScraper
from app.database import engine, SessionLocal, Base
from app.schema import Empresa, Contato, LogScraping
from dotenv import load_dotenv

load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Lead Generator & Data Factory")
    parser.add_argument("--query", type=str, required=True, help="Search query (e.g. 'Padaria SP')")
    parser.add_argument("--limit", type=int, default=5, help="Number of leads to scrape")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.add_argument("--no-enrich", action="store_true", help="Skip AI enrichment")
    parser.add_argument("--deep-enrich", action="store_true", help="Enable deep firmographic enrichment (CNPJ, Capital)")
    parser.add_argument("--segment", type=str, help="Business segment for database organization (e.g. 'Padaria')")
    
    args = parser.parse_args()
    
    # 0. Setup DB
    if args.segment:
        print("🔌 Connecting to Database...")
        # In production use migrations (Alembic). For MVP, create tables if not exist.
        # In production use migrations (Alembic). For MVP, create tables if not exist.
        # Base.metadata.create_all(bind=engine) # DISABLED to prevent concurrency locks
        pass
    
    print(f"🚀 Starting Lead Generation for: '{args.query}' (Limit: {args.limit})")
    
    # 1. Scrape
    print(f"Step 1: Scraping Google Maps...")
    scraper = GoogleMapsScraper(headless=args.headless)
    leads = await scraper.scrape(args.query, args.limit)
    print(f"✅ Scraped {len(leads)} raw leads.")
    
    
    # 2. Enrich (AI)
    if not args.no_enrich:
        print("Step 2a: Enriching with AI (Gemini)...")
        enricher = LeadEnricher()
        if enricher.llm:
            leads = await enricher.enrich_leads(leads)
        else:
            print("⚠️ Skipping enrichment (No API Key found)")
    
    # 2b. Enrich (CNPJ)
    if args.deep_enrich:
        print("Step 2b: Deep Enrichment (CNPJ & Firmographics)...")
        cnpj_scraper = CNPJScraper()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Create a context with user agent to avoid detection if possible
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            page = await context.new_page()
            
            for lead in leads:
                # Find URL
                # Use address to extract city
                city = "Brazil"
                if lead.address and "," in lead.address:
                    parts = lead.address.split(",")
                    if len(parts) >= 2:
                        city = parts[-2].strip() # Assuming standard format ... City, State, Country
                
                url = await cnpj_scraper.search_cnpj_url(lead.name, city)
                
                if url:
                    data = await cnpj_scraper.scrape_data(page, url)
                    if data:
                        print(f"   ✅ Found CNPJ for {lead.name}: {data.get('cnpj')}")
                        lead.cnpj = data.get('cnpj')
                        lead.capital_social = data.get('capital_social')
                        # Prefer official name if found
                        if data.get('razao_social'):
                            lead.name = data.get('razao_social')
                else:
                    print(f"   ⚠️ CNPJ not found for {lead.name}")
            
            await browser.close()

    
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
            # Create Audit Log
            log = LogScraping(
                url_origem="Google Maps",
                status_extracao="Sucesso",
                termo_busca=args.query,
                ferramenta_usada="GoogleMapsScraper"
            )
            db.add(log)
            db.commit()
            
            count_new = 0
            for lead in leads:
                # 1. Create/Check Company
                # Simple check by name for now. In prod, check CNPJ or Site.
                existing_company = db.query(Empresa).filter(Empresa.razao_social == lead.name).first()
                
                if not existing_company:
                    empresa = Empresa(
                        razao_social=lead.name,
                        nome_fantasia=lead.name,
                        site_url=lead.source_url, # Source URL for now, website if enriched
                        setor_cnae=lead.sector,
                        tamanho_colaboradores=lead.employees_estimate,
                        cidade=lead.address, # Basic mapping
                        segmento_mercado=args.segment,
                        cnpj=lead.cnpj,
                        faturamento_estimado=lead.capital_social
                    )
                    db.add(empresa)
                    db.flush() # Get ID
                    company_id = empresa.empresa_id
                    count_new += 1
                else:
                    company_id = existing_company.empresa_id
                
                # 2. Add Contact (Lead Name usually is the business name on Maps, but if we enriched...)
                # If enriched, lead.name might be the person? No, scraper gets Business Name.
                # So we associate the business. Contact info is scarce on Maps.
                # But if we have phone/email:
                if lead.phone or lead.website:
                     contato = Contato(
                         empresa_id=company_id,
                         nome_completo="Contato Geral", # Placeholder
                         telefone_direto=lead.phone,
                         email_corporativo=None # Maps doesn't give email easily
                     )
                     db.add(contato)

            db.commit()
            print(f"✅ Data persisted! ({count_new} new companies added)")
        except Exception as e:
            print(f"❌ Database Error: {e}")
            db.rollback()
            # Log failure
            fail_log = LogScraping(
                url_origem="Google Maps", 
                status_extracao=f"Erro: {str(e)}"[:50], 
                termo_busca=args.query
            )
            db.add(fail_log)
            db.commit()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(main())
