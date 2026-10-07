"""
app.py — Ponto de entrada do sistema MatrizBI UFRGS.

Execução: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from src.loader import load_excel
from src.processor import processar_todos, entradas_para_dataframe
from src.validator import validar, resumo_validacao
from src.views.matriz import render_matriz
from src.views.grafo import render_grafo
from src.views.distribuicao import render_distribuicao
from src.views.comparacao import render_comparacao

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Currículos UFRGS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stMetric label { font-size: 12px !important; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Caminho do arquivo de dados ───────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
ARQUIVO_PADRAO = DATA_DIR / "Curriculo_sistema_2026-2.xlsx"


@st.cache_data(show_spinner="Carregando dados curriculares…")
def carregar_dados(path: str) -> pd.DataFrame:
    """Carrega, processa e retorna DataFrame consolidado. Cache automático."""
    dados_brutos = load_excel(path)
    entradas, _ = processar_todos(dados_brutos)
    return entradas_para_dataframe(entradas)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 Currículos UFRGS")
    st.markdown("---")

    # Upload ou arquivo padrão
    uploaded = st.file_uploader(
        "Substituir planilha de dados:",
        type=["xlsx"],
        help="Faça upload de uma versão atualizada da planilha.",
    )

    if uploaded:
        # Salva temporariamente e usa
        tmp_path = DATA_DIR / "upload_temp.xlsx"
        tmp_path.write_bytes(uploaded.read())
        ARQUIVO_USADO = str(tmp_path)
        st.success("Planilha carregada com sucesso!")
    else:
        ARQUIVO_USADO = str(ARQUIVO_PADRAO)

    try:
        df_todos = carregar_dados(ARQUIVO_USADO)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

    cursos_disponiveis = sorted(df_todos["curso"].unique().tolist())

    st.markdown("---")
    st.markdown("**Navegação**")
    pagina = st.radio(
        "Visualização:",
        options=[
            "🏠 Início",
            "📋 Matriz Curricular",
            "🕸️ Grafo de Pré-requisitos",
            "📊 Distribuição CH/Créditos",
            "🔄 Comparação entre Cursos",
            "⚠️ Validação",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Seleção de curso (para páginas de curso único)
    if pagina not in ("🏠 Início", "🔄 Comparação entre Cursos", "⚠️ Validação"):
        curso_sel = st.selectbox("Curso:", options=cursos_disponiveis)
    else:
        curso_sel = None

    # Filtros adicionais
    if pagina == "📋 Matriz Curricular" and curso_sel:
        st.markdown("---")
        st.markdown("**Filtros**")
        carater_opts = df_todos[df_todos["curso"] == curso_sel]["carater"].unique().tolist()
        carater_filtro = st.multiselect("Caráter:", carater_opts, default=carater_opts,
                                         key="filtro_carater_matriz")

        etapas_opts = sorted([
            int(e) for e in df_todos[df_todos["curso"] == curso_sel]["etapa"].dropna().unique()
        ])
        etapas_filtro = st.multiselect("Etapas:", etapas_opts, default=etapas_opts,
                                        key="filtro_etapas_matriz")
    else:
        carater_filtro = None
        etapas_filtro = None

    st.markdown("---")
    st.caption(f"Cursos carregados: {', '.join(cursos_disponiveis)}")


# ── Área principal ─────────────────────────────────────────────────────────────

if pagina == "🏠 Início":
    st.title("Sistema de Visualização Curricular")
    st.markdown("**UFRGS — Campus Litoral Norte**")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Cursos carregados", len(cursos_disponiveis))
    col2.metric("Componentes únicos", df_todos["codigo"].nunique())
    col3.metric("Total de entradas na matriz", len(df_todos))

    st.markdown("---")
    st.markdown("### Cursos disponíveis")
    for curso in cursos_disponiveis:
        df_c = df_todos[df_todos["curso"] == curso]
        n_obrig = len(df_c[df_c["carater"] == "Obrigatória"])
        n_elet = len(df_c[df_c["carater"] == "Eletiva"])
        ch_total = int(df_c.groupby("codigo")["carga_horaria"].first().sum())
        st.markdown(
            f'<div style="border:1px solid #e4e2d9;border-radius:10px;padding:14px;'
            f'margin-bottom:10px;background:#fff">'
            f'<b style="font-size:16px">{curso}</b><br>'
            f'<span style="color:#1D9E75">{n_obrig} obrigatórias</span> · '
            f'<span style="color:#534AB7">{n_elet} eletivas</span> · '
            f'<span style="color:#555">{ch_total}h total</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("""
    ### Como usar
    Use o **menu lateral** para navegar entre as visualizações:
    - **Matriz Curricular** — grade de componentes por etapa
    - **Grafo de Pré-requisitos** — relações de dependência entre disciplinas
    - **Distribuição CH/Créditos** — análise de carga horária por etapa e caráter
    - **Comparação** — componentes compartilhados e diferenças entre cursos
    - **Validação** — verificação de inconsistências nos dados

    Para **atualizar os dados**, faça upload de uma nova planilha no menu lateral.
    O sistema reconhece automaticamente qualquer nova aba como novo curso.
    """)

elif pagina == "📋 Matriz Curricular":
    st.title(f"Matriz Curricular — {curso_sel}")
    df_curso = df_todos[df_todos["curso"] == curso_sel].copy()

    # Aplicar filtros
    if carater_filtro is not None:
        df_curso = df_curso[df_curso["carater"].isin(carater_filtro)]
    if etapas_filtro is not None:
        df_curso = df_curso[
            df_curso["etapa"].isna() | df_curso["etapa"].isin(etapas_filtro)
        ]

    render_matriz(df_curso)

elif pagina == "🕸️ Grafo de Pré-requisitos":
    st.title(f"Grafo de Pré-requisitos — {curso_sel}")
    st.caption("Use o scroll para zoom. Arraste para mover o grafo.")
    df_curso = df_todos[df_todos["curso"] == curso_sel].copy()
    render_grafo(df_curso)

elif pagina == "📊 Distribuição CH/Créditos":
    st.title(f"Distribuição — {curso_sel}")
    df_curso = df_todos[df_todos["curso"] == curso_sel].copy()
    render_distribuicao(df_curso)

elif pagina == "🔄 Comparação entre Cursos":
    st.title("Comparação entre Cursos")
    cursos_comp = st.multiselect(
        "Selecione os cursos para comparar:",
        options=cursos_disponiveis,
        default=cursos_disponiveis[:2] if len(cursos_disponiveis) >= 2 else cursos_disponiveis,
    )
    render_comparacao(df_todos, cursos_comp)

elif pagina == "⚠️ Validação":
    st.title("Validação dos Dados")
    problemas = validar(df_todos)
    resumo = resumo_validacao(problemas)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de problemas", resumo["total"])
    c2.metric("Erros", resumo["erros"], delta_color="inverse")
    c3.metric("Avisos", resumo["avisos"])

    if not problemas:
        st.success("✅ Nenhum problema encontrado nos dados.")
    else:
        df_prob = pd.DataFrame([
            {"Nível": p.nivel.upper(), "Curso": p.curso,
             "Código": p.codigo, "Mensagem": p.mensagem}
            for p in problemas
        ])
        nivel_filtro = st.multiselect(
            "Filtrar por nível:",
            ["ERRO", "AVISO"],
            default=["ERRO", "AVISO"],
        )
        df_exib = df_prob[df_prob["Nível"].isin(nivel_filtro)]
        st.dataframe(df_exib, use_container_width=True, hide_index=True)
