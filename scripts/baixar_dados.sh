#!/usr/bin/env bash
# Baixa os CSVs da Olist para data/raw.
# Opção 1 (oficial): Kaggle CLI com credenciais configuradas.
# Opção 2: cópia pública no GitHub (mesmos arquivos do Kaggle).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw
if command -v kaggle >/dev/null 2>&1; then
  kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
else
  tmp=$(mktemp -d)
  git clone --depth 1 https://github.com/spdrio/Brazilian-E-Commerce-Public-Dataset-by-Olist "$tmp/olist"
  cp "$tmp"/olist/files/*.csv data/raw/
  rm -rf "$tmp"
fi
ls data/raw
