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
    
    # 2b. Enrich (CNPJ via ReceitaWS + Website Contacts)
    if deep_enrich:
        print("Step 2b: Deep Enrichment (ReceitaWS + Website Contacts)...")
        from app.scrapers.contacts import ContactScraper
        from app.scrapers.receita_ws import ReceitaWSClient
        from app.scrapers.cnpj import CNPJScraper
        
        contact_scraper = ContactScraper()
        receita_client = ReceitaWSClient()
        cnpj_finder = CNPJScraper()  # Still used to FIND CNPJ via DuckDuckGo
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            scrape_page = await context.new_page()

            for lead in leads:
                # 1. Contact Scraping (Website)
                if lead.source_url and lead.source_url.startswith("http"):
                    contact_info = await contact_scraper.scrape_contacts(scrape_page, lead.source_url)
                    if contact_info["email"]:
                        print(f"    📧 Email found for {lead.name}: {contact_info['email']}")
                        lead.email = contact_info["email"] 
                    if contact_info["phone"]:
                        lead.phone = contact_info["phone"]

                # 2. Find CNPJ via DuckDuckGo (if not already known)
                if not getattr(lead, 'cnpj', None):
                    city = "Brazil"
                    if lead.address and "," in lead.address:
                        parts = lead.address.split(",")
                        if len(parts) >= 2:
                            city = parts[-2].strip()
                    
                    url = await cnpj_finder.search_cnpj_url(lead.name, city)
                    if url:
                        # Extract CNPJ from CNPJ.biz URL (format: cnpj.biz/00000000000000)
                        cnpj_from_url = url.split("/")[-1].replace("-", "").replace(".", "").replace("/", "")
                        if len(cnpj_from_url) == 14:
                            lead.cnpj = cnpj_from_url
                
                # 3. Fetch full data from ReceitaWS (if we have CNPJ)
                if getattr(lead, 'cnpj', None):
                    receita_data = await receita_client.fetch(lead.cnpj)
                    if receita_data:
                        # Attach all ReceitaWS data to lead object
                        lead.razao_social = receita_data.get('nome')
                        lead.nome_fantasia = receita_data.get('fantasia')
                        lead.atividade_principal = receita_client.extract_atividade(receita_data)
                        lead.porte = receita_data.get('porte')
                        lead.natureza_juridica = receita_data.get('natureza_juridica')
                        lead.data_abertura = receita_data.get('abertura')
                        lead.situacao_cadastral = receita_data.get('situacao')
                        lead.capital_social = receita_data.get('capital_social')
                        lead.telefone_empresa = receita_data.get('telefone')
                        lead.email_empresa = receita_data.get('email')
                        lead.socios = receita_client.extract_socios(receita_data)
                        
                        # Build complete address
                        endereco_parts = [
                            receita_data.get('logradouro', ''),
                            receita_data.get('numero', ''),
                            receita_data.get('bairro', ''),
                            receita_data.get('municipio', ''),
                            receita_data.get('uf', '')
                        ]
                        lead.endereco_completo = ", ".join([p for p in endereco_parts if p])
                        lead.cidade = receita_data.get('municipio')
                        lead.estado = receita_data.get('uf')
            
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
                # Get enriched fields from lead (attached during deep_enrich)
                nome_fantasia = getattr(lead, 'nome_fantasia', None) or lead.name
                atividade_principal = getattr(lead, 'atividade_principal', None)
                razao_social = getattr(lead, 'razao_social', None) or lead.name
                
                # Use ReceitaWS cidade/estado if available, otherwise parse from Google Maps
                cidade = getattr(lead, 'cidade', None)
                estado = getattr(lead, 'estado', None)
                
                if not cidade and lead.address and "," in lead.address:
                    parts = [p.strip() for p in lead.address.split(",")]
                    for part in reversed(parts):
                        if " - " in part:
                            cidade_estado = part.split(" - ")
                            cidade = cidade_estado[0].strip()
                            if len(cidade_estado) > 1:
                                estado = cidade_estado[1].strip()[:2].upper()
                            break
                
                empresa = Empresa(
                    razao_social=razao_social,
                    nome_fantasia=nome_fantasia,
                    site_url=lead.source_url,
                    setor_cnae=atividade_principal or lead.sector,
                    tamanho_colaboradores=lead.employees_estimate,
                    cidade=cidade,
                    estado=estado,
                    segmento_mercado=segment,
                    cnpj=getattr(lead, 'cnpj', None),
                    # New ReceitaWS fields
                    porte=getattr(lead, 'porte', None),
                    natureza_juridica=getattr(lead, 'natureza_juridica', None),
                    data_abertura=getattr(lead, 'data_abertura', None),
                    situacao_cadastral=getattr(lead, 'situacao_cadastral', None),
                    capital_social=getattr(lead, 'capital_social', None),
                    telefone_empresa=getattr(lead, 'telefone_empresa', None),
                    email_empresa=getattr(lead, 'email_empresa', None),
                    endereco_completo=getattr(lead, 'endereco_completo', None)
                )
                db.add(empresa)
                db.flush()
                company_id = empresa.empresa_id
                count_new += 1
                
                # Create Socio records from QSA data
                socios = getattr(lead, 'socios', [])
                from app.schema import Socio
                for socio_data in socios:
                    if socio_data.get('nome'):
                        socio = Socio(
                            empresa_id=company_id,
                            nome_completo=socio_data.get('nome'),
                            cargo=socio_data.get('cargo')
                        )
                        db.add(socio)
            else:
                company_id = existing_company.empresa_id
            
            # Check for email attached during Deep Enrich
            lead_email = getattr(lead, 'email', None)

            if lead.phone or lead.website or lead_email:
                    contato = Contato(
                        empresa_id=company_id,
                        nome_completo="Contato Geral",
                        telefone_direto=lead.phone,
                        email_corporativo=lead_email
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
