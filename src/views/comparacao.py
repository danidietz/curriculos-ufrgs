"""Comparação entre cursos."""
import streamlit as st
import pandas as pd
import plotly.express as px


def render_comparacao(df_todos: pd.DataFrame, cursos_sel: list[str]) -> None:
    if len(cursos_sel) < 2:
        st.info("Selecione ao menos 2 cursos para comparar.")
        return

    df = df_todos[df_todos["curso"].isin(cursos_sel)]

    tab1, tab2, tab3 = st.tabs(["🔄 Componentes compartilhados", "📊 CH por curso", "📋 Diferenças"])

    with tab1:
        sets = {c: set(df[df["curso"] == c]["codigo"]) for c in cursos_sel}
        compartilhados = set.intersection(*sets.values())
        st.metric("Componentes em comum", len(compartilhados))
        if compartilhados:
            df_comp = df[df["codigo"].isin(compartilhados)].drop_duplicates("codigo")[["codigo","nome","carga_horaria"]]
            st.dataframe(df_comp.rename(columns={"codigo":"Código","nome":"Nome","carga_horaria":"CH (h)"}),
                         use_container_width=True, hide_index=True)

    with tab2:
        df_ch = df.groupby("curso")["carga_horaria"].sum().reset_index()
        df_ch.columns = ["Curso", "CH Total (h)"]
        fig = px.bar(df_ch, x="Curso", y="CH Total (h)",
                     color="Curso", text_auto=True)
        fig.update_layout(showlegend=False, height=380, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("#### Disciplinas exclusivas por curso")
        for curso in cursos_sel:
            outros = set.union(*[s for c, s in sets.items() if c != curso])
            exclusivos = sets[curso] - outros
            df_exc = df[(df["curso"] == curso) & (df["codigo"].isin(exclusivos))][["codigo","nome","etapa","carater","carga_horaria"]]
            with st.expander(f"**{curso}** — {len(exclusivos)} exclusivas"):
                if df_exc.empty:
                    st.write("Nenhuma.")
                else:
                    st.dataframe(df_exc.rename(columns={
                        "codigo":"Código","nome":"Nome","etapa":"Etapa",
                        "carater":"Caráter","carga_horaria":"CH (h)"
                    }), use_container_width=True, hide_index=True)
