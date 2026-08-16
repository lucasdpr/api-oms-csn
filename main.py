import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2 import pool as psycopg2_pool
from psycopg2.extras import RealDictCursor
from pywebpush import webpush, WebPushException
import json as json_lib

load_dotenv()

app = FastAPI(title="API - Oficina de Moldes CSN")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Variável de ambiente DATABASE_URL não configurada. "
        "Defina ela com a connection string do Neon (veja .env.example)."
    )

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_EMAIL = os.environ.get("VAPID_EMAIL", "mailto:contato@exemplo.com")

PUSH_HABILITADO = bool(VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY)
if not PUSH_HABILITADO:
    print("⚠️ VAPID_PRIVATE_KEY/VAPID_PUBLIC_KEY não configuradas — push notification desativado.")

db_pool = psycopg2_pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
    cursor_factory=RealDictCursor,
    connect_timeout=20,
)


@contextmanager
def get_db():
    conn = db_pool.getconn()

    def _descartar_e_pegar_outra():
        try:
            db_pool.putconn(conn, close=True)
        except Exception:
            pass
        return db_pool.getconn()

    if conn.closed:
        conn = _descartar_e_pegar_outra()
    else:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        except Exception:
            conn = _descartar_e_pegar_outra()

    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        db_pool.putconn(conn)


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipamentos (
                id TEXT PRIMARY KEY,
                tipo TEXT,
                local TEXT,
                status TEXT,
                tonelagem REAL,
                dias INTEGER,
                meta REAL,
                posicao TEXT
            )
        ''')

        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS tag_patrimonio TEXT''')
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS data_entrada TEXT''')
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS data_reparo TEXT''')
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS substituido_por TEXT''')
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS observacao TEXT''')

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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_eventos (
                id SERIAL PRIMARY KEY,
                data_hora TEXT,
                operador TEXT,
                peca_id TEXT,
                acao TEXT
            )
        ''')

        # 📸 Categoria do registro (Melhoria, Intervenção, Comentário,
        # Atividade Pendente). Guardada direto em log_eventos.
        cursor.execute('''ALTER TABLE log_eventos ADD COLUMN IF NOT EXISTS categoria TEXT''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS colaboradores (
                matricula TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                cargo TEXT DEFAULT 'Colaborador',
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')

        cursor.execute('''ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS senha_hash TEXT''')
        cursor.execute('''ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS primeiro_acesso BOOLEAN DEFAULT TRUE''')
        cursor.execute('''ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS area TEXT DEFAULT 'Ambos' ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materiais (
                codigo TEXT PRIMARY KEY,
                descricao TEXT NOT NULL,
                qtd REAL NOT NULL DEFAULT 0
            )
        ''')
        cursor.execute('''ALTER TABLE materiais ADD COLUMN IF NOT EXISTS local TEXT''')
        cursor.execute('''ALTER TABLE materiais ADD COLUMN IF NOT EXISTS valor_unit REAL''')
        cursor.execute('''ALTER TABLE materiais ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folhoes_rascunho (
                equipamento_id TEXT PRIMARY KEY,
                tipo_folhao TEXT,
                dados TEXT,
                etapa TEXT,
                atualizado_em TEXT,
                criado_em TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rolos (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                conjunto TEXT,
                mcc_compat TEXT,
                qtd REAL NOT NULL DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hidraulica (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                conjunto TEXT,
                mcc_compat TEXT,
                qtd_aplicado REAL NOT NULL DEFAULT 0,
                qtd_reserva REAL NOT NULL DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id SERIAL PRIMARY KEY,
                matricula TEXT NOT NULL,
                endpoint TEXT NOT NULL UNIQUE,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                criado_em TEXT
            )
        ''')

        # 📸 Fotos anexadas a registros/intervenções em equipamentos.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fotos_registro (
                id SERIAL PRIMARY KEY,
                evento_id INTEGER REFERENCES log_eventos(id) ON DELETE CASCADE,
                peca_id TEXT NOT NULL,
                foto_base64 TEXT NOT NULL,
                criado_em TEXT
            )
        ''')

        # 🧰 Atividades das áreas da oficina — cada linha é 1 tarefa,
        # vinculada a um equipamento OU avulsa (equipamento_id = NULL).
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oficina_atividades (
                id SERIAL PRIMARY KEY,
                area TEXT NOT NULL,
                equipamento_id TEXT,
                descricao TEXT NOT NULL,
                responsavel TEXT,
                prioridade TEXT DEFAULT 'Normal',
                status TEXT DEFAULT 'Pendente',
                criado_por TEXT,
                criado_em TEXT,
                concluido_em TEXT,
                foto_base64 TEXT,
                prazo TEXT
            )
        ''')
        # 🔧 Quem já tinha essa tabela criada antes (v1, sem foto/prazo)
        # ganha as colunas novas aqui — CREATE TABLE IF NOT EXISTS sozinho
        # não adiciona coluna em tabela que já existe.
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS foto_base64 TEXT
        ''')
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS prazo TEXT
        ''')

        # 📝 Anotações livres por área (materiais/procedimento — provisório).
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oficina_notas_area (
                area TEXT PRIMARY KEY,
                texto TEXT,
                atualizado_por TEXT,
                atualizado_em TEXT
            )
        ''')

        # 👥 Equipe da oficina (mecânicos, eletricistas etc. — quem NÃO é
        # liderança), importada da planilha do efetivo. Cada pessoa fica
        # vinculada a UMA área (a mesma chave usada em oficina_atividades
        # e no AREAS_OFICINA do dados.js). Tabela separada de
        # "colaboradores" de propósito — essa é só um roster de exibição,
        # sem login/senha, não mistura com quem acessa o sistema.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipe_oficina (
                matricula TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                cargo TEXT,
                area TEXT NOT NULL,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')

        cursor.executemany('''
            INSERT INTO rolos (id, nome, conjunto, mcc_compat, qtd)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', [
            ("R-S5", "Rolo de Cadeira 450", "Cadeira", "2/3", 14),
            ("R-S5P", "Rolo de Cadeira 450 Puxador", "Cadeira", "2/3", 8),
            ("R-S4", "Rolo de Cadeira 400", "Cadeira", "2/3", 12),
            ("R-S4P", "Rolo de Cadeira 400 Puxador", "Cadeira", "2/3", 6),
            ("R-H300A", "Rolo Horizontal de 300 Acionado", "Segmento", "4", 6),
            ("R-200", "Rolo 200", "Segmento Zero", "2/3/4", 8),
            ("R-FR23", "FOOT ROLL MCC#2,3", "Molde", "2/3", 4),
            ("R-FR4", "FOOT ROLL MCC#4", "Molde", "4", 0),
            ("R-ER4", "EDGE ROLL MCC#4", "Molde", "4", 0),
            ("R-BND4", "ROLO DO BENDER", "Bender", "4", 0),
            ("R-HOR4", "ROLO HORIZONTAL MCC#4", "Horizontal", "4", 0),
            ("R-HOR4P", "ROLO HORIZONTAL PUXADOR MCC#4", "Horizontal", "4", 0),
            ("R-BOWA", "ROLO BOW ACIONADO", "Bow", "4", 0),
            ("R-BOW728", "ROLO BOW 728", "Bow", "4", 0),
            ("R-BOW955", "ROLO BOW 955", "Bow", "4", 0),
            ("R-SZ200", "ROLO SEGMENTO ZERO 200", "Segmento Zero", "2/3", 0),
            ("R-SZ140", "ROLO SEGMENTO ZERO 140", "Segmento Zero", "2/3", 0),
            ("R-GRP1", "ROLO SEGMENTO DE GRUPO 1", "Grupo 1", "2/3", 0),
            ("R-GRP1P", "ROLO SEGMENTO DE GRUPO 1 PUXADOR", "Grupo 1", "2/3", 0),
            ("R-GRP2", "ROLO SEGMENTO DE GRUPO 2", "Grupo 2", "2/3", 0),
            ("R-GRP2P", "ROLO SEGMENTO DE GRUPO 2 PUXADOR", "Grupo 2", "2/3", 0),
            ("R-GRP3", "ROLO SEGMENTO DE GRUPO 3", "Grupo 3", "2/3", 0),
            ("R-GRP3P", "ROLO SEGMENTO DE GRUPO 3 PUXADOR", "Grupo 3", "2/3", 0),
        ])

        cursor.executemany('''
            INSERT INTO hidraulica (id, nome, conjunto, mcc_compat, qtd_aplicado, qtd_reserva)
            VALUES (%s, %s, %s, %s, 0, 0)
            ON CONFLICT (id) DO NOTHING
        ''', [
            ("H-PGH12", "Porca Hidráulica Grupo 1,2", "Grupo 1,2", "2/3"),
            ("H-PGH3", "Porca Hidráulica Grupo 3", "Grupo 3", "2/3"),
            ("H-CIL-G1", "Cilindro de Grupo 1", "Grupo 1", "2/3"),
            ("H-CIL-G2", "Cilindro de Grupo 2", "Grupo 2", "2/3"),
            ("H-CIL-G3", "Cilindro de Grupo 3", "Grupo 3", "2/3"),
            ("H-DESEMP", "Desempenadeira Cadeira", "Cadeira", "2/3"),
            ("H-CIL-ELEV4", "Cilindro de Elevação de Estrutura", "Estrutura", "4"),
            ("H-CIL-PUX4", "Cilindro Puxador", "Puxador", "4"),
            ("H-PH-BOW", "Porca Hidráulica Bow", "Bow", "4"),
            ("H-PH-HOR", "Porca Hidráulica Horizontal", "Horizontal", "4"),
        ])

        conn.commit()


init_db()


def enviar_push_para_area(titulo: str, corpo: str, area: str = "Ambos", url: str = "/"):
    if not PUSH_HABILITADO:
        return

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if area == "Ambos":
                cursor.execute("SELECT endpoint, p256dh, auth FROM push_subscriptions")
            else:
                cursor.execute("""
                    SELECT ps.endpoint, ps.p256dh, ps.auth
                    FROM push_subscriptions ps
                    JOIN colaboradores c ON c.matricula = ps.matricula
                    WHERE c.area = %s OR c.area = 'Ambos'
                """, (area,))
            inscricoes = cursor.fetchall()

        payload = json_lib.dumps({"titulo": titulo, "corpo": corpo, "url": url})

        endpoints_mortos = []
        for inscricao in inscricoes:
            try:
                webpush(
                    subscription_info={
                        "endpoint": inscricao["endpoint"],
                        "keys": {
                            "p256dh": inscricao["p256dh"],
                            "auth": inscricao["auth"]
                        }
                    },
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": VAPID_EMAIL}
                )
            except WebPushException as e:
                if e.response is not None and e.response.status_code in (404, 410):
                    endpoints_mortos.append(inscricao["endpoint"])
                else:
                    print(f"⚠️ Erro ao enviar push: {e}")

        if endpoints_mortos:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM push_subscriptions WHERE endpoint = ANY(%s)",
                    (endpoints_mortos,)
                )
                conn.commit()
    except Exception as e:
        print(f"⚠️ Falha geral ao processar envio de push: {e}")


class PecaUpdate(BaseModel):
    id: str
    tipo: Optional[str] = None
    tonelagem: Optional[float] = None
    dias: Optional[int] = None
    local: Optional[str] = None
    status: Optional[str] = None
    meta: Optional[float] = None
    posicao: Optional[str] = None
    tag_patrimonio: Optional[str] = None
    data_entrada: Optional[str] = None
    data_reparo: Optional[str] = None
    substituido_por: Optional[str] = None
    observacao: Optional[str] = None

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

class EventoLog(BaseModel):
    peca_id: str
    acao: str
    operador: str

class LoginColaborador(BaseModel):
    matricula: str
    senha: str

class DefinirSenhaColaborador(BaseModel):
    matricula: str
    senha_atual: str
    nova_senha: str

class MaterialCadastro(BaseModel):
    codigo: str
    descricao: str
    qtd: float = 0
    local: Optional[str] = None
    valor_unit: Optional[float] = None

class MaterialAjuste(BaseModel):
    codigo: str
    fator: float

class MaterialRemover(BaseModel):
    codigo: str

class PecaExcluir(BaseModel):
    id: str

class FolhaoRascunhoSalvar(BaseModel):
    equipamento_id: str
    tipo_folhao: str
    dados: str
    etapa: Optional[str] = None

class FolhaoRascunhoFinalizar(BaseModel):
    equipamento_id: str

class RoloAjuste(BaseModel):
    id: str
    fator: float

class HidraulicaAjuste(BaseModel):
    id: str
    local: str
    fator: float

class PushSubscribe(BaseModel):
    matricula: str
    endpoint: str
    p256dh: str
    auth: str

class PushUnsubscribe(BaseModel):
    endpoint: str

class RegistroComFoto(BaseModel):
    peca_id: str
    acao: str
    operador: str
    categoria: str
    foto_base64: Optional[str] = None


# ==========================================
# OFICINA — ATIVIDADES POR ÁREA (v1)
# ==========================================
# Nome de exibição de cada área — usado só pra deixar o texto da
# notificação push legível (ex: "hidraulica" -> "Hidráulica"). Precisa
# bater com as chaves de AREAS_OFICINA no dados.js do front-end.
AREA_OFICINA_NOMES = {
    "hidraulica": "Hidráulica",
    "usinagem": "Usinagem",
    "caldeiraria": "Caldeiraria",
    "jato": "Jato",
    "eletrica": "Elétrica",
    "adm": "ADM",
    "logistica": "Logística",
    "ponte-rolante": "Ponte Rolante",
    "almoxarifado": "Almoxarifado",
    "cadeira": "Cadeira (Desempenadeira)",
    "zero": "Segmento Zero",
    "segmento-grupo": "Segmento de Grupo (2 e 3)",
    "mcc4": "MCC4",
    "bender": "Bender",
    "molde-mcc4": "Molde MCC #4",
    "molde-mcc23": "Molde MCC #2,3",
}


class OficinaAtividade(BaseModel):
    area: str
    equipamento_id: Optional[str] = None
    descricao: str
    responsavel: Optional[str] = None
    prioridade: Optional[str] = "Normal"
    operador: str
    foto_base64: Optional[str] = None  # data URL (ex: "data:image/jpeg;base64,...")
    prazo: Optional[str] = None        # data no formato "YYYY-MM-DD", opcional


class OficinaStatus(BaseModel):
    id: int
    status: str  # "Pendente" | "Em Andamento" | "Concluído"


class OficinaExcluir(BaseModel):
    id: int


class OficinaNota(BaseModel):
    area: str
    texto: str
    operador: Optional[str] = None


@app.get("/api/pecas")
def get_pecas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipamentos")
        return cursor.fetchall()


@app.post("/api/atualizar_peca")
def atualizar_peca(peca: PecaUpdate):
    campos = []
    valores = []

    if peca.tipo is not None:
        campos.append("tipo = %s"); valores.append(peca.tipo)
    if peca.tonelagem is not None:
        campos.append("tonelagem = %s"); valores.append(peca.tonelagem)
    if peca.dias is not None:
        campos.append("dias = %s"); valores.append(peca.dias)
    if peca.local is not None:
        campos.append("local = %s"); valores.append(peca.local)
    if peca.status is not None:
        campos.append("status = %s"); valores.append(peca.status)
    if peca.meta is not None:
        campos.append("meta = %s"); valores.append(peca.meta)
    if peca.posicao is not None:
        campos.append("posicao = %s"); valores.append(peca.posicao)
    if peca.tag_patrimonio is not None:
        campos.append("tag_patrimonio = %s"); valores.append(peca.tag_patrimonio)
    if peca.data_entrada is not None:
        campos.append("data_entrada = %s"); valores.append(peca.data_entrada)
    if peca.data_reparo is not None:
        campos.append("data_reparo = %s"); valores.append(peca.data_reparo)
    if peca.substituido_por is not None:
        campos.append("substituido_por = %s"); valores.append(peca.substituido_por)
    if peca.observacao is not None:
        campos.append("observacao = %s"); valores.append(peca.observacao)

    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar foi enviado.")

    valores.append(peca.id)
    query = f"UPDATE equipamentos SET {', '.join(campos)} WHERE id = %s"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(valores))
        criada = False

        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO equipamentos (id, tipo, local, status, tonelagem, dias, meta, posicao, tag_patrimonio, data_entrada, data_reparo, substituido_por, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    tipo = EXCLUDED.tipo,
                    local = EXCLUDED.local,
                    status = EXCLUDED.status,
                    tonelagem = EXCLUDED.tonelagem,
                    dias = EXCLUDED.dias,
                    meta = EXCLUDED.meta,
                    posicao = EXCLUDED.posicao,
                    tag_patrimonio = EXCLUDED.tag_patrimonio,
                    data_entrada = EXCLUDED.data_entrada,
                    data_reparo = EXCLUDED.data_reparo,
                    substituido_por = EXCLUDED.substituido_por,
                    observacao = EXCLUDED.observacao
            ''', (
                peca.id, peca.tipo or "", peca.local or "", peca.status or "",
                peca.tonelagem or 0, peca.dias or 0, peca.meta or 0, peca.posicao or "",
                peca.tag_patrimonio, peca.data_entrada, peca.data_reparo,
                peca.substituido_por, peca.observacao
            ))
            criada = True

        conn.commit()

    return {"sucesso": True, "criada": criada}


@app.post("/api/excluir_peca")
def excluir_peca(peca: PecaExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM equipamentos WHERE id = %s", (peca.id,))
        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail=f"Peça '{peca.id}' não encontrada.")
        cursor.execute("DELETE FROM folhoes_rascunho WHERE equipamento_id = %s", (peca.id,))
        conn.commit()

    return {"sucesso": True}


@app.post("/api/apontar_producao_geral")
def apontar_producao_geral(dados: ProducaoGeral):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        for qtd in (dados.qtd_mcc2, dados.qtd_mcc3, dados.qtd_mcc4):
            if qtd and qtd > 0:
                cursor.execute("""
                    UPDATE equipamentos
                    SET tonelagem = COALESCE(tonelagem, 0) + %s
                    WHERE status = 'Instalado'
                    AND (local LIKE '%%Veio C%%' OR local LIKE '%%Veio D%%'
                         OR local LIKE '%%Veio E%%' OR local LIKE '%%Veio F%%'
                         OR local LIKE '%%Veio G%%' OR local LIKE '%%Veio H%%')
                    AND UPPER(tipo) NOT LIKE '%%MOLDE%%'
                """, (qtd,))

        cursor.execute(
            "INSERT INTO log_apontamento_geral (data_hora, operador, qtd_mcc2, qtd_mcc3, qtd_mcc4, desfeito) "
            "VALUES (%s, %s, %s, %s, %s, 0)",
            (agora, dados.operador, dados.qtd_mcc2, dados.qtd_mcc3, dados.qtd_mcc4)
        )
        conn.commit()

    enviar_push_para_area(
        titulo="📦 Produção atualizada",
        corpo=f"{dados.operador} lançou produção geral (MCC2: {dados.qtd_mcc2}t, MCC3: {dados.qtd_mcc3}t, MCC4: {dados.qtd_mcc4}t).",
        area="Ambos"
    )

    return {"sucesso": True}


@app.post("/api/apontar_moldes")
def apontar_moldes(dados: ApontamentoMoldes):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        for qtd in (dados.qtd_mcc2, dados.qtd_mcc3, dados.qtd_mcc4):
            if qtd and qtd > 0:
                cursor.execute("""
                    UPDATE equipamentos
                    SET tonelagem = COALESCE(tonelagem, 0) + %s
                    WHERE status = 'Instalado'
                    AND (local LIKE '%%Veio C%%' OR local LIKE '%%Veio D%%'
                         OR local LIKE '%%Veio E%%' OR local LIKE '%%Veio F%%'
                         OR local LIKE '%%Veio G%%' OR local LIKE '%%Veio H%%')
                    AND UPPER(tipo) LIKE '%%MOLDE%%'
                """, (qtd,))

        cursor.execute(
            "INSERT INTO log_apontamento_moldes (data_hora, operador, qtd_mcc2, qtd_mcc3, qtd_mcc4, desfeito) "
            "VALUES (%s, %s, %s, %s, %s, 0)",
            (agora, dados.operador, dados.qtd_mcc2, dados.qtd_mcc3, dados.qtd_mcc4)
        )
        conn.commit()

    enviar_push_para_area(
        titulo="📦 Produção de moldes atualizada",
        corpo=f"{dados.operador} lançou produção de moldes (MCC2: {dados.qtd_mcc2}, MCC3: {dados.qtd_mcc3}, MCC4: {dados.qtd_mcc4}).",
        area="Ambos"
    )

    return {"sucesso": True}


@app.get("/api/historico_apontamentos_geral")
def get_historico_geral():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_apontamento_geral ORDER BY id DESC LIMIT 50")
        return cursor.fetchall()


@app.get("/api/historico_apontamentos_moldes")
def get_historico_moldes():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_apontamento_moldes ORDER BY id DESC LIMIT 50")
        return cursor.fetchall()


@app.post("/api/desfazer_apontamento_geral")
def desfazer_apontamento_geral(dados: DesfazerApontamento):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_apontamento_geral WHERE id = %s", (dados.log_id,))
        log = cursor.fetchone()
        if not log:
            raise HTTPException(status_code=404, detail="Log não encontrado")
        if log["desfeito"] == 1:
            raise HTTPException(status_code=400, detail="Já foi desfeito.")

        for qtd in (log["qtd_mcc2"], log["qtd_mcc3"], log["qtd_mcc4"]):
            if qtd and qtd > 0:
                cursor.execute("""
                    UPDATE equipamentos
                    SET tonelagem = GREATEST(0, COALESCE(tonelagem, 0) - %s)
                    WHERE status = 'Instalado'
                    AND (local LIKE '%%Veio C%%' OR local LIKE '%%Veio D%%'
                         OR local LIKE '%%Veio E%%' OR local LIKE '%%Veio F%%'
                         OR local LIKE '%%Veio G%%' OR local LIKE '%%Veio H%%')
                    AND UPPER(tipo) NOT LIKE '%%MOLDE%%'
                """, (qtd,))

        cursor.execute(
            "UPDATE log_apontamento_geral SET desfeito = 1, operador = %s WHERE id = %s",
            (dados.operador, dados.log_id)
        )
        conn.commit()

    return {"sucesso": True}


@app.post("/api/desfazer_apontamento_moldes")
def desfazer_apontamento_moldes(dados: DesfazerApontamento):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_apontamento_moldes WHERE id = %s", (dados.log_id,))
        log = cursor.fetchone()
        if not log:
            raise HTTPException(status_code=404, detail="Log não encontrado")
        if log["desfeito"] == 1:
            raise HTTPException(status_code=400, detail="Já foi desfeito.")

        for qtd in (log["qtd_mcc2"], log["qtd_mcc3"], log["qtd_mcc4"]):
            if qtd and qtd > 0:
                cursor.execute("""
                    UPDATE equipamentos
                    SET tonelagem = GREATEST(0, COALESCE(tonelagem, 0) - %s)
                    WHERE status = 'Instalado'
                    AND (local LIKE '%%Veio C%%' OR local LIKE '%%Veio D%%'
                         OR local LIKE '%%Veio E%%' OR local LIKE '%%Veio F%%'
                         OR local LIKE '%%Veio G%%' OR local LIKE '%%Veio H%%')
                    AND UPPER(tipo) LIKE '%%MOLDE%%'
                """, (qtd,))

        cursor.execute(
            "UPDATE log_apontamento_moldes SET desfeito = 1, operador = %s WHERE id = %s",
            (dados.operador, dados.log_id)
        )
        conn.commit()

    return {"sucesso": True}


@app.get("/")
def root():
    return {"message": "API - Oficina de Moldes CSN Online!"}


@app.get("/api/ping_db")
def ping_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return {"status": "ok", "banco": "acordado"}


@app.post("/api/registrar_evento")
def registrar_evento(evento: EventoLog):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao) VALUES (%s, %s, %s, %s)",
            (agora, evento.operador, evento.peca_id, evento.acao)
        )
        conn.commit()

    PALAVRAS_CRITICAS = ["b.o", "blackout", "quebra", "fim de vida", "alarme"]
    is_critico = any(p in evento.acao.lower() for p in PALAVRAS_CRITICAS)

    enviar_push_para_area(
        titulo="🚨 Evento crítico" if is_critico else "📋 Registro no equipamento",
        corpo=f"{evento.operador} — {evento.peca_id}: {evento.acao}",
        area="Mecânico" if is_critico else "Ambos"
    )

    return {"sucesso": True}


@app.get("/api/historico_eventos")
def get_historico_eventos(peca_id: Optional[str] = None, limite: int = 200):
    with get_db() as conn:
        cursor = conn.cursor()
        if peca_id:
            cursor.execute(
                "SELECT * FROM log_eventos WHERE peca_id = %s ORDER BY id DESC LIMIT %s",
                (peca_id, limite)
            )
        else:
            cursor.execute("SELECT * FROM log_eventos ORDER BY id DESC LIMIT %s", (limite,))
        return cursor.fetchall()


@app.get("/api/colaboradores")
def get_colaboradores():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, primeiro_acesso FROM colaboradores WHERE ativo = TRUE ORDER BY nome"
        )
        return cursor.fetchall()


@app.post("/api/colaboradores/login")
def login_colaborador(dados: LoginColaborador):
    matricula = dados.matricula.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, senha_hash, primeiro_acesso FROM colaboradores WHERE matricula = %s AND ativo = TRUE",
            (matricula,)
        )
        colaborador = cursor.fetchone()

    if not colaborador:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

    if colaborador["primeiro_acesso"]:
        if dados.senha.strip().upper() != matricula:
            raise HTTPException(status_code=401, detail="No primeiro acesso, a senha é a sua própria matrícula.")
        return {
            "sucesso": True,
            "nome": colaborador["nome"],
            "cargo": colaborador["cargo"],
            "precisa_definir_senha": True
        }

    if not colaborador["senha_hash"] or not bcrypt.checkpw(dados.senha.encode(), colaborador["senha_hash"].encode()):
        raise HTTPException(status_code=401, detail="Senha incorreta.")

    return {
        "sucesso": True,
        "nome": colaborador["nome"],
        "cargo": colaborador["cargo"],
        "precisa_definir_senha": False
    }


@app.post("/api/colaboradores/definir_senha")
def definir_senha_colaborador(dados: DefinirSenhaColaborador):
    matricula = dados.matricula.strip().upper()

    if len(dados.nova_senha.strip()) < 4:
        raise HTTPException(status_code=400, detail="A nova senha precisa ter pelo menos 4 caracteres.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, senha_hash, primeiro_acesso FROM colaboradores WHERE matricula = %s AND ativo = TRUE",
            (matricula,)
        )
        colaborador = cursor.fetchone()

        if not colaborador:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

        if colaborador["primeiro_acesso"]:
            if dados.senha_atual.strip().upper() != matricula:
                raise HTTPException(status_code=401, detail="Senha atual inválida.")
        else:
            if not colaborador["senha_hash"] or not bcrypt.checkpw(dados.senha_atual.encode(), colaborador["senha_hash"].encode()):
                raise HTTPException(status_code=401, detail="Senha atual inválida.")

        novo_hash = bcrypt.hashpw(dados.nova_senha.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "UPDATE colaboradores SET senha_hash = %s, primeiro_acesso = FALSE WHERE matricula = %s",
            (novo_hash, matricula)
        )
        conn.commit()

    return {"sucesso": True}


@app.get("/api/materiais")
def get_materiais():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE ativo = TRUE ORDER BY descricao"
        )
        return cursor.fetchall()


@app.post("/api/materiais/cadastrar")
def cadastrar_material(dados: MaterialCadastro):
    codigo = dados.codigo.strip().upper()
    descricao = dados.descricao.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT qtd FROM materiais WHERE codigo = %s", (codigo,))
        existente = cursor.fetchone()

        if existente:
            cursor.execute(
                "UPDATE materiais SET qtd = qtd + %s, ativo = TRUE WHERE codigo = %s",
                (dados.qtd, codigo)
            )
            ja_existia = True
        else:
            cursor.execute(
                "INSERT INTO materiais (codigo, descricao, qtd, local, valor_unit, ativo) "
                "VALUES (%s, %s, %s, %s, %s, TRUE)",
                (codigo, descricao, dados.qtd, dados.local, dados.valor_unit)
            )
            ja_existia = False

        cursor.execute("SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE codigo = %s", (codigo,))
        atualizado = cursor.fetchone()
        conn.commit()

    return {"sucesso": True, "ja_existia": ja_existia, "material": atualizado}


@app.post("/api/materiais/ajustar")
def ajustar_material(dados: MaterialAjuste):
    codigo = dados.codigo.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT qtd FROM materiais WHERE codigo = %s AND ativo = TRUE", (codigo,))
        material = cursor.fetchone()

        if not material:
            raise HTTPException(status_code=404, detail=f"Material '{codigo}' não encontrado.")

        if material["qtd"] + dados.fator < 0:
            raise HTTPException(status_code=400, detail="O estoque não pode ficar negativo.")

        cursor.execute(
            "UPDATE materiais SET qtd = qtd + %s WHERE codigo = %s",
            (dados.fator, codigo)
        )
        cursor.execute("SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE codigo = %s", (codigo,))
        atualizado = cursor.fetchone()
        conn.commit()

    return {"sucesso": True, "material": atualizado}


@app.post("/api/materiais/remover")
def remover_material(dados: MaterialRemover):
    codigo = dados.codigo.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE materiais SET ativo = FALSE WHERE codigo = %s", (codigo,))
        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail=f"Material '{codigo}' não encontrado.")
        conn.commit()

    return {"sucesso": True}


@app.get("/api/rolos")
def get_rolos():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rolos ORDER BY conjunto, nome")
        return cursor.fetchall()


@app.post("/api/rolos/ajustar")
def ajustar_rolo(dados: RoloAjuste):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT qtd FROM rolos WHERE id = %s", (dados.id,))
        rolo = cursor.fetchone()

        if not rolo:
            raise HTTPException(status_code=404, detail=f"Rolo '{dados.id}' não encontrado.")

        if rolo["qtd"] + dados.fator < 0:
            raise HTTPException(status_code=400, detail="O estoque não pode ficar negativo.")

        cursor.execute("UPDATE rolos SET qtd = qtd + %s WHERE id = %s", (dados.fator, dados.id))
        cursor.execute("SELECT * FROM rolos WHERE id = %s", (dados.id,))
        atualizado = cursor.fetchone()
        conn.commit()

    return {"sucesso": True, "rolo": atualizado}


@app.get("/api/hidraulica")
def get_hidraulica():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hidraulica ORDER BY mcc_compat, conjunto, nome")
        return cursor.fetchall()


@app.post("/api/hidraulica/ajustar")
def ajustar_hidraulica(dados: HidraulicaAjuste):
    if dados.local not in ("aplicado", "reserva"):
        raise HTTPException(status_code=400, detail="local precisa ser 'aplicado' ou 'reserva'.")

    coluna = "qtd_aplicado" if dados.local == "aplicado" else "qtd_reserva"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT {coluna} AS saldo FROM hidraulica WHERE id = %s", (dados.id,))
        item = cursor.fetchone()

        if not item:
            raise HTTPException(status_code=404, detail=f"Item hidráulico '{dados.id}' não encontrado.")

        if item["saldo"] + dados.fator < 0:
            raise HTTPException(status_code=400, detail="O estoque não pode ficar negativo.")

        cursor.execute(f"UPDATE hidraulica SET {coluna} = {coluna} + %s WHERE id = %s", (dados.fator, dados.id))
        cursor.execute("SELECT * FROM hidraulica WHERE id = %s", (dados.id,))
        atualizado = cursor.fetchone()
        conn.commit()

    return {"sucesso": True, "item": atualizado}


@app.get("/api/folhao/{equipamento_id}")
def get_rascunho_folhao(equipamento_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM folhoes_rascunho WHERE equipamento_id = %s",
            (equipamento_id,)
        )
        rascunho = cursor.fetchone()

    if not rascunho:
        raise HTTPException(status_code=404, detail="Nenhum rascunho salvo para este equipamento.")

    return rascunho


@app.post("/api/folhao/salvar")
def salvar_rascunho_folhao(dados: FolhaoRascunhoSalvar):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO folhoes_rascunho (equipamento_id, tipo_folhao, dados, etapa, atualizado_em, criado_em)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (equipamento_id) DO UPDATE SET
                tipo_folhao = EXCLUDED.tipo_folhao,
                dados = EXCLUDED.dados,
                etapa = EXCLUDED.etapa,
                atualizado_em = EXCLUDED.atualizado_em
            """,
            (dados.equipamento_id, dados.tipo_folhao, dados.dados, dados.etapa, agora, agora)
        )
        conn.commit()

    return {"sucesso": True}


@app.post("/api/folhao/finalizar")
def finalizar_rascunho_folhao(dados: FolhaoRascunhoFinalizar):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM folhoes_rascunho WHERE equipamento_id = %s",
            (dados.equipamento_id,)
        )
        conn.commit()

    return {"sucesso": True}


@app.get("/api/push/vapid_public_key")
def get_vapid_public_key():
    if not PUSH_HABILITADO:
        raise HTTPException(status_code=503, detail="Push notification não configurado no servidor.")
    return {"publicKey": VAPID_PUBLIC_KEY}


@app.post("/api/push/subscribe")
def subscribe_push(dados: PushSubscribe):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO push_subscriptions (matricula, endpoint, p256dh, auth, criado_em)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (endpoint) DO UPDATE SET
                matricula = EXCLUDED.matricula,
                p256dh = EXCLUDED.p256dh,
                auth = EXCLUDED.auth
            """,
            (dados.matricula.strip().upper(), dados.endpoint, dados.p256dh, dados.auth, agora)
        )
        conn.commit()
    return {"sucesso": True}


@app.post("/api/push/unsubscribe")
def unsubscribe_push(dados: PushUnsubscribe):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (dados.endpoint,))
        conn.commit()
    return {"sucesso": True}


# ==========================================
# 📸 REGISTRO COM FOTO E CATEGORIA
# ==========================================
@app.post("/api/registro_com_foto")
def registrar_com_foto(dados: RegistroComFoto):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, categoria) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (agora, dados.operador, dados.peca_id, dados.acao, dados.categoria)
        )
        evento_id = cursor.fetchone()["id"]

        if dados.foto_base64:
            cursor.execute(
                "INSERT INTO fotos_registro (evento_id, peca_id, foto_base64, criado_em) "
                "VALUES (%s, %s, %s, %s)",
                (evento_id, dados.peca_id, dados.foto_base64, agora)
            )

        conn.commit()

    PALAVRAS_CRITICAS = ["b.o", "blackout", "quebra", "fim de vida", "alarme"]
    is_critico = any(p in dados.acao.lower() for p in PALAVRAS_CRITICAS)

    enviar_push_para_area(
        titulo="🚨 Evento crítico" if is_critico else f"📋 {dados.categoria}",
        corpo=f"{dados.operador} — {dados.peca_id}: {dados.acao}",
        area="Mecânico" if is_critico else "Ambos"
    )

    return {"sucesso": True, "evento_id": evento_id}


@app.get("/api/fotos/{peca_id}")
def get_fotos_da_peca(peca_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, f.foto_base64, f.criado_em, e.data_hora, e.operador, e.acao, e.categoria
            FROM fotos_registro f
            JOIN log_eventos e ON e.id = f.evento_id
            WHERE f.peca_id = %s
            ORDER BY f.id DESC
        """, (peca_id,))
        return cursor.fetchall()


@app.get("/api/registros_ocorrencia")
def get_registros_ocorrencia(categoria: Optional[str] = None, limite: int = 100):
    with get_db() as conn:
        cursor = conn.cursor()
        if categoria:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria,
                       f.foto_base64
                FROM log_eventos e
                LEFT JOIN fotos_registro f ON f.evento_id = e.id
                WHERE e.categoria = %s
                ORDER BY e.id DESC
                LIMIT %s
            """, (categoria, limite))
        else:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria,
                       f.foto_base64
                FROM log_eventos e
                LEFT JOIN fotos_registro f ON f.evento_id = e.id
                WHERE e.categoria IS NOT NULL
                ORDER BY e.id DESC
                LIMIT %s
            """, (limite,))
        return cursor.fetchall()


# ==========================================
# OFICINA — ATIVIDADES POR ÁREA (v1)
# ==========================================
@app.get("/api/oficina/atividades")
def listar_atividades_oficina(area: Optional[str] = None, status: Optional[str] = None):
    """
    Lista as atividades da oficina. Sem filtro, traz TUDO — a grade de
    áreas no front-end filtra por área no próprio navegador (evita uma
    chamada de API por card). Os filtros opcionais ficam disponíveis
    caso precise no futuro (ex: um relatório só de pendências).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM oficina_atividades WHERE 1=1"
        params = []
        if area:
            query += " AND area = %s"
            params.append(area)
        if status:
            query += " AND status = %s"
            params.append(status)
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()


@app.post("/api/oficina/atividade")
def criar_atividade_oficina(dados: OficinaAtividade):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO oficina_atividades
                (area, equipamento_id, descricao, responsavel, prioridade, status, criado_por, criado_em, foto_base64, prazo)
            VALUES (%s, %s, %s, %s, %s, 'Pendente', %s, %s, %s, %s)
            RETURNING id
            """,
            (dados.area, dados.equipamento_id, dados.descricao, dados.responsavel,
             dados.prioridade or "Normal", dados.operador, agora, dados.foto_base64, dados.prazo)
        )
        atividade_id = cursor.fetchone()["id"]
        conn.commit()

    # 📲 Avisa quem estiver com push ativado que uma atividade nova
    # entrou na oficina. Como push_subscriptions hoje só existe pra quem
    # FAZ LOGIN no sistema (não pra equipe_oficina, que é só roster de
    # exibição), o alvo é "Ambos" — todo mundo logado com notificação
    # ligada. Se no futuro os líderes de área tiverem login vinculado à
    # área, dá pra refinar esse filtro.
    nome_area = AREA_OFICINA_NOMES.get(dados.area, dados.area)
    is_alta_prioridade = (dados.prioridade or "Normal") == "Alta"
    enviar_push_para_area(
        titulo="🔴 Atividade prioritária na Oficina" if is_alta_prioridade else f"🧰 Nova atividade — {nome_area}",
        corpo=f"{dados.operador} — {nome_area}: {dados.descricao}",
        area="Ambos"
    )

    return {"sucesso": True, "id": atividade_id}



@app.post("/api/oficina/atividade/status")
def mudar_status_atividade_oficina(dados: OficinaStatus):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    concluido_em = agora if dados.status == "Concluído" else None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE oficina_atividades SET status = %s, concluido_em = %s WHERE id = %s",
            (dados.status, concluido_em, dados.id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()
    return {"sucesso": True}


@app.post("/api/oficina/atividade/excluir")
def excluir_atividade_oficina(dados: OficinaExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM oficina_atividades WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()
    return {"sucesso": True}


@app.get("/api/oficina/nota/{area}")
def get_nota_area_oficina(area: str):
    """404 = área ainda sem anotações — é normal, o front trata como
    campo vazio."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM oficina_notas_area WHERE area = %s", (area,))
        nota = cursor.fetchone()
        if not nota:
            raise HTTPException(status_code=404, detail="Sem anotações ainda para essa área.")
        return nota


@app.post("/api/oficina/nota")
def salvar_nota_area_oficina(dados: OficinaNota):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO oficina_notas_area (area, texto, atualizado_por, atualizado_em)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (area) DO UPDATE SET
                texto = EXCLUDED.texto,
                atualizado_por = EXCLUDED.atualizado_por,
                atualizado_em = EXCLUDED.atualizado_em
            """,
            (dados.area, dados.texto, dados.operador, agora)
        )
        conn.commit()
    return {"sucesso": True}


@app.get("/api/oficina/equipe/{area}")
def get_equipe_area_oficina(area: str):
    """Lista os colaboradores (mecânicos, eletricistas etc.) cadastrados
    naquela área da oficina — vem da planilha do efetivo, importada via
    importar_efetivo_oficina.py. Usado na seção 'Equipe da Área' do
    modal de cada área."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo FROM equipe_oficina WHERE area = %s AND ativo = TRUE ORDER BY nome",
            (area,)
        )
        return cursor.fetchall()