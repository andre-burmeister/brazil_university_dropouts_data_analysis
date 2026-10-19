# Evasão no ensino superior brasileiro

## Informações do Aluno:
Nome: André Bracht Burmeister
Matrícula: 00315365
Nome do Trabalho: Evasão no ensino superior brasileiro

## Informações do Trabalho:

Painel em Streamlit que estima a taxa de evasão na graduação brasileira entre os censos de **2023** e **2024**.

A taxa, em cada oferta de curso, é:

matrículas de 2023 − concluintes de 2023 − matrículas de 2024 + ingressantes de 2024

Uma transferência para outro curso entra nessa conta como saída. Os cursos são agrupados pelo código da classificação CINE, e não pelo nome livre da instituição.

O painel responde três perguntas:

1. Quais cursos têm maior e menor taxa de evasão?
2. Como a taxa de evasão varia de acordo com o estado onde está o curso?
3. Como a taxa de evasão varia entre grupos demográficos, como sexo, cor ou raça e idade?

A primeira aba mostra cursos, áreas do conhecimento e o mapa do Brasil. A segunda compara grupos demográficos. Os filtros da barra lateral valem para as duas abas.

## Dados

Os microdados são do [Censo da Educação Superior](https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-da-educacao-superior), do Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep). A coleta usa o cadastro do Sistema e-MEC, que reúne os registros das instituições, dos cursos e dos locais de oferta. A página de resultados está em [Censo da Educação Superior — Resultados](https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-da-educacao-superior/resultados). Os arquivos são públicos e estão em CSV, com separador `;` e codificação Latin-1. O dicionário de variáveis vem no mesmo pacote, em planilha Excel.

Na primeira execução, o painel baixa sozinho os pacotes do Inep e extrai só o cadastro de cursos para a pasta `dados/`. Isso vale localmente e no Streamlit Cloud. Fontes:

- [Microdados do Censo da Educação Superior 2023](https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2023.zip)
- [Microdados do Censo da Educação Superior 2024](https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip)

Layout esperado após o download (ou após extração manual, se preferir offline):

```text
dados/
  microdados_censo_da_educacao_superior_2023/
    dados/
      MICRODADOS_CADASTRO_CURSOS_2023.CSV
  microdados_censo_da_educacao_superior_2024/
    dados/
      MICRODADOS_CADASTRO_CURSOS_2024.CSV
```

O contorno dos estados já está no repositório, em `geo/brazil_states.geojson`. Os microdados não entram no Git.

## Como rodar

É preciso Python 3.10 ou mais recente e acesso à internet na primeira execução. Na pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O painel abre em [http://localhost:8501](http://localhost:8501). O primeiro cold start pode demorar vários minutos (download dos zips do Inep e leitura dos CSVs); as execuções seguintes usam os arquivos em disco e o cache do Streamlit.
