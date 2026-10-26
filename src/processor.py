"""Processa os DataFrames brutos e retorna EntradaMatriz normalizadas."""
import re
import pandas as pd
from .models import EntradaMatriz, Componente

_CODIGO_RE = re.compile(r'\b([A-Z]{2,}[0-9]{2,}(?:/[0-9]+)*)\b')
_ETAPA_RE = re.compile(r'Etapa\s+(\d+)', re.IGNORECASE)


def _parse_prereqs(texto: str) -> tuple[str, list[str]]:
    """Separa nome e lista de códigos de pré-requisito."""
    if not texto or not isinstance(texto, str):
        return str(texto or ""), []
    partes = texto.split('\n', 1)
    nome = partes[0].strip()
    prereqs = []
    if len(partes) > 1:
        prereqs = _CODIGO_RE.findall(partes[1])
    return nome, prereqs


def _normalizar_carater(valor) -> str:
    if not valor:
        return "Desconhecido"
    v = str(valor).strip().lower()
    if "obrig" in v:
        return "Obrigatória"
    if "elet" in v:
        return "Eletiva"
    return str(valor).strip()


def _normalizar_etapa(valor) -> int | None:
    if valor is None:
        return None
    m = _ETAPA_RE.search(str(valor))
    if m:
        return int(m.group(1))
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None


def _get_col(row: dict, *candidatos) -> any:
    """Retorna o primeiro valor não-None entre as colunas candidatas."""
    for c in candidatos:
        if c in row and row[c] is not None and str(row[c]).strip() != "":
            return row[c]
    return None


def processar_curso(nome_curso: str, df: pd.DataFrame) -> list[EntradaMatriz]:
    """Converte um DataFrame de uma aba em lista de EntradaMatriz."""
    entradas = []
    cols = list(df.columns)

    for _, row in df.iterrows():
        row = row.to_dict()

        # Código
        codigo = str(_get_col(row, "Código", "codigo", "CÓDIGO") or "").strip()
        if not codigo or len(codigo) < 4:
            continue

        # Nome + pré-requisitos (campo pode ter \n embutido)
        campo_atividade = _get_col(row,
            "Atividade de Ensino/Pré-Requisito",
            "Atividade de Ensino",
            "atividade",
        )
        nome, prereqs = _parse_prereqs(str(campo_atividade or ""))

        # Etapa — pode estar numa coluna dedicada ou embutida
        etapa_raw = _get_col(row, "Etapa", "etapa")
        etapa = _normalizar_etapa(etapa_raw)

        # Caráter
        carater = _normalizar_carater(_get_col(row, "Caráter", "Carater", "caráter"))

        # Números
        def _float(v):
            try:
                return float(v or 0)
            except (ValueError, TypeError):
                return 0.0

        creditos = _float(_get_col(row, "Créditos", "creditos"))
        ch = _float(_get_col(row, "Carga Horária", "carga_horaria"))
        che = _float(_get_col(row, "Carga Horária Extensão (CHE)", "che"))

        # Natureza (só BICT)
        natureza = str(_get_col(row, "Natureza", "natureza") or "").strip() or None

        entradas.append(EntradaMatriz(
            curso=nome_curso,
            codigo=codigo,
            nome=nome,
            etapa=etapa,
            carater=carater,
            creditos=creditos,
            carga_horaria=ch,
            che=che,
            prereqs=prereqs,
            natureza=natureza,
        ))

    return entradas


def processar_todos(dados_brutos: dict[str, pd.DataFrame]) -> tuple[list[EntradaMatriz], dict[str, Componente]]:
    """Processa todos os cursos e constrói o catálogo de componentes."""
    todas_entradas: list[EntradaMatriz] = []
    componentes: dict[str, Componente] = {}

    for nome_curso, df in dados_brutos.items():
        entradas = processar_curso(nome_curso, df)
        todas_entradas.extend(entradas)

        for e in entradas:
            if e.codigo not in componentes:
                componentes[e.codigo] = Componente(
                    codigo=e.codigo,
                    nome=e.nome,
                    natureza=e.natureza,
                )

    return todas_entradas, componentes


def entradas_para_dataframe(entradas: list[EntradaMatriz]) -> pd.DataFrame:
    """Converte lista de EntradaMatriz em DataFrame pandas."""
    if not entradas:
        return pd.DataFrame()
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
