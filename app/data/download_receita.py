"""
Receita Federal CNPJ Data Downloader

Downloads the official CNPJ datasets from dados.gov.br.
These are updated monthly by the Brazilian Federal Revenue Service.

Usage:
    python -m app.data.download_receita --output ./data/receita/
"""

import os
import requests
import zipfile
from pathlib import Path
from typing import List
import re

# Base URL for Receita Federal open data
BASE_URL = "https://dadosabertos.rfb.gov.br/CNPJ/"

# Files we need (updated monthly with date suffix)
FILE_PATTERNS = {
    "empresas": "Empresas",
    "estabelecimentos": "Estabelecimentos", 
    "socios": "Socios",
    "cnaes": "Cnaes",  # CNAE lookup table
    "municipios": "Municipios",  # City codes
}

def get_available_files() -> List[str]:
    """List available files from Receita Federal FTP."""
    print("🔍 Checking available files...")
    try:
        response = requests.get(BASE_URL, timeout=30)
        # Parse HTML to find .zip files
        files = re.findall(r'href="([^"]+\.zip)"', response.text)
        return files
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def download_file(filename: str, output_dir: Path) -> bool:
    """Download a single file from Receita Federal."""
    url = f"{BASE_URL}{filename}"
    output_path = output_dir / filename
    
    if output_path.exists():
        print(f"⏩ Already exists: {filename}")
        return True
    
    print(f"⬇️  Downloading: {filename}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        total = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = (downloaded / total) * 100
                    print(f"\r   Progress: {pct:.1f}%", end="", flush=True)
        
        print(f"\n✅ Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False

def extract_file(zip_path: Path, output_dir: Path) -> bool:
    """Extract a zip file."""
    print(f"📦 Extracting: {zip_path.name}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(output_dir)
        print(f"✅ Extracted to: {output_dir}")
        return True
    except Exception as e:
        print(f"❌ Extract failed: {e}")
        return False

def download_receita_data(output_dir: str = "./data/receita/", 
                          file_types: List[str] = None):
    """
    Download Receita Federal CNPJ data.
    
    Args:
        output_dir: Where to save files
        file_types: Which file types to download (empresas, estabelecimentos, socios)
                   If None, downloads all.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    available = get_available_files()
    if not available:
        print("❌ Could not list files. Check your internet connection.")
        return
    
    print(f"📂 Found {len(available)} files available")
    
    # Filter to only the file types we need
    file_types = file_types or list(FILE_PATTERNS.keys())
    
    for file_type in file_types:
        pattern = FILE_PATTERNS.get(file_type)
        if not pattern:
            continue
            
        # Find matching files (there may be multiple parts: Empresas0.zip, Empresas1.zip, etc.)
        matching = [f for f in available if pattern in f]
        
        if not matching:
            print(f"⚠️  No files found for: {file_type}")
            continue
        
        print(f"\n📥 {file_type.upper()}: Found {len(matching)} file(s)")
        
        for filename in matching[:1]:  # Start with just first file for testing
            if download_file(filename, output_path):
                extract_file(output_path / filename, output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download Receita Federal CNPJ data")
    parser.add_argument("--output", default="./data/receita/", help="Output directory")
    parser.add_argument("--types", nargs="+", default=["estabelecimentos", "cnaes"], 
                        help="File types to download")
    args = parser.parse_args()
    
    download_receita_data(args.output, args.types)
