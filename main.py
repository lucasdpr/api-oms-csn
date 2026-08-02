from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional

app = FastAPI(title="API - Oficina de Moldes CSN")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🔥 CONFIGURAÇÃO DO BANCO DE DADOS POSTGRESQL (RENDER)
# ==========================================
DB_HOST = "dpg-d9nsgpvqj5pc73fi170g-a.ohio-postgres.render.com"
DB_NAME = "oficina_zvft"
DB_USER = "oficina_user"
DB_PASSWORD = "xwHUrq4qtkm8E8bFdMxwUcBdkJ8FHUXA"
DB_PORT = "5432"

def get_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Cria as tabelas se elas não existirem (compatível com PostgreSQL)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipamentos (
            ID TEXT PRIMARY KEY,
            TIPO TEXT,
            LOCAL TEXT,
            STATUS TEXT,
            TONELAGEM REAL,
            DIAS INTEGER,
            META REAL,
            POSICAO TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_apontamento_geral (
            id SERIAL PRIMARY KEY,
            data_hora TEXT,
            operador TEXT,
            qtd_mcc2 REAL,
            qtd_mcc3 REAL,
            qtd_mcc4 REAL,
            desfeito INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_apontamento_moldes (
            id SERIAL PRIMARY KEY,
            data_hora TEXT,
            operador TEXT,
            qtd_mcc2 INTEGER,
            qtd_mcc3 INTEGER,
            qtd_mcc4 INTEGER,
            desfeito INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db() # Roda na inicialização da API

# ==========================================
# MODELOS
# ==========================================
class PecaUpdate(BaseModel):
    id: str
    tonelagem: Optional[float] = None
    dias: Optional[int] = None
    local: Optional[str] = None
    status: Optional[str] = None

class ProducaoGeral(BaseModel):
    operador: str
    qtd_mcc2: float
    qtd_mcc3: float
    qtd_mcc4: float

class ApontamentoMoldes(BaseModel):
    operador: str
    qtd_mcc2: int
    qtd_mcc3: int
    qtd_mcc4: int

class DesfazerApontamento(BaseModel):
    log_id: int
    operador: str

# ==========================================
# ROTAS DA API
# ==========================================
@app.get("/api/pecas")
def get_pecas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipamentos")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.post("/api/atualizar_peca")
def atualizar_peca(peca: PecaUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE equipamentos SET TONELAGEM = %s, DIAS = %s WHERE ID = %s",
        (peca.tonelagem, peca.dias, peca.id)
    )
    conn.commit()
    conn.close()
    return {"sucesso": True}

@app.post("/api/apontar_producao_geral")
def apontar_producao_geral(dados: ProducaoGeral):
    conn = get_db()
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for mcc, qtd in [("2", dados.qtd_mcc2), ("3", dados.qtd_mcc3), ("4", dados.qtd_mcc4)]:
        if qtd and qtd > 0:
            cursor.execute(f"""
                UPDATE equipamentos 
                SET TONELAGEM = COALESCE(TONELAGEM, 0) + %s 
                WHERE STATUS = 'Instalado' 
                AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%' 
                     OR LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%' 
                     OR LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%')
                AND UPPER(TIPO) NOT LIKE '%MOLDE%'
            """, (qtd,))

    cursor.execute(
        "INSERT INTO log_apontamento_geral (data_hora, operador, qtd_mcc2, qtd_mcc3, qtd_mcc4, desfeito) VALUES (%s, %s, %s, %s, %s, 0)",
        (agora, dados.operador, dados.qtd_mcc2, dados.qtd_mcc3, dados.qtd_mcc4)
    )
    conn.commit()
    conn.close()
    return {"sucesso": True}

@app.post("/api/apontar_moldes")
def apontar_moldes(dados: ApontamentoMoldes):
    conn = get_db()
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for mcc, qtd in [("2", dados.qtd_mcc2), ("3", dados.qtd_mcc3), ("4", dados.qtd_mcc4)]:
        if qtd and qtd > 0:
            cursor.execute(f"""
                UPDATE equipamentos 
                SET TONELAGEM = COALESCE(TONELAGEM, 0) + %s 
                WHERE STATUS = 'Instalado' 
                AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%' 
                     OR LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%' 
                     OR LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%')
                AND UPPER(TIPO) LIKE '%MOLDE%'
            """, (qtd,))

    cursor.execute(
        "INSERT INTO log_apontamento_moldes (data_hora, operador, qtd_mcc2, qtd_mcc3, qtd_mcc4, desfeito) VALUES (%s, %s, %s, %s, %s, 0)",
        (agora, dados.operador, dados.qtd_mcc2, dados.qtd_mcc3, dados.qtd_mcc4)
    )
    conn.commit()
    conn.close()
    return {"sucesso": True}

@app.get("/api/historico_apontamentos_geral")
def get_historico_geral():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM log_apontamento_geral ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.get("/api/historico_apontamentos_moldes")
def get_historico_moldes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM log_apontamento_moldes ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.post("/api/desfazer_apontamento_geral")
def desfazer_apontamento_geral(dados: DesfazerApontamento):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM log_apontamento_geral WHERE id = %s", (dados.log_id,))
    log = cursor.fetchone()
    if not log: raise HTTPException(status_code=404, detail="Log não encontrado")
    if log["desfeito"] == 1: raise HTTPException(status_code=400, detail="Já foi desfeito.")

    for mcc, qtd in [("2", log["qtd_mcc2"]), ("3", log["qtd_mcc3"]), ("4", log["qtd_mcc4"])]:
        if qtd and qtd > 0:
            cursor.execute(f"""
                UPDATE equipamentos 
                SET TONELAGEM = GREATEST(0, COALESCE(TONELAGEM, 0) - %s) 
                WHERE STATUS = 'Instalado' 
                AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%' 
                     OR LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%' 
                     OR LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%')
                AND UPPER(TIPO) NOT LIKE '%MOLDE%'
            """, (qtd,))

    cursor.execute(
        "UPDATE log_apontamento_geral SET desfeito = 1, operador = %s WHERE id = %s",
        (dados.operador, dados.log_id)
    )
    conn.commit()
    conn.close()
    return {"sucesso": True}

@app.post("/api/desfazer_apontamento_moldes")
def desfazer_apontamento_moldes(dados: DesfazerApontamento):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM log_apontamento_moldes WHERE id = %s", (dados.log_id,))
    log = cursor.fetchone()
    if not log: raise HTTPException(status_code=404, detail="Log não encontrado")
    if log["desfeito"] == 1: raise HTTPException(status_code=400, detail="Já foi desfeito.")

    for mcc, qtd in [("2", log["qtd_mcc2"]), ("3", log["qtd_mcc3"]), ("4", log["qtd_mcc4"])]:
        if qtd and qtd > 0:
            cursor.execute(f"""
                UPDATE equipamentos 
                SET TONELAGEM = GREATEST(0, COALESCE(TONELAGEM, 0) - %s) 
                WHERE STATUS = 'Instalado' 
                AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%' 
                     OR LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%' 
                     OR LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%')
                AND UPPER(TIPO) LIKE '%MOLDE%'
            """, (qtd,))

    cursor.execute(
        "UPDATE log_apontamento_moldes SET desfeito = 1, operador = %s WHERE id = %s",
        (dados.operador, dados.log_id)
    )
    conn.commit()
    conn.close()
    return {"sucesso": True}

@app.get("/")
def root():
    return {"message": "API - Oficina de Moldes CSN Online!"}