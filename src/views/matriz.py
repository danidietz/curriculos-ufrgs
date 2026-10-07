"""
views/matriz.py — Visualização da matriz curricular (grade por etapas).
"""
import pandas as pd
import streamlit as st


_COR_OBRIG = "#1D9E75"
_COR_ELET  = "#534AB7"
_COR_OUTRO = "#888780"

_NATUREZA_LABEL = {
    "HUM": "Humanidades",
    "INT": "Interdisciplinar",
    "TEC": "Tecnológica",
    "CFU": "Ciências Fundamentais",
}
_NATUREZA_COR = {
    "HUM": "#854F0B",
    "INT": "#0F6E56",
    "TEC": "#185FA5",
    "CFU": "#26215C",
    None: "#666",
}


def _card_html(row: pd.Series) -> str:
    """Gera o HTML de um cartão de disciplina."""
    cor_borda = (
        _COR_OBRIG if row["carater"] == "Obrigatória"
        else _COR_ELET if row["carater"] == "Eletiva"
        else _COR_OUTRO
    )
    nat = row.get("natureza")
    nat_label = _NATUREZA_LABEL.get(nat, nat or "")
    nat_cor = _NATUREZA_COR.get(nat, "#666")
    prereqs = row.get("prereqs", [])
    prereq_txt = ", ".join(prereqs) if isinstance(prereqs, list) and prereqs else ""

    badge_nat = (
        f'<span style="font-size:10px;background:{nat_cor};color:#fff;'
        f'padding:1px 6px;border-radius:10px;margin-right:4px">{nat_label}</span>'
        if nat_label else ""
    )
    badge_car = (
        f'<span style="font-size:10px;background:{cor_borda};color:#fff;'
        f'padding:1px 6px;border-radius:10px">{row["carater"]}</span>'
    )
    prereq_html = (
        f'<div style="font-size:10px;color:#888;margin-top:4px">Pré-req: {prereq_txt}</div>'
        if prereq_txt else ""
    )

    return f"""
    <div style="border-left:3px solid {cor_borda};background:#fff;
                border-radius:6px;padding:8px 10px;margin-bottom:6px;
                box-shadow:0 1px 3px rgba(0,0,0,.08)">
      <div style="font-size:10px;font-family:monospace;color:#888">{row['codigo']}</div>
      <div style="font-size:12px;font-weight:600;line-height:1.3;margin:3px 0">{row['nome']}</div>
      <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:4px">
        {badge_nat}{badge_car}
        <span style="font-size:10px;color:#555;margin-left:auto">{int(row['creditos'])}cr · {int(row['carga_horaria'])}h</span>
      </div>
      {prereq_html}
    </div>"""


def render_matriz(df_curso: pd.DataFrame) -> None:
    """Renderiza a matriz curricular completa de um curso."""
    etapas = sorted(
        [e for e in df_curso["etapa"].dropna().unique()],
        key=lambda x: int(x)
    )
    sem_etapa = df_curso[df_curso["etapa"].isna()]
    df_etapas = df_curso[df_curso["etapa"].notna()]

    n_cols = min(len(etapas), 6)  # máx 6 colunas lado a lado
    cols_por_linha = n_cols

    # Estatísticas rápidas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de componentes", len(df_curso))
    c2.metric("Obrigatórias", len(df_curso[df_curso["carater"] == "Obrigatória"]))
    c3.metric("Eletivas", len(df_curso[df_curso["carater"] == "Eletiva"]))
    c4.metric("Carga horária total",
              f"{int(df_curso.groupby('codigo')['carga_horaria'].first().sum())}h")

    st.markdown("---")

    # Grade por etapas
    for i in range(0, len(etapas), cols_por_linha):
        grupo = etapas[i:i + cols_por_linha]
        cols = st.columns(len(grupo))
        for col, etapa in zip(cols, grupo):
            disc_etapa = df_etapas[df_etapas["etapa"] == etapa].sort_values("nome")
            ch_etapa = int(disc_etapa["carga_horaria"].sum())
            cr_etapa = int(disc_etapa["creditos"].sum())
            with col:
                st.markdown(
                    f'<div style="background:#26215C;color:#fff;border-radius:8px 8px 0 0;'
                    f'padding:6px 10px;font-weight:600;font-size:13px;text-align:center">'
                    f'Etapa {int(etapa)}<br>'
                    f'<span style="font-size:10px;font-weight:400">{cr_etapa}cr · {ch_etapa}h</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                html = "".join(_card_html(row) for _, row in disc_etapa.iterrows())
                st.markdown(
                    f'<div style="max-height:600px;overflow-y:auto;'
                    f'background:#f7f6f2;padding:6px;border-radius:0 0 8px 8px">{html}</div>',
                    unsafe_allow_html=True
                )

    # Sem etapa definida
    if not sem_etapa.empty:
        st.markdown("### Sem Etapa Definida")
        html = "".join(_card_html(row) for _, row in sem_etapa.iterrows())
        st.markdown(
            f'<div style="background:#f7f6f2;padding:8px;border-radius:8px">{html}</div>',
            unsafe_allow_html=True
        )
