-- Migration: Add ReceitaWS fields to empresas and create socios table
-- Date: 2026-02-03
-- Add new columns to empresas table
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS porte VARCHAR(100);
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS natureza_juridica VARCHAR(255);
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS data_abertura VARCHAR(10);
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS situacao_cadastral VARCHAR(50);
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS capital_social VARCHAR(50);
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS telefone_empresa VARCHAR(20);
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS email_empresa VARCHAR(255);
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS endereco_completo TEXT;
-- Create socios table for QSA data
CREATE TABLE IF NOT EXISTS socios (
    socio_id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(empresa_id),
    nome_completo VARCHAR(255) NOT NULL,
    cargo VARCHAR(150),
    data_extracao TIMESTAMPTZ DEFAULT NOW()
);
-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_socios_empresa_id ON socios(empresa_id);