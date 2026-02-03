import os
import asyncio
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from app.models import Lead

class LeadEnricher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found. Enrichment will be skipped.")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0, google_api_key=self.api_key)

    async def _fetch_website_content(self, url: str) -> str:
        """
        Visits the website and extracts main text content.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=30000)
                content = await page.content()
                await browser.close()
                
                soup = BeautifulSoup(content, 'html.parser')
                # Remove scripts and styles
                for script in soup(["script", "style", "nav", "footer"]):
                    script.extract()
                return soup.get_text(separator=' ', strip=True)[:5000] # Limit context
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    async def enrich(self, lead: Lead) -> Lead:
        if not self.llm or not lead.website:
            return lead
            
        print(f"Enriching {lead.name} ({lead.website})...")
        website_text = await self._fetch_website_content(lead.website)
        
        if not website_text:
            return lead

        prompt = PromptTemplate.from_template(
            """
            Analyze the following company website content and extract strategic information.
            
            Company Name: {name}
            Website Content:
            {content}
            
            Return the following fields in a concise manner:
            1. Sector (Industry)
            2. Business Type (B2B, B2C, or Both)
            3. Detailed Description (1 sentence summary)
            4. Estimated Employee Count (if mentioned, otherwise "Unknown")
            
            Format: JSON
            """
        )
        
        try:
            response = await self.llm.ainvoke(prompt.format(name=lead.name, content=website_text))
            content = response.content.replace('```json', '').replace('```', '')
            import json
            data = json.loads(content)
            
            lead.sector = data.get("Sector")
            lead.business_type = data.get("Business Type")
            lead.employees_estimate = data.get("Estimated Employee Count")
            
        except Exception as e:
            print(f"AI Error: {e}")
            
        return lead

    async def enrich_leads(self, leads: list[Lead]) -> list[Lead]:
        """Enriches a list of leads in parallel"""
        tasks = [self.enrich(lead) for lead in leads]
        return await asyncio.gather(*tasks)
