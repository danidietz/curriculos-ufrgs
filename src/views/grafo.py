"""
views/grafo.py — Grafo interativo de pré-requisitos.

Usa Plotly para renderizar no Streamlit com zoom, pan e destaque de nós.
NetworkX cuida do layout.
"""
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from typing import Optional


_COR_OBRIG   = "#1D9E75"
_COR_ELET    = "#534AB7"
_COR_DESTAQ  = "#D85A30"
_COR_DEPEND  = "#BA7517"
_COR_NEUTRO  = "#AAAAAA"
_COR_FUNDO   = "#F7F6F2"


def _build_graph(df: pd.DataFrame) -> nx.DiGraph:
    """Constrói dígrafo: aresta A→B significa 'A é pré-requisito de B'."""
    G = nx.DiGraph()

    for _, row in df.iterrows():
        codigo = row["codigo"]
        nome_curto = row["nome"][:35] + ("…" if len(row["nome"]) > 35 else "")
        G.add_node(
            codigo,
            nome=row["nome"],
            nome_curto=nome_curto,
            carater=row["carater"],
            etapa=row["etapa"],
            creditos=row["creditos"],
            carga_horaria=row["carga_horaria"],
        )
        prereqs = row.get("prereqs", [])
        if isinstance(prereqs, list):
            for pre in prereqs:
                if pre in df["codigo"].values:
                    G.add_edge(pre, codigo)  # pre → codigo (pre é requisito de codigo)

    return G


def _layout_por_etapa(G: nx.DiGraph, df: pd.DataFrame) -> dict:
    """
    Posiciona nós em colunas por etapa.
    Nós sem etapa ficam numa coluna extra à direita.
    """
    etapa_map = dict(zip(df["codigo"], df["etapa"]))
    etapas_unicas = sorted(set(
        int(e) for e in df["etapa"].dropna().unique()
    ))

    pos = {}
    for etapa in etapas_unicas:
        nos_etapa = [n for n in G.nodes if etapa_map.get(n) == etapa]
        x = etapa
        for i, no in enumerate(sorted(nos_etapa)):
            pos[no] = (x, -i)

    # Nós sem etapa
    sem_etapa = [n for n in G.nodes if etapa_map.get(n) is None]
    x_extra = (max(etapas_unicas) + 1) if etapas_unicas else 1
    for i, no in enumerate(sorted(sem_etapa)):
        pos[no] = (x_extra, -i)

    return pos


def render_grafo(df_curso: pd.DataFrame) -> None:
    """Renderiza o grafo de pré-requisitos de um curso."""

    # Filtros laterais
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filtros do grafo**")

    etapas_disp = sorted([int(e) for e in df_curso["etapa"].dropna().unique()])
    etapas_sel = st.sidebar.multiselect(
        "Etapas visíveis",
        options=etapas_disp,
        default=etapas_disp,
        key="grafo_etapas"
    )

    carater_sel = st.sidebar.multiselect(
        "Caráter",
        options=df_curso["carater"].unique().tolist(),
        default=df_curso["carater"].unique().tolist(),
        key="grafo_carater"
    )

    # Seleção de nó para destaque
    codigos_ord = sorted(df_curso["codigo"].unique().tolist())
    destaque = st.selectbox(
        "Destacar disciplina (e seus pré-requisitos / dependentes):",
        options=["— nenhuma —"] + codigos_ord,
        key="grafo_destaque"
    )

    # Filtrar DataFrame
    df_filtrado = df_curso[
        (df_curso["etapa"].isna() | df_curso["etapa"].isin(etapas_sel)) &
        (df_curso["carater"].isin(carater_sel))
    ].copy()

    if df_filtrado.empty:
        st.info("Nenhum componente com os filtros selecionados.")
        return

    G = _build_graph(df_filtrado)
    pos = _layout_por_etapa(G, df_filtrado)

    # Determinar nós em destaque
    nos_destaq = set()
    nos_depend = set()
    no_sel = destaque if destaque != "— nenhuma —" else None

    if no_sel and no_sel in G:
        nos_destaq = nx.ancestors(G, no_sel)      # pré-requisitos (diretos e indiretos)
        nos_depend = nx.descendants(G, no_sel)    # dependentes
        nos_destaq.add(no_sel)

    # — Arestas —
    edge_traces = []
    for u, v in G.edges():
        if u not in pos or v not in pos:
            continue
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        if no_sel:
            if u in nos_destaq or v in nos_destaq or u in nos_depend or v in nos_depend:
                cor_aresta = _COR_DESTAQ
                opacidade = 0.9
                largura = 2
            else:
                cor_aresta = _COR_NEUTRO
                opacidade = 0.15
                largura = 1
        else:
            cor_aresta = "#AFA9EC"
            opacidade = 0.6
            largura = 1.2

        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=largura, color=cor_aresta),
            opacity=opacidade,
            hoverinfo="none",
            showlegend=False,
        ))

    # — Nós —
    node_x, node_y, node_text, node_color, node_size, node_hover = [], [], [], [], [], []

    for no in G.nodes():
        if no not in pos:
            continue
        x, y = pos[no]
        data = G.nodes[no]
        carater = data.get("carater", "")
        etapa = data.get("etapa")
        creditos = data.get("creditos", 0)
        ch = data.get("carga_horaria", 0)

        node_x.append(x)
        node_y.append(y)
        node_text.append(data.get("nome_curto", no))

        # Cor
        if no_sel:
            if no == no_sel:
                cor = _COR_DESTAQ
                tam = 20
            elif no in nos_destaq:
                cor = _COR_DEPEND
                tam = 16
            elif no in nos_depend:
                cor = _COR_OBRIG
                tam = 16
            else:
                cor = "#DDDDDD"
                tam = 10
        else:
            cor = _COR_OBRIG if carater == "Obrigatória" else (
                _COR_ELET if carater == "Eletiva" else _COR_NEUTRO
            )
            tam = 14

        node_color.append(cor)
        node_size.append(tam)

        prereqs_lista = data.get("prereqs", [])
        node_hover.append(
            f"<b>{data.get('nome', no)}</b><br>"
            f"Código: {no}<br>"
            f"Etapa: {int(etapa) if etapa else 'Sem etapa'}<br>"
            f"Caráter: {carater}<br>"
            f"Créditos: {creditos} | CH: {ch}h"
        )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        textfont=dict(size=9, family="Arial"),
        hovertext=node_hover,
        hoverinfo="text",
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=1.5, color="#fff"),
        ),
        showlegend=False,
    )

    # — Rótulos de etapa (eixo x) —
    etapa_shapes = []
    etapa_annotations = []
    for etapa in etapas_disp:
        etapa_annotations.append(dict(
            x=etapa, y=1.02,
            xref="x", yref="paper",
            text=f"<b>Etapa {etapa}</b>",
            showarrow=False,
            font=dict(size=11, color="#26215C"),
        ))
        etapa_shapes.append(dict(
            type="line",
            x0=etapa, x1=etapa,
            y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="#E4E2D9", width=1, dash="dot"),
        ))

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            paper_bgcolor=_COR_FUNDO,
            plot_bgcolor=_COR_FUNDO,
            height=650,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            shapes=etapa_shapes,
            annotations=etapa_annotations,
            dragmode="pan",
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "scrollZoom": True,
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],
    })

    # Legenda manual
    leg1, leg2, leg3, leg4 = st.columns(4)
    leg1.markdown(
        f'<span style="color:{_COR_OBRIG}">●</span> Obrigatória', unsafe_allow_html=True)
    leg2.markdown(
        f'<span style="color:{_COR_ELET}">●</span> Eletiva', unsafe_allow_html=True)
    leg3.markdown(
        f'<span style="color:{_COR_DESTAQ}">●</span> Selecionada', unsafe_allow_html=True)
    leg4.markdown(
        f'<span style="color:{_COR_DEPEND}">●</span> Pré-requisito direto/indireto',
        unsafe_allow_html=True)
