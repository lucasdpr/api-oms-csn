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


# Lista de materiais pra popular a área "segmento-grupo" na primeira
# vez que o servidor sobe (ver seed dentro de init_db, mais abaixo).
# Gerado automaticamente a partir de dadosMateriaisSegmentoGrupo.js (Grupos 1+2+3, deduplicado por codigo)
SEED_MATERIAIS_SEGMENTO_GRUPO = [
    ('1010420', 'PINO GRAXEIRO BOTAO ACO NPTF 1/4 "'),
    ('1027643', 'BUJAO QUAD A105 NPT 3000 3/8 "'),
    ('1064438', 'CONECTOR COMP LATAO 1/4 "'),
    ('1064442', 'COTOVELO COMP LATAO 1/4 " 1/4 "'),
    ('1179315', 'PAPELAO ISOLANTE 1,6X 210X 240MM'),
    ('1179316', 'PAPELAO ISOLANTE 1,6X 270X 300MM'),
    ('1190018', 'ANEL RETEN EXT DIN471 70,00X 2,50MM'),
    ('1190023', 'ANEL RETEN EXT DIN471 50,00X 2,00MM'),
    ('1195185', 'GRAMPO U 8MM TUBO 1 "'),
    ('1195298', 'FITA FIBRA ARAMIDA 1,7X 38,1MMX 30M'),
    ('1203902', 'ARRUELA PRES STANDARD ACO MOLA M24'),
    ('1204249', 'PARAFUSO SEXT CL4.6 M12X 70MM'),
    ('1204312', 'PORCA SEXT CL5 MG M16'),
    ('1204599', 'PARAFUSO SEXT CL4.6 M24X 70MM'),
    ('1204624', 'PARAFUSO SEXT CL8.8 M12X 30MM'),
    ('1205001', 'PARAFUSO SEXT CL4.6 M24X 80MM'),
    ('1205033', 'PARAFUSO SEXT CL4.6 M30X 60MM'),
    ('1205095', 'PORCA SEXT CL5 MG M8'),
    ('1205116', 'PARAFUSO ESC CL4.6 M12X 90MM'),
    ('1205134', 'PARAFUSO CIL CL12.9 M20X 65MM'),
    ('1205301', 'ARRUELA PRES ACO MOLA M30'),
    ('1205317', 'ARRUELA PRES ACO MOLA M20'),
    ('1205361', 'PORCA SEXT CL5 MG M12'),
    ('1205571', 'PARAFUSO SEXT CL4.6 M16X 190MM'),
    ('1205593', 'ARRUELA LIS CIRC ACO CARB M12'),
    ('1205769', 'ARRUELA PRES ACO MOLA M12'),
    ('1205772', 'ARRUELA PRES ACO MOLA M16'),
    ('1207628', 'RETENTOR NBR 170,00X 140,00X 14,00MM'),
    ('1209909', 'ROLAMENTO AUT ROLO 90,00X 160,00MM'),
    ('1211500', 'ENGATE RAP ROSC LATAO 2 "'),
    ('1216378', 'BUCHA RED A105 BSP 1/2X 3/8"'),
    ('1217487', 'PARAFUSO CIL CL10.9 M12X 25MM'),
    ('1219941', 'ANEL O VITON 8,80X 1,90MM'),
    ('1221192', 'PARAFUSO SEXT CL4.6 M12X 120MM'),
    ('1221377', 'PARAFUSO SEXT AISI304 M 8X 50MM'),
    ('1221385', 'PARAFUSO SEXT AISI316 M12X 30MM'),
    ('1223257', 'PARAFUSO CIL CL10.9 M12X 50MM'),
    ('1223278', 'PARAFUSO CIL CL10.9 M24X 90MM'),
    ('1228240', 'PORCA SEXT CL8 MG M24'),
    ('1268070', 'ENGATE RAP ROSC ACO CARB 3/8 "'),
    ('1271352', 'PARAFUSO CIL CL10.9 M16X 65MM'),
    ('1601922', 'RETENTOR NBR 60,00X 40,00X 8,00MM'),
    ('1606249', 'ARRUELA PRES AISI304 M12'),
    ('1617579', 'ANEL O NBR 33,70X 3,50MM'),
    ('1617598', 'ANEL O NBR 54,60X 5,70MM'),
    ('1620770', 'PARAFUSO SEXT CL8.8 M16X 35MM'),
    ('1622643', 'RETENTOR NBR 140,00X 110,00X 14,00MM'),
    ('1624649', 'TUBO FLEX SANF AISI304 3/4 " 800MM'),
    ('1624835', 'MANGUEIRA SBR 6,4 X 800MM'),
    ('1624945', 'TUBO FLEX SANF AISI304 1.1/2 " 900MM'),
    ('1625069', 'ROLAMENTO AUT ROLO 120,00X 180,00MM'),
    ('1628930', 'PARAFUSO SEXT AISI304 M16X 90MM'),
    ('1629283', 'PARAFUSO SEXT AISI304 M20X 70MM'),
    ('1630487', 'TAMPA HITACHI 0294840 FL H-3510 2'),
    ('1630742', 'TAMPA HITACHI 0294841 FL H-3511 1'),
    ('1631445', 'TAMPA HITACHI 0294739 FL H-3504 4'),
    ('1634947', 'RETENTOR NBR 145,00X 115,00X 14,00MM'),
    ('1635200', 'PARAFUSO SEXT CL8.8 M20X 45MM'),
    ('1635659', 'PROTECAO HITACHI 0294878 FL H-3901 7'),
    ('1635660', 'PROTECAO HITACHI 0294878 FL H-3901 4'),
    ('1635661', 'PROTECAO HITACHI 0294878 FL H-3901 1'),
    ('1635721', 'MANCAL HITACHI 2253612 FL H-3502 1'),
    ('1635722', 'MANCAL HITACHI 2253614 FL H-3505 1'),
    ('1635732', 'MANCAL HITACHI 2253611 FL H-3501 1'),
    ('1635733', 'MANCAL HITACHI 2253613 FL H-3503 1'),
    ('1635734', 'MANCAL HITACHI 0294739 FL H-3504 1'),
    ('1636098', 'ESPACADOR HITACHI 0294840 FL H-3510 4'),
    ('1638483', 'RETENTOR SBR 90,00X 70,00X 12,00MM'),
    ('1638492', 'RETENTOR SBR 200,00X 160,00X 15,00MM'),
    ('1638493', 'RETENTOR SBR 200,00X 170,00X 16,00MM'),
    ('1638571', 'ROLAMENTO AUT ROLO 150,00X 225,00MM'),
    ('1638572', 'ROLAMENTO AUT ROLO 130,00X 210,00MM'),
    ('1638677', 'PARAFUSO SEXT CL4.6 M12X 190MM'),
    ('1638717', 'ROLAMENTO ROLO CIL 150,00X 225,00MM'),
    ('1638721', 'ARRUELA TRAVA ROLAM 2,00X 145MM'),
    ('1638724', 'PARAFUSO SEXT CL4.6 M12X 180MM'),
    ('1638725', 'PORCA FIX ROLAM M145X2'),
    ('1638726', 'PORCA FIX ROLAM M115X2'),
    ('1638727', 'ARRUELA TRAVA ROLAM 2,00X 115MM'),
    ('1639149', 'BUCHA HITACHI 0294840 FL H-3510 3'),
    ('1639385', 'PROTECAO HITACHI 0294879 FL H-3902'),
    ('1639386', 'TAMPA HITACHI 0294848 FL H-3520 8'),
    ('1639495', 'BUCHA HITACHI 0294841 FL H-3511 5'),
    ('1639496', 'ESPACADOR HITACHI 0294841 FL H-3511 10'),
    ('1639500', 'ESPACADOR HITACHI 0294841 FL H-3511 7'),
    ('1639501', 'ESPACADOR HITACHI 0294841 FL H-3511 3'),
    ('1639606', 'CHAVETA HITACHI 0294795 FL H3101 2'),
    ('1639630', 'ESPACADOR HITACHI 0294843 FL H-3513 19'),
    ('1639778', 'ESPELHO HITACHI 2256062 FL H-3518 4'),
    ('1639780', 'BUCHA HITACHI 0294847 FL H-3519 4'),
    ('1640577', 'BUCHA HITACHI 0296769 FL J-3507 7'),
    ('1640582', 'MANCAL HITACHI 0294049 FL J-3505 1'),
    ('1640662', 'TAMPA HITACHI 0294740 FL H-3509 4'),
    ('1640663', 'TAMPA HITACHI 0294740 FL H-3509 5'),
    ('1640664', 'MANCAL HITACHI 0294740 FL H-3509 1'),
    ('1640665', 'MANCAL HITACHI 0294736 FL H-3508 1'),
    ('1640667', 'BUCHA HITACHI 0294845 FL H-3516 1'),
    ('1640668', 'BUCHA HITACHI 0294845 FL H-3516 2'),
    ('1640670', 'MANCAL HITACHI 2253616 FL H-3507 1'),
    ('1640671', 'MANCAL HITACHI 2253615 FL H-3506 1'),
    ('1640673', 'BUCHA HITACHI 0294844 FL H-3515 2'),
    ('1640674', 'CHAVETA HITACHI 0294796 FL H3102 2'),
    ('1640675', 'ESPACADOR HITACHI 0294846 FL H-3517 8'),
    ('1640676', 'ESPACADOR HITACHI 0294846 FL H-3517 7'),
    ('1640677', 'BUCHA HITACHI 0294841 FL H-3511 6'),
    ('1641054', 'ABRACADEIRA BIPARTIDA PP 20,0MM'),
    ('1641290', 'ROLO HITACHI 0294737 FL H-3203 1'),
    ('1641291', 'ROLO HITACHI 0294065 FL H-3201 1'),
    ('1641292', 'ROLO HITACHI 0294066 FL H-3202 1'),
    ('1641293', 'ROLO HITACHI 0294795 FL H-3101 01, 04'),
    ('1641294', 'ROLO HITACHI 0294797 FL H-3103 1'),
    ('1641558', 'ROLO HITACHI 0294796 FL H-3102 01, 04'),
    ('1641559', 'TAMPA HITACHI 2256061 FL H-3514 1'),
    ('1641567', 'ESPACADOR HITACHI 2256061 FL H-3514 3'),
    ('1644361', 'TAMPA HITACHI 0294847 FL H-3519 1'),
    ('1644362', 'ESPACADOR HITACHI 0294846 FL H-3517 6'),
    ('1660669', 'ABRACADEIRA BIPARTIDA PP 12,MM'),
    ('1664836', 'RESFRIADOR HITACHI 0295344 FL H-5102'),
    ('1664838', 'RESFRIADOR HITACHI 0295344 FL H-5102'),
    ('1664839', 'RESFRIADOR HITACHI 0295343 FL H-5101'),
    ('1664840', 'RESFRIADOR HITACHI 0295343 FL H-5101'),
    ('1664841', 'RESFRIADOR HITACHI 0295345 FL H-5103'),
    ('1664842', 'RESFRIADOR HITACHI 0295345 FL H-5103'),
    ('1667375', 'GUIA HITACHI 0294842 FL H-3512 2'),
    ('1667376', 'GUIA HITACHI 0294842 FL H-3512 1'),
    ('1667377', 'PINO HITACHI 0294846 FL H-3517 2'),
    ('1667378', 'BLOCO HITACHI 0294846 FL H-3517 1'),
    ('1668393', 'GUIA HITACHI 0294736 11'),
    ('1668394', 'GUIA HITACHI 0294736 12'),
    ('1668395', 'GUIA HITACHI 0294736 6'),
    ('1668396', 'GUIA HITACHI 0294736 7'),
    ('1672218', 'PROTECAO HITACHI 0294879 FL H-3902 4'),
    ('1672219', 'PROTECAO HITACHI 0294879 FL H-3902 7'),
    ('1672220', 'PROTECAO HITACHI 0294879 FL H-3902 1'),
    ('1672221', 'PROTECAO HITACHI 0294880 FL H-3903 1'),
    ('1672222', 'PROTECAO HITACHI 0294880 FL H-3903 4'),
    ('1672223', 'PROTECAO HITACHI 0294880 FL H-3903 7'),
    ('1674830', 'BUCHA HITACHI 0294858 FL H-4401 10'),
    ('1674831', 'BUCHA HITACHI 0294858 FL H-4401 9'),
    ('1674832', 'BUCHA HITACHI 0294859 FL H-4402 9'),
    ('1674833', 'BUCHA HITACHI 0294859 FL H-4402 10'),
    ('1681354', 'ARRUELA PRES AISI304 M20'),
    ('1726447', 'UNIAO A182 304 SW 3000 3/8 "'),
    ('1726448', 'TE A182 304 SW 3000 3/8 "'),
    ('1726708', 'COTOVELO COMP INOX 3/8 " 12,0MM'),
    ('1728817', 'COTOVELO HITACHI 2271315 7'),
    ('1728820', 'COTOVELO HITACHI 2271315 4'),
    ('1729413', 'GUIA CSN SL08373 C'),
    ('1729414', 'GUIA CSN SL08373 B'),
    ('1729415', 'GUIA CSN SL08373 A'),
    ('1729419', 'HASTE HITACHI 0294859 5'),
    ('1740514', 'ESTRUTURA HITACHI 2245054 1'),
    ('1767804', 'TAMPA TOPC TOM00002 11'),
    ('1767805', 'ESPELHO CSN TOM00002 13'),
    ('1767806', 'BUCHA CSN TOM00002 12'),
    ('1777216', 'RESFRIADOR TOPC TOT00025'),
    ('1777217', 'RESFRIADOR TOPC TOT00025'),
    ('1777218', 'RESFRIADOR TOPC TOT00026'),
    ('1777219', 'RESFRIADOR TOPC TOT00026'),
    ('1779031', 'PONTA HITACHI 0295345 FL H-5103'),
    ('1779032', 'PONTA HITACHI 0295343 FL H-5101'),
    ('1779033', 'PONTA HITACHI 0295343 FL H-5101'),
    ('1779034', 'PINO HITACHI 0294841 FL H-3511 12'),
    ('1779035', 'PONTA HITACHI 0295344 FL H-5102'),
    ('1779037', 'PONTA HITACHI 0295345 FL H-5103'),
    ('1779127', 'PARAFUSO CIL CL8.8 M16X 60MM'),
    ('1779128', 'PARAFUSO CIL CL8.8 M12X 35MM'),
    ('1779153', 'PARAFUSO CIL CL8.8 M16X 40MM'),
    ('1779161', 'DISTRIBUIDOR GRAXA 3/8 X1/4" NPT 12SAID'),
    ('1779162', 'DISTRIBUIDOR GRAXA 3/8 X1/4" NPT 10SAID'),
    ('1790098', 'CONECTOR COMP AISI316 3/8 " 12,0MM'),
    ('8001279', 'PORCA DYNAR IEP12L PARA TUBO 12MM'),
    ('8003284', 'CONECTOR COMP INOX 1/4 " 10,0MM'),
    ('8003514', 'TUBO A312 PLN 2,0 MM 10 MM'),
    ('8005265', 'CHAVETA HITACHI 0294751 3'),
    ('8005890', 'PARAFUSO CIL CL10.9 M12X 85MM'),
    ('8006731', 'BLOCO HITACHI 2268134 FL H5314 A'),
    ('8008877', 'BUCHA CSN DM028280 1'),
    ('8010560', 'ESPACADOR HITACHI 0294841 8'),
    ('8010827', 'BATENTE HITACHI 0294845 3'),
    ('8023215', 'BUJAO SEXT INT ACO CARB BSP 1/4 "'),
    ('8023495', 'PONTA HITACHI 0295344 FL H-5102'),
    ('8028816', 'ESPACADOR HITACHI 0294841 4'),
    ('8029310', 'PARAFUSO CIL CL12.9 M10X 80MM'),
    ('8029315', 'PARAFUSO CIL CL12.9 M16X 70MM'),
    ('8029318', 'PARAFUSO CIL CL12.9 M20X 65MM'),
    ('8029319', 'PARAFUSO CIL CL12.9 M22X 100MM'),
    ('8029330', 'PARAFUSO CIL CL12.9 M22X 150MM'),
    ('8040801', 'BLOCO CSN DM048964 1'),
    ('8042163', 'COTOVELO COMP ACO CARB 1/4 " 10,0MM'),
    ('8131681', 'GRAXA GPU310PTA MINERAL NLGI 1 180 KG'),
    ('8271759', 'PORCA SEXT STANDA CL10 MG M20'),
    ('8287526', 'TUBO CU-DHP PLN 0,7 MM 6 MM'),
    ('8288919', 'CONECTOR COMP LATAO 1/4 " 1/4 "'),
    ('8297848', 'COTOVELO M/F ACO 1/4 "'),
    ('8500119', 'PINO HITACHI 189601 13'),
    ('8672336', 'ARRUELA PRES STANDARD AISI316 5/8 "'),
    ('8734948', 'HASTE HITACHI 0294858 5 ATE 8'),
    ('8739547', 'ESPACADOR HITACHI 0294845 14'),
    ('8741139', 'ROLAMENTO ROLO CIL 120,00X 180,00MM'),
    ('8742789', 'LUVA 3/8" INOX ROSCA/SOLDA - NPT'),
    ('9120417', 'MANCAL HITACHI 0294858 1'),
    ('9120418', 'MANCAL HITACHI 0294859 1'),
    ('9137818', 'ACOPLAMENTO PRIMETALS PMVROSME000100301'),
    ('9137819', 'ACOPLAMENTO PRIMETALS PMVROSME000100401'),
    ('9140829', 'RESFRIADOR HITACHI ZOSEN 0295218'),
    ('9140945', 'PORCA CSN DM613216 2'),
    ('9140946', 'CORPO CSN DM613216 1'),
    ('9141175', 'RESFRIADOR HITACHI ZOSEN 0295218'),
    ('9142429', 'CILINDRO HIDR DUPL/ACAO 15MM/ 260MM'),
    ('9146801', 'CILINDRO HIDR DUPL/ACAO 25MM/ 250MM'),
    ('9147671', 'VALVULA ALIV ROSCA M20X1,5 630BAR'),
    ('9155910', 'CILINDRO HIDR DUPL/ACAO 100MM/ 125MM'),
    ('9156000', 'CILINDRO HIDR DUPL/ACAO 100MM/ 100MM'),
    ('9156568', 'CILINDRO HIDR DUPL/ACAO 100MM/ 140MM'),
    ('9158654', 'PARAFUSO SEXT CL5.8 M12X 140MM'),
    ('9158800', 'JUNTA DEUBLIN 2412004145174IC'),
    ('9186514', 'CALCO HITACHI 0294736 8'),
    ('9220402', 'VALVULA RET HIDR CARTUCHO'),
    ('9259157', 'MANGUEIRA NBR 6,4 X 600MM'),
    ('9264172', 'MANGUEIRA NBR 6,4 X 1000MM'),
    ('9265400', 'MANGUEIRA NBR 10,0 X 1000MM'),
    ('9272309', 'PONTA SPRAYING SYSTEMS 470462B 1480'),
    ('9321450', 'PONTA SPRAYING SYSTEMS 470462B 1780'),
    ('9409100', 'CHAVETA HITACHI 2256061 6'),
]


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
        # 🆕 ROLOS TRAVADOS: guarda um JSON (texto) com a lista de rolos
        # marcados como travados nesta peça, ex: '["S-4","I-2"]'. Só se
        # aplica a equipamentos com rolos (Horizontal, Bender, Zero,
        # Segmento de Grupo, Bow) — o layout de cada um (quantos rolos,
        # base superior/inferior, qual é o acionado) fica no front-end
        # (dados.js -> LAYOUT_ROLOS_POR_TIPO), aqui é só texto livre.
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS rolos_travados TEXT''')
        # 🆕 MANCAIS: guarda um JSON (texto) com as ocorrências dos
        # mancais (rolamentos) das pontas de cada rolo, ex:
        # '{"S-3-A":"rolamento","I-1-B":"graxa"}'. Só se aplica, por
        # enquanto, ao Segmento de Grupo 1/2/3 (dados.js ->
        # LAYOUT_ROLOS_POR_TIPO -> temMancais: true), mas o campo fica
        # disponível pra qualquer peça, igual rolos_travados.
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS mancais_ocorrencias TEXT''')

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

        # 🔩 Materiais técnicos por área — catálogo (código + descrição) do
        # que aquela área normalmente usa. UNIQUE(area, codigo) evita
        # duplicar o mesmo item na mesma área se alguém cadastrar 2x.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materiais_area (
                id SERIAL PRIMARY KEY,
                area TEXT NOT NULL,
                codigo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                criado_por TEXT,
                criado_em TEXT,
                UNIQUE(area, codigo)
            )
        ''')

        # 📋 Execuções de procedimento (checklist). Os procedimentos em si
        # (passo a passo, EPIs, ferramentas) ficam definidos como dados
        # estáticos no front-end (procedimentosOficina.js) — aqui só fica
        # o REGISTRO de cada vez que alguém executou um, com quais etapas
        # foram marcadas como feitas. "etapas_marcadas" guarda uma lista
        # em JSON com os IDs das etapas concluídas (ex: ["1.1","1.2"]),
        # pra permitir consultar depois quais passos foram (ou não)
        # cumpridos numa execução específica.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS procedimentos_execucoes (
                id SERIAL PRIMARY KEY,
                area TEXT NOT NULL,
                procedimento_id TEXT NOT NULL,
                procedimento_nome TEXT,
                operador TEXT,
                etapas_marcadas TEXT,
                total_etapas INTEGER,
                concluido BOOLEAN DEFAULT FALSE,
                data_hora TEXT
            )
        ''')

        # 🆕 ORDENS DE SERVIÇO (OS) — registro digital das OS em papel.
        # A OS real da CSN vem em várias páginas (cabeçalho, EPIs/
        # ferramentas/operações, confirmação) — por isso as fotos ficam
        # numa tabela separada (os_fotos, 1 OS pode ter N fotos, uma por
        # página), em vez de uma coluna só de foto na própria ordens_servico.
        # A pessoa opcionalmente anota o número da OS e uma descrição, e
        # acompanha o status (Em Andamento -> Concluído). Fica na aba
        # "Registro de OS", dentro de Monitoramento de Máquinas.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ordens_servico (
                id SERIAL PRIMARY KEY,
                numero_os TEXT,
                descricao TEXT,
                status TEXT DEFAULT 'Em Andamento',
                criado_por TEXT,
                criado_em TEXT,
                concluido_por TEXT,
                concluido_em TEXT
            )
        ''')
        # Coluna antiga de uma versão anterior (1 OS = 1 foto só) — quem
        # já tinha essa tabela criada com CREATE TABLE IF NOT EXISTS não
        # ganha a mudança de estrutura sozinho, mas como as fotos agora
        # vivem em os_fotos, essa coluna simplesmente deixa de ser usada
        # (mantida só pra não quebrar quem já tinha dado no ar antes).
        cursor.execute('''ALTER TABLE ordens_servico ADD COLUMN IF NOT EXISTS foto_base64 TEXT''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS os_fotos (
                id SERIAL PRIMARY KEY,
                os_id INTEGER REFERENCES ordens_servico(id) ON DELETE CASCADE,
                foto_base64 TEXT NOT NULL,
                criado_em TEXT
            )
        ''')

        # 🌱 Seed único da área "segmento-grupo": já existia uma lista real
        # de materiais (Grupos 1+2+3, do documento oficial da CSN) usada
        # no folhão de Segmento Grupo — reaproveitamos aqui como ponto de
        # partida da aba Oficina. Só roda se a área ainda estiver vazia,
        # pra não reinserir toda vez que o servidor sobe.
        cursor.execute("SELECT COUNT(*) as qtd FROM materiais_area WHERE area = 'segmento-grupo'")
        if cursor.fetchone()["qtd"] == 0:
            agora_seed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.executemany('''
                INSERT INTO materiais_area (area, codigo, descricao, criado_por, criado_em)
                VALUES ('segmento-grupo', %s, %s, 'Sistema (importado)', %s)
                ON CONFLICT (area, codigo) DO NOTHING
            ''', [(codigo, descricao, agora_seed) for codigo, descricao in SEED_MATERIAIS_SEGMENTO_GRUPO])

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


import re as re_lib


# 🔧 CORREÇÃO ("notificação chega feia no celular, cheia de coisa
# escrita"): o texto de várias ações (Intervenção, Melhoria, Comentário,
# Atividade Pendente, Registro Manual) é salvo no banco já com tags HTML
# — ex: '<span style="color:#eab308;">[INTERVENÇÃO]</span>' — usadas só
# pra colorir a categoria dentro do Prontuário do app. O problema é que
# a notificação push mostra TEXTO PURO (o celular não entende HTML), e
# essas tags apareciam escritas literalmente na notificação, deixando
# ela poluída e ilegível. Esta função limpa o texto SÓ pra exibição na
# notificação — o que fica salvo no banco/Prontuário continua intacto.
def limpar_texto_para_notificacao(texto: str) -> str:
    if not texto:
        return texto
    # Remove qualquer tag HTML (ex: <span ...>, </span>)
    limpo = re_lib.sub(r"<[^>]+>", "", texto)
    # Espaços duplicados que sobram depois de tirar as tags
    limpo = re_lib.sub(r"\s{2,}", " ", limpo).strip()
    return limpo


def enviar_push_para_area(titulo: str, corpo: str, area: str = "Ambos", url: str = "/"):
    if not PUSH_HABILITADO:
        return

    corpo = limpar_texto_para_notificacao(corpo)
    titulo = limpar_texto_para_notificacao(titulo)

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
    rolos_travados: Optional[str] = None
    mancais_ocorrencias: Optional[str] = None
    # 🆕 Preenchidos SÓ quando o front-end registra uma ocorrência nova
    # (quebra de rolamento / vazamento de graxa / vazamento de água) num
    # mancal — não em toda troca de rolos_travados/observacao. Servem só
    # pra disparar o push notification; o texto já vem pronto do
    # front-end (ver salvarMancalOcorrencia no Sinotico3d.html), porque
    # é lá que se sabe qual peça, qual mancal e qual veio.
    mancal_evento_titulo: Optional[str] = None
    mancal_evento_corpo: Optional[str] = None

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

class ColaboradorMudarCargo(BaseModel):
    matricula: str
    cargo: str

class ColaboradorAlternarAtivo(BaseModel):
    matricula: str
    ativo: bool

class ColaboradorResetarSenha(BaseModel):
    matricula: str

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


class OficinaMaterial(BaseModel):
    area: str
    codigo: str
    descricao: str
    operador: Optional[str] = None


class OficinaMaterialExcluir(BaseModel):
    id: int


class ProcedimentoExecucao(BaseModel):
    area: str
    procedimento_id: str
    procedimento_nome: Optional[str] = None
    etapas_marcadas: list = []
    total_etapas: Optional[int] = None
    concluido: bool = False
    operador: Optional[str] = None


class OficinaAtividadeEditar(BaseModel):
    id: int
    equipamento_id: Optional[str] = None
    descricao: str
    responsavel: Optional[str] = None
    prioridade: Optional[str] = "Normal"
    prazo: Optional[str] = None
    foto_base64: Optional[str] = None  # null = sem foto anexada / mantém a que já tinha, ver rota


class OrdemServicoCriar(BaseModel):
    numero_os: Optional[str] = None
    descricao: Optional[str] = None
    fotos_base64: list[str] = []  # 1 OS pode ter várias páginas/fotos
    operador: str


class OrdemServicoStatus(BaseModel):
    id: int
    status: str  # "Em Andamento" | "Concluído"
    operador: str


class OrdemServicoExcluir(BaseModel):
    id: int


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
    if peca.rolos_travados is not None:
        campos.append("rolos_travados = %s"); valores.append(peca.rolos_travados)
    if peca.mancais_ocorrencias is not None:
        campos.append("mancais_ocorrencias = %s"); valores.append(peca.mancais_ocorrencias)

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
                INSERT INTO equipamentos (id, tipo, local, status, tonelagem, dias, meta, posicao, tag_patrimonio, data_entrada, data_reparo, substituido_por, observacao, rolos_travados, mancais_ocorrencias)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    observacao = EXCLUDED.observacao,
                    rolos_travados = EXCLUDED.rolos_travados,
                    mancais_ocorrencias = EXCLUDED.mancais_ocorrencias
            ''', (
                peca.id, peca.tipo or "", peca.local or "", peca.status or "",
                peca.tonelagem or 0, peca.dias or 0, peca.meta or 0, peca.posicao or "",
                peca.tag_patrimonio, peca.data_entrada, peca.data_reparo,
                peca.substituido_por, peca.observacao, peca.rolos_travados, peca.mancais_ocorrencias
            ))
            criada = True

        conn.commit()

    # 🆕 Notificação push quando uma ocorrência de mancal é registrada
    # (não dispara em toda edição de peça — só quando o front-end manda
    # o texto pronto, ou seja, quando de fato marcou quebra de
    # rolamento / vazamento de graxa ou água num mancal).
    if peca.mancal_evento_corpo:
        enviar_push_para_area(
            titulo=peca.mancal_evento_titulo or "⚠️ Ocorrência em mancal",
            corpo=peca.mancal_evento_corpo,
            area="Ambos"
        )

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


# ==========================================
# ADMINISTRAÇÃO DE COLABORADORES (Área Restrita — só as 2 matrículas
# admin, checagem feita no front-end igual ao resto da Área Restrita;
# essas rotas não têm autenticação própria, seguindo o mesmo padrão do
# resto da API neste sistema).
# ==========================================
@app.get("/api/colaboradores/todos")
def get_colaboradores_todos():
    """Lista TODOS os colaboradores, ativos e inativos — usado só no
    painel de administração (a rota /api/colaboradores normal, usada
    pelo login e por outras telas, continua trazendo só quem está
    ativo)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, ativo, primeiro_acesso FROM colaboradores ORDER BY ativo DESC, nome"
        )
        return cursor.fetchall()


@app.post("/api/colaboradores/mudar_cargo")
def mudar_cargo_colaborador(dados: ColaboradorMudarCargo):
    matricula = dados.matricula.strip().upper()
    cargo = dados.cargo.strip()
    if not cargo:
        raise HTTPException(status_code=400, detail="Informe um cargo.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE colaboradores SET cargo = %s WHERE matricula = %s", (cargo, matricula))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
        conn.commit()

    return {"sucesso": True}


@app.post("/api/colaboradores/alternar_ativo")
def alternar_ativo_colaborador(dados: ColaboradorAlternarAtivo):
    matricula = dados.matricula.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE colaboradores SET ativo = %s WHERE matricula = %s", (dados.ativo, matricula))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
        conn.commit()

    return {"sucesso": True, "ativo": dados.ativo}


@app.post("/api/colaboradores/resetar_senha")
def resetar_senha_colaborador(dados: ColaboradorResetarSenha):
    """Zera a senha do colaborador e marca como 'primeiro acesso' de
    novo — a senha temporária volta a ser a própria matrícula, igual
    faz o resetar_colaboradores.py no terminal, mas só pra UMA pessoa
    por vez em vez de apagar todo mundo."""
    matricula = dados.matricula.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE colaboradores SET senha_hash = NULL, primeiro_acesso = TRUE WHERE matricula = %s",
            (matricula,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
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


# ==========================================
# OFICINA — MATERIAIS POR ÁREA
# ==========================================
@app.get("/api/oficina/materiais_todos")
def get_materiais_todas_areas():
    """Lista os materiais técnicos de TODAS as áreas de uma vez, cada um
    já com a área a que pertence — usado no Catálogo geral (busca única
    em vez de precisar abrir área por área)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, area, codigo, descricao FROM materiais_area ORDER BY area, descricao"
        )
        return cursor.fetchall()


@app.get("/api/oficina/materiais/{area}")
def get_materiais_area_oficina(area: str):
    # 🔧 CORREÇÃO ("aparece tudo no Catálogo geral, mas nada na aba
    # Materiais de dentro da área"): o Catálogo geral (materiais_todos)
    # não filtra por área — só lista tudo, então sempre "funciona"
    # mesmo se o texto salvo em materiais_area.area tiver um espaço a
    # mais, acento diferente ou letra maiúscula/minúscula trocada em
    # relação à "chave" que o app usa (ex: "Bender " ≠ "bender"). Essa
    # rota, que FILTRA por área, é onde esse tipo de divergência
    # silenciosa aparece como "lista vazia" mesmo com dado cadastrado.
    # TRIM + LOWER dos dois lados evita que isso quebre a busca.
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, codigo, descricao FROM materiais_area WHERE LOWER(TRIM(area)) = LOWER(TRIM(%s)) ORDER BY descricao",
            (area,)
        )
        return cursor.fetchall()


@app.post("/api/oficina/materiais")
def criar_material_area_oficina(dados: OficinaMaterial):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO materiais_area (area, codigo, descricao, criado_por, criado_em)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (area, codigo) DO UPDATE SET descricao = EXCLUDED.descricao
            RETURNING id
            """,
            (dados.area.strip(), dados.codigo.strip(), dados.descricao.strip(), dados.operador, agora)
        )
        material_id = cursor.fetchone()["id"]
        conn.commit()
    return {"sucesso": True, "id": material_id}


@app.post("/api/oficina/materiais/excluir")
def excluir_material_area_oficina(dados: OficinaMaterialExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM materiais_area WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material não encontrado.")
        conn.commit()
    return {"sucesso": True}


# ==========================================
# OFICINA — EDITAR ATIVIDADE
# ==========================================
@app.post("/api/oficina/atividade/editar")
def editar_atividade_oficina(dados: OficinaAtividadeEditar):
    """Edita os campos de uma atividade já lançada. Área, status e
    autoria original não mudam aqui — só descrição/equipamento/
    responsável/prioridade/prazo/foto. Pra mudar status, usa a rota
    /api/oficina/atividade/status."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE oficina_atividades
            SET equipamento_id = %s, descricao = %s, responsavel = %s,
                prioridade = %s, prazo = %s, foto_base64 = %s
            WHERE id = %s
            """,
            (dados.equipamento_id, dados.descricao, dados.responsavel,
             dados.prioridade or "Normal", dados.prazo, dados.foto_base64, dados.id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()
    return {"sucesso": True}

# ==========================================
# PROCEDIMENTOS (checklist de etapas por área)
# ==========================================
# O conteúdo do procedimento (passo a passo, EPIs, ferramentas) fica
# como dado estático no front-end (procedimentosOficina.js) — aqui só
# fica o REGISTRO de cada execução: quem fez, quando, e quais etapas
# foram marcadas. Isso permite auditar depois (ex: "esse procedimento
# foi mesmo seguido por completo na última execução?").
@app.post("/api/oficina/procedimento/executar")
def registrar_execucao_procedimento(dados: ProcedimentoExecucao):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO procedimentos_execucoes
                (area, procedimento_id, procedimento_nome, operador, etapas_marcadas, total_etapas, concluido, data_hora)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                dados.area,
                dados.procedimento_id,
                dados.procedimento_nome,
                dados.operador,
                json_lib.dumps(dados.etapas_marcadas),
                dados.total_etapas,
                dados.concluido,
                agora,
            )
        )
        execucao_id = cursor.fetchone()["id"]

        # Só registra no histórico do log geral (Auditoria) quando o
        # técnico de fato concluiu todas as etapas — execuções parciais
        # (ex: ele só queria salvar o progresso e continuar depois) não
        # geram um evento de "procedimento concluído" na Auditoria.
        # Importante: isso precisa acontecer DENTRO do mesmo 'with',
        # usando a mesma conexão/cursor — se rodar depois que a conexão
        # já foi devolvida ao pool, ela pode ser reaproveitada por outra
        # requisição ao mesmo tempo (ThreadedConnectionPool), causando
        # erros aleatórios ou gravação na conexão errada.
        if dados.concluido:
            try:
                cursor.execute(
                    "INSERT INTO log_eventos (data_hora, operador, peca_id, acao) VALUES (%s, %s, %s, %s)",
                    (agora, dados.operador or "Sistema", f"OFICINA-{dados.area.upper()}",
                     f"📋 Procedimento concluído: {dados.procedimento_nome or dados.procedimento_id}")
                )
            except Exception as e:
                print(f"⚠️ Não consegui registrar o log de conclusão do procedimento: {e}")

        conn.commit()

    return {"sucesso": True, "id": execucao_id}


@app.get("/api/oficina/procedimento/historico/{area}")
def historico_execucoes_procedimento(area: str, procedimento_id: Optional[str] = None, limite: int = 20):
    """Últimas execuções de procedimentos de uma área — usado pra mostrar
    'última vez que isso foi feito, e por quem' na tela do procedimento."""
    with get_db() as conn:
        cursor = conn.cursor()
        if procedimento_id:
            cursor.execute(
                """
                SELECT id, procedimento_id, procedimento_nome, operador, etapas_marcadas,
                       total_etapas, concluido, data_hora
                FROM procedimentos_execucoes
                WHERE area = %s AND procedimento_id = %s
                ORDER BY id DESC LIMIT %s
                """,
                (area, procedimento_id, limite)
            )
        else:
            cursor.execute(
                """
                SELECT id, procedimento_id, procedimento_nome, operador, etapas_marcadas,
                       total_etapas, concluido, data_hora
                FROM procedimentos_execucoes
                WHERE area = %s
                ORDER BY id DESC LIMIT %s
                """,
                (area, limite)
            )
        return cursor.fetchall()

# ==========================================
# 🆕 ORDENS DE SERVIÇO (OS) — registro digital de OS em papel (várias
# fotos por OS, uma por página), com acompanhamento de status (Em
# Andamento / Concluído).
# ==========================================
@app.get("/api/ordens_servico")
def listar_ordens_servico(status: Optional[str] = None):
    """Lista as OS com uma foto de "capa" (a primeira cadastrada) e o
    total de fotos — pra montar o card na lista sem precisar buscar
    TODAS as fotos de TODAS as OS de uma vez (isso ficaria pesado)."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT
                o.*,
                (SELECT f.foto_base64 FROM os_fotos f WHERE f.os_id = o.id ORDER BY f.id ASC LIMIT 1) AS foto_capa,
                (SELECT COUNT(*) FROM os_fotos f WHERE f.os_id = o.id) AS total_fotos
            FROM ordens_servico o
        """
        if status:
            query += " WHERE o.status = %s ORDER BY o.id DESC"
            cursor.execute(query, (status,))
        else:
            query += " ORDER BY o.id DESC"
            cursor.execute(query)
        return cursor.fetchall()


@app.get("/api/ordens_servico/{os_id}/fotos")
def get_fotos_ordem_servico(os_id: int):
    """Todas as fotos/páginas de uma OS específica, na ordem em que
    foram cadastradas — usado pra abrir a galeria completa da OS."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, foto_base64, criado_em FROM os_fotos WHERE os_id = %s ORDER BY id ASC",
            (os_id,)
        )
        return cursor.fetchall()


@app.post("/api/ordens_servico")
def criar_ordem_servico(dados: OrdemServicoCriar):
    if not dados.fotos_base64:
        raise HTTPException(status_code=400, detail="É preciso pelo menos 1 foto da OS.")

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ordens_servico (numero_os, descricao, status, criado_por, criado_em)
            VALUES (%s, %s, 'Em Andamento', %s, %s)
            RETURNING id
            """,
            (dados.numero_os, dados.descricao, dados.operador, agora)
        )
        os_id = cursor.fetchone()["id"]

        cursor.executemany(
            "INSERT INTO os_fotos (os_id, foto_base64, criado_em) VALUES (%s, %s, %s)",
            [(os_id, foto, agora) for foto in dados.fotos_base64]
        )
        conn.commit()

    return {"sucesso": True, "id": os_id}


@app.post("/api/ordens_servico/status")
def mudar_status_ordem_servico(dados: OrdemServicoStatus):
    if dados.status not in ("Em Andamento", "Concluído"):
        raise HTTPException(status_code=400, detail="Status inválido.")

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        if dados.status == "Concluído":
            cursor.execute(
                "UPDATE ordens_servico SET status = %s, concluido_por = %s, concluido_em = %s WHERE id = %s",
                (dados.status, dados.operador, agora, dados.id)
            )
        else:
            # Voltando pra "Em Andamento" — limpa quem/quando concluiu,
            # já que essa conclusão deixou de valer.
            cursor.execute(
                "UPDATE ordens_servico SET status = %s, concluido_por = NULL, concluido_em = NULL WHERE id = %s",
                (dados.status, dados.id)
            )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada.")
        conn.commit()

    return {"sucesso": True}


@app.post("/api/ordens_servico/excluir")
def excluir_ordem_servico(dados: OrdemServicoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        # os_fotos tem ON DELETE CASCADE — apagar a OS já apaga as fotos
        # dela junto, sem precisar de um DELETE separado.
        cursor.execute("DELETE FROM ordens_servico WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada.")
        conn.commit()

    return {"sucesso": True}