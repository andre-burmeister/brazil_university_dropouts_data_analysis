"""Painel da taxa de evasão no ensino superior, entre 2023 e 2024."""

import streamlit as st
from streamlit_folium import st_folium

import evasao

st.set_page_config(
    page_title="Evasão no ensino superior",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.6rem; padding-left: 1.6rem; padding-right: 1.6rem; max-width: 100%; }
    h1 { letter-spacing: -0.03em; font-weight: 650; }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid rgba(20, 34, 43, 0.08);
        border-radius: 14px;
        padding: 0.7rem 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Lendo os microdados do Censo da Educação Superior...")
def carregar_ofertas():
    return evasao.carregar_ofertas()


@st.cache_data(show_spinner=False)
def carregar_geojson():
    return evasao.carregar_geojson()


def filtros_laterais():
    st.sidebar.header("Filtros")
    st.sidebar.caption(
        "Valem para as duas abas. O mínimo de matrículas soma, no Brasil, "
        "todas as ofertas do mesmo curso na classificação CINE."
    )
    matriculas_minimas = st.sidebar.slider(
        "Matrículas mínimas no curso",
        min_value=0,
        max_value=20000,
        value=3000,
        step=100,
    )
    excluir_sem_concluintes = st.sidebar.toggle(
        "Excluir cursos sem concluintes em 2023",
        value=True,
    )
    st.sidebar.markdown("**Modalidade**")
    presencial = st.sidebar.checkbox("Presencial", value=True)
    distancia = st.sidebar.checkbox("A distância", value=False)
    organizacao = st.sidebar.selectbox(
        "Organização acadêmica",
        ["Todas", *evasao.ORGANIZACAO.values()],
    )
    categoria = st.sidebar.selectbox(
        "Categoria administrativa",
        ["Todas", *evasao.CATEGORIA.values()],
    )
    modalidades = []
    if presencial:
        modalidades.append(1)
    if distancia:
        modalidades.append(2)
    codigo_organizacao = None if organizacao == "Todas" else _codigo(evasao.ORGANIZACAO, organizacao)
    codigo_categoria = None if categoria == "Todas" else _codigo(evasao.CATEGORIA, categoria)
    return {
        "modalidades": modalidades,
        "matriculas_minimas": matriculas_minimas,
        "excluir_sem_concluintes": excluir_sem_concluintes,
        "organizacao": codigo_organizacao,
        "categoria": codigo_categoria,
    }


def _codigo(rotulos, nome):
    return next(codigo for codigo, rotulo in rotulos.items() if rotulo == nome)


def _marca_clique(evento):
    if not isinstance(evento, dict):
        return None
    lat, lng = evento.get("lat"), evento.get("lng")
    if lat is None or lng is None:
        return None
    return (round(float(lat), 5), round(float(lng), 5))


def _sigla_clicada(saida, geojson, lat, lng):
    desenho = (saida or {}).get("last_active_drawing") or {}
    sigla = (desenho.get("properties") or {}).get("sigla")
    mesma_coordenada = (
        sigla
        and desenho.get("click_lat") is not None
        and abs(float(desenho["click_lat"]) - lat) < 1e-3
        and abs(float(desenho["click_lng"]) - lng) < 1e-3
    )
    if mesma_coordenada:
        return sigla
    return evasao.estado_no_ponto(geojson, lat, lng)


def aplicar_clique_mapa(saida, geojson):
    """Troca o estado filtrado quando o clique é novo. Clicar de novo no mesmo limpa."""
    evento = (saida or {}).get("last_clicked")
    marca = _marca_clique(evento)
    if marca is None or marca == st.session_state.get("evento_mapa"):
        return False
    st.session_state.evento_mapa = marca
    sigla = _sigla_clicada(saida, geojson, float(evento["lat"]), float(evento["lng"]))
    if not sigla:
        return False
    atual = st.session_state.get("uf_selecionada")
    st.session_state.uf_selecionada = None if sigla == atual else sigla
    return True


def faixa_extremos(dados, coluna):
    ordenado = dados.sort_values(["TX_EVAS", coluna], ascending=[False, True])
    maior = ordenado.iloc[0]
    menor = ordenado.iloc[-1]
    st.markdown(
        f"**Maior:** {maior[coluna]} ({evasao.percentual(maior['TX_EVAS'])})"
        f" · **Menor:** {menor[coluna]} ({evasao.percentual(menor['TX_EVAS'])})"
    )


OPCAO_TODAS_AREAS = "Todas as áreas"


def _ao_escolher_areas():
    escolhidas = st.session_state.areas_do_grafico
    if OPCAO_TODAS_AREAS in escolhidas and escolhidas != [OPCAO_TODAS_AREAS]:
        st.session_state.areas_do_grafico = [OPCAO_TODAS_AREAS]


def mostrar_barras(dados, coluna, titulo, rolar=False):
    if dados.empty:
        st.info("Nenhum curso passou pelos filtros.")
        return
    faixa_extremos(dados, coluna)
    grafico = evasao.grafico_barras(dados, coluna, titulo)
    if rolar and len(dados) > 12:
        with st.container(height=520, border=False):
            st.altair_chart(grafico, width="stretch", theme=None)
    else:
        st.altair_chart(grafico, width="stretch", theme=None)


st.title("Evasão no ensino superior brasileiro")
st.markdown(
    "O painel compara a permanência na graduação entre os censos de **2023** e **2024**. "
    "A taxa estima quem deixou o curso: matrículas de 2023, menos concluintes de 2023, "
    "menos matrículas de 2024, mais ingressantes de 2024. Uma transferência para outro "
    "curso entra nessa conta como saída."
)
st.markdown(
    """
**Perguntas**

1. Quais cursos têm maior e menor taxa de evasão?
2. Como a taxa de evasão varia de acordo com o estado onde está o curso?
3. Como a taxa de evasão varia entre grupos demográficos, como sexo, cor ou raça e idade?
"""
)

escolhas = filtros_laterais()
aba_cursos, aba_grupos = st.tabs(["Cursos e estados", "Grupos demográficos"])

with aba_cursos:
    if "uf_selecionada" not in st.session_state:
        st.session_state.uf_selecionada = None
    if "evento_mapa" not in st.session_state:
        st.session_state.evento_mapa = None

    if not escolhas["modalidades"]:
        st.warning("Marque ao menos uma modalidade na barra lateral.")
    else:
        recorte = evasao.preparar_recorte(carregar_ofertas(), **escolhas)
        if recorte["cursos"].empty or recorte["ofertas"].empty:
            st.info("Nenhum curso passou pelos filtros.")
        else:
            geojson = carregar_geojson()
            uf = st.session_state.uf_selecionada
            nome = evasao.nome_uf(geojson, uf) if uf else None
            visao = evasao.visao_uf(recorte, uf)
            ofertas = visao["ofertas"]
            cursos = visao["cursos"]
            matriculas = int(ofertas["QT_MAT_2023"].sum()) if not ofertas.empty else 0
            taxa_txt = evasao.percentual(ofertas["QT_EVAS"].sum() / matriculas) if matriculas else "—"
            coluna_cursos, coluna_matriculas, coluna_taxa, coluna_estado = st.columns(4)
            coluna_cursos.metric("Cursos no recorte", evasao.inteiro(len(cursos)))
            coluna_matriculas.metric("Matrículas em 2023", evasao.inteiro(matriculas))
            coluna_taxa.metric("Taxa do recorte", taxa_txt)
            coluna_estado.metric("Estado", nome or "Brasil")
            if nome:
                st.markdown(
                    f"""
                    <div style="
                        background: #ffffff;
                        border: 1px solid rgba(14, 124, 116, 0.35);
                        border-left: 8px solid {evasao.COR_SELECAO};
                        border-radius: 12px;
                        padding: 0.85rem 1rem;
                        margin: 0.15rem 0 0.9rem;
                        color: {evasao.COR_TEXTO};
                    ">
                        <div style="font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase; color: {evasao.COR_SELECAO}; font-weight: 700;">
                            Mostrando só este estado
                        </div>
                        <div style="font-size: 1.7rem; font-weight: 700; line-height: 1.15; margin-top: 0.15rem;">{nome}</div>
                        <div style="font-size: 0.95rem; margin-top: 0.25rem;">
                            Os gráficos usam as ofertas de {nome}. O curso entra no recorte pelo total de matrículas no Brasil.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            coluna_graficos, coluna_mapa = st.columns([1, 1.35], gap="large")

            with coluna_mapa:
                st.header("Como a taxa varia entre os estados?")
                st.caption(
                    "A cor é a taxa dos cursos que passaram nos filtros, "
                    "somada dentro de cada estado. Onde não há cursos neste recorte, o estado fica cinza. "
                    "Clique em um estado para filtrar os gráficos da esquerda. "
                    "Clique de novo no mesmo estado para voltar ao Brasil."
                )
                limpar = st.button("Ver o Brasil todo", disabled=uf is None, key="limpar_uf")
                mapa, dados_mapa = evasao.mapa_estados(recorte["estados"], geojson, uf)
                if dados_mapa.empty:
                    st.info("Nenhum estado tem cursos neste recorte.")
                    saida_mapa = None
                else:
                    faixa_extremos(dados_mapa, "nome_estado")
                    saida_mapa = st_folium(
                        mapa,
                        height=820,
                        use_container_width=True,
                        returned_objects=["last_clicked", "last_active_drawing"],
                        key="mapa_estados",
                    )
                if limpar:
                    st.session_state.uf_selecionada = None
                    st.session_state.evento_mapa = _marca_clique((saida_mapa or {}).get("last_clicked"))
                    st.rerun()
                elif aplicar_clique_mapa(saida_mapa, geojson):
                    st.rerun()

            with coluna_graficos:
                sufixo = f" — {nome}" if nome else ""
                st.header("Por área do conhecimento")
                st.caption(
                    "A taxa da área soma os cursos cuja maior parte das matrículas está nela. "
                    "A cor é a mesma do gráfico de cursos, e o nome completo aparece ao passar o mouse."
                )
                mostrar_barras(
                    visao["areas"],
                    "NO_CINE_AREA_GERAL",
                    f"Taxa de evasão por área do conhecimento{sufixo}",
                )

                st.header("Quais cursos têm maior e menor taxa de evasão?")
                escopo = f"as instituições de {nome}" if nome else "todas as instituições"
                st.caption(
                    f"Cada barra é o curso da classificação CINE, somando {escopo}. "
                    "Nomes parecidos no cadastro, como Sistema e Sistemas de informação, "
                    "entram no mesmo curso. A cor é a da área de conhecimento, "
                    "a mesma usada no gráfico de áreas. O nome completo aparece ao passar o mouse."
                )
                if cursos.empty:
                    st.info("Nenhum curso passou pelos filtros.")
                else:
                    nomes_areas = sorted(cursos["NO_CINE_AREA_GERAL"].dropna().astype(str).unique())
                    opcoes_areas = [OPCAO_TODAS_AREAS, *nomes_areas]
                    if "areas_do_grafico" not in st.session_state:
                        st.session_state.areas_do_grafico = [OPCAO_TODAS_AREAS]
                    else:
                        validas = [item for item in st.session_state.areas_do_grafico if item in opcoes_areas]
                        if validas != list(st.session_state.areas_do_grafico):
                            st.session_state.areas_do_grafico = validas or [OPCAO_TODAS_AREAS]

                    escolhidas = st.multiselect(
                        "Área do conhecimento",
                        opcoes_areas,
                        key="areas_do_grafico",
                        placeholder="Selecione as áreas",
                        help="Vale só para este gráfico. Escolha quantas quiser, ou Todas as áreas.",
                        select_all=False,
                        on_change=_ao_escolher_areas,
                    )
                    if not escolhidas:
                        st.info("Selecione ao menos uma área.")
                    else:
                        visiveis = (
                            cursos
                            if OPCAO_TODAS_AREAS in escolhidas
                            else cursos[cursos["NO_CINE_AREA_GERAL"].isin(escolhidas)]
                        )
                        mostrar_barras(
                            visiveis,
                            "NO_CINE_ROTULO",
                            f"Taxa de evasão por curso{sufixo}",
                            rolar=True,
                        )

            if not dados_mapa.empty:
                st.caption("Ranking de todos os estados deste recorte. O clique no mapa não altera esta tabela.")
                tabela = dados_mapa.sort_values("TX_EVAS", ascending=False).rename(
                    columns={
                        "SG_UF": "UF",
                        "nome_estado": "Estado",
                        "QT_MAT_2023": "Matrículas em 2023",
                        "QT_EVAS": "Evadidos estimados",
                        "taxa_pct": "Taxa (%)",
                    }
                )
                st.dataframe(
                    tabela.loc[:, ["UF", "Estado", "Matrículas em 2023", "Evadidos estimados", "Taxa (%)"]],
                    hide_index=True,
                    height=360,
                    column_config={
                        "Matrículas em 2023": st.column_config.NumberColumn(format="%d"),
                        "Evadidos estimados": st.column_config.NumberColumn(format="%d"),
                        "Taxa (%)": st.column_config.NumberColumn(format="%.1f"),
                    },
                )

with aba_grupos:
    pass
