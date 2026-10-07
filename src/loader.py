"""
loader.py — Leitura da fonte de dados.

Interface clara entre fonte e processamento.
Para trocar Excel por Google Sheets futuramente:
  substituir apenas a função load_excel() por load_google_sheets()
  mantendo o mesmo formato de retorno: dict[str, pd.DataFrame]
"""
import re
import openpyxl
import pandas as pd
from pathlib import Path


# Colunas esperadas nas abas de curso (com e sem Natureza)
_COL_BASE = ["Código", "Atividade de Ensino/Pré-Requisito", "Caráter",
             "Créditos", "Carga Horária", "Carga Horária Extensão (CHE)"]
_COL_NATUREZA = _COL_BASE + ["Natureza"]

# Abas que NÃO são cursos
_ABAS_IGNORADAS = {"Página6", "Leia-me", "Instruções", "Capa"}


def load_excel(path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Lê o arquivo Excel e retorna um dict {nome_curso: dataframe_bruto}.

    O DataFrame bruto contém as linhas exatamente como estão na planilha,
    incluindo linhas de cabeçalho de etapa — o processamento fica em processor.py.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    wb = openpyxl.load_workbook(path, data_only=True)
    resultado = {}

    for nome_aba in wb.sheetnames:
        if nome_aba in _ABAS_IGNORADAS:
            continue

        ws = wb[nome_aba]
        linhas = [row for row in ws.iter_rows(values_only=True)
                  if any(c is not None for c in row)]

        if not linhas:
            continue

        # Verificar se tem estrutura de currículo (contém "Etapa" ou colunas esperadas)
        conteudo_texto = " ".join(str(c) for row in linhas[:5] for c in row if c)
        if "Etapa" not in conteudo_texto and "Código" not in conteudo_texto:
            continue

        df = pd.DataFrame(linhas)
        resultado[nome_aba] = df

    return resultado


def load_google_sheets(sheet_id: str, credentials_path: str) -> dict[str, pd.DataFrame]:
    """
    [FUTURO] Lê de uma Google Sheet e retorna o mesmo formato de load_excel().

    Requer: pip install gspread google-auth
    O sheet_id é o ID da planilha na URL do Google Sheets.
    Cada aba com estrutura de currículo será carregada automaticamente.
    """
    raise NotImplementedError(
        "Integração com Google Sheets será implementada na V2. "
        "Use load_excel() por enquanto."
    )
