import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="IPCA Aracaju vs. Brasil", layout="wide")
st.title("📊 Análise da Inflação: Aracaju vs. Média Nacional (2014–2026)")

df_full = pd.read_parquet("data/processed/ipca_aracaju_comparativo.parquet")
df_decomp = pd.read_csv("reports/analise/decomposicao_aracaju_vs_brasil.csv")

col_data = "data_ref" if "data_ref" in df_full.columns else "data"
col_grupo = "grupo_nome" if "grupo_nome" in df_full.columns else "grupo"

st.sidebar.header("Filtros do Painel")
opcoes_cidades = list(df_full["localidade"].unique())
cidades = st.sidebar.multiselect(
    "Selecione as Localidades:",
    options=opcoes_cidades,
    default=opcoes_cidades
)

st.subheader("Figura 1: Inflação Acumulada em 12 Meses (%)")
df_geral = df_full[
    (df_full[col_grupo].str.contains("geral", case=False, na=False)) &
    (df_full["localidade"].isin(cidades))
].sort_values(col_data)

fig1 = px.line(
    df_geral, x=col_data, y="var_12m", color="localidade",
    labels={col_data: "Período", "var_12m": "Acumulado 12 meses (%)", "localidade": "Localidade"}
)
fig1.add_vline(x="2020-01-01", line_dash="dash", line_color="gray", annotation_text="Mudança POF (2020)")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Figura 2: Diferença de Contribuição Acumulada por Grupo (Aracaju vs. Brasil em p.p.)")
col_diff = [c for c in df_decomp.columns if "dif" in c.lower() and "contrib" in c.lower()][0]
col_grp_csv = [c for c in df_decomp.columns if "grupo" in c.lower() and "cod" not in c.lower()][0]

df_decomp_sorted = df_decomp.sort_values(col_diff)
fig2 = px.bar(
    df_decomp_sorted, x=col_diff, y=col_grp_csv, orientation="h",
    color=col_diff, color_continuous_scale="RdBu_r",
    labels={col_diff: "Diferença de Contribuição (p.p.)", col_grp_csv: "Grupo do IPCA"}
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Tabela 1: Resumo da Inflação Acumulada por Localidade")
df_resumo = pd.read_csv("reports/analise/resumo_inflacao_localidades.csv")
st.dataframe(df_resumo, use_container_width=True, hide_index=True)