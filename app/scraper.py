import asyncio
import random
from typing import List, Optional
from playwright.async_api import async_playwright, Page, Locator
from app.models import Lead

class GoogleMapsScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape(self, query: str, limit: int = 5) -> List[Lead]:
        leads: List[Lead] = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                print(f"Searching for: {query}")
                await page.goto(f"https://www.google.com/maps/search/{query}", timeout=60000)
                
                # Check for consent dialog (common in EU, less so in BR but good practice)
                # await page.get_by_text("Aceitar tudo").click() # Optional
                
                # Wait for the results feed
                # The feed usually has role="feed"
                feed_selector = 'div[role="feed"]'
                try:
                    await page.wait_for_selector(feed_selector, timeout=10000)
                except:
                    print("Feed not found, taking screenshot")
                    await page.screenshot(path="error_no_feed.png")
                    return []

                # Scroll to load items
                feed = page.locator(feed_selector)
                
                print("Scrolling to load results...")
                previous_count = 0
                stale_count = 0
                max_stale = 5  # Break if no new cards after 5 scroll attempts
                
                while len(leads) < limit:
                    # selector for cards
                    card_selector = 'div.Nv2PK' 
                    
                    if await feed.locator(card_selector).count() == 0:
                        await page.wait_for_timeout(2000)
                    
                    cards = await feed.locator(card_selector).all()
                    current_card_count = len(cards)
                    
                    print(f"Found {current_card_count} cards so far...")
                    
                    # Stale detection: if same count after scroll, increment stale counter
                    if current_card_count == previous_count:
                        stale_count += 1
                        if stale_count >= max_stale:
                            print(f"No new cards after {max_stale} scrolls. Breaking.")
                            break
                    else:
                        stale_count = 0
                    
                    previous_count = current_card_count
                    
                    for card in cards:
                        if len(leads) >= limit:
                            break
                            
                        try:
                            name_loc = card.locator('.fontHeadlineSmall')
                            if await name_loc.count() == 0:
                                continue
                            name = await name_loc.first.inner_text()
                            
                            # Check if we already have this lead
                            if any(l.name == name for l in leads):
                                continue

                            link_loc = card.locator('a.hfpxzc')
                            source_url = await link_loc.get_attribute('href') if await link_loc.count() > 0 else None
                            
                            lead = Lead(
                                name=name,
                                source_url=source_url,
                                address=None,
                                phone=None
                            )
                            leads.append(lead)
                            print(f"  + Scraped: {name}")
                            
                        except Exception as e:
                            print(f"Error scraping card: {e}")
                            
                    if len(leads) >= limit:
                        break
                        
                    # Scroll down
                    await feed.evaluate("node => node.scrollTop += 2000")
                    await page.wait_for_timeout(random.uniform(1000, 2000))
                    
            except Exception as e:
                print(f"Critical error: {e}")
                await page.screenshot(path="error_critical.png")
            finally:
                await browser.close()
                
        return leads

if __name__ == "__main__":
    scraper = GoogleMapsScraper(headless=True)
    # Testing with a small limit
    results = asyncio.run(scraper.scrape("Marketing Digital São Paulo", limit=3))
    for r in results:
        print(f"Result: {r}")
