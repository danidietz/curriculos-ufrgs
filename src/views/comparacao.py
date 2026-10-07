"""
views/comparacao.py — Comparação entre dois ou mais cursos.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


_PALETA = ["#534AB7", "#1D9E75", "#D85A30", "#BA7517", "#185FA5", "#854F0B"]


def render_comparacao(df_todos: pd.DataFrame, cursos_sel: list[str]) -> None:
    """Renderiza a comparação entre os cursos selecionados."""
    if len(cursos_sel) < 2:
        st.info("Selecione ao menos 2 cursos para comparar.")
        return

    df = df_todos[df_todos["curso"].isin(cursos_sel)].copy()

    tab1, tab2, tab3 = st.tabs([
        "🔄 Componentes Compartilhados",
        "📊 CH Comparativa",
        "📋 Diferenças Detalhadas",
    ])

    with tab1:
        _compartilhados(df, cursos_sel)

    with tab2:
        _ch_comparativa(df, cursos_sel)

    with tab3:
        _diferencas(df, cursos_sel)


def _compartilhados(df: pd.DataFrame, cursos: list[str]) -> None:
    st.markdown("### Componentes em comum entre os cursos selecionados")

    # Conjuntos de códigos por curso
    sets = {c: set(df[df["curso"] == c]["codigo"]) for c in cursos}
    todos = set.union(*sets.values())
    comuns = set.intersection(*sets.values())
    exclusivos = {c: sets[c] - set.union(*(sets[cc] for cc in cursos if cc != c))
                  for c in cursos}

    c1, c2 = st.columns(2)
    c1.metric("Componentes únicos no total", len(todos))
    c2.metric("Compartilhados por TODOS os cursos", len(comuns))

    # Tabela de componentes compartilhados
    if comuns:
        st.markdown("#### Compartilhados por todos os cursos selecionados")
        df_comuns = df[df["codigo"].isin(comuns)].copy()
        resumo = []
        for cod in sorted(comuns):
            linha = {"Código": cod}
            nome = df_comuns[df_comuns["codigo"] == cod]["nome"].iloc[0]
            linha["Nome"] = nome
            for curso in cursos:
                sub = df_comuns[(df_comuns["codigo"] == cod) & (df_comuns["curso"] == curso)]
                if not sub.empty:
                    r = sub.iloc[0]
                    linha[curso] = f"Etapa {int(r['etapa']) if r['etapa'] else '?'} · {r['carater'][:3]}"
                else:
                    linha[curso] = "—"
            resumo.append(linha)
        st.dataframe(pd.DataFrame(resumo), use_container_width=True)
    else:
        st.info("Nenhum componente é compartilhado por TODOS os cursos selecionados.")

    # Exclusivos por curso
    st.markdown("#### Componentes exclusivos de cada curso")
    cols = st.columns(len(cursos))
    for col, curso in zip(cols, cursos):
        excl = exclusivos[curso]
        with col:
            st.markdown(f"**{curso}** ({len(excl)})")
            if excl:
                df_excl = df[(df["curso"] == curso) & (df["codigo"].isin(excl))][["codigo", "nome"]]
                for _, row in df_excl.iterrows():
                    st.markdown(
                        f'<div style="font-size:11px;border-left:2px solid #534AB7;'
                        f'padding:2px 6px;margin-bottom:3px">'
                        f'<span style="font-family:monospace;color:#888">{row["codigo"]}</span><br>'
                        f'{row["nome"]}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("Sem exclusivos")


def _ch_comparativa(df: pd.DataFrame, cursos: list[str]) -> None:
    st.markdown("### Carga Horária Comparativa")

    # Total por curso e caráter
    agrup = df.groupby(["curso", "carater"])["carga_horaria"].sum().reset_index()
    fig = px.bar(
        agrup, x="curso", y="carga_horaria", color="carater",
        barmode="group",
        color_discrete_map={"Obrigatória": "#1D9E75", "Eletiva": "#534AB7"},
        labels={"curso": "Curso", "carga_horaria": "CH (h)", "carater": "Caráter"},
        title="Carga Horária Total por Curso e Caráter",
        text_auto=True,
    )
    fig.update_layout(paper_bgcolor="#F7F6F2", plot_bgcolor="#F7F6F2")
    st.plotly_chart(fig, use_container_width=True)

    # CH por etapa, lado a lado
    df_etapas = df[df["etapa"].notna()].copy()
    df_etapas["etapa"] = df_etapas["etapa"].astype(int)
    agrup_etapa = df_etapas.groupby(["curso", "etapa"])["carga_horaria"].sum().reset_index()
    fig2 = px.line(
        agrup_etapa, x="etapa", y="carga_horaria", color="curso",
        color_discrete_sequence=_PALETA,
        markers=True,
        labels={"etapa": "Etapa", "carga_horaria": "CH (h)", "curso": "Curso"},
        title="Evolução da CH por Etapa",
    )
    fig2.update_layout(paper_bgcolor="#F7F6F2", plot_bgcolor="#F7F6F2")
    st.plotly_chart(fig2, use_container_width=True)


def _diferencas(df: pd.DataFrame, cursos: list[str]) -> None:
    st.markdown("### Componentes com caráter ou etapa diferente entre cursos")

    # Componentes que aparecem em ≥2 cursos
    contagem = df.groupby("codigo")["curso"].nunique()
    codigos_comuns = contagem[contagem >= 2].index.tolist()

    if not codigos_comuns:
        st.info("Nenhum componente compartilhado entre os cursos selecionados.")
        return

    df_comuns = df[df["codigo"].isin(codigos_comuns)].copy()
    diferencas = []
    for cod in codigos_comuns:
        sub = df_comuns[df_comuns["codigo"] == cod]
        etapas_unicas = sub["etapa"].dropna().unique()
        carater_unicos = sub["carater"].unique()
        if len(etapas_unicas) > 1 or len(carater_unicos) > 1:
            linha = {
                "Código": cod,
                "Nome": sub["nome"].iloc[0],
            }
            for curso in cursos:
                r = sub[sub["curso"] == curso]
                if not r.empty:
                    rr = r.iloc[0]
                    linha[curso] = (
                        f"Etapa {int(rr['etapa']) if rr['etapa'] else '?'} · "
                        f"{rr['carater']} · {int(rr['carga_horaria'])}h"
                    )
                else:
                    linha[curso] = "—"
            diferencas.append(linha)

    if diferencas:
        st.dataframe(pd.DataFrame(diferencas), use_container_width=True)
        st.caption(f"{len(diferencas)} componentes com diferenças de etapa ou caráter entre os cursos.")
    else:
        st.success("Todos os componentes compartilhados têm etapa e caráter iguais nos cursos selecionados.")
