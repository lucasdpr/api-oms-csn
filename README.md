# OMS (Oficina de Moldes e Segmentos) - Backend & Database Utilities

Este repositório contém a infraestrutura de back-end e os scripts de automação de banco de dados para o sistema OMS. O projeto utiliza uma API rápida e moderna, aliada a rotinas em Python para sincronização de dados industriais (equipamentos, estoque e equipes) a partir de planilhas Excel para um banco de dados em nuvem.

## 🛠️ Tecnologias Utilizadas

*   **API Web:** FastAPI e Uvicorn.
*   **Banco de Dados:** PostgreSQL (hospedado no Neon).
*   **Manipulação de Dados:** Pandas e Openpyxl (para leitura de arquivos `.xlsx`)[cite: 3].
*   **Notificações:** PyWebPush (para Web Push Notifications)[cite: 3, 8].
*   **Autenticação/Segurança:** Bcrypt e Python-dotenv[cite: 3].
*   **Deploy:** Configurado para rodar na plataforma Render.

## ⚙️ Configuração do Ambiente

1. Clone este repositório.
2. Instale as dependências executando:
   ```bash
   pip install -r requirements.txt
