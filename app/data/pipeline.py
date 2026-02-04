"""
Data Pipeline Orchestrator

Automates the end-to-end data process:
1. Download Receita Federal data (if not present)
2. Iterate through market segments
3. Filter data for each segment
4. Import to database

Usage:
    python -m app.data.pipeline --uf SP --segments restaurantes advocacia
"""

import argparse
import sys
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

# Import steps
from app.data.download_receita import download_receita_data
from app.data.filter_cnae import filter_by_segment, CNAE_SEGMENTS
from app.data.import_to_db import import_csv_to_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DATA_DIR = "./data/receita"
SEGMENTS_DIR = "./data/segments"

def run_pipeline(uf: str, segments: list = None, force_download: bool = False):
    """Run the full data pipeline."""
    
    # 0. Setup
    Path(RAW_DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(SEGMENTS_DIR).mkdir(parents=True, exist_ok=True)
    
    if not segments:
        segments = list(CNAE_SEGMENTS.keys())
    
    logger.info(f"🚀 Starting pipeline for UF={uf}")
    logger.info(f"🎯 Target Segments: {segments}")
    
    # 1. Download Data
    # Only download 'estabelecimentos' as it contains the core data we need for filtering
    logger.info("⬇️ Phase 1: Checking Data Source")
    data_available = False
    
    try:
        if force_download or not list(Path(RAW_DATA_DIR).glob("*stabelecimento*.csv")):
             download_receita_data(output_dir=RAW_DATA_DIR, file_types=["estabelecimentos"])
        
        if list(Path(RAW_DATA_DIR).glob("*stabelecimento*.csv")):
            data_available = True
            logger.info("✅ Data Source: Official CSVs")
        else:
             logger.warning("⚠️ Download failed or incomplete.")
             
    except Exception as e:
        logger.error(f"❌ Download phase failed: {e}")

    # Fallback to ReceitaWS API if no CSVs
    if not data_available:
        logger.warning("🔄 Switching to FALLBACK mode: API (ReceitaWS)")
        from app.data.generate_sample import generate_sample_dataset
        import asyncio
        
        for segment in segments:
            logger.info(f"   📡 Fallback: Fetching live data for {segment}...")
            # Run async generator
            asyncio.run(generate_sample_dataset(segment=f"{segment.capitalize()} {uf}", limit=5))
        
        logger.info("\n🎉 Pipeline Complete (Fallback Mode)!")
        return

    # 2. Filter & Import Per Segment (CSV Mode)
    logger.info("🔍 Phase 2: Segmentation & Import")
    
    total_imported = 0
    
    for segment in segments:
        logger.info(f"\n👉 Processing Segment: {segment.upper()}")
        
        # Define output file for this segment
        segment_file = Path(SEGMENTS_DIR) / f"{segment}_{uf}.csv"
        
        # 2a. Filter
        if not segment_file.exists():
            logger.info("   Filtering data...")
            matched = filter_by_segment(
                input_dir=RAW_DATA_DIR,
                segment=segment,
                uf=uf,
                output_file=str(segment_file)
            )
            if matched == 0:
                logger.warning(f"   ⚠️ No records found for {segment} in {uf}")
                continue
        else:
            logger.info("   ✅ Segment file already exists, using cached")
            
        # 2b. Import to DB
        logger.info("   📥 Importing to Database...")
        imported = import_csv_to_db(
            input_file=str(segment_file),
            segment=f"{segment.capitalize()} {uf}",
            batch_size=1000
        )
        total_imported += imported
        
    logger.info(f"\n🎉 Pipeline Complete! Imported {total_imported} records across {len(segments)} segments.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Data Pipeline")
    parser.add_argument("--uf", default="SP", help="User Location (State)")
    parser.add_argument("--segments", nargs="+", help="Specific segments to process (default: all)")
    parser.add_argument("--force-download", action="store_true", help="Force re-download of raw data")
    
    args = parser.parse_args()
    
    run_pipeline(args.uf, args.segments, args.force_download)
