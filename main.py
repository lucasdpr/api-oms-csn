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
    allow_headers=["*"],
)

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
        conexao = sqlite3.connect('oficina.db')
        cursor = conexao.cursor()
        
        # Cria a tabela de histórico (agora com a coluna para o PDF)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_reparos (
                id_peca TEXT PRIMARY KEY,
                tipo_equipamento TEXT,
                tecnico TEXT,
                tipo_manutencao TEXT,
                dados_chegada TEXT,
                dados_saida TEXT,
                status_reparo TEXT,
                pdf_base64 TEXT,
                ultima_modificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Salva tudo na nuvem, incluindo o arquivo PDF
        cursor.execute('''
            INSERT OR REPLACE INTO historico_reparos 
            (id_peca, tipo_equipamento, tecnico, tipo_manutencao, dados_chegada, dados_saida, status_reparo, pdf_base64)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (folhao.id_peca, folhao.tipo_equipamento, folhao.tecnico, folhao.tipo_manutencao,
              folhao.dados_chegada, folhao.dados_saida, folhao.status_reparo, folhao.pdf_base64))
        
        # A REGRA DE OURO DA LIBERAÇÃO (Geral vs Parcial)
        if folhao.status_reparo == "Concluido":
            cursor.execute("SELECT TONELAGEM, DIAS, META FROM equipamentos WHERE ID = ?", (folhao.id_peca,))
            resultado = cursor.fetchone()
            
            ton_atual = resultado[0] if resultado else 0
            dias_atual = resultado[1] if resultado else 0
            meta_atual = resultado[2] if resultado else 0
            
            ton_final = 0 if folhao.tipo_manutencao == "Geral" else ton_atual
            dias_final = 0 if folhao.tipo_manutencao == "Geral" else dias_atual
            meta_final = folhao.nova_meta if folhao.nova_meta > 0 else meta_atual
            
            cursor.execute('''
                UPDATE equipamentos 
                SET TONELAGEM = ?, DIAS = ?, META = ?, STATUS = 'Oficina / Reserva', LOCAL = 'Estoque Reserva'
                WHERE ID = ?
            ''', (ton_final, dias_final, meta_final, folhao.id_peca))
        
        conexao.commit()
        conexao.close()
        
        return {"status": "sucesso", "mensagem": f"Laudo PDF e dados da peça {folhao.id_peca} salvos com sucesso!"}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}