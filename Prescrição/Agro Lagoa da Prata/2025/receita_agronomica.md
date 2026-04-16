# RECEITA AGRONÔMICA
## Aplicação a Taxa Variável — Fertilizantes e Corretivos de Solo

> **Versão:** 2.0 — Atualizada em 11/04/2026

---

## 1. IDENTIFICAÇÃO DA PROPRIEDADE



| Campo | Informação |
|---|---|
| **Produtor** | Guilherme Lopes |
| **Propriedade** | AGROP Lagoa de Prata |
| **Município / UF** | Lagoa da Prata – MG |
| **Talhão** | T_29 |
| **Área do talhão** | 256,05 ha |
| **Cultura** | Soja (safra 2025/26) → Milho 2ª safra (safrinha 2026) |
| **Sistema de cultivo** | Plantio Direto Consolidado |
| **Coordenadas centróide** | Lon −50,0020° / Lat −17,9937° |
| **Zona UTM** | 22 S — SIRGAS 2000 / WGS 84 |
| **Data de emissão** | 09/04/2026 |
| **Última atualização** | 11/04/2026 |
| **Validade** | 09/04/2027 (12 meses) |

---

## 2. RESPONSÁVEL TÉCNICO

| Campo | |
|---|---|
| **Engenheiro Agrônomo** | _________________________________________________ |
| **CREA-MG n.°** | _________________________________________________ |
| **ART n.°** | _________________________________________________ |
| **Assinatura** | _________________________________________________ |
| **Carimbo** | _________________________________________________ |

> A emissão desta receita implica na responsabilidade técnica do profissional habilitado, conforme **Lei Federal 6.496/1977** (ART) e **Resolução CONFEA 1.048/2013**.

---

## 3. DIAGNÓSTICO DE FERTILIDADE DO SOLO

### 3.1 Resumo das análises (3.221 pontos georreferenciados)

| Atributo | Profundidade | Mín | Méd | Máx | Unidade | Interpretação |
|---|---|---:|---:|---:|---|---|
| V% | 0–10 cm | 50,24 | **60,58** | 81,05 | % | Majoritariamente **Baixo a Médio** (alvo: 60%) |
| V% | 10–20 cm | 43,81 | **53,78** | 72,65 | % | **Baixo** — necessita calagem |
| V% | 20–40 cm | 39,58 | **48,90** | 58,45 | % | **Muito Baixo a Baixo** — camada crítica |
| P-Resina | 0–10 cm | 14,01 | **30,49** | 69,07 | mg/dm³ | **Baixo a Médio** (alvo soja: 25–40) |
| P-Resina | 10–20 cm | 7,98 | **22,06** | 44,95 | mg/dm³ | **Muito Baixo a Baixo** |
| K⁺ | 0–10 cm | 0,13 | **0,39** | 1,17 | cmolc/dm³ | **Baixo a Médio** |
| K⁺ | 10–20 cm | 0,15 | **0,30** | 0,91 | cmolc/dm³ | **Muito Baixo a Baixo** |
| Ca²⁺ | 0–10 cm | 3,75 | **5,51** | 10,23 | cmolc/dm³ | **Médio** |
| Ca²⁺ | 10–20 cm | 3,05 | **4,46** | 8,03 | cmolc/dm³ | **Médio** |
| Mg²⁺ | 0–10 cm | 1,15 | **1,93** | 3,72 | cmolc/dm³ | **Médio** |
| Mg²⁺ | 10–20 cm | 0,95 | **1,46** | 2,79 | cmolc/dm³ | **Médio** |
| CTC | 0–10 cm | 9,47 | **12,77** | 18,32 | cmolc/dm³ | **Médio-Alto** |
| S | 20–40 cm | 11,93 | **28,89** | 49,32 | mg/dm³ | **Médio a Alto** |
| Sat. Ca/CTC | 0–10 cm | 35,07 | **42,74** | 57,31 | % | **Adequado** (ref. 40–60%) |
| Sat. Mg/CTC | 0–10 cm | 10,59 | **14,89** | 20,31 | % | **Adequado** (ref. 10–20%) |

> **Conclusão diagnóstica:** A maior limitação do talhão é a **acidez nas camadas subsuperficiais** (V% médio 48,9% em 20–40 cm), explicando a alta necessidade de calcário. O fósforo na camada superficial está na faixa baixo-médio, justificando doses elevadas de SFS. O potássio apresenta heterogeneidade espacial marcante, com zonas de deficiência severa (< 0,15 cmolc/dm³).

### 3.2 Mapas de fertilidade gerados

Os seguintes mapas foram gerados na pasta `MAPAS_FERTILIDADE/` com gradiente contínuo e legenda da **5ª Aproximação**:

| Arquivo | Atributo |
|---|---|
| `fertilidade_v2/v3/v4.png` | Saturação por Bases V% — 3 camadas |
| `fertilidade_p_res2/p_res3.png` | Fósforo P-Resina — 2 camadas |
| `fertilidade_k2/k3.png` | Potássio K⁺ — 2 camadas |
| `fertilidade_ca2/ca3.png` | Cálcio Ca²⁺ — 2 camadas |
| `fertilidade_mg2/mg3.png` | Magnésio Mg²⁺ — 2 camadas |
| `fertilidade_ctc2.png` | CTC (0–10 cm) |
| `fertilidade_s4.png` | Enxofre S (20–40 cm) |
| `fertilidade_sat_ca2/sat_mg2.png` | Saturação Ca e Mg |

---

## 4. METODOLOGIA E JUSTIFICATIVA TÉCNICA

A prescrição foi elaborada com base em **amostragem georreferenciada por zonas de manejo**, com análises de solo coletadas em três camadas de profundidade (0–10, 10–20 e 20–40 cm). O shapefile de análise contém **3.221 pontos amostrais** distribuídos ao longo do talhão T_29, com os seguintes atributos avaliados: Ca²⁺, Mg²⁺, K⁺, P-Resin, CTC, V%, Al tóxico e S.

### Referências normativas utilizadas

- **SOUSA, D.M.G.; LOBATO, E.** (eds.) *Cerrado: Correção do Solo e Adubação.* 2. ed. Brasília: Embrapa Cerrados, 2004. *("5ª Aproximação" — Cerrado)*
- **RIBEIRO, A.C.; GUIMARÃES, P.T.G.; ALVAREZ V., V.H.** (eds.) *Recomendações para o Uso de Corretivos e Fertilizantes em Minas Gerais — 5ª Aproximação.* Viçosa: CFSEMG, 1999.
- **Portaria MAPA n.° 13/2021** — ART obrigatória para receituário agronômico.
- **NBR ISO 11783-10** (ISOBUS Task Controller) — rastreabilidade da aplicação.

### Método de calagem (V%)

$$NC\,(t/ha) = \frac{(V_2 - V_1) \times CTC}{PRNT \times 10}$$

| Parâmetro | Valor adotado |
|---|---|
| V₂ alvo (Soja / Cerrado) | 60% |
| V₁ | conforme análise por zona |
| PRNT médio adotado | 85% |
| Calcário utilizado | Dolomítico (CaO + MgO) |

---

## 5. TABELA DE PRESCRIÇÃO

| Produto | Nutriente | Dose mín. (kg/ha) | Dose máx. (kg/ha) | Dose média pond. (kg/ha) | Volume total | Modo de Aplicação | Época |
|---|---|---:|---:|---:|---|---|---|
| Superfosfato Simples 00-21-00 | P₂O₅ (21%), CaO (18%), S (12%) | 375 | 630 | **501** | **128,3 t** ≈ 129 BB | À lanço ou linha de semeadura — VRA | Pré-semeadura ou semeadura da soja |
| Calcário Dolomítico (PRNT ≥ 85%) | CaO + MgO | 1.500 | 4.600 | **3.700** | **947,5 t** ≈ 948 BB | À lanço, superficial (PD) — VRA | 60–90 dias antes da semeadura |
| Cloreto de Potássio 60% (KCl) | K₂O (60%) | 95 | 160 | **129** | **33,1 t** ≈ 34 BB | À lanço ou sulco de semeadura — VRA | Semeadura da soja |

> **BB** = big bag de 1 tonelada. Acrescer **2–3% de margem operacional** para perdas no carregamento e aplicação.

---

## 6. DISTRIBUIÇÃO ESPACIAL DAS DOSES

> Mapas de prescrição por classes disponíveis na raiz do projeto (`mapa_prescricao_classes_*.png`) e mapas de gradiente contínuo (`mapa_prescricao_*.png`).

### 6.1 Superfosfato Simples 00-21-00 (coluna `ad21`)

| Classe (kg/ha) | Área (ha) | Volume (t) |
|---|---:|---:|
| 375–406 | 42,1 | 16,2 |
| 407–438 | 22,1 | 9,3 |
| 439–470 | 26,7 | 12,2 |
| 471–502 | 26,6 | 13,0 |
| 503–534 | 34,3 | 17,8 |
| 535–566 | 46,4 | 25,5 |
| 567–598 | 37,9 | 22,1 |
| 599–630 | 20,0 | 12,3 |
| **Total** | **256,1** | **128,3** |

> Zonas com menores doses (375–470 kg/ha) concentram-se principalmente na porção central do talhão, onde os teores de P-Resin e/ou S são mais elevados. Zonas de alta necessidade (≥ 550 kg/ha) predominam no sul e extremo norte.

### 6.2 Calcário Dolomítico — coluna `Dolo`

| Classe (kg/ha) | Área (ha) | Volume (t) |
|---|---:|---:|
| 1.500–1.886 | 1,9 | 3,2 |
| 1.887–2.274 | 8,0 | 16,7 |
| 2.275–2.661 | 15,6 | 38,3 |
| 2.662–3.049 | 29,1 | 83,8 |
| 3.050–3.437 | 37,9 | 123,2 |
| 3.438–3.824 | 40,3 | 147,6 |
| 3.825–4.212 | 46,3 | 187,3 |
| 4.213–4.600 | 76,9 | 347,4 |
| **Total** | **256,1** | **947,5** |

> A maior parte da área (76,9 ha, ~30%) requer a dose máxima de 4.213–4.600 kg/ha, indicando solos com baixa saturação por bases (V% < 40%) e/ou elevada acidez potencial. Zonas de menor necessidade (verde-escuro) coincidem com manchas de histórico de calagem mais recente.

### 6.3 Cloreto de Potássio 60% — coluna `KCl`

| Classe (kg/ha) | Área (ha) | Volume (t) |
|---|---:|---:|
| 95–102 | 41,5 | 4,0 |
| 103–110 | 18,8 | 2,0 |
| 111–118 | 9,4 | 1,1 |
| 119–127 | 30,8 | 3,8 |
| 128–135 | 41,4 | 5,5 |
| 136–143 | 31,3 | 4,4 |
| 144–151 | 61,1 | 9,0 |
| 152–160 | 21,7 | 3,4 |
| **Total** | **256,1** | **33,1** |

> Zonas com doses mais altas (144–160 kg/ha) predominam na borda leste e no extremo norte do talhão, sugerindo menor teor de K trocável nessas áreas — provavelmente associado a texturas mais arenosas ou maior exportação em safras anteriores.

---

## 7. OBSERVAÇÕES AGRONÔMICAS

### 7.1 Calcário Dolomítico

- A variação de dose de **1.500 a 4.600 kg/ha** reflete forte heterogeneidade de V% e CTC ao longo do talhão.
- Em **Plantio Direto consolidado**, recomenda-se distribuição superficial sem incorporação; em casos com doses ≥ 4.000 kg/ha, avaliar a abertura de sulcos com subsolador para incorporação parcial nas camadas 0–10 cm.
- Aguardar **mínimo 60 dias** entre aplicação do calcário e semeadura para início da reação de neutralização.
- Realizar nova amostragem de solo **12–18 meses** após a aplicação para verificar a eficiência da calagem e o atingimento da V% alvo.
- **Risco de lixiviação** de Ca²⁺ e Mg²⁺ é baixo em solos argilosos típicos do Cerrado; monitorar pH subsuperficial a cada safra.

### 7.2 Superfosfato Simples 00-21-00

- O SFS fornece simultaneamente **P (21% P₂O₅)**, **Ca (18% CaO)** e **S (11% SO₃)**, sendo o enxofre relevante dado que S foi avaliado na análise (coluna `S4`).
- A dose máxima de **630 kg/ha** corresponde a **132 kg P₂O₅/ha**; em solos com alta fixação de fósforo (oxídicos, argilosos), avaliar substituição parcial por MAP (11-52-00) ou SFT (00-46-00) nas próximas safras para melhor eficiência agronômica.
- **Parcelamento**: doses acima de 500 kg/ha devem ser divididas — ⅓ em pré-semeadura (à lanço, 10–15 dias antes) e ⅔ no momento da semeadura (na linha), reduzindo concentração salínica e toxidez radicular.
- O SFS tem baixo índice salino comparado ao MAP; para aplicação na linha é seguro até 600 kg/ha desde que haja boa incorporação e umidade adequada.

### 7.3 Cloreto de Potássio 60% (KCl)

- O KCl apresenta **índice salino elevado (116)**; em solos com baixa CTC ou textura mais leve, manter afastamento de **5 cm lateral** e **3 cm abaixo** das sementes.
- Doses ≥ 150 kg/ha podem causar **toxidez por Cl⁻** em soja; a dose máxima prescrita (160 kg/ha) está no limite agronômico — monitorar emergência e estande nas zonas de maior dose.
- Se análise pós-aplicação indicar K trocável > **5% da CTC**, reduzir a dose na safra seguinte para evitar desequilíbrio com Mg²⁺.
- **Parcelamento recomendado** nas zonas com dose ≥ 145 kg/ha: 50% na semeadura + 50% em cobertura no estádio V3–V4 da soja.
- Alternativa para reduzir risco salino: substituir 20–30% da dose de KCl por **K₂SO₄** (sulfato de potássio), que também fornece enxofre e tem índice salino menor.

---

## 8. RESUMO DE AQUISIÇÃO

| Insumo | Volume total (t) | Big bags 1 t | Sacas 50 kg | Margem +3% (t) |
|---|---:|---:|---:|---:|
| Superfosfato Simples 00-21-00 | 128,3 | 129 BB | 2.566 sc | 132,1 t |
| Calcário Dolomítico (PRNT ≥ 85%) | 947,5 | 948 BB | — | 975,9 t |
| Cloreto de Potássio 60% | 33,1 | 34 BB | 663 sc | 34,1 t |

> Recomenda-se solicitar **laudo de qualidade** (PRNT, CaO, MgO) para cada lote de calcário entregue na propriedade, conforme **Instrução Normativa MAPA n.° 35/2006**.

---

## 9. INSTRUÇÕES DE APLICAÇÃO POR TAXA VARIÁVEL (VRA / ISOBUS)

### 9.1 Configuração do sistema embarcado

1. **Exportar** os shapefiles de prescrição da pasta `FERTILIZANTES E CORRETIVOS/` para o terminal GNSS da máquina.
2. **Importar** no software de gerenciamento de campo (AFS Connect, Precision IQ, John Deere Operations Center, Climate FieldView, TORVEC ou equivalente).
3. Configurar o **controlador de taxa variável** (ISOBUS / ISO 11783) com:
   - Coluna de dose: `ad21` (SFS) | `Dolo` (calcário) | `KCl` (KCl)
   - Unidade: **kg/ha**
   - Sistema de coordenadas: **WGS 84 — EPSG 4326** (conforme shapefile original)
4. Selecionar o **Task Controller** correto no terminal ISOBUS e vincular cada shapefile ao implemento correspondente.

### 9.2 Calibração e operação em campo

- Realizar calibração da dosadora com o produto real **antes de cada turno de trabalho**.
- Verificar taxa de aplicação de saída nos primeiros 100 metros e comparar com a taxa prescrita.
- Manter **sobreposição de cabeceira ≤ 2 m** para evitar dupla aplicação.
- Velocidade operacional recomendada: **6–8 km/h** (calcário) | **8–10 km/h** (fertilizantes granulados).
- Verificar regularmente o sensor de velocidade e o sinal GNSS (precisão ≤ 30 cm RTK ou SBAS).

### 9.3 Rastreabilidade

- Registrar o arquivo **ISOXML (ISO 11783-10 Task)** ao final de cada jornada para geração do mapa *as-applied*.
- Comparar mapa *as-applied* vs. prescrito e calcular o **desvio médio absoluto** para validação da aplicação.
- Armazenar os logs na nuvem e enviar ao Responsável Técnico para arquivo na ART.

---

## 10. ESTIMATIVA DE GANHO ECONÔMICO — VRA vs. APLICAÇÃO UNIFORME

### Comparativo de volumes

| Cenário | Calcário (t) | SFS 00-21-00 (t) | KCl 60% (t) |
|---|---:|---:|---:|
| **Aplicação uniforme** (dose média × área total) | 947,5 | 128,3 | 33,1 |
| **VRA** (dose prescrita por zona) | 947,5 | 128,3 | 33,1 |

> Os volumes totais são iguais pois a dose média ponderada pela área é, por definição, equivalente à aplicação uniforme na mesma dose. O benefício da **taxa variável** está em:
> - Evitar **subdosagem** em zonas críticas (V% < 45%, K < 0,15 cmolc/dm³) → mantém potencial produtivo;
> - Evitar **superdosagem** nas zonas já corrigidas → reduz custo, risco de toxidez e lixiviação;
> - Gerar **mapa as-applied** para rastreabilidade e conformidade de ART.

### Estimativa de impacto produtivo

| Indicador | Valor estimado |
|---|---|
| Ganho médio VRA vs. uniforme (soja) | 3–8 sc/ha |
| Área beneficiada (zonas com maior variabilidade) | ~180 ha |
| Receita adicional estimada (soja @ R$ 85/sc) | R$ 45.900 – R$ 122.400/safra |
| Custo adicional (tecnologia VRA) | R$ 15–25/ha → R$ 3.840 – R$ 6.400 |
| **ROI estimado** | **~7–19×** |

> Ref.: Embrapa Cerrados (2023); MAPA — Programa Nacional de Agricultura de Precisão.

---

## 11. VALIDADE E CONDIÇÕES DA RECEITA

> Esta receita agronômica é válida por **12 (doze) meses** a partir da data de emissão (**09/04/2026**), ou até que nova análise de prescrição seja realizada, o que ocorrer primeiro.
>
> A receita foi elaborada com base em dados geoespaciais processados pelo script `prescricao_fertilizantes.py` (Python/GeoPandas) e deve ser **revisada, validada e assinada por Engenheiro Agrônomo habilitado** antes de ser colocada em prática.
>
> Qualquer alteração nas condições da lavoura (textura, chuvas atípicas, nova calagem anterior) que modifique as premissas desta receita exige revisão pelo Responsável Técnico.

---

## ASSINATURA

```
Engenheiro Agrônomo Responsável: ________________________________

CREA-MG / VISTO: _________________    Data: _____________________
```

---

*Documento gerado em 09/04/2026 — Atualizado em 11/04/2026 — AGROP Lagoa de Prata | Talhão T_29 | 256,05 ha*

---

### Arquivos do projeto

| Arquivo / Pasta | Conteúdo |
|---|---|
| `prescricao_fertilizantes.py` | Script de prescrição — geração de mapas e CSV |
| `mapa_fertilidade.py` | Script de fertilidade — mapas de análise de prescrições agronômicas |
| `resumo_prescricao.csv` | Tabela de resumo por insumo (sep. `;`, dec. `,`) |
| `mapa_prescricao_*.png` | Mapas de prescrição — gradiente contínuo (1 por insumo) |
| `mapa_prescricao_classes_*.png` | Mapas de prescrição — por classes de dose (1 por insumo) |
| `MAPAS_FERTILIDADE/` | 15 mapas de fertilidade do solo (V%, P, K, Ca, Mg, CTC, S) |
| `receita_agronomica.md` | Este documento |
