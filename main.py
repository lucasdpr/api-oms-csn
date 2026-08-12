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

# Carrega variáveis de um arquivo .env quando rodando localmente.
# No Render, as variáveis já vêm configuradas no ambiente e essa
# chamada simplesmente não faz nada (não existe .env lá).
load_dotenv()

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
# 🔥 CONFIGURAÇÃO DO BANCO DE DADOS (via variável de ambiente única)
# ==========================================
# IMPORTANTE: nunca coloque a connection string direto no código.
# Configure essa variável:
#   - No Render: aba "Environment" do serviço da API.
#   - Localmente: crie um arquivo .env (nunca commitado) com base no .env.example.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Variável de ambiente DATABASE_URL não configurada. "
        "Defina ela com a connection string do Neon (veja .env.example)."
    )

# ==========================================
# 🔧 POOL DE CONEXÕES (em vez de abrir uma conexão nova do zero a cada
# requisição)
# ==========================================
# ANTES: get_db() chamava psycopg2.connect(...) toda vez que uma rota
# era acionada. O problema aparecia logo depois do login: o app dispara
# várias chamadas quase ao mesmo tempo (equipamentos, rolos, hidráulica,
# materiais...). Se o Neon ainda estivesse "acordando" naquele instante,
# cada uma dessas chamadas tentava abrir sua PRÓPRIA conexão nova e
# esperar o banco acordar por conta própria — várias tentativas de
# handshake competindo ao mesmo tempo, o que deixava tudo mais lento e
# fazia algumas chamadas estourarem o timeout mesmo com o retry no
# front-end, mesmo o banco já tendo "acordado" fisicamente.
#
# AGORA: um pool é criado uma única vez quando a API sobe. Toda rota
# empresta uma conexão já pronta do pool (put/get) em vez de abrir uma
# nova — só a primeira conexão de verdade precisa esperar o Neon
# acordar; as demais reaproveitam conexões que já estão de pé.
db_pool = psycopg2_pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
    cursor_factory=RealDictCursor,
    connect_timeout=20,
)


@contextmanager
def get_db():
    """
    Empresta uma conexão do pool e garante que ela sempre volta pro
    pool no final, mesmo se a rota lançar uma exceção no meio do
    caminho (nunca fecha a conexão de verdade — só devolve pro pool
    pra outra requisição reaproveitar).

    Se a rota lançar uma exceção no meio de uma transação, faz um
    rollback antes de devolver a conexão — sem isso, uma transação
    "presa" nessa conexão contaminaria a PRÓXIMA requisição que
    reaproveitasse ela do pool (erro tipo "current transaction is
    aborted"), o que seria pior e mais confuso que abrir uma conexão
    nova a cada vez.

    🔧 CORREÇÃO ("entra mas o banco não carregou na primeira tentativa"):
    o Neon suspende o banco por inatividade de forma INDEPENDENTE do
    Render — mesmo com a API já acordada e respondendo normal (porque
    alguém acessou há pouco em outro celular), o Neon pode voltar a
    dormir sozinho enquanto a conexão fica parada, sem uso, dentro do
    pool. Nesse caso o psycopg2, do lado do Python, continua achando
    que a conexão está de pé — só descobre que morreu na hora de rodar
    uma query de verdade. Sem essa checagem, a PRIMEIRA rota a pegar
    essa conexão "zumbi" batia de frente com o erro e devolvia 500 pro
    app, mesmo tudo parecendo "ligado". Como o front-end só repete a
    tentativa em timeout/erro de rede (não em erro 500), isso aparecia
    como "não carregou" — e só sumia quando o usuário fechava e abria
    o app de novo (uma requisição nova, por sorte, pegava do pool uma
    conexão diferente e saudável).

    Agora, antes de entregar a conexão pra rota, faz um teste rápido
    (SELECT 1). Se falhar, descarta essa conexão específica do pool e
    pega (ou abre) outra na hora — a rota nunca chega a ver a conexão
    morta, então o app não precisa mais "tentar de novo" manualmente.
    """
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

        # Nota: identificadores sem aspas no Postgres são sempre convertidos
        # para minúsculo automaticamente. As colunas abaixo já nascem em
        # minúsculo por baixo dos panos (id, tipo, local, status,
        # tonelagem, dias, meta, posicao) — deixamos assim no código pra
        # não haver ambiguidade entre "como está escrito" e "como o banco
        # realmente guarda".
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

        # Guarda o código de patrimônio real da peça física, separado do
        # id de sistema (que representa a vaga/posição, não a peça).
        cursor.execute('''
            ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS tag_patrimonio TEXT
        ''')
        cursor.execute('''
            ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS data_entrada TEXT
        ''')
        # 🔧 CORREÇÃO: "dataReparo" (quando a peça entrou em Oficina/Reparo,
        # usado pra contar os dias) e "substituidoPor" (qual peça a
        # substituiu no veio) só existiam na memória do navegador — nunca
        # eram salvos aqui. Todo login roda sincronizarAtivosReaisMCC4()
        # no front, que reconstrói TUDO a partir do que a API devolve; sem
        # essas colunas, essa reconstrução sempre vinha sem elas, e o
        # contador de dias "esquecia" quando a peça realmente saiu do veio,
        # voltando a mostrar um valor congelado/desatualizado.
        cursor.execute('''
            ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS data_reparo TEXT
        ''')
        cursor.execute('''
            ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS substituido_por TEXT
        ''')
        # 🔧 CORREÇÃO: o campo "Observação" (usado no Sinótico 3D e em
        # outros lugares) sempre foi mandado pro back-end, mas nunca
        # existiu de verdade aqui nem no modelo PecaUpdate — o Pydantic
        # descartava ele silenciosamente, e como às vezes era o ÚNICO
        # campo enviado, a rota respondia 400 "Nenhum campo para
        # atualizar foi enviado", e a observação nunca era salva.
        cursor.execute('''
            ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS observacao TEXT
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_eventos (
                id SERIAL PRIMARY KEY,
                data_hora TEXT,
                operador TEXT,
                peca_id TEXT,
                acao TEXT
            )
        ''')

        # Colaboradores autorizados a logar no sistema (importados da planilha
        # de cadastro da CSN + acesso de desenvolvedor).
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS colaboradores (
                matricula TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                cargo TEXT DEFAULT 'Colaborador',
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')

        # Senha própria por colaborador (hash, nunca texto puro). No primeiro
        # acesso, a senha temporária é a própria matrícula; depois do login o
        # sistema obriga a troca e passa a usar senha_hash.
        cursor.execute('''
            ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS senha_hash TEXT
        ''')
        cursor.execute('''
            ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS primeiro_acesso BOOLEAN DEFAULT TRUE
        ''')

        # Almoxarifado de materiais gerais — antes vivia só no localStorage
        # do navegador (cada colaborador via um estoque diferente!). Agora
        # é compartilhado de verdade, igual equipamentos e colaboradores.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materiais (
                codigo TEXT PRIMARY KEY,
                descricao TEXT NOT NULL,
                qtd REAL NOT NULL DEFAULT 0
            )
        ''')
        cursor.execute('''
            ALTER TABLE materiais ADD COLUMN IF NOT EXISTS local TEXT
        ''')
        cursor.execute('''
            ALTER TABLE materiais ADD COLUMN IF NOT EXISTS valor_unit REAL
        ''')
        cursor.execute('''
            ALTER TABLE materiais ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE
        ''')

        # Rascunho do folhão em andamento. Guarda TODAS as respostas do
        # formulário (chegada, revisão, saída etc) enquanto o equipamento
        # está na oficina. Assim um técnico pode preencher a chegada hoje
        # e outro (ou o mesmo) completar a saída dias depois, sem perder
        # nada — o rascunho só é apagado quando o folhão é finalizado e
        # impresso. dados fica em TEXT guardando um JSON serializado com
        # o valor de cada campo do formulário.
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

        # Estoque de rolos — antes vivia só no localStorage (cada
        # colaborador via um saldo diferente). Agora fica no Neon,
        # igual equipamentos e materiais.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rolos (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                conjunto TEXT,
                mcc_compat TEXT,
                qtd REAL NOT NULL DEFAULT 0
            )
        ''')

        # Estoque hidráulico — diferente dos rolos/materiais, guarda DOIS
        # saldos separados por item: o que está aplicado na máquina
        # (qtd_aplicado) e o que está de reserva na oficina (qtd_reserva).
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

        # Semeia os itens padrão (só na primeira vez — se o item já existe,
        # o ON CONFLICT ignora e mantém o saldo real que já estiver lá).
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


init_db()  # Roda na inicialização da API

# ==========================================
# MODELOS
# ==========================================
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
    dados: str  # JSON serializado (string) com os valores do formulário
    etapa: Optional[str] = None

class FolhaoRascunhoFinalizar(BaseModel):
    equipamento_id: str

class RoloAjuste(BaseModel):
    id: str
    fator: float

class HidraulicaAjuste(BaseModel):
    id: str
    local: str  # "aplicado" (na máquina) ou "reserva" (oficina)
    fator: float

# ==========================================
# ROTAS DA API
# ==========================================
@app.get("/api/pecas")
def get_pecas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipamentos")
        return cursor.fetchall()


@app.post("/api/atualizar_peca")
def atualizar_peca(peca: PecaUpdate):
    """
    Atualiza só os campos que vieram preenchidos no payload. Se o id
    ainda não existir no banco — por exemplo, um slot de Swap que
    nunca teve peça instalada antes, ou uma peça nova cadastrada só
    no navegador — CRIA a linha em vez de devolver 404.

    🔧 CORREÇÃO: antes essa rota só sabia fazer UPDATE. Uma peça sem
    linha prévia batia com 0 linhas afetadas e o front recebia "Peça
    'X' não encontrada" — o Swap/instalação funcionava na tela
    (localStorage), mas nunca persistia no Postgres. Também faltavam
    tipo/meta/posicao no modelo (PecaUpdate), então mesmo o front já
    mandando esses campos, eram descartados antes de chegar aqui.
    """
    campos = []
    valores = []

    if peca.tipo is not None:
        campos.append("tipo = %s")
        valores.append(peca.tipo)
    if peca.tonelagem is not None:
        campos.append("tonelagem = %s")
        valores.append(peca.tonelagem)
    if peca.dias is not None:
        campos.append("dias = %s")
        valores.append(peca.dias)
    if peca.local is not None:
        campos.append("local = %s")
        valores.append(peca.local)
    if peca.status is not None:
        campos.append("status = %s")
        valores.append(peca.status)
    if peca.meta is not None:
        campos.append("meta = %s")
        valores.append(peca.meta)
    if peca.posicao is not None:
        campos.append("posicao = %s")
        valores.append(peca.posicao)
    if peca.tag_patrimonio is not None:
        campos.append("tag_patrimonio = %s")
        valores.append(peca.tag_patrimonio)
    if peca.data_entrada is not None:
        campos.append("data_entrada = %s")
        valores.append(peca.data_entrada)
    if peca.data_reparo is not None:
        campos.append("data_reparo = %s")
        valores.append(peca.data_reparo)
    if peca.substituido_por is not None:
        campos.append("substituido_por = %s")
        valores.append(peca.substituido_por)
    if peca.observacao is not None:
        campos.append("observacao = %s")
        valores.append(peca.observacao)

    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar foi enviado.")

    valores.append(peca.id)
    query = f"UPDATE equipamentos SET {', '.join(campos)} WHERE id = %s"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(valores))
        criada = False

        if cursor.rowcount == 0:
            # Não existia — cria a linha agora com os dados disponíveis.
            # ON CONFLICT cobre o caso raro de outra requisição ter
            # criado a mesma peça entre o UPDATE acima e este INSERT.
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
                peca.id,
                peca.tipo or "",
                peca.local or "",
                peca.status or "",
                peca.tonelagem or 0,
                peca.dias or 0,
                peca.meta or 0,
                peca.posicao or "",
                peca.tag_patrimonio,
                peca.data_entrada,
                peca.data_reparo,
                peca.substituido_por,
                peca.observacao
            ))
            criada = True

        conn.commit()

    return {"sucesso": True, "criada": criada}


@app.post("/api/excluir_peca")
def excluir_peca(peca: PecaExcluir):
    """
    Exclusão permanente de verdade (não é soft-delete como os materiais).
    🔧 CORREÇÃO: esse endpoint não existia. O botão "Excluir" do front
    (excluirEquipamento, em ui.js) só tirava a peça do localStorage —
    parecia funcionar (sumia da tela, dava a mensagem de sucesso), mas
    nunca mexia no Postgres. Na próxima sincronização (ex: recarregar a
    página), sincronizarAtivosReaisMCC4() busca tudo nesse banco de novo
    e a peça, que nunca tinha sido apagada de verdade, voltava a aparecer.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM equipamentos WHERE id = %s", (peca.id,))
        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail=f"Peça '{peca.id}' não encontrada.")
        # Limpa também um eventual rascunho de folhão em andamento pra essa
        # peça — senão fica órfão no banco, referenciando um id que não
        # existe mais.
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
    """
    Rota feita pra ser chamada periodicamente por um serviço externo
    (ex: cron-job.org) a cada poucos minutos. Diferente da rota "/",
    que só confirma que a API (Render) está de pé, esta aqui faz uma
    consulta de verdade no banco (Neon) — é isso que impede o Neon de
    suspender o banco por inatividade, mesmo com a API sempre ligada.
    """
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
    """
    Lista os colaboradores autorizados a logar no sistema. Usado apenas
    para fins administrativos — o login em si é validado pela rota
    /api/colaboradores/login, que não expõe a lista inteira ao navegador.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, primeiro_acesso FROM colaboradores WHERE ativo = TRUE ORDER BY nome"
        )
        return cursor.fetchall()


@app.post("/api/colaboradores/login")
def login_colaborador(dados: LoginColaborador):
    """
    Valida matrícula + senha no servidor (nunca no navegador).
    No primeiro acesso, a senha temporária é a própria matrícula;
    o front-end deve então chamar /api/colaboradores/definir_senha
    para cadastrar a senha definitiva.
    """
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
    """
    Cadastra a senha definitiva do colaborador. Só aceita se a senha
    atual informada bater (seja o primeiro acesso usando a matrícula,
    seja uma troca posterior usando a senha já cadastrada).
    """
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


# ==========================================
# ALMOXARIFADO (compartilhado entre todos os colaboradores)
# ==========================================
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
    """
    Cadastra um material novo, ou soma a quantidade se o código já existir
    (mesmo comportamento que o front-end tinha localmente antes).
    """
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
    """
    Ajusta o saldo de um material (+1/-1 nos botões, ou qualquer fator).
    Bloqueia se o resultado ficar negativo.
    """
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


# ==========================================
# ESTOQUE DE ROLOS (compartilhado entre todos os colaboradores)
# ==========================================
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


# ==========================================
# ESTOQUE HIDRÁULICO (aplicado na máquina x reserva na oficina)
# ==========================================
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

    # Coluna vem de uma whitelist fixa (nunca do texto puro do usuário),
    # então não tem risco de SQL injection aqui mesmo montando a query
    # com f-string.
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


# ==========================================
# RASCUNHO DE FOLHÃO (chegada -> saída, persistido entre sessões)
# ==========================================
@app.get("/api/folhao/{equipamento_id}")
def get_rascunho_folhao(equipamento_id: str):
    """
    Retorna o rascunho salvo do folhão daquele equipamento, se existir.
    Usado ao reabrir o folhão pra continuar de onde parou (ex: já fez a
    chegada, falta preencher a saída dias depois).
    """
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
    """
    Salva (upsert) o progresso do folhão. Chamado automaticamente
    conforme o técnico preenche o formulário, então o trabalho nunca é
    perdido mesmo se ele fechar a aba, trocar de computador ou voltar
    outro dia pra terminar a saída.
    """
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
    """
    Apaga o rascunho quando o folhão é finalizado e impresso (o
    equipamento libera a oficina). Se não existir rascunho, não é erro
    — só significa que o folhão foi preenchido e impresso de uma vez só.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM folhoes_rascunho WHERE equipamento_id = %s",
            (dados.equipamento_id,)
        )
        conn.commit()

    return {"sucesso": True}