"""Visualização da matriz curricular em grade por etapa."""
import streamlit as st
import pandas as pd

_COR_CARATER = {
    "Obrigatória": "#1a6b3c",
    "Eletiva":     "#1a4a7a",
}
_COR_NATUREZA = {
    "HUM": "#8B1A1A",
    "INT": "#2E6B4F",
    "TEC": "#1A4A8B",
    "CFU": "#6B4F1A",
}
_LABEL_NATUREZA = {
    "HUM": "Humanidades",
    "INT": "Interdisciplinar",
    "TEC": "Tecnologia",
    "CFU": "Ciências Fund.",
}


def _badge_carater(carater: str) -> str:
    cor = _COR_CARATER.get(carater, "#555")
    return f'<span style="background:{cor};color:#fff;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:600">{carater}</span>'


def _badge_natureza(natureza: str) -> str:
    if not natureza:
        return ""
    cor = _COR_NATUREZA.get(natureza, "#888")
    label = _LABEL_NATUREZA.get(natureza, natureza)
    return f'<span style="background:{cor};color:#fff;padding:2px 6px;border-radius:10px;font-size:10px;margin-left:4px">{label}</span>'


def render_matriz(df_curso: pd.DataFrame) -> None:
    if df_curso.empty:
        st.warning("Sem dados para este curso.")
        return

    # ── Resumo numérico ──────────────────────────────────────────────────
    # Deduplica por código para evitar contar a mesma disciplina duas vezes
    df_unico = df_curso.drop_duplicates(subset="codigo")
    ch_total = int(df_unico["carga_horaria"].sum())
    cr_total = int(df_unico["creditos"].sum())
    n_obrig = int((df_curso["carater"] == "Obrigatória").sum())
    n_elet  = int((df_curso["carater"] == "Eletiva").sum())
    n_total = len(df_curso)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Componentes", n_total)
    c2.metric("Obrigatórias", n_obrig)
    c3.metric("Eletivas", n_elet)
    c4.metric("Carga Horária Total", f"{ch_total}h")

    st.divider()

    # ── Grade por etapa ──────────────────────────────────────────────────
    etapas = sorted(df_curso["etapa"].dropna().unique())
    sem_etapa = df_curso[df_curso["etapa"].isna()]

    if not etapas:
        st.info("Nenhuma etapa identificada.")
        return

    # Filtros inline
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        etapas_sel = st.multiselect(
            "Filtrar etapas",
            options=[int(e) for e in etapas],
            default=[int(e) for e in etapas],
            format_func=lambda x: f"Etapa {x}",
        )
    with col_f2:
        carater_sel = st.multiselect(
            "Filtrar caráter",
            options=df_curso["carater"].unique().tolist(),
            default=df_curso["carater"].unique().tolist(),
        )

    df_filtrado = df_curso[
        df_curso["etapa"].isin(etapas_sel) &
        df_curso["carater"].isin(carater_sel)
    ]

    # Renderiza colunas por etapa
    etapas_vis = sorted(df_filtrado["etapa"].dropna().unique())
    if not etapas_vis:
        st.info("Nenhuma disciplina para os filtros selecionados.")
        return

    colunas = st.columns(len(etapas_vis))
    for col, etapa in zip(colunas, etapas_vis):
        df_etapa = df_filtrado[df_filtrado["etapa"] == etapa]
        ch_etapa = int(df_etapa["carga_horaria"].sum())
        with col:
            st.markdown(
                f"<div style='text-align:center;font-weight:700;font-size:13px;"
                f"background:#f0f2f6;padding:6px;border-radius:6px;margin-bottom:8px'>"
                f"Etapa {int(etapa)}<br><small>{len(df_etapa)} disc · {ch_etapa}h</small></div>",
                unsafe_allow_html=True,
            )
            for _, row in df_etapa.sort_values("nome").iterrows():
                prereqs_txt = ""
                if row["prereqs"]:
                    prereqs_txt = f"<div style='font-size:9px;color:#888;margin-top:4px'>Pré: {', '.join(row['prereqs'])}</div>"
                natureza_badge = _badge_natureza(row.get("natureza", ""))
                carater_badge = _badge_carater(row["carater"])
                ch = int(row["carga_horaria"])

                card = f"""
<div style="border:1px solid #ddd;border-radius:8px;padding:8px 10px;margin-bottom:8px;
background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.08)">
  <div style="font-size:10px;color:#888;font-family:monospace">{row['codigo']}</div>
  <div style="font-size:12px;font-weight:600;line-height:1.3;margin:3px 0">{row['nome']}</div>
  <div style="display:flex;flex-wrap:wrap;gap:3px;align-items:center;margin-top:5px">
    {carater_badge}{natureza_badge}
    <span style="margin-left:auto;font-size:10px;color:#555">{ch}h</span>
  </div>
  {prereqs_txt}
</div>"""
                st.markdown(card, unsafe_allow_html=True)

    # Disciplinas sem etapa
    if not sem_etapa.empty and len(carater_sel) == len(df_curso["carater"].unique()):
        with st.expander(f"Sem etapa definida ({len(sem_etapa)})"):
            for _, row in sem_etapa.iterrows():
                st.markdown(f"- `{row['codigo']}` {row['nome']} — {row['carater']} — {int(row['carga_horaria'])}h")
