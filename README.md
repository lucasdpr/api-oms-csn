# Sistema de Gestão de Laudos Técnicos - Manutenção MCC#4

Este projeto é uma aplicação web desenvolvida para a digitalização, gestão e automação de laudos de manutenção industrial (Segmentos Bender e Moldes). O sistema visa substituir processos manuais por um fluxo digital ágil, gerando relatórios em PDF padronizados e seguindo rigorosamente as normas de manutenção.

## 🚀 Funcionalidades Principais

* **Digitalização de Checklists:** Mapeamento completo dos itens de inspeção de chegada, execução e saída.
* **Geração Automática de Laudos (PDF):** Automação na criação de relatórios técnicos com layout oficial, seguindo o padrão de engenharia.
* **Gestão de Ativos:** Cadastro e acompanhamento do histórico de manutenção de cada segmento (Bender/Molde).
* **Cálculos e Medições Técnicas:** Suporte para registros complexos como folga de aresta, medições de rolos, isolamento elétrico e parâmetros de termopares.
* **Interface Responsiva:** Desenvolvido para uso rápido na oficina ou em campo.

## 🛠️ Tecnologias Utilizadas

* **Front-end:** HTML5, CSS3 e JavaScript (ES6 Modules).
* **Armazenamento:** LocalStorage (Persistência de dados local sem necessidade de banco de dados externo).
* **PDF Engine:** Manipulação dinâmica via DOM para geração de laudos impressos.

## 📂 Estrutura do Projeto

* `index.html`: Estrutura principal da interface.
* `folhao.js`: O "motor" do sistema. Contém a lógica de preenchimento, cálculos, navegação de abas e a engine de impressão PDF.
* `dados.js`: Onde ficam armazenadas as bibliotecas de checklists e especificações técnicas.
* `banco.js`: Simulação do banco de dados de ativos.
* `ui.js`: Gerenciamento dos componentes visuais (tabelas, listas de ativos).

## 💻 Como Rodar o Projeto

Como o projeto é desenvolvido em Vanilla JS (JavaScript puro), você não precisa de um servidor complexo.

1. Clone o repositório ou baixe a pasta do projeto.
2. Certifique-se de que todos os arquivos (`index.html`, `folhao.js`, `dados.js`, etc.) estejam na mesma pasta raiz.
3. Abra o arquivo `index.html` diretamente no seu navegador (Chrome, Edge ou Firefox).
4. O sistema irá carregar os dados locais e a interface estará pronta para uso.

## 🛠️ Personalização e Manutenção

### Adicionando Imagens Técnicas
O sistema foi configurado para buscar desenhos técnicos automaticamente se eles estiverem na pasta do projeto:
* Nomeie o desenho do molde como: `desenho-molde.jpg`
* Nomeie o desenho do bender como: `desenho-bender.jpg`
* Se a imagem não existir, o sistema ocultará automaticamente a moldura, mantendo o layout limpo.

### Ajustando Parâmetros
Para alterar tolerâncias ou itens de inspeção, edite o arquivo `dados.js`. As tabelas são geradas automaticamente pelo motor de funções no `folhao.js`.

## 📝 Licença
Este sistema é de uso interno para a equipe de manutenção da MCC#4 - CSN.

---
*Desenvolvido para otimizar o tempo de preenchimento e garantir a precisão dos laudos de manutenção.*
