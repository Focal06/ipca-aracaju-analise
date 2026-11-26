from pathlib import Path
import numpy as np
import pandas as pd

PARQUET_PATH = Path("data/processed/ipca_aracaju_comparativo.parquet")
OUT_DIR = Path("reports/analise")
OUT_DIR.mkdir(parents=True, exist_ok=True)

COD_INDICE_GERAL = "7169"
GRUPOS_9 = [
    "7170",
    "7445",
    "7486",
    "7558",
    "7625",
    "7660",
    "7712",
    "7766",
    "7786",
]


def _inflacao_acumulada_pct(serie_var_mensal: pd.Series) -> float:
    fatores = 1.0 + (serie_var_mensal.dropna() / 100.0)
    if len(fatores) == 0:
        return np.nan
    return float((np.prod(fatores) - 1.0) * 100.0)


def rodar_analise():
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo {PARQUET_PATH} não encontrado. Rode src/transform.py primeiro."
        )

    df = pd.read_parquet(PARQUET_PATH)
    df["data_ref"] = pd.to_datetime(df["data_ref"])
    df["grupo_codigo"] = df["grupo_codigo"].astype(str).str.strip()

    # Contribuição mensal aproximada de cada grupo em pontos percentuais (p.p.)
    df["contrib_mensal_pp"] = (
        df["peso_mensal"].fillna(0.0) * df["var_mensal"].fillna(0.0)
    ) / 100.0

    # 1. Inflação acumulada total e por regime POF (Tabela 1419 vs Tabela 7060) para o Índice Geral
    df_geral = df[df["grupo_codigo"] == COD_INDICE_GERAL].copy()

    resumo_loc = []
    for loc, g in df_geral.groupby("localidade"):
        g = g.sort_values("data_ref")
        acum_total = _inflacao_acumulada_pct(g["var_mensal"])
        acum_1419 = _inflacao_acumulada_pct(
            g[g["tabela_sidra"] == "1419"]["var_mensal"]
        )
        acum_7060 = _inflacao_acumulada_pct(
            g[g["tabela_sidra"] == "7060"]["var_mensal"]
        )
        resumo_loc.append(
            {
                "localidade": loc,
                "acum_total_pct": round(acum_total, 2),
                "acum_t1419_pct": round(acum_1419, 2),
                "acum_t7060_pct": round(acum_7060, 2),
                "var_mensal_media_pct": round(float(g["var_mensal"].mean()), 3),
            }
        )

    df_resumo_loc = pd.DataFrame(resumo_loc)
    base_br = df_resumo_loc.loc[
        df_resumo_loc["localidade"] == "Brasil", "acum_total_pct"
    ].iloc[0]
    df_resumo_loc["diff_vs_brasil_pp"] = (
        df_resumo_loc["acum_total_pct"] - base_br
    ).round(2)
    df_resumo_loc = df_resumo_loc.sort_values("acum_total_pct", ascending=False)

    # 2. Decomposição da soma das contribuições mensais para os 9 grupos oficiais
    df_grupos = df[df["grupo_codigo"].isin(GRUPOS_9)].copy()

    contrib_por_grupo = (
        df_grupos.groupby(
            ["localidade", "grupo_codigo", "grupo"], as_index=False, dropna=False
        )
        .agg(
            soma_contrib_pp=("contrib_mensal_pp", "sum"),
            peso_medio_pct=("peso_mensal", "mean"),
            var_mensal_media_pct=("var_mensal", "mean"),
        )
    )
    contrib_por_grupo["soma_contrib_pp"] = contrib_por_grupo[
        "soma_contrib_pp"
    ].round(2)
    contrib_por_grupo["peso_medio_pct"] = contrib_por_grupo["peso_medio_pct"].round(
        2
    )
    contrib_por_grupo["var_mensal_media_pct"] = contrib_por_grupo[
        "var_mensal_media_pct"
    ].round(3)

    aju_grp = (
        contrib_por_grupo[contrib_por_grupo["localidade"] == "Aracaju"]
        .set_index(["grupo_codigo", "grupo"])
    )
    br_grp = (
        contrib_por_grupo[contrib_por_grupo["localidade"] == "Brasil"]
        .set_index(["grupo_codigo", "grupo"])
    )

    comp_aju_br = pd.DataFrame(
        {
            "peso_medio_aju": aju_grp["peso_medio_pct"],
            "peso_medio_br": br_grp["peso_medio_pct"],
            "diff_peso_pp": (
                aju_grp["peso_medio_pct"] - br_grp["peso_medio_pct"]
            ).round(2),
            "contrib_aju_pp": aju_grp["soma_contrib_pp"],
            "contrib_br_pp": br_grp["soma_contrib_pp"],
            "diff_contrib_pp": (
                aju_grp["soma_contrib_pp"] - br_grp["soma_contrib_pp"]
            ).round(2),
        }
    ).reset_index()
    comp_aju_br = comp_aju_br.sort_values(
        "diff_contrib_pp", key=abs, ascending=False
    )

    # 3. Decomposição por regime POF (Tabela 1419 vs Tabela 7060)
    contrib_regime = (
        df_grupos[df_grupos["localidade"].isin(["Aracaju", "Brasil"])]
        .groupby(
            ["tabela_sidra", "localidade", "grupo_codigo", "grupo"],
            as_index=False,
            dropna=False,
        )["contrib_mensal_pp"]
        .sum()
    )
    contrib_regime["contrib_mensal_pp"] = contrib_regime[
        "contrib_mensal_pp"
    ].round(2)
    pivot_regime = contrib_regime.pivot_table(
        index=["tabela_sidra", "grupo_codigo", "grupo"],
        columns="localidade",
        values="contrib_mensal_pp",
        aggfunc="first",
    ).reset_index()
    pivot_regime["diff_aju_menos_br_pp"] = (
        pivot_regime["Aracaju"] - pivot_regime["Brasil"]
    ).round(2)

    df_resumo_loc.to_csv(OUT_DIR / "resumo_inflacao_localidades.csv", index=False)
    comp_aju_br.to_csv(OUT_DIR / "decomposicao_aracaju_vs_brasil.csv", index=False)
    pivot_regime.to_csv(
        OUT_DIR / "decomposicao_por_tabela_pof.csv", index=False
    )

    print("=== RESUMO INFLACAO ACUMULADA (DESDE JAN/2014) ===")
    print(df_resumo_loc.to_string(index=False))
    print("\n=== DECOMPOSICAO COMPLETA (9 GRUPOS): ARACAJU VS BRASIL ===")
    print(comp_aju_br.to_string(index=False))
    print(f"\nArquivos salvos em: {OUT_DIR}")


if __name__ == "__main__":
    rodar_analise()
