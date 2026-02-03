import asyncio
import pandas as pd
from app.scraper import GoogleMapsScraper
from app.enrichment import LeadEnricher
from app.scrapers.cnpj import CNPJScraper
from app.database import engine, SessionLocal, Base
from app.schema import Empresa, Contato, LogScraping
from playwright.async_api import async_playwright

async def process_lead_generation(query: str, limit: int, segment: str, no_enrich: bool = False, deep_enrich: bool = False):
    """
    Core function to execute the scraping pipeline.
    Identical logic to main.py but callable.
    """
    print(f"🚀 Starting Lead Generation for: '{query}' (Limit: {limit})")
    
    # 1. Scrape
    print("Step 1: Scraping Google Maps...")
    scraper = GoogleMapsScraper(headless=True)
    leads = await scraper.scrape(query, limit)
    print(f"✅ Scraped {len(leads)} raw leads.")
    
    if not leads:
        print("⚠️ No leads found.")
        return {"status": "success", "leads_found": 0, "message": "No leads found"}

    # 2. Enrich (AI)
    if not no_enrich:
        print("Step 2a: Enriching with AI (Gemini)...")
        enricher = LeadEnricher()
        if enricher.llm:
            leads = await enricher.enrich_leads(leads)
        else:
            print("⚠️ Skipping enrichment (No API Key found)")
    
    # 2b. Enrich (CNPJ)
    if deep_enrich:
        print("Step 2b: Deep Enrichment (CNPJ & Firmographics)...")
        cnpj_scraper = CNPJScraper()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            page = await context.new_page()
            
            for lead in leads:
                city = "Brazil"
                if lead.address and "," in lead.address:
                    parts = lead.address.split(",")
                    if len(parts) >= 2:
                        city = parts[-2].strip()
                
                url = await cnpj_scraper.search_cnpj_url(lead.name, city)
                
                if url:
                    data = await cnpj_scraper.scrape_data(page, url)
                    if data:
                        lead.cnpj = data.get('cnpj')
                        lead.capital_social = data.get('capital_social')
                        if data.get('razao_social'):
                            lead.name = data.get('razao_social')
            
            await browser.close()

    # 3. Save to DB
    print(f"💾 Saving to Database (Segment: {segment})...")
    db = SessionLocal()
    try:
        # Create Audit Log
        log = LogScraping(
            url_origem="Google Maps",
            status_extracao="Sucesso",
            termo_busca=query,
            ferramenta_usada="GoogleMapsScraper"
        )
        db.add(log)
        db.commit()
        
        count_new = 0
        for lead in leads:
            existing_company = db.query(Empresa).filter(Empresa.razao_social == lead.name).first()
            
            if not existing_company:
                empresa = Empresa(
                    razao_social=lead.name,
                    nome_fantasia=lead.name,
                    site_url=lead.source_url,
                    setor_cnae=lead.sector,
                    tamanho_colaboradores=lead.employees_estimate,
                    cidade=lead.address,
                    segmento_mercado=segment,
                    cnpj=lead.cnpj,
                    faturamento_estimado=lead.capital_social
                )
                db.add(empresa)
                db.flush()
                company_id = empresa.empresa_id
                count_new += 1
            else:
                company_id = existing_company.empresa_id
            
            if lead.phone or lead.website:
                    contato = Contato(
                        empresa_id=company_id,
                        nome_completo="Contato Geral",
                        telefone_direto=lead.phone,
                        email_corporativo=None
                    )
                    db.add(contato)

        db.commit()
        print(f"✅ Data persisted! ({count_new} new companies added)")
        return {"status": "success", "leads_found": len(leads), "new_companies": count_new}
        
    except Exception as e:
        print(f"❌ Database Error: {e}")
        db.rollback()
        fail_log = LogScraping(
            url_origem="Google Maps", 
            status_extracao=f"Erro: {str(e)}"[:50], 
            termo_busca=query
        )
        db.add(fail_log)
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
