# Relatório de Qualidade dos Dados — IPCA (Aracaju e Comparativos)

- **Gerado em:** 2026-11-25 21:46:25 UTC
- **Arquivo validado:** `data\processed\ipca_aracaju_comparativo.parquet`
- **Total de registros:** 3,580
- **Período coberto:** 2014-01 a 2026-10
- **Localidades:** Aracaju, Brasil, Sao_Luis

## Resultados dos Testes Automatizados

| Teste de Qualidade | Status | Detalhes |
| --- | --- | --- |
| Ausência de duplicatas por (data_ref, localidade, grupo) | **APROVADO** | 0 linha(s) duplicada(s) encontrada(s). |
| Completude de var_mensal e peso_mensal (sem nulos) | **APROVADO** | Nulos em var_mensal: 0 | Nulos em peso_mensal: 0. |
| Soma dos pesos dos 9 grupos próxima de 100% (99.5%–100.5%) | **APROVADO** | 0 recorte(s) (localidade/mês) fora da faixa (média geral: 100.0000%). |
| Transição limpa Tabela 1419 (2019-12) -> Tabela 7060 (2020-01) | **APROVADO** | Máx Tabela 1419: 2019-12 | Mín Tabela 7060: 2020-01. |
| Consistência soma das contribuições vs. variação do Índice Geral | **APROVADO** | Erro absoluto médio: 0.0026 p.p. | Máximo: 0.0067 p.p. |

## Observações Metodológicas
- Pequenas diferenças entre a soma dos grupos e o índice geral ocorrem por arredondamento nativo das séries divulgadas no SIDRA e pela mudança metodológica da POF entre as tabelas 1419 (até 2019) e 7060 (a partir de 2020).
- Este relatório atende à Etapa 4 (Carga e Qualidade) do pipeline.