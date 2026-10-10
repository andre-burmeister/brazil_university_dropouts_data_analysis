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

5. Correções nos gráficos da nova aba:

"""
Mudanças nos gráficos da nova aba:

1. Nas duas abas, há um espaço grande entre o texto acima do mapa e o mapa em sí. Se possível, diminua esse espaço.

2. A maior e menor taxa de evasão são desnecessárias acima do mapa da segunda aba, quando há mais de duas categorias (grupos B e C).

3. Nos grupos com duas categorias (A, D, E e F) as cores do gráfico de barras deve ser a mesma das pontas da barra contínua de cores. Assim fica mais fácil de entender o que as cores do mapa significam

"""

"""

Correções:

1. Impedir de arrastar o mapa: consigo clicar e arrastar o mapa, o que não deveria ser possível.
2. O botão de "Ver o Brasil todo" deve aparecer apenas quando um estado está selecionado, junto com o aviso de que apenas os dados daquele estado estão sendo mostrados.

"""

"""

Os gráficos da aba de grupos demográficos não estão mudando ao modificar os filtros da barra lateral (Matrículas mínimas no curso,Excluir cursos sem concluintes em 2023, Modalidade, Organização acadêmica e Categoria administrativa). Aplique esses filtros também aos gráficos da aba de grupos demográficos

"""

6. Mudanças finais de aparência:

"""

No streamlit padrão tem um modo escuro. Porque ele sumiu?
Por favor, inclua o modo escuro de volta.

"""

7. Novas cnfigurações no colorplath:

"""

Na verdade, ao invés de 
- Número de estudantes matriculados no estado,
- Númeto de instituições de ensino do estado
Eu gostaria que fosse:
- Número de estudantes matriculados no estado por habitante
- Númeto de instituições de ensino do estado por habitante

"""

8. Novos gráficos:

"""

Estou pensando em um gráfio assim para a aba com comparações entre grupos demográficos:

Scatter plot da segunda aba:
    - Para grupos demográficos com 2 categorias (Mulheres e Homens, Deficiência, Cotas, alunos vindo de escolas pública vs particular): 
        - Gráfico com a taxa de evasão de um grupo no eixo X e outro no eixo Y
        - Cada ponto pode ser: um curso ou uma área do conhecimento (seletor ao lado).
        - Tamanho dos pontos é a quantidade de matrículas naquele curso ou área do conhecimento.
    - Para grupos demográficos com vários grupos:
        - Tem alguma sugestão?

Que gráfico poderia estar no lugar desse para os grupos demográficos com várias categorias (ex.: Cor ou Raça, idade). 
Teria como fazer um scatterplot parecido? Como?
Se não, você teria alguma sugestão de outro tipo de gráfico para fazer no lugar?


"""


# Notas:

## Opções de gráficos extras para fazer:

- Gráficos boxplot: 
	- gráficos onde cada curso é um ponto e cada área do conhecimento tem um box plot
	- Mesma coisa, mas pra grupos demográficos

- Scatter plots: 
	- Quantidade de matriculados vs taxa de evasão

- Star plots
- Heat maps

- Barras empilhadas para grupos diferentes, em cursos e estados diferentes

- Adicionar os links para os dados no dashboard



## Gráficos motivados pelo roteiro da apresentação:
1. Adição ao colorplath da primeira página:
    - Um seletor que seleciona se a cor do colorplath representa:
        - A taxa de evasão do estado (já está assim)
        - O número total de estudantes matriculados no estado
        - O númeto total de instituições de ensino do estado


Novos gráficos a serem adicionados:


### Na primeira aba:

1. Scatter plot:
    - Eixo Y é a taxa de evasão
    - Eixo X pode ser:
        - Número de instituições oferecendo o curso
        - Número de aluno mariculados vs taxa de evasão
    - Adicione um seletor dropdown para selecionar se os pontos representam cursos ou áreas do conhecimento.
    - Tamanho dos pontos é a quantidade de matrículas naquele curso ou área do conhecimento.

2. Vários Box plots alinhados horizontalmente, cada um representando uma área do conhecimento. 
    - O box plot é sobre o dados de taxa de evasão de cada curso, mas ele deve ser pesado pelo número de alunos matriculados. Ou seja, na prática é um box plot de "probabilidade de evasão por aluno"
    - Sobre cada um dos box plots, adicione pontos representando cada curso. 
    - O tamanho dos ponto representa a quantidade de matriculados naquele cursos.
    - Lembrando, o box plot NÃO é baseado linearmente na taxa de evasão dos cursos, mas sim pela taxa de evasão PESADA PELO NÚMERO DE ALUNOS.

### Na segunda aba:

3. Scatter plot:
    - Para grupos demográficos com 2 categorias (Mulheres e Homens, Deficiência, Cotas, alunos vindo de escolas pública vs particular): 
        - Gráfico com a taxa de evasão de um grupo no eixo X e outro no eixo Y
        - Cada ponto pode ser: um curso ou uma área do conhecimento (seletor ao lado).
        - Tamanho dos pontos é a quantidade de matrículas naquele curso ou área do conhecimento.
    - Para idades, o gráfico de linhas como foi sugerido
        - No eixo X, as faixas em ordem. No eixo Y, a taxa de evasão. Cada linha é uma área do conhecimento. A espessura acompanha o volume de matrículas.
    - Para cor e raça, o mesmo scatterplot usado para 2 categorias, mas com um seletor para selecionar a cor/raça em destaque




9. Alterações no dashboard:

"""

Crie um readme com:

- Informações básicas sobre o app
- Onde e como baixar os dados
- Como rodar o app

Baseie-se nas informações contidas em @atividade01_proposta_analise_visual.ipynb.

Na introdução do dashboard, abaixo do título, adicione o link para o site do Censo da Educação Superior do INEP e informações sobre como os dados foram coletados  


"""


"""

Correções nos gráficos da primeira aba:

1. No scatter plot da primeira aba:
    - Permita selecionar uma área do conhecimento para destacar, clicando na bolinha. Ao selecionar, as outras devem ficar mais transparentes
    - Ao selecionar para que cada ponto seja uma área do conhecimento (ao invés de curso), os eixos somem. Corrija isso. Os eixos devem aparecer nos dois gráficos. Além disso, retire o nome de cada ponto. Isso deixa o gráfico poluído.

2. Nos box plots:
    - Mude a direção dos box plots (de verticais para horizontais)
    - Deixe o eixo da taxa de evasão visível (agora eixo X). 
    - Sobreponha os pontos ao box plot (talvez deixe o box plot mais transparente para facilitar a visualização dos pontos) 

3. Não consigo ver a legenda de tamanho dos círculos no modo escuro. Modifique a cor delas nesse modo.

"""

"""

Correções nos gráficos da segunda aba:

1. Nos scatter plots com duas categorias (incluindo de cor e raça):
    - Mantenha os eixos aparecendo.
    - Mantenha a razão entre eixo x e y fixa. Nesse gráfico, isso é importante pois os dois eixos medem taxa de evasão.
    - Deixe selecionar uma área de conhecimento para destacá-la. As outras devem ficar semitransparentes (exatamente como no scatter-plot da primeira aba)

2. No gráfico de linhas (idades):
    - Aumente a diferença de espessura das linhas. A espessura deve ser proporcional ao número de matriculados no curso.
    - Adicione transparência às linhas para que seja visível onde estão mais concentradas.
    - Deixe os eixos do gráfico visíveis.

3. Para todos os gráficos com pontos de tamanho variável. A área do ponto deve ser proporcional ao número que ele representa. Nesse caso, número de matriculados. Ou seja, o raio ou diâmetro do círculo tem que ser proporcional à raiz quadrada do número de matriculados.

"""