from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import os

class PecaUpdate(BaseModel):
    id: str
    tonelagem: float
    dias: int
    local: str = ""
    status: str = ""

class ProducaoGeral(BaseModel):
    mcc2: float
    mcc3: float
    mcc4: float
    operador: str

class ApontamentoMoldes(BaseModel):
    qtd_mcc2: int
    qtd_mcc3: int
    qtd_mcc4: int
    operador: str

class DesfazerApontamento(BaseModel):
    log_id: int
    operador: str

app = FastAPI(title="API - Oficina de Moldes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/api/salvar_folhao")
def salvar_folhao(dados: dict):
    try:
        conexao = sqlite3.connect('oficina.db', timeout=10)
        cursor = conexao.cursor()
        
        # Cria tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folhoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_peca TEXT,
                tipo_equipamento TEXT,
                tecnico TEXT,
                nova_meta REAL,
                tipo_manutencao TEXT,
                dados_chegada TEXT,
                dados_saida TEXT,
                status_reparo TEXT,
                data_hora TEXT,
                pdf_base64 TEXT
            )
        ''')
        
        from datetime import datetime
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO folhoes 
            (id_peca, tipo_equipamento, tecnico, nova_meta, tipo_manutencao,
             dados_chegada, dados_saida, status_reparo, data_hora, pdf_base64)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados.get('id_peca', ''),
            dados.get('tipo_equipamento', ''),
            dados.get('tecnico', ''),
            dados.get('nova_meta', 0),
            dados.get('tipo_manutencao', ''),
            dados.get('dados_chegada', '{}'),
            dados.get('dados_saida', '{}'),
            dados.get('status_reparo', 'Concluido'),
            data_hora,
            dados.get('pdf_base64', '')
        ))
        
        conexao.commit()
        conexao.close()
        return {"status": "sucesso", "mensagem": "Folhão salvo com sucesso!"}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

def corrigir_banco():
    conexao = sqlite3.connect('oficina.db', timeout=10)
    cursor = conexao.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS equipamentos (ID TEXT PRIMARY KEY)''')
    
    colunas = ['TIPO TEXT', 'LOCAL TEXT', 'STATUS TEXT', 'TONELAGEM REAL', 'DIAS INTEGER', 'META REAL', 'POSICAO TEXT']
    for col in colunas:
        try: cursor.execute(f"ALTER TABLE equipamentos ADD COLUMN {col}")
        except: pass
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_apontamento_geral (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT, operador TEXT,
            qtd_mcc2 REAL, qtd_mcc3 REAL, qtd_mcc4 REAL,
            desfeito INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_apontamento_moldes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT, operador TEXT,
            qtd_mcc2 INTEGER, qtd_mcc3 INTEGER, qtd_mcc4 INTEGER,
            desfeito INTEGER DEFAULT 0
        )
    """)
    conexao.commit()
    conexao.close()

corrigir_banco()

@app.get("/api/pecas")
def get_pecas_reais():
    conexao = sqlite3.connect('oficina.db')
    conexao.row_factory = sqlite3.Row 
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM equipamentos")
    linhas = cursor.fetchall()
    
    lista_de_pecas = []
    for linha in linhas:
        d = dict(linha)
        ton = d.get("TONELAGEM") if d.get("TONELAGEM") is not None else d.get("TONELAGEM REAL", 0)
        dias = d.get("DIAS") if d.get("DIAS") is not None else d.get("DIAS INTEGER", 0)
        meta = d.get("META") if d.get("META") is not None else d.get("META REAL", 2000000)
        
        pos_bruta = str(d.get("POSICAO", "")).strip()
        if pos_bruta.endswith(".0"): pos_bruta = pos_bruta[:-2]
        
        tipo = str(d.get("TIPO", "")).upper()
        tag = str(d.get("ID", "")).upper()
        local = d.get("LOCAL", "")
        
        slot_chassi = pos_bruta
        
        if "MOLDE" in tipo: slot_chassi = "MOLDE"
        elif "OSCILADORA" in tipo: slot_chassi = "OSCILADORA"
        elif "ZERO" in tipo: slot_chassi = "SEG-ZERO"
        elif "BENDER" in tipo: slot_chassi = "BENDER"
        elif "BOW" in tipo: slot_chassi = f"BOW-{pos_bruta}" if pos_bruta and "BOW" not in pos_bruta else pos_bruta
        elif "HORIZONTAL" in tipo: slot_chassi = f"HOR-{pos_bruta}" if pos_bruta and "HOR" not in pos_bruta else pos_bruta
        elif "STR" in tipo or "R1" in tipo or "R2" in tipo:
            if "R2" in tag or "RII" in tag: slot_chassi = "STR-2"
            else: slot_chassi = "STR-1"
        elif "CADEIRA SUPERIOR" in tipo: 
            slot_chassi = f"CAD-SUP-{pos_bruta}" if pos_bruta and "CAD" not in pos_bruta else pos_bruta
        elif "CADEIRA INFERIOR" in tipo: 
            slot_chassi = f"CAD-INF-{pos_bruta}" if pos_bruta and "CAD" not in pos_bruta else pos_bruta
        elif "SEGMENTO" in tipo and "ZERO" not in tipo: 
            slot_chassi = f"SEG-{pos_bruta}" if pos_bruta and "SEG" not in pos_bruta else pos_bruta
        
        if "SEG-0" in tag or "ZERO" in tag: slot_chassi = "SEG-ZERO"
        
        lista_de_pecas.append({
            "id": d.get("ID", ""),
            "tipo": d.get("TIPO", ""),
            "local": local,
            "status": d.get("STATUS", ""),
            "ton": ton or 0,
            "dias": dias or 0,
            "meta": meta or 2000000,
            "posicaoFixa": slot_chassi,
            "pos": pos_bruta,
            "mcc_compat": "4" if "MCC 4" in local else "2/3",
            "veio": str(local).split("Veio ")[-1] if "Veio" in str(local) else ""
        })
    conexao.close()
    return lista_de_pecas

@app.post("/api/atualizar_peca")
def atualizar_peca(peca: PecaUpdate):
    try:
        conexao = sqlite3.connect('oficina.db')
        cursor = conexao.cursor()
        
        # Verifica se a requisição enviou um "local" e "status" válidos
        if peca.local != "" and peca.status != "":
            # ✅ ATUALIZA TUDO: Tonelagem, Dias, Local (Veio) e Status
            cursor.execute("""
                UPDATE equipamentos 
                SET TONELAGEM = ?, DIAS = ?, LOCAL = ?, STATUS = ? 
                WHERE ID = ?
            """, (peca.tonelagem, peca.dias, peca.local, peca.status, peca.id))
        else:
            # Mantém o comportamento antigo se por acaso o JS não enviar o local/status
            cursor.execute("""
                UPDATE equipamentos 
                SET TONELAGEM = ?, DIAS = ? 
                WHERE ID = ?
            """, (peca.tonelagem, peca.dias, peca.id))
            
        conexao.commit()
        conexao.close()
        return {"status": "sucesso"}
    except Exception as e: 
        return {"status": "erro", "mensagem": str(e)}

@app.post("/api/apontar_producao_geral")
def apontar_producao_geral(dados: ProducaoGeral):
    try:
        conexao = sqlite3.connect('oficina.db', timeout=20)
        cursor = conexao.cursor()
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if dados.mcc2 > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) + ? WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%') AND UPPER(TIPO) NOT LIKE '%MOLDE%'", (dados.mcc2,))
        if dados.mcc3 > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) + ? WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%') AND UPPER(TIPO) NOT LIKE '%MOLDE%'", (dados.mcc3,))
        if dados.mcc4 > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) + ? WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%') AND UPPER(TIPO) NOT LIKE '%MOLDE%'", (dados.mcc4,))

        cursor.execute("INSERT INTO log_apontamento_geral (data_hora, operador, qtd_mcc2, qtd_mcc3, qtd_mcc4, desfeito) VALUES (?, ?, ?, ?, ?, 0)", (data_atual, dados.operador, dados.mcc2, dados.mcc3, dados.mcc4))
        conexao.commit()
        conexao.close()
        return {"status": "sucesso"}
    except Exception as e: return {"status": "erro", "mensagem": str(e)}

@app.get("/api/historico_apontamentos_geral")
def get_historico_apontamentos_geral():
    conexao = sqlite3.connect('oficina.db', timeout=10)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM log_apontamento_geral ORDER BY id DESC LIMIT 50")
    linhas = cursor.fetchall()
    conexao.close()
    return {"status": "sucesso", "dados": [dict(linha) for linha in linhas]}

@app.post("/api/desfazer_apontamento_geral")
def desfazer_apontamento_geral(dados: DesfazerApontamento):
    conexao = sqlite3.connect('oficina.db', timeout=10)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM log_apontamento_geral WHERE id = ?", (dados.log_id,))
    log = cursor.fetchone()
    if not log or log['desfeito'] == 1: return {"status": "erro", "mensagem": "Já desfeito."}
    
    if log['qtd_mcc2'] > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = MAX(0, IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) - ?) WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%') AND UPPER(TIPO) NOT LIKE '%MOLDE%'", (log['qtd_mcc2'],))
    if log['qtd_mcc3'] > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = MAX(0, IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) - ?) WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%') AND UPPER(TIPO) NOT LIKE '%MOLDE%'", (log['qtd_mcc3'],))
    if log['qtd_mcc4'] > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = MAX(0, IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) - ?) WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%') AND UPPER(TIPO) NOT LIKE '%MOLDE%'", (log['qtd_mcc4'],))
    
    cursor.execute("UPDATE log_apontamento_geral SET desfeito = 1, operador = ? WHERE id = ?", (f"{log['operador']} (DESFEITO)", dados.log_id))
    conexao.commit()
    conexao.close()
    return {"status": "sucesso"}

@app.post("/api/apontar_moldes")
def apontar_moldes(dados: ApontamentoMoldes):
    try:
        conexao = sqlite3.connect('oficina.db', timeout=20)
        cursor = conexao.cursor()
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if dados.qtd_mcc2 > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) + ? WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%') AND UPPER(TIPO) LIKE '%MOLDE%'", (dados.qtd_mcc2,))
        if dados.qtd_mcc3 > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) + ? WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%') AND UPPER(TIPO) LIKE '%MOLDE%'", (dados.qtd_mcc3,))
        if dados.qtd_mcc4 > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) + ? WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%') AND UPPER(TIPO) LIKE '%MOLDE%'", (dados.qtd_mcc4,))
        cursor.execute("INSERT INTO log_apontamento_moldes (data_hora, operador, qtd_mcc2, qtd_mcc3, qtd_mcc4, desfeito) VALUES (?, ?, ?, ?, ?, 0)", (data_atual, dados.operador, dados.qtd_mcc2, dados.qtd_mcc3, dados.qtd_mcc4))
        conexao.commit()
        conexao.close()
        return {"status": "sucesso"}
    except Exception as e: return {"status": "erro", "mensagem": str(e)}

@app.get("/api/historico_apontamentos_moldes")
def get_historico_apontamentos_moldes():
    conexao = sqlite3.connect('oficina.db', timeout=10)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM log_apontamento_moldes ORDER BY id DESC LIMIT 50")
    linhas = cursor.fetchall()
    conexao.close()
    return {"status": "sucesso", "dados": [dict(linha) for linha in linhas]}

@app.post("/api/desfazer_apontamento_moldes")
def desfazer_apontamento_moldes(dados: DesfazerApontamento):
    conexao = sqlite3.connect('oficina.db', timeout=10)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM log_apontamento_moldes WHERE id = ?", (dados.log_id,))
    log = cursor.fetchone()
    if not log or log['desfeito'] == 1: return {"status": "erro", "mensagem": "Já desfeito."}
    if log['qtd_mcc2'] > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = MAX(0, IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) - ?) WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio C%' OR LOCAL LIKE '%Veio D%') AND UPPER(TIPO) LIKE '%MOLDE%'", (log['qtd_mcc2'],))
    if log['qtd_mcc3'] > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = MAX(0, IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) - ?) WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio E%' OR LOCAL LIKE '%Veio F%') AND UPPER(TIPO) LIKE '%MOLDE%'", (log['qtd_mcc3'],))
    if log['qtd_mcc4'] > 0: cursor.execute("UPDATE equipamentos SET TONELAGEM = MAX(0, IFNULL(TONELAGEM, IFNULL(\"TONELAGEM REAL\", 0)) - ?) WHERE STATUS = 'Instalado' AND (LOCAL LIKE '%Veio H%' OR LOCAL LIKE '%Veio G%') AND UPPER(TIPO) LIKE '%MOLDE%'", (log['qtd_mcc4'],))
    cursor.execute("UPDATE log_apontamento_moldes SET desfeito = 1, operador = ? WHERE id = ?", (f"{log['operador']} (DESFEITO)", dados.log_id))
    conexao.commit()
    conexao.close()
    return {"status": "sucesso"}

# 🔥 A MÁGICA FINAL: PYTHON HOSPEDANDO A TELA INTEIRA 🔥
@app.get("/")
def serve_html():
    if os.path.exists("app.html"):
        return FileResponse("app.html", media_type="text/html")
    elif os.path.exists("index.html"):
        return FileResponse("index.html", media_type="text/html")
    return {"status": "Erro: Arquivo HTML principal não encontrado."}

# 🔥 A VACINA DO WINDOWS (Ignora registros nativos e força a entrega perfeita)
@app.get("/{filename:path}")
def serve_files(filename: str):
    if os.path.exists(filename):
        # Obriga o navegador a ler os módulos com a extensão absoluta correta
        tipo = "text/plain"
        if filename.endswith(".js"): tipo = "application/javascript"
        elif filename.endswith(".css"): tipo = "text/css"
        elif filename.endswith(".html"): tipo = "text/html"
        elif filename.endswith(".png"): tipo = "image/png"
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"): tipo = "image/jpeg"
        elif filename.endswith(".svg"): tipo = "image/svg+xml"
        elif filename.endswith(".json"): tipo = "application/json"
        
        return FileResponse(filename, media_type=tipo)
    return {"erro": "Arquivo não encontrado"}