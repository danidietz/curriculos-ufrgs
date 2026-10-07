"""
processor.py — Transforma os DataFrames brutos em estrutura normalizada.

Responsabilidades:
  - Detectar etapas (linhas de título como "Etapa 1")
  - Separar nome e pré-requisitos do campo misto
  - Normalizar caráter, etapa, créditos
  - Produzir lista de EntradaMatriz e dict de Componentes
"""
import re
import pandas as pd
from typing import Optional
from src.models import Componente, EntradaMatriz

# Regex para identificar códigos de componentes (DIL01113, DIR04016, VAERE201...)
_CODIGO_RE = re.compile(r'\b([A-Z]{2,}[0-9]{2,}(?:/[0-9]+)*)\b')

# Linha que indica início de uma etapa
_ETAPA_RE = re.compile(r'^Etapa\s+(\d+)$', re.IGNORECASE)
_SEM_ETAPA_RE = re.compile(r'sem\s+etapa', re.IGNORECASE)


def _parse_nome_prereqs(campo: str) -> tuple[str, list[str]]:
    """
    Extrai nome limpo e lista de pré-requisitos do campo misto.

    Formato exportado pelo sistema UFRGS:
      'NOME DA DISCIPLINA\n - COD1 - NOME PREREQ1  - e COD2 - NOME PREREQ2'
    ou
      'NOME DA DISCIPLINA\n - COD1 - NOME PREREQ1'
    """
    if not campo or not isinstance(campo, str):
        return ("", [])

    # Normalizar quebras de linha e espaços múltiplos
    campo = campo.replace('\n', ' ').strip()
    campo = re.sub(r'  +', ' ', campo)

    codigos_encontrados = _CODIGO_RE.findall(campo)

    if not codigos_encontrados:
        return (campo.strip(), [])

    # Nome = tudo antes do primeiro código, removendo separador ' - '
    primeiro_cod = codigos_encontrados[0]
    idx = campo.find(primeiro_cod)
    nome_bruto = campo[:idx]
    nome = re.sub(r'\s*-\s*$', '', nome_bruto).strip()

    # Pré-requisitos = todos os códigos encontrados após o nome
    # (excluir se o único código É o próprio componente — não deve ocorrer, mas defensivo)
    prereqs = codigos_encontrados

    return (nome, prereqs)


def _normalizar_carater(valor) -> str:
    if not valor:
        return "Desconhecido"
    v = str(valor).strip()
    if "letiva" in v:
        return "Eletiva"
    if "brigatória" in v or "brigatorio" in v.lower() or "brigat" in v.lower():
        return "Obrigatória"
    return v


def _normalizar_etapa(valor) -> Optional[int]:
    if valor is None:
        return None
    try:
        return int(float(str(valor)))
    except (ValueError, TypeError):
        return None


def _eh_linha_cabecalho(row: tuple) -> bool:
    """Verdadeiro se a linha é cabeçalho de coluna (repete a cada etapa)."""
    return row[0] == "Código" or (
        isinstance(row[1], str) and "Atividade de Ensino" in str(row[1])
    )


def processar_curso(nome_curso: str, df: pd.DataFrame) -> list[EntradaMatriz]:
    """
    Processa o DataFrame bruto de um curso e retorna lista de EntradaMatriz.

    Detecta automaticamente a etapa atual lendo as linhas de título.
    """
    entradas = []
    etapa_atual: Optional[int] = None
    tem_natureza = (df.shape[1] >= 7)  # BICT tem coluna extra Natureza

    for _, row in df.iterrows():
        row = tuple(row)
        celula_0 = str(row[0]).strip() if row[0] is not None else ""
        celula_1 = str(row[1]).strip() if row[1] is not None else ""

        # — Linha de título de etapa —
        m_etapa = _ETAPA_RE.match(celula_0)
        if m_etapa:
            etapa_atual = int(m_etapa.group(1))
            continue

        # — "Sem Etapa" —
        if _SEM_ETAPA_RE.search(celula_0) or _SEM_ETAPA_RE.search(celula_1):
            etapa_atual = None
            continue

        # — Linha de cabeçalho de colunas —
        if _eh_linha_cabecalho(row):
            continue

        # — Linha vazia ou sem dados relevantes —
        codigo_raw = row[0]
        campo_atividade = row[1] if len(row) > 1 else None

        if not campo_atividade:
            continue

        # Código pode ser None para alguns componentes (TCC sem código no sistema)
        codigo = str(codigo_raw).strip() if codigo_raw else None

        nome, prereqs = _parse_nome_prereqs(str(campo_atividade))
        if not nome:
            continue

        carater = _normalizar_carater(row[2] if len(row) > 2 else None)
        creditos = float(row[3]) if len(row) > 3 and row[3] is not None else 0.0
        carga_horaria = float(row[4]) if len(row) > 4 and row[4] is not None else 0.0
        che = float(row[5]) if len(row) > 5 and row[5] is not None else 0.0
        natureza = str(row[6]).strip() if tem_natureza and len(row) > 6 and row[6] else None

        entrada = EntradaMatriz(
            curso=nome_curso,
            codigo=codigo or f"SEM_CODIGO_{nome[:20]}",
            nome=nome,
            etapa=etapa_atual,
            carater=carater,
            creditos=creditos,
            carga_horaria=carga_horaria,
            che=che,
            prereqs=prereqs,
            natureza=natureza,
        )
        entradas.append(entrada)

    return entradas


def processar_todos(dados_brutos: dict[str, pd.DataFrame]) -> tuple[
    list[EntradaMatriz], dict[str, Componente]
]:
    """
    Processa todos os cursos e retorna:
      - lista completa de EntradaMatriz (uma por disciplina×curso)
      - dict de Componentes únicos {codigo: Componente}
    """
    todas_entradas: list[EntradaMatriz] = []
    componentes: dict[str, Componente] = {}

    for nome_curso, df in dados_brutos.items():
        entradas = processar_curso(nome_curso, df)
        todas_entradas.extend(entradas)

        # Registrar componentes únicos (primeira ocorrência define nome e natureza)
        for e in entradas:
            if e.codigo not in componentes:
                componentes[e.codigo] = Componente(
                    codigo=e.codigo,
                    nome=e.nome,
                    natureza=e.natureza,
                )

    return todas_entradas, componentes


def entradas_para_dataframe(entradas: list[EntradaMatriz]) -> pd.DataFrame:
    """Converte lista de EntradaMatriz em DataFrame para uso nas views."""
    return pd.DataFrame([
        {
            "curso": e.curso,
            "codigo": e.codigo,
            "nome": e.nome,
            "etapa": e.etapa,
            "carater": e.carater,
            "creditos": e.creditos,
            "carga_horaria": e.carga_horaria,
            "che": e.che,
            "prereqs": e.prereqs,
            "natureza": e.natureza,
        }
        for e in entradas
    ])
