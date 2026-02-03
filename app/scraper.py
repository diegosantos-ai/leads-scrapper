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
                previous_height = 0
                while len(leads) < limit:
                    # Extract items currently visible
                    # Result items usually have class 'Nv2PK' or are direct children of the feed
                    # A robust way is looking for 'a' tags with href containing '/maps/place' inside the feed
                    # But often the text is in a div.
                    
                    # selector for cards
                    card_selector = 'div.Nv2PK' 
                    
                    if await feed.locator(card_selector).count() == 0:
                        # Fallback or maybe not loaded yet
                        await page.wait_for_timeout(2000)
                    
                    cards = await feed.locator(card_selector).all()
                    
                    print(f"Found {len(cards)} cards so far...")
                    
                    for card in cards:
                        if len(leads) >= limit:
                            break
                            
                        try:
                            # Extract Name
                            # Usually in a div with class 'fontHeadlineSmall'
                            name_loc = card.locator('.fontHeadlineSmall')
                            if await name_loc.count() == 0:
                                continue
                            name = await name_loc.first.inner_text()
                            
                            # Check if we already have this lead
                            if any(l.name == name for l in leads):
                                continue

                            # Extract Link (to go to details if needed, but we try to get info from card first)
                            # The card itself or a child 'a' tag has the link
                            link_loc = card.locator('a.hfpxzc')
                            source_url = await link_loc.get_attribute('href') if await link_loc.count() > 0 else None
                            
                            # Extract Rating/Address/Phone text lines
                            # These are usually in 'div.W4P4ne' or 'span.W4P4ne'
                            # It's messy.
                            
                            text_content = await card.inner_text()
                            lines = text_content.split('\n')
                            
                            # Heuristic extraction
                            phone = None
                            address = None
                            
                            # Basic string matching for now (robust extraction needs visiting the page)
                            # Visiting each page takes time. For valid MVP, we scrape the list.
                            # But often phone is not in the list view, only in the detail view.
                            # Strategy: We can click each item to see details on the side panel, allowing better extraction.
                            
                            # Let's try to just get name/url from list, then visit details IS BETTER?
                            # No, Google Maps puts details in a side panel when you click.
                            
                            lead = Lead(
                                name=name,
                                source_url=source_url,
                                address=None, # Placeholder
                                phone=None    # Placeholder
                            )
                            leads.append(lead)
                            print(f"  + Scraped: {name}")
                            
                        except Exception as e:
                            print(f"Error scraping card: {e}")
                            
                    if len(leads) >= limit:
                        break
                        
                    # Scroll down
                    # We need to scroll the FEED element, not the window
                    await feed.evaluate("node => node.scrollTop += 2000")
                    await page.wait_for_timeout(random.uniform(1000, 3000))
                    
                    # simple break if no new items loaded? (omitted for MVP)
                    
            except Exception as e:
                print(f"Critial error: {e}")
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
