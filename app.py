"""Visualizador de Matrizes Curriculares — UFRGS BICT"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.loader import load_excel
from src.processor import processar_todos, entradas_para_dataframe
from src.views.matriz import render_matriz
from src.views.grafo import render_grafo
from src.views.distribuicao import render_distribuicao
from src.views.comparacao import render_comparacao

# ── Nomes amigáveis ──────────────────────────────────────────────────────────
NOMES_CURSOS = {
    "BICT": "Bacharelado Interdisciplinar em C&T",
    "ES":   "Engenharia de Serviços",
    "EGE":  "Engenharia de Gestão de Energia",
    "LG":   "Licenciatura em Geografia",
    "GPDR": "Gestão Pública p/ o Des. Regional",
}

st.set_page_config(
    page_title="Matrizes Curriculares BICT",
    page_icon="🎓",
    layout="wide",
)

# ── Carregamento de dados ────────────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando matrizes...")
def carregar_dados(caminho: str):
    dados_brutos = load_excel(caminho)
    entradas, componentes = processar_todos(dados_brutos)
    df = entradas_para_dataframe(entradas)
    return df, list(dados_brutos.keys())

DADOS_PADRAO = Path(__file__).parent / "data" / "Curriculo_sistema_2026-2.xlsx"

# Upload opcional na sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    arquivo = st.file_uploader("Substituir arquivo de dados (.xlsx)", type="xlsx")

if arquivo:
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(arquivo.read())
        tmp_path = tmp.name
    df_todos, cursos_disponiveis = carregar_dados(tmp_path)
else:
    if not DADOS_PADRAO.exists():
        st.error(f"Arquivo de dados não encontrado: {DADOS_PADRAO}")
        st.stop()
    df_todos, cursos_disponiveis = carregar_dados(str(DADOS_PADRAO))

# ── Navegação na sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    pagina = st.radio(
        "Navegação",
        ["🏠 Início", "📋 Matriz Curricular", "🔗 Grafo de Pré-req.", "📊 Distribuição", "🔄 Comparação"],
        label_visibility="collapsed",
    )

# ── SELETOR DE CURSO PROEMINENTE ─────────────────────────────────────────────
PAGINAS_COM_CURSO = ["📋 Matriz Curricular", "🔗 Grafo de Pré-req.", "📊 Distribuição"]

if pagina in PAGINAS_COM_CURSO:
    opcoes = {NOMES_CURSOS.get(c, c): c for c in cursos_disponiveis}
    labels = list(opcoes.keys())

    st.markdown(
        "<h2 style='margin-bottom:4px'>Selecione o curso</h2>",
        unsafe_allow_html=True,
    )
    cols = st.columns(min(len(labels), 5))
    curso_sel_label = st.session_state.get("curso_sel_label", labels[0])

    for i, (col, label) in enumerate(zip(cols, labels)):
        with col:
            ativo = curso_sel_label == label
            cor_bg = "#1a6b3c" if ativo else "#f0f2f6"
            cor_tx = "#fff" if ativo else "#333"
            if st.button(label, key=f"btn_curso_{i}",
                         use_container_width=True):
                st.session_state["curso_sel_label"] = label
                st.rerun()

    curso_sel_label = st.session_state.get("curso_sel_label", labels[0])
    curso_sel = opcoes[curso_sel_label]
    df_curso = df_todos[df_todos["curso"] == curso_sel].copy()

    st.markdown(f"### {curso_sel_label} `({curso_sel})`")
    st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# PÁGINAS
# ═══════════════════════════════════════════════════════════════════════════

if pagina == "🏠 Início":
    st.title("🎓 Matrizes Curriculares — UFRGS")
    st.markdown("""
    Sistema de visualização das matrizes curriculares do
    **Bacharelado Interdisciplinar em Ciência e Tecnologia (BICT)**
    e dos cursos de segundo ciclo.
    """)

    st.divider()
    st.markdown("### Cursos disponíveis")
    cols = st.columns(min(len(cursos_disponiveis), 3))
    for i, curso in enumerate(cursos_disponiveis):
        with cols[i % 3]:
            df_c = df_todos[df_todos["curso"] == curso]
            ch = int(df_c.drop_duplicates("codigo")["carga_horaria"].sum())
            nome_longo = NOMES_CURSOS.get(curso, curso)
            st.metric(
                label=nome_longo,
                value=f"{len(df_c)} componentes",
                delta=f"{ch}h total",
            )

    st.divider()
    st.markdown("""
    **Como usar:**
    - Use o menu à esquerda para navegar entre as seções
    - Em cada seção, escolha o curso pelos botões no topo
    - Para comparar cursos, acesse a seção **Comparação**
    """)

elif pagina == "📋 Matriz Curricular":
    render_matriz(df_curso)

elif pagina == "🔗 Grafo de Pré-req.":
    st.markdown("#### Grafo de pré-requisitos")
    render_grafo(df_curso)

elif pagina == "📊 Distribuição":
    st.markdown("#### Distribuição de carga horária e créditos")
    render_distribuicao(df_curso)

elif pagina == "🔄 Comparação":
    st.title("🔄 Comparação entre cursos")
    opcoes_comp = {NOMES_CURSOS.get(c, c): c for c in cursos_disponiveis}
    labels_comp = list(opcoes_comp.keys())
    sel = st.multiselect(
        "Selecione 2 ou mais cursos para comparar",
        labels_comp,
        default=labels_comp[:2],
    )
    cursos_sel = [opcoes_comp[s] for s in sel]
    render_comparacao(df_todos, cursos_sel)
