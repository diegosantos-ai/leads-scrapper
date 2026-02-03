import re
from playwright.async_api import Page
from typing import Dict, List, Optional

class ContactScraper:
    def __init__(self):
        # Regex básico para emails
        self.email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        # Regex básico para telefones BR (com ou sem DDD)
        self.phone_regex = re.compile(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}")

    async def scrape_contacts(self, page: Page, url: str) -> Dict[str, Optional[str]]:
        """
        Visits the URL and attempts to extract email and phone.
        Returns a dict with 'email' and 'phone'.
        """
        contacts = {"email": None, "phone": None}
        
        try:
            print(f"    🔎 Scanning website: {url}...")
            # Timeout curto pois só queremos texto
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            
            # 1. Estratégia: Links mailto: e tel:
            mailto_links = await page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href^="mailto:"]'));
                return anchors.map(a => a.href.replace('mailto:', ''));
            }""")
            
            tel_links = await page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href^="tel:"]'));
                return anchors.map(a => a.href.replace('tel:', ''));
            }""")

            if mailto_links:
                contacts["email"] = mailto_links[0].strip()
            
            if tel_links:
                contacts["phone"] = tel_links[0].strip()

            # 2. Estratégia: Regex no texto visível
            if not contacts["email"] or not contacts["phone"]:
                content = await page.inner_text("body")
                
                if not contacts["email"]:
                    emails = self.email_regex.findall(content)
                    if emails:
                        # Filtra emails inválidos comuns (ex: png, jpg)
                        valid_emails = [e for e in emails if not e.endswith(('png', 'jpg', 'jpeg', 'gif', 'webp'))]
                        if valid_emails:
                            contacts["email"] = valid_emails[0]
                
                if not contacts["phone"]:
                    phones = self.phone_regex.findall(content)
                    if phones:
                         contacts["phone"] = phones[0]

            # 3. Estratégia: Procurar link de "Contato" se não achou nada
            if not contacts["email"]:
                try:
                    contact_link = await page.get_attribute("a:has-text('Contato')", "href") or \
                                   await page.get_attribute("a:has-text('Fale Conosco')", "href")
                    
                    if contact_link:
                        # Resolve URL relativa
                        if not contact_link.startswith("http"):
                            contact_link = url.rstrip("/") + "/" + contact_link.lstrip("/")
                            
                        print(f"    ➡️  Visiting Contact Page: {contact_link}")
                        await page.goto(contact_link, timeout=10000, wait_until="domcontentloaded")
                        
                        # Repete busca regex na página de contato
                        content_contact = await page.inner_text("body")
                        emails = self.email_regex.findall(content_contact)
                        if emails:
                             contacts["email"] = emails[0]
                except Exception:
                    pass # Ignora erro ao navegar para página de contato

        except Exception as e:
            print(f"    ⚠️  Failed to scrape site {url}: {str(e)[:50]}")
        
        return contacts
