"""
views/distribuicao.py — Gráficos de distribuição de créditos e carga horária.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


_CORES = {
    "Obrigatória": "#1D9E75",
    "Eletiva":     "#534AB7",
    "Desconhecido":"#888780",
}
_NATUREZA_CORES = {
    "HUM": "#854F0B",
    "INT": "#0F6E56",
    "TEC": "#185FA5",
    "CFU": "#26215C",
}


def render_distribuicao(df_curso: pd.DataFrame) -> None:
    """Renderiza os gráficos de distribuição para um curso."""

    df = df_curso[df_curso["etapa"].notna()].copy()
    df["etapa"] = df["etapa"].astype(int)

    tab1, tab2, tab3 = st.tabs([
        "📊 CH por Etapa", "🎓 Créditos por Etapa", "🥧 Obrigatórias vs Eletivas"
    ])

    with tab1:
        _grafico_ch_por_etapa(df)

    with tab2:
        _grafico_creditos_por_etapa(df)

    with tab3:
        _grafico_pizza(df_curso)

    # Natureza (só se tiver dados)
    if df_curso["natureza"].notna().any():
        st.markdown("---")
        _grafico_natureza(df_curso)


def _grafico_ch_por_etapa(df: pd.DataFrame) -> None:
    agrupado = (
        df.groupby(["etapa", "carater"])["carga_horaria"]
        .sum()
        .reset_index()
    )
    fig = px.bar(
        agrupado, x="etapa", y="carga_horaria", color="carater",
        color_discrete_map=_CORES,
        labels={"etapa": "Etapa", "carga_horaria": "Carga Horária (h)", "carater": "Caráter"},
        title="Carga Horária por Etapa",
        barmode="stack",
        text_auto=True,
    )
    fig.update_layout(
        paper_bgcolor="#F7F6F2", plot_bgcolor="#F7F6F2",
        legend_title_text="Caráter",
        xaxis=dict(tickmode="linear"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabela resumo
    pivot = agrupado.pivot_table(
        index="etapa", columns="carater", values="carga_horaria", fill_value=0
    )
    pivot["Total"] = pivot.sum(axis=1)
    st.dataframe(pivot.style.format("{:.0f}h"), use_container_width=True)


def _grafico_creditos_por_etapa(df: pd.DataFrame) -> None:
    agrupado = (
        df.groupby(["etapa", "carater"])["creditos"]
        .sum()
        .reset_index()
    )
    fig = px.bar(
        agrupado, x="etapa", y="creditos", color="carater",
        color_discrete_map=_CORES,
        labels={"etapa": "Etapa", "creditos": "Créditos", "carater": "Caráter"},
        title="Créditos por Etapa",
        barmode="stack",
        text_auto=True,
    )
    fig.update_layout(
        paper_bgcolor="#F7F6F2", plot_bgcolor="#F7F6F2",
        xaxis=dict(tickmode="linear"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_pizza(df_curso: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    # Por caráter — CH
    with col1:
        por_carater = df_curso.groupby("carater")["carga_horaria"].sum().reset_index()
        fig = go.Figure(go.Pie(
            labels=por_carater["carater"],
            values=por_carater["carga_horaria"],
            marker_colors=[_CORES.get(c, "#aaa") for c in por_carater["carater"]],
            hole=0.4,
            textinfo="label+percent",
        ))
        fig.update_layout(
            title="CH por Caráter",
            paper_bgcolor="#F7F6F2",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Por caráter — componentes
    with col2:
        contagem = df_curso.groupby("carater")["codigo"].count().reset_index()
        fig = go.Figure(go.Pie(
            labels=contagem["carater"],
            values=contagem["codigo"],
            marker_colors=[_CORES.get(c, "#aaa") for c in contagem["carater"]],
            hole=0.4,
            textinfo="label+percent",
        ))
        fig.update_layout(
            title="Nº de Componentes por Caráter",
            paper_bgcolor="#F7F6F2",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


def _grafico_natureza(df_curso: pd.DataFrame) -> None:
    """Apenas para cursos com coluna Natureza preenchida (BICT)."""
    st.markdown("#### Distribuição por Natureza (BICT)")
    por_nat = df_curso.groupby("natureza")["carga_horaria"].sum().reset_index()
    fig = px.bar(
        por_nat, x="natureza", y="carga_horaria",
        color="natureza",
        color_discrete_map=_NATUREZA_CORES,
        labels={"natureza": "Natureza", "carga_horaria": "CH (h)"},
        title="Carga Horária por Natureza",
        text_auto=True,
    )
    fig.update_layout(paper_bgcolor="#F7F6F2", plot_bgcolor="#F7F6F2", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
