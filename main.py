from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

# Inicializa o motor da API
app = FastAPI(title="API - Oficina de Moldes e Segmentos")

# Configuração para permitir a comunicação com o painel visual
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota de teste
@app.get("/")
def read_root():
    return {"status": "Motor Python rodando 100%!", "banco_de_dados": "Conectado"}

# A ROTA PRINCIPAL: Onde o seu site vai buscar os dados reais
@app.get("/api/pecas")
def get_pecas_reais():
    # 1. Abre o nosso cofre
    conexao = sqlite3.connect('oficina.db')
    
    # Faz o Python devolver os dados no formato perfeito para a web (JSON)
    conexao.row_factory = sqlite3.Row 
    cursor = conexao.cursor()
    
    # 2. Pede os dados ao banco (Limitado a 50 por enquanto para testar)
    cursor.execute("SELECT * FROM equipamentos LIMIT 50")
    linhas = cursor.fetchall()
    
    # 3. Transforma o resultado e fecha o cofre
    lista_de_pecas = [dict(linha) for linha in linhas]
    conexao.close()
    
    # 4. Envia tudo para o Front-end
    return lista_de_pecas