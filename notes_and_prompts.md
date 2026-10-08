# Prompts utilizados:

## Criação dos gráficos na atividade 1

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

## Criação do dashboard:

"""
Crie um dashboard usando o streamlit no arquivo app.py

O dashboard deve conter:

1. Um título e resumo do objetivo, contendo as três perguntas principais a serem respondidas

2. Duas abas:
    - A primeira que responde as duas primeiras perguntas (taxa de evasão por curso e estado)
    - A segunda que responde a terceira pergunta (como a taxa de evasão muda em diferentes grupos demográficos)
Por enquanto, apenas a primeira aba deve ser preenchida, com os gráficos criados em atividade01_proposta_analise_visual.ipynb. A segunda aba deve permanescer vazia por enquanto.

3. Uma barra lateral com os filtros comuns a todos os gráficos (das duas abas): 
    - Barra deslizante: Quantidade mínima de estudantes no curso (default: 1000); 
    - Toggle: Excluir cursos com zero estudantes concluintes em 2023 (default: true);
    - Caixas de seleção: Cursos presenciais, cursos a distância, ou os dois (default: apenas presenciais);
    - Dropdown de seleção: Filtro por tipo de organização acadêmica (default: todas);
    - Dropdown de seleção: Filtro por tipo de categoria administrativa (default: todas).

Deixe os gráficos o mais modernos e bonitos possível, mantendo a organização e a simplicidade do código. É permitido criar arquivos novos para organização do código.
"""

### Correções do Dashboard

1. Correção dos dados
"""
No gráfico de barras feito em @atividade01_proposta_analise_visual.ipynb , os primeiros cursos estão diferentes do cursos listados no dashboard. Além disso, há cursos duplicados (quase o mesmo nome. Por exemplo: "Sistemas De Informação" e "Sistema De Informação"). Porque isso está acontecendo. É algum erro? Se sim, corrija.
"""

2. Correções de aparência:

"""
Modifique o colorplath para que a barra de cores seja contínua e que o mapa não apareca em baixo (apenas o contorno dos estados. Se não houver dados naquele estado, ele deve ser cinza)
"""

"""
Impeça o zoom no colorplath
"""

"""
Mudanças nos gráficos de barra:

- O gráfico po curso deve conter uma opção de selecionar todos os cursos. De preferência deve ser uma combo box (dropdown, onde pode selecionar quantos quiser).
- Cada área do conhecimento deve ter uma cor associada. As barras dos dois gráficos devem ser coloridas de acordo com a área do conhecimento.
- Os nomes de cada barra (curso ou área do conhecimento) devem ser escritos dentro da própria barra. Quando um nome for muito grande, coloque reticências. O nome completo do curso/área deve aparecer ao passar o mouse sobre ela.
"""

"""

Melhoria no gráfico de barras de cursos: 
1. Remova a legenda de cores (deixe apenas as barras coloridas, de acordo com a área do conhecimento)
2. Ao invés de um filtro (combo box) por curso, ele deve ser um filtro por área do conhecimento.
3. O filtro (combo box) está com uma opção "Select all" e outa "Todos os cursos" Deixe apenas uma.
4. O gŕafico de barras está com linhas demais em um espaço muito pequeno. Coloque uma barra de rolagem e mantenha as linhas do mesmo tamanho.

"""

3. Interatividade do colorplath:

"""
É possível fazer com que o colorplath seja clicável? Quero que, ao clicar em um estado, os dados sejam filtrados apenas para aquele estado. Isso é possível? Como poderia ser feito? O ideal é que o gráfico de estados fique a direita dos outros.
"""

"""
Melhorias e correções:

1. O gráfico de barras por área de conhecimento deve ficar acima do gráfico de barras por curso. 
2. Há muito espaço inutilizado dos lados e o gráfico do Brasil está muito prqueno. Utilize o espaço sobrando para que o mapa do Brasil possa ficar maior.
3. Ao clicar em um estado, deve haver uma indicaçao maior de que apenas os dados dele estado estão sendo mostrados. Ou o estado fica maior no mapa, ou a borda fica mais grossa do que já está, ou com uma cor diferente.
4. Deve também haver escrito em algum lugar o estado do qual os dados estão sendo mostrados.

"""

4. Criação dos gráficos de comparação entre demográficos:

"""
Preencha a segunda aba com os dois gráficos que ajudam a responder a pergunta 3:
Como a taxa de evasão varia entre grupos demográficos (sexo, etnia, idade, ...)?

Serão dois gráficos que seguem exatamente o mesmo esqueleto, disposição e filtros dos gráficos na primeira aba. Mas que servem para comparar a taxa de evasão entre diferentes grupos demográficos. Haverão algumas comparações possíveis (selecionadas em um dropdown no topo da aba):

A. Mulheres e Homens:
QT_ING_FEM
QT_ING_MASC

B. Faixas de Idade:
QT_ING_0_17
QT_ING_18_24
QT_ING_25_29
QT_ING_30_34
QT_ING_35_39
QT_ING_40_49
QT_ING_50_59
QT_ING_60_MAIS

C. Etnia/raça:
QT_ING_BRANCA
QT_ING_PRETA
QT_ING_PARDA
QT_ING_AMARELA
QT_ING_INDIGENA
QT_ING_CORND

D. Alunos com ou sem deficiência:
QT_ING_DEFICIENTE
QT_ING - QT_ING_DEFICIENTE

E. Alunos cotistas ou não cotistas:
QT_ING_RESERVA_VAGA
QT_ING - QT_ING_RESERVA_VAGA

F. Alunos de escola pública vs particular:
QT_ING_PROCESCPUBLICA
QT_ING_PROCESCPRIVADA
QT_ING_PROCNAOINFORMADA

Os gráficos devem ser os seguintes:

1. Gráfico de barras que representam a taxa de evasão média dos diferentes grupos demográficos;

2. Colorplath dos estado brasileiros:
- Para os grupos A, D, E e F, deve haver uma barra de cores contínua que representa a diferença entre a taxa de evasão de um grupo e com a taxa do outro (por exemplo QT_ING_FEM - QT_ING_MASC). A barra contínua de cores deve ter uma cor do meio neutra, para representar diferença zero.
- Para os grupos B e C, a cor de cada estado deve representar o grupo com maior taxa de evasão naquele estado.

Eles devem seguir exatamente o mesmo formato e disposição dos gráficos na primeira aba.

"""