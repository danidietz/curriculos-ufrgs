"""Gráficos de distribuição de CH e créditos por etapa."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_distribuicao(df_curso: pd.DataFrame) -> None:
    if df_curso.empty:
        st.warning("Sem dados.")
        return

    tab1, tab2, tab3 = st.tabs(["📊 CH por Etapa", "📈 Créditos por Etapa", "🥧 Obrig vs Eletiva"])

    with tab1:
        df_ch = (
            df_curso[df_curso["etapa"].notna()]
            .groupby(["etapa", "carater"], as_index=False)["carga_horaria"]
            .sum()
        )
        df_ch["etapa"] = df_ch["etapa"].astype(int)
        df_ch = df_ch.sort_values("etapa")
        fig = px.bar(df_ch, x="etapa", y="carga_horaria", color="carater",
                     labels={"etapa": "Etapa", "carga_horaria": "Carga Horária (h)", "carater": "Caráter"},
                     color_discrete_map={"Obrigatória": "#1a6b3c", "Eletiva": "#1a4a7a"},
                     barmode="stack")
        fig.update_layout(height=400, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_cr = (
            df_curso[df_curso["etapa"].notna()]
            .groupby(["etapa", "carater"], as_index=False)["creditos"]
            .sum()
        )
        df_cr["etapa"] = df_cr["etapa"].astype(int)
        df_cr = df_cr.sort_values("etapa")
        fig2 = px.bar(df_cr, x="etapa", y="creditos", color="carater",
                      labels={"etapa": "Etapa", "creditos": "Créditos", "carater": "Caráter"},
                      color_discrete_map={"Obrigatória": "#1a6b3c", "Eletiva": "#1a4a7a"},
                      barmode="stack")
        fig2.update_layout(height=400, margin=dict(t=20))
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        contagem = df_curso["carater"].value_counts().reset_index()
        contagem.columns = ["carater", "quantidade"]
        fig3 = px.pie(contagem, values="quantidade", names="carater",
                      color="carater",
                      color_discrete_map={"Obrigatória": "#1a6b3c", "Eletiva": "#1a4a7a"})
        fig3.update_layout(height=350, margin=dict(t=20))

        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(fig3, use_container_width=True)
        with col2:
            st.markdown("### Resumo")
            for _, row in contagem.iterrows():
                pct = 100 * row["quantidade"] / len(df_curso)
                st.metric(row["carater"], f"{row['quantidade']} disc", f"{pct:.0f}%")
            ch_obrig = df_curso[df_curso["carater"]=="Obrigatória"]["carga_horaria"].sum()
            ch_elet  = df_curso[df_curso["carater"]=="Eletiva"]["carga_horaria"].sum()
            st.markdown(f"**CH Obrigatória:** {int(ch_obrig)}h")
            st.markdown(f"**CH Eletiva:** {int(ch_elet)}h")

        # Distribuição por Natureza (só BICT)
        if df_curso["natureza"].notna().any():
            st.divider()
            st.markdown("### Distribuição por Natureza (BICT)")
            df_nat = df_curso[df_curso["natureza"].notna()].copy()
            nat_ch = df_nat.groupby("natureza")["carga_horaria"].sum().reset_index()
            _labels = {"HUM": "Humanidades", "INT": "Interdisciplinar",
                       "TEC": "Tecnologia", "CFU": "Ciências Fund."}
            nat_ch["label"] = nat_ch["natureza"].map(_labels).fillna(nat_ch["natureza"])
            fig4 = px.pie(nat_ch, values="carga_horaria", names="label",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig4.update_layout(height=300, margin=dict(t=10))
            st.plotly_chart(fig4, use_container_width=True)
