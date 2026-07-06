from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

# ==========================================
# MODELOS DE DADOS (A planta baixa)
# ==========================================
class PecaUpdate(BaseModel):
    id: str
    tonelagem: float
    dias: int
    local: str = ""
    status: str = ""

class FolhaoUpdate(BaseModel):
    id_peca: str
    tipo_equipamento: str = "" 
    tecnico: str = ""
    nova_meta: float = 0.0     
    tipo_manutencao: str = "Geral" 
    dados_chegada: str = ""    
    dados_saida: str = ""      
    status_reparo: str = "Em Andamento"
    pdf_base64: str = ""       # Aqui o Python vai guardar o arquivo PDF!

# ==========================================
# INICIALIZAÇÃO DA API
# ==========================================
app = FastAPI(title="API - Oficina de Moldes e Segmentos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
) # <--- O Python sentiu falta de fechar este parêntese!

# ==========================================
# CORREÇÃO AUTOMÁTICA DO BANCO DE DADOS
# ==========================================
def corrigir_banco():
    import sqlite3
    conexao = sqlite3.connect('oficina.db', timeout=10)
    cursor = conexao.cursor()
    
    # 1. Garante que a tabela de equipamentos existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS equipamentos (ID TEXT PRIMARY KEY)''')
    
    # 2. Adiciona colunas ausentes na tabela principal
    colunas_faltando = ['TONELAGEM REAL', 'DIAS INTEGER', 'STATUS TEXT', 'LOCAL TEXT', 'META REAL']
    for coluna in colunas_faltando:
        try: cursor.execute(f"ALTER TABLE equipamentos ADD COLUMN {coluna}")
        except: pass
            
    # 🔥 A MÁGICA AQUI: Cria a coluna nova_meta no histórico!
    try: cursor.execute("ALTER TABLE historico_reparos ADD COLUMN nova_meta REAL")
    except: pass
            
    conexao.commit()
    conexao.close()

# Roda a verificação
corrigir_banco()

# ==========================================
# ROTAS DO SISTEMA
# ==========================================

@app.get("/")
def read_root():
    return {"status": "Motor Python rodando 100%!", "banco_de_dados": "Conectado"}

@app.get("/api/pecas")
def get_pecas_reais():
    conexao = sqlite3.connect('oficina.db')
    conexao.row_factory = sqlite3.Row 
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM equipamentos LIMIT 50")
    linhas = cursor.fetchall()
    lista_de_pecas = [dict(linha) for linha in linhas]
    conexao.close()
    return lista_de_pecas

@app.post("/api/atualizar_peca")
def atualizar_peca(peca: PecaUpdate):
    try:
        conexao = sqlite3.connect('oficina.db')
        cursor = conexao.cursor()
        cursor.execute('''
            UPDATE equipamentos 
            SET TONELAGEM = ?, DIAS = ?
            WHERE ID = ?
        ''', (peca.tonelagem, peca.dias, peca.id))
        conexao.commit()
        conexao.close()
        return {"status": "sucesso", "mensagem": f"Peça {peca.id} atualizada no SQLite!"}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

@app.post("/api/salvar_folhao")
def salvar_folhao_nuvem(folhao: FolhaoUpdate):
    try:
        import sqlite3
        from datetime import datetime
        conexao = sqlite3.connect('oficina.db', timeout=10)
        cursor = conexao.cursor()
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Salva no Histórico com a NOVA META gravada para sempre
        cursor.execute("""
            INSERT INTO historico_reparos 
            (id_peca, tipo_equipamento, tecnico, tipo_manutencao, dados_chegada, dados_saida, status_reparo, pdf_base64, ultima_modificacao, nova_meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (folhao.id_peca, folhao.tipo_equipamento, folhao.tecnico, folhao.tipo_manutencao, folhao.dados_chegada, folhao.dados_saida, folhao.status_reparo, folhao.pdf_base64, data_atual, folhao.nova_meta))
        
        # 2. Atualiza a tabela de equipamentos (zera se for GERAL, mantém se for PARCIAL)
        if folhao.tipo_manutencao == "GERAL":
            cursor.execute("UPDATE equipamentos SET STATUS = 'Oficina / Reserva', TONELAGEM = 0, DIAS = 0, META = ? WHERE ID = ?", (folhao.nova_meta, folhao.id_peca))
        else:
            cursor.execute("UPDATE equipamentos SET STATUS = 'Oficina / Reserva', META = ? WHERE ID = ?", (folhao.nova_meta, folhao.id_peca))
            
        conexao.commit()
        conexao.close()
        return {"status": "sucesso", "mensagem": "Salvo com sucesso"}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
    # A ROTA PARA LER O HISTÓRICO: Busca os reparos salvos na nuvem
@app.get("/api/historico_reparos")
def get_historico_reparos():
    try:
        conexao = sqlite3.connect('oficina.db')
        conexao.row_factory = sqlite3.Row # Isso transforma as linhas em dicionários/JSON
        cursor = conexao.cursor()
        
        # Busca todo o histórico na tabela que criamos mais cedo
        cursor.execute("SELECT * FROM historico_reparos ORDER BY ultima_modificacao DESC LIMIT 50")
        linhas = cursor.fetchall()
        lista_de_reparos = [dict(linha) for linha in linhas]
        
        conexao.close()
        return lista_de_reparos
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}