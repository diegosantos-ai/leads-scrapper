import asyncio
from app.services import process_lead_generation

async def main():
    print("🚀 Starting Direct Enrichment Test...")
    # Using a query likely to have results
    result = await process_lead_generation(
        query="Agência Marketing Pinheiros", 
        limit=2, 
        segment="Debug", 
        no_enrich=True, 
        deep_enrich=True
    )
    print("🏁 Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
