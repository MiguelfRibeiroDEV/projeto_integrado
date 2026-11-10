"""Dashboard 5 — Panorama e mesa de negociação (síntese + notícias/fotos + análise).
Base própria: dados/panorama.csv  (indicadores: desocupacao, informalidade, rendimento)."""
import nucleo as n

TITULO = "Panorama e mesa de negociação"
ARQUIVO = "panorama.csv"
PREFIXO = "d5"


def render():
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.header(TITULO)
    st.caption("Márcia (Trabalho), Renato (Indústrias) e Sílvia (Sebrae) · visão integrada "
               "das UFs para decidir prioridades")
    df = n.carregar_base(PREFIXO, ARQUIVO, ["desocupacao", "informalidade", "rendimento"],
                         "python coletar_dados.py --dashboard panorama")
    if df is None:
        return
    f = n.filtros(df, PREFIXO)
    if f is None:
        return
    d_base, d, anos, faixa = f
    ref = n.seletor_ano_ref(anos, PREFIXO)

    ser = {ind: n.valores_por_uf(d_base, ind, ref) for ind in n.INDICADORES_ROTULO}
    quadro = pd.DataFrame({n.INDICADORES_ROTULO[i]: s for i, s in ser.items() if not s.empty})
    st.subheader(f"Quadro-resumo por UF ({ref})")
    if quadro.empty:
        st.info(f"Sem dados para {ref}.")
        return
    cols = st.columns(len(quadro.columns))
    for c, nome in zip(cols, quadro.columns):
        c.metric(f"{nome}: média das UFs", n.fmt(quadro[nome].mean()))
    quadro.index.name = "UF"
    st.dataframe(quadro.round(2).sort_index(), use_container_width=True)

    st.subheader("Ranking de prioridade")
    rotulo = st.selectbox("Indicador do ranking", list(quadro.columns), key=f"rk_{PREFIXO}")
    s = quadro[rotulo].dropna().sort_values(ascending=False)
    st.plotly_chart(px.bar(s.rename("valor").reset_index(), x="UF", y="valor",
                           category_orders={"UF": s.index.tolist()}, labels={"valor": rotulo}),
                    use_container_width=True)

    ri, rr = n.INDICADORES_ROTULO["informalidade"], n.INDICADORES_ROTULO["rendimento"]
    if {ri, rr} <= set(quadro.columns):
        st.subheader("Informalidade × rendimento (cada ponto é uma UF)")
        x = quadro[[ri, rr]].dropna().reset_index()
        st.plotly_chart(px.scatter(x, x=ri, y=rr, hover_name="UF"), use_container_width=True)
        if len(x) >= 3:
            r = float(x[ri].corr(x[rr]))
            st.caption(f"Correlação de Pearson entre as UFs: **{n.fmt(r, 2)}**. Correlação não "
                       "indica causa: descreve como os dois indicadores variam juntos.")

    st.subheader("Evolução 2012 × 2022 (desocupação)")
    ano_a, ano_b = n.seletor_anos(anos, PREFIXO)
    comp = n.comparar_anos(d_base, "desocupacao", ano_a, ano_b)
    if not comp.empty:
        st.success(f"UF que mais reduziu a desocupação: **{comp.index[0]}** "
                   f"({n.fmt(comp.iloc[0]['variacao_pp'], sinal=True)} p.p.).")
        n.barras_variacao(comp)

    n.painel_serie(ser["desocupacao"], "Taxa de desocupação", "%", PREFIXO, f"— {ref}")

    st.header("Leitura para a mesa de negociação")
    pontos = []
    if not comp.empty:
        pontos.append(f"**Márcia:** melhor desempenho entre {ano_a} e {ano_b} em "
                      f"**{comp.index[0]}**; pior em **{comp.index[-1]}**.")
    if not ser["informalidade"].empty:
        top = ser["informalidade"].sort_values(ascending=False).head(3)
        pontos.append("**Sílvia:** maior informalidade em "
                      + ", ".join(f"**{u}** ({n.fmt(v, 1)}%)" for u, v in top.items()) + ".")
    if not ser["rendimento"].empty:
        r = n.resumo_estatistico(ser["rendimento"])
        pontos.append(f"**Renato:** use a **mediana** (R$ {n.fmt(r['mediana'])}) como referência "
                      "de renda; a média é sensível a UFs atípicas.")
    st.markdown("\n".join(f"- {p}" for p in pontos))

    n.noticias_e_fotos(PREFIXO)

    st.header("Análise descritiva (entregável)")
    md = n.gerar_analise_md(d_base, ano_a, ano_b, ref, "Panorama (integrante 5)")
    st.download_button("Baixar análise descritiva (Markdown)", data=md.encode("utf-8"),
                       file_name="analise_descritiva_tema6.md", mime="text/markdown",
                       key=f"dl_md_{PREFIXO}")
    n.fontes(["CAGED/MTE (notícias): https://www.gov.br/trabalho-e-emprego/"])
