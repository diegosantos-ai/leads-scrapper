import asyncio
from playwright.async_api import async_playwright
from app.scrapers.contacts import ContactScraper

async def test_scraper():
    print("🚀 Testing ContactScraper Unit...")
    scraper = ContactScraper()
    
    # URL de teste (empresa real ou site conhecido)
    # Vamos usar um site que sabemos que tem contato, ex: um site oficial ou agência
    # Vou usar o site do Python.org ou similar que tenha footer
    url = "https://www.python.org/about/" 
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        result = await scraper.scrape_contacts(page, url)
        
        print("\n📊 Result:")
        print(f"Email: {result['email']}")
        print(f"Phone: {result['phone']}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scraper())
