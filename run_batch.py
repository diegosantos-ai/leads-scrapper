import subprocess
import time
from datetime import datetime

# Estratégia de Coleta (Ondas)
# Formato: (Query, Limit, Segment)
TARGETS = [
    # Onda 1: São Paulo Capital (Energia Solar - Alto Consumo)
    ("Supermercado São Paulo", 50, "Energia Solar"), # Já rodamos, mas bom garantir
    ("Padaria São Paulo", 50, "Energia Solar"),
    ("Oficina Mecanica São Paulo", 50, "Energia Solar"),
    ("Galpão Industrial São Paulo", 50, "Energia Solar"),
    ("Frigorífico São Paulo", 30, "Energia Solar"),
    
    # Onda 2: Interior SP (Campinas)
    ("Supermercado Campinas", 30, "Energia Solar"),
    ("Padaria Campinas", 30, "Energia Solar"),
]

def run_scraper(query, limit, segment):
    print(f"\n🚀 [ {datetime.now().strftime('%H:%M:%S')} ] Iniciando: {query}...")
    
    # Comando sem enriquecimento para velocidade (focamos em volume primeiro)
    cmd = [
        "python", "main.py",
        "--query", query,
        "--limit", str(limit),
        "--segment", segment,
        "--no-enrich" 
    ]
    
    try:
        # Executa e espera terminar
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print(f"✅ Sucesso: {query}")
        else:
            print(f"⚠️ Erro (Código {result.returncode}): {query}")
            
    except Exception as e:
        print(f"❌ Falha crítica: {e}")

    # Pausa para "resfriar" e evitar bloqueio do Google
    print("⏳ Aguardando 10s para evitar bloqueio...")
    time.sleep(10)

def main():
    print("🤖 --- INICIANDO AUTOMAÇÃO DE COLETA ---")
    print(f"🎯 Total de Alvos: {len(TARGETS)}\n")
    
    for target in TARGETS:
        run_scraper(*target)
        
    print("\n🏁 --- COLETA FINALIZADA ---")

if __name__ == "__main__":
    main()
