import asyncio
from typing import Optional, Dict
from duckduckgo_search import DDGS
from playwright.async_api import Page, BrowserContext

class CNPJScraper:
    def __init__(self):
        self.ddgs = DDGS()

    async def search_cnpj_url(self, company_name: str, city: str) -> Optional[str]:
        """Finds the best CNPJ.biz URL for the company"""
        query = f"site:cnpj.biz {company_name} {city}"
        print(f"   🔍 Searching CNPJ for: {query}")
        
        try:
            results = self.ddgs.text(query, max_results=1)
            if results:
                return results[0]['href']
        except Exception as e:
            print(f"   ❌ Search Error: {e}")
        return None

    async def scrape_data(self, page: Page, url: str) -> Dict:
        """Extracts data from CNPJ.biz page"""
        print(f"   🌐 Opening: {url}")
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            
            # Extract basic data using reliable selectors or text search
            # CNPJ.biz structure is usually simple lists
            
            data = {}
            
            # 1. CNPJ & Razao Social (Usually in H1 or H2)
            # Standard: "Empresa Razao Social (CNPJ: 00.000...)"
            title = await page.title()
            data['meta_title'] = title
            
            # 2. Extract specific fields by looking for strong tags
            # Example: <strong>Capital Social:</strong> R$ 10.000,00
            
            # Helper to get text by label
            async def get_by_label(label: str):
                return await page.evaluate(f'''(label) => {{
                    const elements = Array.from(document.querySelectorAll('p, li, div'));
                    const found = elements.find(el => el.textContent.includes(label));
                    return found ? found.textContent.split(label)[1].trim() : null;
                }}''', label)

            data['cnpj'] = await get_by_label("CNPJ:")
            data['capital_social'] = await get_by_label("Capital Social:")
            data['razao_social'] = await page.evaluate("document.querySelector('h1') ? document.querySelector('h1').textContent : ''")
            data['nome_fantasia'] = await get_by_label("Nome Fantasia:")
            data['atividade_principal'] = await get_by_label("Atividade Principal:")
            
            # Cleaning
            if data['cnpj']:
                data['cnpj'] = data['cnpj'].split(" ")[0].replace(".", "").replace("/", "").replace("-", "")
            
            return data
            
        except Exception as e:
            print(f"   ❌ Scraping Error: {e}")
            return {}
