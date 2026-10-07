Prompts utilizados:



"""
Crie 3 gráficos para responder as perguntas 1 e 2:

1. Quais cursos tem maior e menor taxa de evasão?
- Gráfico de barras horizontais que representam a taxa de evasão média de cada curso, independente da instituição (somando os números de todos os cursos com o mesmo nome e código no Brasil). Filtro exclusivo para esse gráfico: apenas cursos de uma certa área do conhecimento.
- Gráfico de barras horizontais que representam a taxa de evasão média em cada área do cconhecimento
2. Como a taxa de evasão vaira de acordo com o estado onde está o curso?
- Diagrama Colorplath, com a cor de cada estado representando a taxa de evasão média daquele estado

Os três gráficos devem ter os mesmos filtros:
- Filtro 1: Quantidade mínima de estudantes no curso (somando o número de estudantes matriculados em todos os cursos com o mesmo nome no Brasil todo). Default: 1000
- Filtro 2: Excluir cursos com zero estudantes concluintes em 2023. Default: true
- Filtro 3: Cursos presenciais, cursos a distância, ou os dois. Default: apenas presenciais
- Filtro 4: Filtro por tipo de organização acadêmica. Default: todas
- Filtro 5: Filtro por tipo de categoria administrativa. Default: todas

Crie o código de preparação dos gráficos no arquivo atividade01_proposta_analise_visual.ipynb, nos blocos de "Preparação do ambiente" "Carregamento dos dados". Separe o bloco de "Estatísticas e gráficos" em três: em cada um deve ser criado e rodado um dos gráficos.

Os filtros podem ficar no código por enquanto. Os gráficos podem utilizar bibliotecas como Altair e Foil. Tenha em mente que eles serão adicionados a um dashboard que usa streamlit depois.

A pasta brazil_droptouts_dashboard foi uma primeira tentativa de fzer um dashboard com gráficos semelhantes. Os novos gráficos devem ser feitos do zero, porém os arquivos da pasta brazil_droptouts_dashboard ainda podem ser usados apenas para consulta. Só não podem ser referenciados no código, ou em comentários dentro do código. Mais tarde, será feita uma nova versão do dashboard mais organizada e focada em responder as perguntas

Ao final adicione uma linha na tabela de log de pedidos para a IA no bloco de ## Registro do uso de IA e das referências.
"""

