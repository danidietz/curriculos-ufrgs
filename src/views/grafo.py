"""Grafo de pré-requisitos usando NetworkX + Plotly."""
import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go


def _build_graph(df: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_node(row["codigo"], nome=row["nome"], etapa=row["etapa"],
                   carater=row["carater"], ch=row["carga_horaria"])
        for pre in (row["prereqs"] or []):
            G.add_edge(pre, row["codigo"])
    return G


def _layout(G: nx.DiGraph, df: pd.DataFrame) -> dict:
    etapa_map = df.set_index("codigo")["etapa"].to_dict()
    etapas_unicas = sorted(set(v for v in etapa_map.values() if v is not None))
    etapa_idx = {e: i for i, e in enumerate(etapas_unicas)}

    pos = {}
    contadores = {e: 0 for e in etapas_unicas}
    for node in G.nodes():
        et = etapa_map.get(node)
        if et in etapa_idx:
            x = etapa_idx[et]
            y = -contadores[et]
            contadores[et] += 1
        else:
            x = len(etapas_unicas)
            y = -contadores.get("sem", 0)
            contadores["sem"] = contadores.get("sem", 0) + 1
        pos[node] = (x, y)
    return pos


def render_grafo(df_curso: pd.DataFrame) -> None:
    if df_curso.empty:
        st.warning("Sem dados.")
        return

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        etapas = sorted(df_curso["etapa"].dropna().unique())
        etapas_sel = st.multiselect("Etapas", [int(e) for e in etapas],
                                    default=[int(e) for e in etapas],
                                    format_func=lambda x: f"Etapa {x}")
    with col2:
        carateres = df_curso["carater"].unique().tolist()
        carater_sel = st.multiselect("Caráter", carateres, default=carateres)

    df_f = df_curso[df_curso["etapa"].isin(etapas_sel) & df_curso["carater"].isin(carater_sel)]

    G = _build_graph(df_f)
    if len(G.nodes()) == 0:
        st.info("Nenhum nó para exibir.")
        return

    pos = _layout(G, df_f)

    # Arestas
    edge_x, edge_y = [], []
    for u, v in G.edges():
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                             line=dict(width=1, color="#aaa"),
                             hoverinfo="none", showlegend=False)

    # Nós
    cores = {"Obrigatória": "#1a6b3c", "Eletiva": "#1a4a7a"}
    node_x, node_y, node_text, node_hover, node_color = [], [], [], [], []
    meta = df_f.set_index("codigo")

    for node in G.nodes():
        if node not in pos:
            continue
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        if node in meta.index:
            r = meta.loc[node]
            node_text.append(node)
            node_hover.append(f"<b>{r['nome']}</b><br>{node}<br>Etapa {r['etapa']} · {int(r['ch'])}h")
            node_color.append(cores.get(r["carater"], "#888"))
        else:
            node_text.append(node)
            node_hover.append(node)
            node_color.append("#ccc")

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=14, color=node_color, line=dict(width=1, color="#fff")),
        text=node_text, textposition="top center", textfont=dict(size=8),
        hovertext=node_hover, hoverinfo="text", showlegend=False,
    )

    etapas_unicas = sorted(df_f["etapa"].dropna().unique())
    annotations = [
        dict(x=i, y=1, xref="x", yref="paper",
             text=f"<b>Etapa {int(e)}</b>", showarrow=False,
             font=dict(size=12), align="center")
        for i, e in enumerate(etapas_unicas)
    ]

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        height=550, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#f8f9fa",
        annotations=annotations,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🟢 Obrigatória   🔵 Eletiva   Setas = pré-requisitos")
