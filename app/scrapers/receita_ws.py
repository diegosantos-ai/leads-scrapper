import httpx
import asyncio
from typing import Dict, Optional
import time

class ReceitaWSClient:
    """
    Client for ReceitaWS API - Official CNPJ data from Receita Federal.
    Free tier: 3 requests per minute.
    """
    
    BASE_URL = "https://receitaws.com.br/v1/cnpj"
    
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 20  # 3 req/min = 1 req every 20 seconds
    
    async def _rate_limit(self):
        """Ensure we don't exceed 3 requests per minute."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            print(f"    ⏳ Rate limiting: waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _clean_cnpj(self, cnpj: str) -> str:
        """Remove formatting from CNPJ (dots, slashes, dashes)."""
        return ''.join(filter(str.isdigit, cnpj))
    
    async def fetch(self, cnpj: str) -> Optional[Dict]:
        """
        Fetch complete CNPJ data from ReceitaWS.
        
        Returns dict with: nome, fantasia, situacao, tipo, porte, 
        natureza_juridica, atividade_principal, qsa (sócios), 
        capital_social, telefone, email, endereço completo, etc.
        """
        await self._rate_limit()
        
        clean_cnpj = self._clean_cnpj(cnpj)
        
        if len(clean_cnpj) != 14:
            print(f"    ⚠️ Invalid CNPJ format: {cnpj}")
            return None
        
        url = f"{self.BASE_URL}/{clean_cnpj}"
        print(f"    🔎 Fetching CNPJ data: {clean_cnpj[:8]}...")
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "ERROR":
                        print(f"    ⚠️ CNPJ not found or invalid")
                        return None
                    
                    print(f"    ✅ Found: {data.get('nome', 'N/A')[:40]}...")
                    return data
                    
                elif response.status_code == 429:
                    print(f"    ⚠️ Rate limit exceeded. Waiting 60s...")
                    await asyncio.sleep(60)
                    return await self.fetch(cnpj)  # Retry
                    
                else:
                    print(f"    ❌ API Error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"    ❌ Request failed: {str(e)[:50]}")
            return None
    
    def extract_socios(self, data: Dict) -> list:
        """Extract list of partners/administrators from QSA."""
        qsa = data.get("qsa", [])
        socios = []
        for socio in qsa:
            socios.append({
                "nome": socio.get("nome"),
                "cargo": socio.get("qual"),  # "Sócio-Administrador", "Diretor", etc.
            })
        return socios
    
    def extract_atividade(self, data: Dict) -> str:
        """Extract main activity description (CNAE)."""
        atividades = data.get("atividade_principal", [])
        if atividades:
            return atividades[0].get("text", "")
        return ""
