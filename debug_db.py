from app.database import SessionLocal
from app.schema import Empresa, Socio, Contato

def check_receita_data():
    db = SessionLocal()
    try:
        print(f"🔌 Checking ReceitaWS Data...")
        
        # Get most recent companies from test segment
        companies = db.query(Empresa).filter(
            Empresa.segmento_mercado.in_(['Teste Enrich', 'TesteReceitaWS', 'TesteReceitaWS2'])
        ).order_by(Empresa.empresa_id.desc()).limit(5).all()
        
        for c in companies:
            print(f"\n{'='*50}")
            print(f"📊 {c.razao_social}")
            print(f"   Nome Fantasia: {c.nome_fantasia}")
            print(f"   CNPJ: {c.cnpj}")
            print(f"   Porte: {c.porte}")
            print(f"   Situação: {c.situacao_cadastral}")
            print(f"   Capital Social: {c.capital_social}")
            print(f"   Cidade/UF: {c.cidade}/{c.estado}")
            print(f"   Telefone: {c.telefone_empresa}")
            print(f"   Email: {c.email_empresa}")
            print(f"   CNAE: {c.setor_cnae[:50] if c.setor_cnae else 'N/A'}...")
            
            # Check socios
            socios = db.query(Socio).filter(Socio.empresa_id == c.empresa_id).all()
            if socios:
                print(f"   👔 Sócios ({len(socios)}):")
                for s in socios:
                    print(f"      - {s.nome_completo} ({s.cargo})")
            
            # Check contacts
            contatos = db.query(Contato).filter(Contato.empresa_id == c.empresa_id).all()
            if contatos:
                print(f"   📧 Contatos ({len(contatos)}):")
                for ct in contatos:
                    print(f"      - {ct.email_corporativo or 'sem email'} | {ct.telefone_direto or 'sem tel'}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_receita_data()
