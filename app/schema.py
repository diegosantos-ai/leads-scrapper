from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    empresa_id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(18), unique=True, nullable=True)
    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255), nullable=True)
    site_url = Column(String(255), nullable=True)
    linkedin_empresa = Column(String(255), nullable=True)
    setor_cnae = Column(String(255), nullable=True)  # Increased for full description
    tamanho_colaboradores = Column(String(50), nullable=True)
    faturamento_estimado = Column(String(50), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    segmento_mercado = Column(String(100), index=True)
    
    # New fields from ReceitaWS
    porte = Column(String(100), nullable=True)  # MEI, EPP, etc.
    natureza_juridica = Column(String(255), nullable=True)
    data_abertura = Column(String(10), nullable=True)
    situacao_cadastral = Column(String(50), nullable=True)  # ATIVA, BAIXADA, etc.
    capital_social = Column(String(50), nullable=True)
    telefone_empresa = Column(String(20), nullable=True)
    email_empresa = Column(String(255), nullable=True)
    endereco_completo = Column(Text, nullable=True)
    
    data_extracao = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contatos = relationship("Contato", back_populates="empresa")
    socios = relationship("Socio", back_populates="empresa")

class Socio(Base):
    """Partners and Administrators from QSA (Quadro de Sócios e Administradores)"""
    __tablename__ = "socios"

    socio_id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.empresa_id"))
    
    nome_completo = Column(String(255), nullable=False)
    cargo = Column(String(150), nullable=True)  # Sócio-Administrador, Diretor, etc.
    
    data_extracao = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    empresa = relationship("Empresa", back_populates="socios")

class Contato(Base):
    __tablename__ = "contatos"

    contato_id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.empresa_id"))
    
    nome_completo = Column(String(255), nullable=True)
    cargo = Column(String(150), nullable=True)
    email_corporativo = Column(String(255), nullable=True) # Unique constrained removed for flexibility
    telefone_direto = Column(String(20), nullable=True)
    linkedin_pessoal = Column(String(255), nullable=True)
    perfil_tomador_decisao = Column(Boolean, default=False)
    
    data_extracao = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    empresa = relationship("Empresa", back_populates="contatos")

class LogScraping(Base):
    __tablename__ = "logs_scraping"

    log_id = Column(Integer, primary_key=True, index=True)
    url_origem = Column(Text, nullable=True)
    ferramenta_usada = Column(String(50), default="GoogleMapsScraper")
    status_extracao = Column(String(50)) # 'Sucesso', 'Erro'
    termo_busca = Column(String(255))
    data_hora = Column(DateTime(timezone=True), server_default=func.now())
