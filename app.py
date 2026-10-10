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
        background: light-dark(#ffffff, #262730);
        border: 1px solid light-dark(rgba(20, 34, 43, 0.08), rgba(250, 250, 250, 0.12));
        border-radius: 14px;
        padding: 0.7rem 0.9rem;
    }
    .aviso-estado {
        background: light-dark(#ffffff, #262730);
        border: 1px solid light-dark(rgba(14, 124, 116, 0.35), rgba(94, 234, 212, 0.45));
        border-left: 8px solid light-dark(#0e7c74, #5eead4);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin: 0.15rem 0 0.9rem;
        color: light-dark(#14222b, #fafafa);
    }
    .aviso-estado-rotulo {
        font-size: 0.78rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: light-dark(#0e7c74, #5eead4);
        font-weight: 700;
    }
    .aviso-estado-nome {
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.15;
        margin-top: 0.15rem;
    }
    .aviso-estado-texto { font-size: 0.95rem; margin-top: 0.25rem; }
    [data-testid="stVegaLiteChart"] [fill="#14222b"] {
        fill: light-dark(#14222b, #fafafa) !important;
    }
    [data-testid="stVegaLiteChart"] [stroke="#14222b"] {
        stroke: light-dark(#14222b, #fafafa) !important;
    }
    [data-testid="stColumn"]:has([data-testid="stCustomComponentV1"]) [data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }
    [data-testid="stColumn"]:has([data-testid="stCustomComponentV1"]) [data-testid="stHeading"] {
        margin-bottom: 0;
    }
    [data-testid="stColumn"]:has([data-testid="stCustomComponentV1"]) [data-testid="stElementContainer"]:has([data-testid="stCustomComponentV1"]) {
        margin-top: 0;
    }
    .st-key-comparacao_grupos {
        position: sticky !important;
        top: 3.75rem;
        z-index: 200;
        background: light-dark(#f6f4ef, #0e1117);
        padding-top: 0.35rem;
        padding-bottom: 0.85rem;
        margin-bottom: -0.85rem;
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
    tamanho_circulos = st.sidebar.toggle(
        "Tamanho dos círculos pela matrícula",
        value=True,
        help="Desligue para deixar todos os círculos do mesmo tamanho.",
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
    }, tamanho_circulos


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


def iniciar_mapa(chave_uf, chave_evento):
    if chave_uf not in st.session_state:
        st.session_state[chave_uf] = None
    if chave_evento not in st.session_state:
        st.session_state[chave_evento] = None


def aplicar_clique_mapa(saida, geojson, chave_uf="uf_selecionada", chave_evento="evento_mapa"):
    """Troca o estado filtrado quando o clique é novo. Clicar de novo no mesmo limpa."""
    evento = (saida or {}).get("last_clicked")
    marca = _marca_clique(evento)
    if marca is None or marca == st.session_state.get(chave_evento):
        return False
    st.session_state[chave_evento] = marca
    sigla = _sigla_clicada(saida, geojson, float(evento["lat"]), float(evento["lng"]))
    if not sigla:
        return False
    atual = st.session_state.get(chave_uf)
    st.session_state[chave_uf] = None if sigla == atual else sigla
    return True


def faixa_cor_mapa(dados, metrica):
    info = evasao.METRICAS_MAPA[metrica]
    ordenado = dados.sort_values([info["coluna"], "nome_estado"], ascending=[False, True])
    maior = ordenado.iloc[0]
    menor = ordenado.iloc[-1]
    st.markdown(
        f"**Maior:** {maior['nome_estado']} ({evasao.formatar_metrica_mapa(metrica, maior[info['coluna']])})"
        f" · **Menor:** {menor['nome_estado']} ({evasao.formatar_metrica_mapa(metrica, menor[info['coluna']])})"
    )


def faixa_extremos(dados, coluna):
    ordenado = dados.sort_values(["TX_EVAS", coluna], ascending=[False, True])
    maior = ordenado.iloc[0]
    menor = ordenado.iloc[-1]
    st.markdown(
        f"**Maior:** {maior[coluna]} ({evasao.percentual(maior['TX_EVAS'])})"
        f" · **Menor:** {menor[coluna]} ({evasao.percentual(menor['TX_EVAS'])})"
    )


def faixa_diferenca(dados):
    ordenado = dados.sort_values(["diferenca_pp", "nome_estado"], ascending=[False, True])
    maior = ordenado.iloc[0]
    menor = ordenado.iloc[-1]
    st.markdown(
        f"**Maior diferença:** {maior['nome_estado']} ({evasao.pontos(maior['diferenca_pp'])})"
        f" · **Menor:** {menor['nome_estado']} ({evasao.pontos(menor['diferenca_pp'])})"
    )


def mostrar_recorte(cursos, ofertas, nome, chave_limpar):
    matriculas = int(ofertas["QT_MAT_2023"].sum()) if not ofertas.empty else 0
    taxa_txt = evasao.percentual(ofertas["QT_EVAS"].sum() / matriculas) if matriculas else "—"
    coluna_cursos, coluna_matriculas, coluna_taxa, coluna_estado = st.columns(4)
    coluna_cursos.metric("Cursos no recorte", evasao.inteiro(len(cursos)))
    coluna_matriculas.metric("Matrículas em 2023", evasao.inteiro(matriculas))
    coluna_taxa.metric("Taxa do recorte", taxa_txt)
    coluna_estado.metric("Estado", nome or "Brasil")
    if not nome:
        return False
    coluna_aviso, coluna_acao = st.columns([5, 1], vertical_alignment="center")
    with coluna_aviso:
        st.markdown(
            f"""
            <div class="aviso-estado">
                <div class="aviso-estado-rotulo">Mostrando só este estado</div>
                <div class="aviso-estado-nome">{nome}</div>
                <div class="aviso-estado-texto">
                    Os gráficos usam as ofertas de {nome}. O curso entra no recorte pelo total de matrículas no Brasil.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with coluna_acao:
        return st.button("Ver o Brasil todo", key=chave_limpar)


def _area_selecionada(estado):
    """Lê a área clicada no gráfico. A seleção vazia devolve None."""
    if not estado:
        return None
    try:
        bruto = estado["selection"].get("area_clicada")
    except (KeyError, TypeError, AttributeError):
        return None
    if not bruto:
        return None
    if isinstance(bruto, dict):
        valores = bruto.get("NO_CINE_AREA_GERAL")
        if isinstance(valores, list) and valores:
            return str(valores[0])
        if isinstance(valores, str) and valores:
            return valores
        ponto = bruto.get("vlPoint")
        itens = ponto.get("or") if isinstance(ponto, dict) else None
        if isinstance(itens, list):
            for item in itens:
                nome = item.get("NO_CINE_AREA_GERAL") if isinstance(item, dict) else None
                if nome:
                    return str(nome)
        return None
    if isinstance(bruto, list):
        for item in bruto:
            nome = item.get("NO_CINE_AREA_GERAL") if isinstance(item, dict) else None
            if nome:
                return str(nome)
    return None


def _nomes_de_area(areas):
    if areas is None or areas.empty or "NO_CINE_AREA_GERAL" not in areas.columns:
        return set()
    return set(areas["NO_CINE_AREA_GERAL"].fillna("Sem área").astype(str))


def _chave_grafico_areas():
    if "ciclo_grafico_areas" not in st.session_state:
        st.session_state.ciclo_grafico_areas = 0
    return f"grafico_areas_{st.session_state.ciclo_grafico_areas}"


def mostrar_barras(dados, coluna, titulo, rolar=False, selecionavel=False, chave=None):
    if dados.empty:
        st.info("Nenhum curso passou pelos filtros.")
        return None
    faixa_extremos(dados, coluna)
    grafico = evasao.grafico_barras(dados, coluna, titulo, selecionavel=selecionavel)
    kwargs = {"width": "stretch"}
    if selecionavel:
        kwargs["on_select"] = "rerun"
        kwargs["key"] = chave
    if rolar and len(dados) > 12:
        with st.container(height=520, border=False):
            return st.altair_chart(grafico, **kwargs)
    return st.altair_chart(grafico, **kwargs)


def mostrar_barras_grupos(dados, comparacao, titulo):
    if dados.empty:
        st.info("Nenhum grupo tem matrículas neste recorte.")
        return
    faixa_extremos(dados, "grupo")
    grafico = evasao.grafico_barras_grupos(dados, comparacao, titulo)
    st.altair_chart(grafico, width="stretch")


def _seletor_grano(chave):
    return st.selectbox(
        "Cada ponto é",
        list(evasao.GRANULACAO),
        format_func=lambda item: evasao.GRANULACAO[item],
        key=chave,
    )


def _rotulo_grupo(comparacao, identificador):
    if identificador == evasao.TAXA_GERAL:
        return evasao.ROTULO_TAXA_GERAL
    return next(grupo["rotulo"] for grupo in comparacao["grupos"] if grupo["id"] == identificador)


def mostrar_dispersao_demografica(ofertas, comparacao, escolha, sufixo, tamanho_variavel):
    if escolha == "idade":
        st.header("Como a evasão muda ao longo da idade, em cada área?")
        st.caption(
            "Cada linha é uma área do conhecimento. A espessura é proporcional às matrículas da área, "
            "e as linhas são semitransparentes para mostrar onde se concentram. "
            f"Uma faixa com menos de {evasao.MIN_MATRICULAS_FAIXA} matrículas na área "
            "fica sem ponto e corta a linha."
        )
        serie = evasao.serie_idade(ofertas)
        if serie.empty or serie["taxa_pct"].isna().all():
            st.info("Nenhuma área tem matrículas suficientes nas faixas de idade.")
            return
        st.altair_chart(
            evasao.grafico_linhas_idade(serie, f"Taxa de evasão por faixa de idade{sufixo}"),
            width="stretch",
        )
        return

    if escolha == "raca":
        st.header("Como a taxa de uma raça se compara à outra?")
        rotulos = [grupo["rotulo"] for grupo in comparacao["grupos"]]
        ids = {grupo["rotulo"]: grupo["id"] for grupo in comparacao["grupos"]}
        ids[evasao.ROTULO_TAXA_GERAL] = evasao.TAXA_GERAL
        coluna_x, coluna_y, coluna_ponto = st.columns(3)
        with coluna_x:
            rotulo_x = st.selectbox(
                "Eixo X",
                [evasao.ROTULO_TAXA_GERAL, *rotulos],
                key="eixo_x_raca",
            )
        with coluna_y:
            padrao_y = rotulos.index("Preta") if "Preta" in rotulos else 0
            rotulo_y = st.selectbox("Eixo Y", rotulos, index=padrao_y, key="eixo_y_raca")
        with coluna_ponto:
            grano = _seletor_grano("grano_raca")
        id_x = ids[rotulo_x]
        id_y = ids[rotulo_y]
        if id_x == id_y:
            st.info("Escolha grupos diferentes nos dois eixos.")
            return
    else:
        st.header("Onde a taxa de um grupo passa a do outro?")
        id_x, id_y = comparacao["diferenca"]
        rotulo_x = _rotulo_grupo(comparacao, id_x)
        rotulo_y = _rotulo_grupo(comparacao, id_y)
        coluna_ponto, _ = st.columns([1, 1])
        with coluna_ponto:
            grano = _seletor_grano("grano_par")

    if rotulo_x == evasao.ROTULO_TAXA_GERAL:
        frase_x = "O eixo X é a taxa geral do curso ou da área"
    else:
        frase_x = f"O eixo X é a taxa de {rotulo_x}"
    nota = comparacao.get("nota") if escolha != "raca" else None
    st.caption(
        f"{frase_x} e o eixo Y a de {rotulo_y}. "
        "A linha tracejada marca taxas iguais, e a mesma distância vale nos dois eixos. "
        f"Um ponto acima dela tem evasão maior em {rotulo_y}. "
        + (
            "A área do ponto é proporcional às matrículas. "
            if tamanho_variavel
            else "Os círculos têm o mesmo tamanho. "
        )
        + "Onde falta matrícula num dos grupos, o ponto não aparece. "
        "Clique em um ponto para destacar a área. Os outros ficam mais transparentes. "
        "Clique de novo para soltar."
        + (f" {nota}" if nota else "")
    )
    cursos, areas = evasao.pares_de_grupos(ofertas, id_x, id_y)
    dados = areas if grano == "area" else cursos
    if dados.empty:
        st.info("Nenhum curso tem matrículas nos dois grupos deste recorte.")
        return
    st.altair_chart(
        evasao.grafico_dispersao_grupos(
            dados,
            f"Taxa de evasão, {rotulo_x} e {rotulo_y}{sufixo}",
            rotulo_x,
            rotulo_y,
            grano == "area",
            tamanho_variavel,
        ),
        width="content",
    )


def texto_mapa_grupos(comparacao):
    if comparacao["modo"] == "diferenca":
        texto = (
            f"A cor é a diferença de taxa, em pontos percentuais: {comparacao['texto_diferenca']}. "
            "O meio da escala é neutro e representa diferença zero. "
            "Onde falta matrícula em algum dos dois grupos, o estado fica cinza."
        )
        nota = comparacao.get("nota")
        if nota:
            texto += " " + nota
    else:
        texto = (
            "A cor é o grupo com maior taxa de evasão no estado. "
            "Se as taxas empatam, fica o grupo com mais matrículas. "
            "Onde não há cursos neste recorte, o estado fica cinza."
        )
    return (
        texto
        + " Clique em um estado para filtrar o gráfico da esquerda."
        + " Clique de novo no mesmo estado para voltar ao Brasil."
    )


def tabela_grupos(dados, comparacao):
    if comparacao["modo"] == "diferenca":
        esquerda, direita = comparacao["diferenca"]
        rotulos = {grupo["id"]: grupo["rotulo"] for grupo in comparacao["grupos"]}
        nome_esquerda = rotulos[esquerda]
        nome_direita = rotulos[direita]
        tabela = dados.sort_values("diferenca_pp", ascending=False).rename(
            columns={
                "SG_UF": "UF",
                "nome_estado": "Estado",
                "taxa_esquerda": f"Taxa {nome_esquerda} (%)",
                "taxa_direita": f"Taxa {nome_direita} (%)",
                "diferenca_pp": "Diferença (p.p.)",
                f"QT_MAT_{esquerda}_2023": f"Matrículas {nome_esquerda}",
                f"QT_MAT_{direita}_2023": f"Matrículas {nome_direita}",
            }
        )
        colunas = [
            "UF",
            "Estado",
            f"Taxa {nome_esquerda} (%)",
            f"Taxa {nome_direita} (%)",
            "Diferença (p.p.)",
            f"Matrículas {nome_esquerda}",
            f"Matrículas {nome_direita}",
        ]
    else:
        tabela = dados.sort_values("TX_EVAS", ascending=False).rename(
            columns={
                "SG_UF": "UF",
                "nome_estado": "Estado",
                "grupo": "Grupo com maior taxa",
                "QT_MAT_2023": "Matrículas em 2023",
                "taxa_pct": "Taxa (%)",
            }
        )
        colunas = ["UF", "Estado", "Grupo com maior taxa", "Taxa (%)", "Matrículas em 2023"]
    config = {}
    for coluna in colunas:
        if coluna.startswith("Matrículas"):
            config[coluna] = st.column_config.NumberColumn(format="%d")
        elif coluna.startswith("Taxa") or coluna == "Diferença (p.p.)":
            config[coluna] = st.column_config.NumberColumn(format="%.1f")
    return tabela.loc[:, colunas], config


st.title("Evasão no ensino superior brasileiro")
st.markdown(
    "Os números vêm do "
    "[Censo da Educação Superior](https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-da-educacao-superior) "
    "do Inep. A coleta usa o cadastro do Sistema e-MEC, que reúne os registros "
    "das instituições, dos cursos e dos locais de oferta."
)
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

escolhas, tamanho_circulos = filtros_laterais()
recorte = (
    evasao.preparar_recorte(carregar_ofertas(), **escolhas) if escolhas["modalidades"] else None
)
aba_cursos, aba_grupos = st.tabs(["Cursos e estados", "Grupos demográficos"])

with aba_cursos:
    iniciar_mapa("uf_selecionada", "evento_mapa")

    if not escolhas["modalidades"]:
        st.warning("Marque ao menos uma modalidade na barra lateral.")
    elif recorte["cursos"].empty or recorte["ofertas"].empty:
        st.info("Nenhum curso passou pelos filtros.")
    else:
        geojson = carregar_geojson()
        uf = st.session_state.uf_selecionada
        nome = evasao.nome_uf(geojson, uf) if uf else None
        visao = evasao.visao_uf(recorte, uf)
        ofertas = visao["ofertas"]
        cursos = visao["cursos"]
        limpar = mostrar_recorte(cursos, ofertas, nome, "limpar_uf")

        sufixo = f" — {nome}" if nome else ""
        chave_areas = _chave_grafico_areas()
        area = _area_selecionada(st.session_state.get(chave_areas))
        if area and area not in _nomes_de_area(visao["areas"]):
            st.session_state.ciclo_grafico_areas += 1
            st.rerun()
        if area:
            coluna_aviso, coluna_acao = st.columns([5, 1], vertical_alignment="center")
            with coluna_aviso:
                st.markdown(
                    f"""
                    <div class="aviso-estado">
                        <div class="aviso-estado-rotulo">Mostrando só esta área</div>
                        <div class="aviso-estado-nome">{area}</div>
                        <div class="aviso-estado-texto">
                            Os cursos e o mapa usam só esta área do conhecimento.
                            Clique de novo na mesma barra para ver todas.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with coluna_acao:
                if st.button("Ver todas as áreas", key="limpar_area"):
                    st.session_state.ciclo_grafico_areas += 1
                    st.rerun()

        coluna_areas, coluna_cursos = st.columns(2, gap="large")
        with coluna_areas:
            st.header("Por área do conhecimento")
            st.caption(
                "A taxa da área soma os cursos cuja maior parte das matrículas está nela. "
                "A cor é a mesma do gráfico de cursos, e o nome completo aparece ao passar o mouse. "
                "Clique em uma área para filtrar os cursos e o mapa. "
                "Clique de novo na mesma área para ver todas."
            )
            mostrar_barras(
                visao["areas"],
                "NO_CINE_AREA_GERAL",
                f"Taxa de evasão por área do conhecimento{sufixo}",
                selecionavel=True,
                chave=chave_areas,
            )

        with coluna_cursos:
            st.header("Por curso")
            escopo = f"as instituições de {nome}" if nome else "todas as instituições"
            frase_area = f" Só entram os cursos de {area}." if area else ""
            st.caption(
                f"Cada barra é o curso da classificação CINE, somando {escopo}. "
                "Nomes parecidos no cadastro, como Sistema e Sistemas de informação, "
                "entram no mesmo curso. A cor é a da área de conhecimento, "
                "a mesma usada no gráfico de áreas. O nome completo aparece ao passar o mouse."
                + frase_area
            )
            if cursos.empty:
                st.info("Nenhum curso passou pelos filtros.")
            else:
                if area:
                    visiveis = cursos[cursos["NO_CINE_AREA_GERAL"].fillna("Sem área") == area]
                else:
                    visiveis = cursos
                if visiveis.empty:
                    st.info(f"Nenhum curso de {area} passou pelos filtros.")
                else:
                    mostrar_barras(
                        visiveis,
                        "NO_CINE_ROTULO",
                        f"Taxa de evasão por curso{sufixo}",
                        rolar=True,
                    )

        titulos_mapa = {
            "taxa": "Como a taxa varia entre os estados?",
            "matriculas": "Onde há mais estudantes em relação à população?",
            "instituicoes": "Onde há mais instituições em relação à população?",
            "municipios": "Onde a oferta alcança mais municípios?",
        }
        textos_cor = {
            "taxa": "A cor é a taxa dos cursos que passaram nos filtros, somada dentro de cada estado.",
            "matriculas": (
                "A cor é o número de estudantes matriculados em 2023 neste recorte, a cada mil habitantes. "
                "A população é a estimativa do IBGE para 2024. Nessa escala os estados ficam na casa das dezenas."
            ),
            "instituicoes": (
                "A cor é o número de instituições com cursos deste recorte a cada milhão de habitantes. "
                "Nessa escala os estados ficam na casa das unidades ou dezenas."
            ),
            "municipios": (
                "A cor é a porcentagem dos municípios do estado com ao menos uma oferta deste recorte. "
                "O denominador é a quantidade de municípios do estado em 2024."
            ),
        }
        cor_mapa = st.session_state.get("cor_mapa_estados", "taxa")
        st.header(titulos_mapa[cor_mapa])
        coluna_cor, _ = st.columns([1, 2])
        with coluna_cor:
            cor_mapa = st.selectbox(
                "A cor representa",
                list(evasao.METRICAS_MAPA),
                format_func=lambda chave: evasao.METRICAS_MAPA[chave]["rotulo"],
                key="cor_mapa_estados",
            )
        frase_area_mapa = f" Só entra a área {area}." if area else ""
        st.caption(
            textos_cor[cor_mapa]
            + frase_area_mapa
            + " Onde não há cursos neste recorte, o estado fica cinza. "
            "Clique em um estado para filtrar os gráficos de barras. "
            "Clique de novo no mesmo estado para voltar ao Brasil."
        )
        mapa, dados_mapa = evasao.mapa_estados(
            evasao.estados_da_area(recorte, area), geojson, uf, cor_mapa
        )
        if dados_mapa.empty:
            st.info("Nenhum estado tem cursos neste recorte.")
            saida_mapa = None
        else:
            faixa_cor_mapa(dados_mapa, cor_mapa)
            saida_mapa = st_folium(
                mapa,
                height=820,
                use_container_width=True,
                returned_objects=["last_clicked", "last_active_drawing"],
                key=f"mapa_estados_{cor_mapa}_{area or 'todas'}",
            )
        if limpar:
            st.session_state.uf_selecionada = None
            st.session_state.evento_mapa = _marca_clique((saida_mapa or {}).get("last_clicked"))
            st.rerun()
        elif aplicar_clique_mapa(saida_mapa, geojson):
            st.rerun()

        sufixo_recorte = sufixo
        st.header("A evasão acompanha o tamanho da oferta?")
        coluna_ponto, coluna_eixo = st.columns(2)
        with coluna_ponto:
            grano_volume = _seletor_grano("grano_volume")
        with coluna_eixo:
            eixo_volume = st.selectbox(
                "Eixo X",
                list(evasao.EIXOS_VOLUME),
                format_func=lambda chave: evasao.EIXOS_VOLUME[chave],
                key="eixo_volume",
            )
        if eixo_volume == "instituicoes":
            texto_eixo = "O eixo X conta instituições distintas com oferta nesse curso ou nessa área."
        elif tamanho_circulos:
            texto_eixo = (
                "O eixo X e o tamanho usam as mesmas matrículas: o tamanho só destaca os pontos maiores."
            )
        else:
            texto_eixo = "O eixo X é o número de matrículas em 2023."
        texto_tamanho = (
            "O tamanho é o número de matrículas em 2023. "
            if tamanho_circulos
            else "Os círculos têm o mesmo tamanho. "
        )
        st.caption(
            "Cada ponto é um curso ou uma área deste recorte. "
            + texto_tamanho
            + "A taxa soma as saídas e só depois divide. "
            + texto_eixo
            + " Clique em um ponto para destacar a área. Os outros ficam mais transparentes."
            + " Clique de novo para soltar."
        )
        cursos_vol, areas_vol = evasao.com_instituicoes(
            visao["ofertas"], visao["cursos"], visao["areas"]
        )
        dados_vol = areas_vol if grano_volume == "area" else cursos_vol
        if dados_vol.empty:
            st.info("Nenhum ponto passou pelos filtros.")
        else:
            st.altair_chart(
                evasao.grafico_dispersao_volume(
                    dados_vol,
                    eixo_volume,
                    grano_volume == "area",
                    f"Taxa de evasão e tamanho da oferta{sufixo_recorte}",
                    tamanho_circulos,
                ),
                width="stretch",
            )

        st.header("Como a evasão se distribui dentro de cada área?")
        st.caption(
            "Cada caixa é uma área. Os quartis pesam o curso pelo número de matrículas: "
            "a mediana é a taxa do curso em que a matrícula acumulada chega à metade dos alunos. "
            "Os pontos são os cursos, por cima da caixa, e o tamanho é a matrícula. "
            "Os bigodes vão até o curso mais extremo ainda dentro de 1,5 intervalo interquartil."
        )
        if visao["cursos"].empty:
            st.info("Nenhum curso passou pelos filtros.")
        else:
            st.altair_chart(
                evasao.grafico_boxplot_areas(
                    visao["cursos"],
                    f"Distribuição da taxa de evasão por área{sufixo_recorte}",
                    tamanho_circulos,
                ),
                width="stretch",
            )

        if not dados_mapa.empty:
            frase_ranking = (
                f"Ranking dos estados na área {area}"
                if area
                else "Ranking de todos os estados deste recorte"
            )
            st.caption(
                f"{frase_ranking}, do maior para o menor valor da cor. "
                "O clique no mapa não altera esta tabela."
            )
            ordem = evasao.METRICAS_MAPA[cor_mapa]["coluna"]
            tabela = dados_mapa.sort_values([ordem, "nome_estado"], ascending=[False, True]).rename(
                columns={
                    "SG_UF": "UF",
                    "nome_estado": "Estado",
                    "QT_MAT_2023": "Matrículas em 2023",
                    "QT_IES": "Instituições",
                    "QT_EVAS": "Evadidos estimados",
                    "taxa_pct": "Taxa (%)",
                    "MAT_POR_MIL": "Matrículas por mil hab.",
                    "IES_POR_MILHAO": "Instituições por milhão",
                    "PCT_MUN_IES": "Municípios com IES (%)",
                }
            )
            st.dataframe(
                tabela.loc[
                    :,
                    [
                        "UF",
                        "Estado",
                        "Taxa (%)",
                        "Matrículas por mil hab.",
                        "Instituições por milhão",
                        "Municípios com IES (%)",
                        "Matrículas em 2023",
                        "Instituições",
                        "Evadidos estimados",
                    ],
                ],
                hide_index=True,
                height=360,
                column_config={
                    "Taxa (%)": st.column_config.NumberColumn(format="%.1f"),
                    "Matrículas por mil hab.": st.column_config.NumberColumn(format="%.1f"),
                    "Instituições por milhão": st.column_config.NumberColumn(format="%.1f"),
                    "Municípios com IES (%)": st.column_config.NumberColumn(format="%.1f"),
                    "Matrículas em 2023": st.column_config.NumberColumn(format="%d"),
                    "Instituições": st.column_config.NumberColumn(format="%d"),
                    "Evadidos estimados": st.column_config.NumberColumn(format="%d"),
                },
            )

with aba_grupos:
    iniciar_mapa("uf_grupos", "evento_mapa_grupos")
    escolha = st.selectbox(
        "Comparação",
        list(evasao.COMPARACOES),
        format_func=lambda chave: evasao.COMPARACOES[chave]["rotulo"],
        key="comparacao_grupos",
    )
    comparacao = evasao.COMPARACOES[escolha]

    if not escolhas["modalidades"]:
        st.warning("Marque ao menos uma modalidade na barra lateral.")
    elif recorte["cursos"].empty or recorte["ofertas"].empty:
        st.info("Nenhum curso passou pelos filtros.")
    else:
        geojson = carregar_geojson()
        uf = st.session_state.uf_grupos
        nome = evasao.nome_uf(geojson, uf) if uf else None
        visao = evasao.visao_uf(recorte, uf)
        limpar = mostrar_recorte(visao["cursos"], visao["ofertas"], nome, "limpar_uf_grupos")
        por_estado = evasao.estados_dos_grupos(recorte["elegiveis"], comparacao)
        grupos = evasao.taxas_dos_grupos(visao["ofertas"], comparacao)

        coluna_graficos, coluna_mapa = st.columns([1, 1.35], gap="large")

        with coluna_mapa:
            if comparacao["modo"] == "diferenca":
                st.header("Como a diferença varia entre os estados?")
            else:
                st.header("Qual grupo tem a maior taxa em cada estado?")
            st.caption(texto_mapa_grupos(comparacao))
            mapa, dados_mapa = evasao.mapa_grupos(por_estado, geojson, comparacao, uf)
            if dados_mapa.empty:
                if comparacao["modo"] == "diferenca":
                    st.info("Nenhum estado tem matrículas nos dois grupos desta comparação.")
                else:
                    st.info("Nenhum estado tem cursos neste recorte.")
                saida_mapa = None
            else:
                if comparacao["modo"] == "diferenca":
                    faixa_diferenca(dados_mapa)
                saida_mapa = st_folium(
                    mapa,
                    height=820,
                    use_container_width=True,
                    returned_objects=["last_clicked", "last_active_drawing"],
                    key="mapa_grupos",
                )
            if limpar:
                st.session_state.uf_grupos = None
                st.session_state.evento_mapa_grupos = _marca_clique((saida_mapa or {}).get("last_clicked"))
                st.rerun()
            elif aplicar_clique_mapa(saida_mapa, geojson, "uf_grupos", "evento_mapa_grupos"):
                st.rerun()

        with coluna_graficos:
            sufixo = f" — {nome}" if nome else ""
            st.header("Qual grupo tem maior e menor taxa de evasão?")
            escopo = f"as instituições de {nome}" if nome else "todas as instituições"
            st.caption(
                f"Cada barra soma {escopo}. A taxa usa a mesma conta do painel, "
                "com as matrículas, os concluintes e os ingressantes daquele grupo. "
                "O nome completo aparece ao passar o mouse."
            )
            mostrar_barras_grupos(
                grupos,
                comparacao,
                f"Taxa de evasão por grupo{sufixo}",
            )

        mostrar_dispersao_demografica(
            visao["ofertas"], comparacao, escolha, sufixo, tamanho_circulos
        )

        if not dados_mapa.empty:
            st.caption("Ranking de todos os estados deste recorte. O clique no mapa não altera esta tabela.")
            tabela, config = tabela_grupos(dados_mapa, comparacao)
            st.dataframe(tabela, hide_index=True, height=360, column_config=config)
