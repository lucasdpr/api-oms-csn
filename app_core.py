import os
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone, timedelta
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

# 🕒 Servidor roda em UTC (padrão em serviços de deploy tipo Render), mas
# a fábrica é no Brasil (UTC-3, sem horário de verão desde 2019). Sem
# isso, todo horário salvo no banco (criado_em, concluido_em etc.) ficava
# 3h à frente do horário real de quem tava usando o app. Esse helper
# substitui datetime.now() em TODA a API — trocar aqui já corrige todo
# mundo de uma vez.
FUSO_BRASIL = timezone(timedelta(hours=-3))


def agora_brasil() -> datetime:
    return datetime.now(FUSO_BRASIL)


# 🔧 CORRIGIDO (matrícula duplicada dentro do próprio main.py — risco de
# uma lista ser atualizada e a outra não): antes existia uma
# MATRICULAS_ADM separada aqui, com as mesmas 3
# matrículas de MATRICULAS_ADM (definida mais abaixo). Confirmado que
# as 3 matrículas ADM devem ter acesso a tudo, então os 4 pontos que
# usavam a lista separada (cadastrar/editar/excluir/reordenar etapas do
# Checklist de Execução) agora usam MATRICULAS_ADM direto — uma lista
# só, uma fonte de verdade só.





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

# 🆕 Regra de notificação por área: administrador (MATRICULAS_ADM,
# definida mais abaixo) recebe TODA notificação, não importa a área.
# Colaborador comum só recebe quando a notificação é da área dele
# (comparando com o campo "area" salvo em colaboradores/equipe_oficina).
# Eventos "gerais" (produção, OS, ocorrência, peça pra Reserva, troca de
# equipamento...) não têm uma área da oficina associada de forma
# confiável no banco hoje — só uma peça/equipamento, não um responsável
# por área — então esses continuam só pros administradores por enquanto.
# Só as notificações de Atividade da Oficina (nova / atrasada) já têm o
# campo "area" certo pra valer, e são as que de fato chegam pros
# técnicos da área correspondente.

db_pool = psycopg2_pool.ThreadedConnectionPool(
    minconn=1,
    # 🔧 CORREÇÃO ("connection pool exhausted" causando 500 em
    # /api/oficina/atividades no meio de uma rajada de requisições —
    # app.html dispara várias chamadas em paralelo ao carregar, ex: um
    # status/laudo por equipamento): 10 conexões simultâneas era pouco
    # pra esse padrão de uso. psycopg2.pool não espera por uma conexão
    # livre — se estourar o limite, falha na hora (é isso que virava
    # 500). Subido pra 20, com folga pro pico de carregamento.
    maxconn=20,
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
        # 🆕 CORREÇÃO CRÍTICA: essa coluna nunca existiu no banco — o
        # "mcc_compat" (que diz se o equipamento é MCC 2/3 ou MCC 4) só
        # vivia no localStorage do navegador que cadastrou a peça. Quando
        # outro login/dispositivo sincronizava com a nuvem, recebia o
        # equipamento SEM esse campo, e o front-end (`a.mcc_compat ||
        # "2/3"`) assumia "2/3" por padrão — fazendo um Molde MCC4
        # cadastrado corretamente "virar" MCC 2/3 pros outros usuários,
        # inclusive gerando o Folhão errado. Agora persiste de verdade.
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS mcc_compat TEXT''')
        # 🆕 BARRA TRANSVERSAL: guarda um JSON (texto) com o estado de
        # cada componente clicável do Sinótico 3D — cilindros de
        # elevação (CIL-1..4), cilindros centrais (BALL-RE/BALL-AV) e a
        # própria barra transversal (BARRA-TRANSVERSAL), ex:
        # '{"CIL-2":{"flexivelAvanco":"amarelo","observacao":"..."}}'.
        # Só se aplica a Bow, Horizontal e Straightener (R1/R2) — MCC4
        # menos Molde e Bender (dados.js -> LAYOUT_BARRA_TRANSVERSAL_POR_TIPO).
        cursor.execute('''ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS barra_transversal TEXT''')

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
        # 🆕 Área da oficina onde a ocorrência aconteceu (mesma chave de
        # AREAS_OFICINA no front-end, ex: "hidraulica") — opcional, pra
        # dar contexto na Central de Notificações sem precisar adivinhar
        # a área a partir do equipamento.
        cursor.execute('''ALTER TABLE log_eventos ADD COLUMN IF NOT EXISTS area TEXT''')
        # 🆕 Id da oficina_atividades quando o evento é sobre uma
        # Atividade da Oficina (categoria='Atividade Oficina') — permite
        # a Central de Notificações abrir a "Conversa da Atividade" DIRETO
        # ao clicar, em vez de só levar pro quadro geral da área e a
        # pessoa ter que procurar o card certo pra clicar no balão de
        # chat. NULL pra todo o resto (Ocorrência, OS, achado...).
        cursor.execute('''ALTER TABLE log_eventos ADD COLUMN IF NOT EXISTS atividade_id INTEGER''')
        # 🆕 Classifica o evento de Atividade Oficina pra saber pra ONDE o
        # clique na Central de Notificações deve levar: 'mensagem' abre a
        # Conversa da Atividade, enquanto 'status'/'criacao'/'edicao'
        # abrem a Atividade em si (o técnico não precisa entrar no chat
        # só pra ver que a peça mudou de status). NULL pro resto dos
        # tipos de evento (Ocorrência, OS, achado, sinótico, estoque) —
        # esses já têm rota própria fixa no front (ver
        # abrirItemNotificacao). Ver registrar_evento_atividade_oficina.
        cursor.execute('''ALTER TABLE log_eventos ADD COLUMN IF NOT EXISTS tipo_evento TEXT''')

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

        # 🆕 Controle de "lido/não lido" da Central de Notificações — POR
        # PESSOA. Um evento (ocorrência, OS, achado...) é identificado por
        # (tipo, evento_id) — tipo distingue as tabelas de origem, já que
        # os IDs numéricos se repetem entre elas (ocorrência #5 e OS #5
        # são coisas diferentes). Cada matrícula tem sua própria linha:
        # o ADM marcar como visto NÃO afeta o que outra pessoa já viu.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificacoes_lidas (
                tipo TEXT NOT NULL,
                evento_id TEXT NOT NULL,
                matricula TEXT NOT NULL,
                lido_em TEXT NOT NULL,
                PRIMARY KEY (tipo, evento_id, matricula)
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
        # 🆕 Marca se já foi disparada notificação de atraso pra essa
        # atividade — sem isso, toda vez que alguém abrisse o app de
        # novo (e a atividade continuasse atrasada), a notificação
        # repetiria de novo e de novo.
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS notificado_atraso BOOLEAN DEFAULT FALSE
        ''')
        # 🆕 Data de Início — quando preenchida com uma data futura, a
        # atividade fica "programada": existe no banco, mas o front-end
        # só mostra ela como "pra fazer" (Pendente/Em Andamento) a
        # partir desse dia. Sem valor, conta como já disponível pra
        # começar (compatível com todo registro antigo, que não tem
        # essa coluna preenchida).
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS data_inicio TEXT
        ''')

        # 🆕 JUSTIFICATIVA — pra quando a área não pode simplesmente
        # "passar por cima" de uma atividade: precisa dizer POR QUE não
        # iniciou (status "Recusado", ex: pediram e não forneceram o
        # material) ou por que travou depois de já ter começado (status
        # "Aguardando", ex: aguardando material chegar). Quem pediu a
        # atividade (o solicitante_matricula) é avisado por push com
        # esse motivo — ver enviar_push_para_matricula.
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS motivo_status TEXT
        ''')
        # 🆕 Quem PEDIU essa atividade (matrícula) — separado de
        # "criado_por" (que hoje guarda o NOME de exibição, não dá pra
        # mandar push só com isso). Preenchido automaticamente quando a
        # atividade nasce de um "Registrar Atividade Extra" no
        # Checklist de Execução (ver registrar_atividade_extra_
        # checklist_execucao); atividade criada direto no quadro da
        # área fica sem solicitante (não tem "quem pediu" — quem criou
        # e quem executa são a mesma pessoa/área).
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS solicitante_matricula TEXT
        ''')
        # 🆕 Nome de quem está EXECUTANDO a atividade agora — "responsavel"
        # é um campo livre digitado na criação/edição (pode nem ser
        # preenchido, e não muda sozinho), então não dava pra saber quem
        # de fato pegou o serviço. Preenchido com o nome de quem mudou o
        # status pra "Em Andamento" (ver mudar_status_atividade_oficina)
        # — é o jeito mais simples de capturar "quem tá executando" sem
        # inventar um fluxo de "assumir atividade" novo. Importante pro
        # solicitante de outra área ver não só a ÁREA que tá cuidando do
        # pedido, mas a PESSOA.
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS executado_por TEXT
        ''')

        # 🆕 Quantas vezes essa atividade já foi REABERTA (ver fluxo de
        # window.reabrirAtividadeOficina) — guardado direto na própria
        # atividade pra o front-end mostrar o indicador "🔄 Reaberta Nx"
        # sem precisar de JOIN/COUNT em oficina_atividades_reaberturas
        # toda vez que lista as atividades (ver listar_atividades_oficina).
        cursor.execute('''
            ALTER TABLE oficina_atividades ADD COLUMN IF NOT EXISTS reaberturas_count INTEGER DEFAULT 0
        ''')

        # 🆕 HISTÓRICO DE REABERTURAS — antes de reabrir (ver mudar_status_
        # atividade_oficina com dados.reabertura=True), o UPDATE zera
        # concluido_em e SOBRESCREVE motivo_status com o motivo da
        # reabertura — perdendo pra sempre a data da conclusão original e
        # o motivo/observação de quem concluiu. Essa tabela guarda uma
        # linha por reabertura com o que a atividade tinha ANTES de mudar,
        # pra dar pra reconstruir o histórico completo depois (indicador
        # visual, relatório de retrabalho — ver /mais_reabertas).
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oficina_atividades_reaberturas (
                id SERIAL PRIMARY KEY,
                atividade_id INTEGER NOT NULL REFERENCES oficina_atividades(id) ON DELETE CASCADE,
                concluido_em_anterior TEXT,
                motivo_conclusao_anterior TEXT,
                motivo_reabertura TEXT NOT NULL,
                reaberto_por TEXT,
                executado_por_anterior TEXT,
                data_reabertura TEXT
            )
        ''')

        # 🆕 CONVERSA DA ATIVIDADE — thread de mensagens de mão dupla
        # numa atividade específica. Sem isso, o único jeito de "avisar"
        # alguma coisa era recusar/pausar (que exige motivo, mas é uma
        # via só: área -> solicitante). Casos reais que isso resolve:
        #   - Solicitante pede algo urgente: "preciso disso pra hoje"
        #     (mensagem já na criação, ou logo depois).
        #   - Área pausou por falta de material; solicitante responde
        #     "levei o material agora" — sem precisar reabrir/recriar
        #     nada, só conversar na mesma atividade.
        #   - Área pergunta algo antes de começar ("é essa tag mesmo?").
        #   - Área conclui e deixa uma observação final pro solicitante.
        # Cada mensagem nova dispara push pro OUTRO lado (quem mandou
        # não recebe aviso da própria mensagem) — ver
        # criar_mensagem_atividade_oficina.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oficina_atividade_mensagens (
                id SERIAL PRIMARY KEY,
                atividade_id INTEGER NOT NULL REFERENCES oficina_atividades(id) ON DELETE CASCADE,
                autor_matricula TEXT,
                autor_nome TEXT,
                mensagem TEXT NOT NULL,
                criado_em TEXT
            )
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

        # 🆕 Status "Não Executada" — bate com o campo "[ ] Não Executada" +
        # "Motivo/Justificativa" que já existe no papel da OS real (parte
        # de confirmação, no final do documento). Cobre o caso de uma OS
        # que estava "Em Andamento" mas precisou ser encerrada sem ter
        # sido feita (falta de peça, condição não permitiu, replanejada
        # etc) — precisa ficar registrado o motivo, não só sumir.
        cursor.execute('''ALTER TABLE ordens_servico ADD COLUMN IF NOT EXISTS motivo_nao_executada TEXT''')
        cursor.execute('''ALTER TABLE ordens_servico ADD COLUMN IF NOT EXISTS encerrado_por TEXT''')
        cursor.execute('''ALTER TABLE ordens_servico ADD COLUMN IF NOT EXISTS encerrado_em TEXT''')
        # 🆕 Mesma ideia de área de log_eventos.area — opcional, pra dar
        # contexto na Central de Notificações.
        cursor.execute('''ALTER TABLE ordens_servico ADD COLUMN IF NOT EXISTS area TEXT''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS os_fotos (
                id SERIAL PRIMARY KEY,
                os_id INTEGER REFERENCES ordens_servico(id) ON DELETE CASCADE,
                foto_base64 TEXT NOT NULL,
                criado_em TEXT
            )
        ''')

        # 🆕 QUALIDADE (Entrada/Saída) — o responsável pela Qualidade
        # registra com fotos como o equipamento chegou na oficina (Entrada)
        # e, quando o serviço termina, registra também como ele está saindo
        # (Saída). Cada registro fica "Aguardando Saída" até a segunda
        # etapa ser preenchida, quando vira "Concluído". Fotos de entrada e
        # saída ficam numa tabela separada (qualidade_fotos, com a coluna
        # etapa dizendo se é 'entrada' ou 'saida'), igual ao padrão já
        # usado em os_fotos.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_registros (
                id SERIAL PRIMARY KEY,
                peca_id TEXT NOT NULL,
                observacao_entrada TEXT,
                observacao_saida TEXT,
                status TEXT DEFAULT 'Aguardando Saída',
                criado_por TEXT,
                criado_em TEXT,
                concluido_por TEXT,
                concluido_em TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_fotos (
                id SERIAL PRIMARY KEY,
                registro_id INTEGER REFERENCES qualidade_registros(id) ON DELETE CASCADE,
                etapa TEXT NOT NULL,
                foto_base64 TEXT NOT NULL,
                criado_em TEXT
            )
        ''')

        # 🆕 QUALIDADE — ACHADOS: em vez de 1 observação corrida só, cada
        # problema que o inspetor encontra (ex: "distribuidor vazando")
        # vira uma linha própria, com foto opcional e status individual
        # (Pendente -> Resolvido). Pode ser adicionado a qualquer momento
        # enquanto o registro estiver "Aguardando Saída" — não só na
        # entrada — porque a Qualidade pode ir achando coisa durante o
        # processo também.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_achados (
                id SERIAL PRIMARY KEY,
                registro_id INTEGER REFERENCES qualidade_registros(id) ON DELETE CASCADE,
                descricao TEXT NOT NULL,
                foto_base64 TEXT,
                status TEXT DEFAULT 'Pendente',
                criado_por TEXT,
                criado_em TEXT,
                foto_resolucao_base64 TEXT,
                resolvido_por TEXT,
                resolvido_em TEXT
            )
        ''')

        # 🆕 Um achado pode ter mais de 1 foto (antes só tinha a coluna
        # foto_base64 na própria tabela, limitando a 1). A coluna antiga
        # continua existindo pra não perder foto de achado já cadastrado
        # antes dessa mudança — achados novos usam essa tabela.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_achado_fotos (
                id SERIAL PRIMARY KEY,
                achado_id INTEGER REFERENCES qualidade_achados(id) ON DELETE CASCADE,
                foto_base64 TEXT NOT NULL,
                criado_em TEXT
            )
        ''')

        # 🆕 LAUDOS (PDFs de folhão finalizado) — antes ficavam SÓ no
        # localStorage de quem gerou o laudo (window.salvarLaudoNoHistorico
        # em script.js), então: 1) sumiam se a pessoa limpasse os dados do
        # navegador, e 2) nunca apareciam pra outro técnico em outro
        # aparelho, nem na Auditoria de ninguém além de quem gerou. Agora
        # o HTML completo do laudo é salvo no Neon, igual todo o resto do
        # sistema.
        # 🆕 CHECKLIST DE EXECUÇÃO — passo a passo REAL de como os técnicos
        # fazem o reparo (diferente do "Procedimento" oficial, que já
        # existe mas não reflete o passo a passo de verdade). Cada etapa
        # é cadastrada por EQUIPAMENTO específico (não por tipo genérico)
        # e pertence a uma seção/área (mecânica, elétrica, hidráulica,
        # caldeiraria, usinagem, tubulação, jato). "ordem" controla a
        # posição da etapa dentro da seção — dá pra reordenar e inserir
        # etapa esquecida no meio depois.
        # 🆕 EXECUÇÕES — 1 linha = 1 reparo real de 1 tag específica (ex:
        # M4-12, do dia 26/08). É isso que faltava: antes, "marcar uma
        # etapa" só sabia de qual ETAPA era, não de qual REPARO — o que
        # quebraria na hora de compartilhar as mesmas etapas entre vários
        # moldes do mesmo tipo (marcar no M4-12 ia aparecer marcado no
        # M4-15 também, por engano). Agora cada execução tem seu próprio
        # id, e as marcações ficam amarradas nele.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklist_execucao_execucoes (
                id SERIAL PRIMARY KEY,
                equipamento_id TEXT NOT NULL,
                tipo_equipamento TEXT NOT NULL,
                tipo_execucao TEXT NOT NULL,
                tecnico_matricula TEXT,
                tecnico_nome TEXT,
                iniciada_em TEXT,
                concluida_em TEXT,
                status TEXT DEFAULT 'em_andamento'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklist_execucao_etapas (
                id SERIAL PRIMARY KEY,
                equipamento_id TEXT NOT NULL,
                area TEXT NOT NULL,
                texto TEXT NOT NULL,
                ordem INTEGER DEFAULT 0,
                ativo BOOLEAN DEFAULT TRUE,
                criado_por TEXT,
                criado_em TEXT
            )
        ''')

        # Estado ATUAL de cada etapa (marcada ou não), agora 1 linha por
        # (execução, etapa) — não mais 1 linha por etapa sozinha. Isso é
        # o que permite a MESMA etapa (cadastrada uma vez pro tipo de
        # equipamento) ser marcada de forma independente em cada reparo.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklist_execucao_marcacoes (
                id SERIAL PRIMARY KEY,
                etapa_id INTEGER NOT NULL REFERENCES checklist_execucao_etapas(id) ON DELETE CASCADE,
                execucao_id INTEGER REFERENCES checklist_execucao_execucoes(id) ON DELETE CASCADE,
                equipamento_id TEXT NOT NULL,
                marcado BOOLEAN DEFAULT FALSE,
                colaborador TEXT,
                tecnico_matricula TEXT,
                tecnico_nome TEXT,
                data_hora TEXT,
                UNIQUE(etapa_id)
            )
        ''')

        # 🆕 Corrige a trava de unicidade: antes era só (etapa_id), o que
        # travava 1 marcação por etapa NO SISTEMA INTEIRO. Agora precisa
        # ser (execucao_id, etapa_id) — 1 marcação por etapa DENTRO DE
        # CADA reparo. O nome da constraint antiga segue o padrão padrão
        # do Postgres pra UNIQUE(coluna) numa CREATE TABLE.
        cursor.execute('''
            ALTER TABLE checklist_execucao_marcacoes
            DROP CONSTRAINT IF EXISTS checklist_execucao_marcacoes_etapa_id_key
        ''')
        cursor.execute('''
            ALTER TABLE checklist_execucao_marcacoes
            ADD COLUMN IF NOT EXISTS execucao_id INTEGER REFERENCES checklist_execucao_execucoes(id) ON DELETE CASCADE
        ''')
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS checklist_execucao_marcacoes_execucao_etapa_key
            ON checklist_execucao_marcacoes (execucao_id, etapa_id)
        ''')

        # Histórico de marcações/desmarcações — guarda TODO evento (não só
        # o estado atual), pra registrar retrabalho: se uma etapa marcada
        # foi desmarcada e refeita, fica tudo salvo aqui pra consulta.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklist_execucao_historico (
                id SERIAL PRIMARY KEY,
                etapa_id INTEGER NOT NULL REFERENCES checklist_execucao_etapas(id) ON DELETE CASCADE,
                equipamento_id TEXT NOT NULL,
                acao TEXT NOT NULL,
                colaborador TEXT,
                tecnico_matricula TEXT,
                tecnico_nome TEXT,
                data_hora TEXT
            )
        ''')

        # 🆕 PONTE COM O FOLHÃO — colunas aditivas, todas com valor
        # default NULL/'sim_nao'. Nenhuma etapa ou marcação já existente
        # muda de comportamento: elas simplesmente ficam com essas
        # colunas vazias até serem editadas pra usar a ponte.
        # - folhao_campo: id do campo no documento oficial (ex:
        #   "m4-aj-tfr") que essa etapa deve preencher sozinha.
        # - tipo_resposta: "sim_nao" (padrão, igual hoje) ou "medicao"
        #   (guarda um valor/número em vez de só marcado/desmarcado).
        cursor.execute('''
            ALTER TABLE checklist_execucao_etapas
            ADD COLUMN IF NOT EXISTS folhao_campo TEXT,
            ADD COLUMN IF NOT EXISTS tipo_resposta TEXT DEFAULT 'sim_nao'
        ''')

        # - valor: resposta de medição (torque, folga, etc.) — NULL pra
        #   etapas sim/não, que continuam usando só "marcado".
        # - trocado: só usado quando a execução é "parcial" — indica se
        #   ESSE item foi de fato trocado/interveio (True) ou só
        #   conferido/OK (False). NULL em execuções "geral".
        cursor.execute('''
            ALTER TABLE checklist_execucao_marcacoes
            ADD COLUMN IF NOT EXISTS valor TEXT,
            ADD COLUMN IF NOT EXISTS trocado BOOLEAN
        ''')

        # 🆕 Passo a passo de referência (o "como fazer" daquele tópico,
        # ex: régua -> talha -> parafusos -> retirar -> bancada). É texto
        # fixo, escrito 1 vez no cadastro — não é preenchido pelo técnico
        # na execução, é só consulta.
        cursor.execute('''
            ALTER TABLE checklist_execucao_etapas
            ADD COLUMN IF NOT EXISTS descricao TEXT
        ''')

        # 🆕 ESPECIALIDADE (mecanica/eletrica/hidraulica) — separada de
        # "area", que virou a ETAPA (chegada/manutencao/saida) pro Molde
        # MCC4. Antes disso, o Molde MCC4 migrou a maioria das etapas de
        # area="mecanica/eletrica/hidraulica" pra area="chegada/
        # manutencao/saida" pra bater com as novas abas — só que isso
        # jogou fora a informação de especialidade, deixando tudo
        # misturado numa lista só dentro de cada aba (era esse o motivo
        # de "elétrica não tem nada, hidráulica não tem nada": os itens
        # existiam, só não davam pra separar visualmente). Default
        # 'mecanica' porque é a maioria — etapas antigas sem classificação
        # nova continuam aparecendo (só que agrupadas como mecânica) em
        # vez de sumirem.
        cursor.execute('''
            ALTER TABLE checklist_execucao_etapas
            ADD COLUMN IF NOT EXISTS especialidade TEXT NOT NULL DEFAULT 'mecanica'
        ''')

        # 🆕 AVISO ENTRE ÁREAS — controla quais avisos ("Elétrica, se
        # prepara que a Mecânica tá terminando") já foram disparados,
        # pra não mandar push de novo a cada etapa marcada. 1 linha por
        # (execução, aba, área avisada) — UNIQUE trava duplicata mesmo
        # que dois técnicos marquem ao mesmo tempo.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklist_execucao_avisos_area (
                id SERIAL PRIMARY KEY,
                execucao_id INTEGER NOT NULL REFERENCES checklist_execucao_execucoes(id) ON DELETE CASCADE,
                aba TEXT NOT NULL,
                area_avisada TEXT NOT NULL,
                criado_em TEXT,
                UNIQUE(execucao_id, aba, area_avisada)
            )
        ''')

        # 🆕 ATIVIDADE EXTRA — registro de algo que aconteceu fora do
        # checklist padrão daquele tipo de equipamento (ex: precisou
        # envolver Caldeiraria ou Usinagem numa reparo que normalmente
        # não passa por elas). Fica gravado ligado à execução (pra
        # constar no histórico do reparo) e dispara push pra área
        # escolhida na hora do registro.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklist_execucao_atividades_extra (
                id SERIAL PRIMARY KEY,
                execucao_id INTEGER REFERENCES checklist_execucao_execucoes(id) ON DELETE CASCADE,
                equipamento_id TEXT NOT NULL,
                area TEXT NOT NULL,
                descricao TEXT NOT NULL,
                operador_matricula TEXT,
                operador_nome TEXT,
                criado_em TEXT
            )
        ''')
        # 🐛 CORRIGIDO ("registrei pra Caldeiraria e não chegou nada lá,
        # nem aparece de volta como concluído"): o registro de Atividade
        # Extra criava só uma linha "informativa" aqui, sem nunca virar
        # uma atividade DE VERDADE no quadro da área (oficina_atividades
        # — a mesma tela com Pendente/Em Andamento/Concluído que cada
        # área já usa). Essa coluna liga as duas: quando a área concluir
        # a atividade no quadro dela, o Checklist de Execução consegue
        # mostrar "Concluído" só fazendo join com oficina_atividades.
        cursor.execute('''
            ALTER TABLE checklist_execucao_atividades_extra
            ADD COLUMN IF NOT EXISTS oficina_atividade_id INTEGER REFERENCES oficina_atividades(id) ON DELETE SET NULL
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laudos (
                id SERIAL PRIMARY KEY,
                peca_id TEXT NOT NULL,
                tipo TEXT,
                html TEXT NOT NULL,
                criado_por TEXT,
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
            agora_seed = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
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


def _disparar_push_para_inscricoes(inscricoes, titulo: str, corpo: str, url: str, dados_extra: Optional[dict] = None):
    """Núcleo comum de envio — usado tanto por área (enviar_push_para_area)
    quanto por matrícula específica (enviar_push_para_matricula). Fica
    num lugar só pra não duplicar a limpeza de endpoint morto.

    🆕 `dados_extra` (tipo_evento, atividade_id, área...) vai junto no
    payload — é o que o Service Worker usa em `notificationclick` pra
    montar a URL certa (Conversa da Atividade vs Atividade destacada no
    quadro), o mesmo destino que o clique dentro da Central já usa. Sem
    isso, o SW só tinha `url` genérica ("/app.html#notificacoes") e
    nunca sabia pra qual atividade/conversa ir."""
    if not inscricoes:
        return
    corpo = limpar_texto_para_notificacao(corpo)
    titulo = limpar_texto_para_notificacao(titulo)
    payload_dict = {"titulo": titulo, "corpo": corpo, "url": url}
    if dados_extra:
        payload_dict.update({k: v for k, v in dados_extra.items() if v is not None})
    payload = json_lib.dumps(payload_dict)

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
                # 🔧 DIAGNÓSTICO TEMPORÁRIO: todo push vinha falhando com
                # "400 Bad Request" sem detalhe nenhum (str(e) não traz o
                # corpo da resposta do serviço de push) — impossível saber
                # se é chave VAPID errada, payload, ou outra coisa sem ver
                # o texto de verdade que o serviço respondeu.
                corpo_erro = None
                try:
                    corpo_erro = e.response.text if e.response is not None else None
                except Exception:
                    pass
                print(f"⚠️ Erro ao enviar push: {e} | status={getattr(e.response, 'status_code', '?')} | corpo={corpo_erro} | endpoint={inscricao['endpoint'][:60]}...")

    if endpoints_mortos:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM push_subscriptions WHERE endpoint = ANY(%s)",
                (endpoints_mortos,)
            )
            conn.commit()


def enviar_push_para_area(titulo: str, corpo: str, area: str = "Ambos", url: str = "/app.html#notificacoes", dados_extra: Optional[dict] = None):
    if not PUSH_HABILITADO:
        return
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if area == "Ambos":
                # Evento sem área da oficina associada (produção, OS,
                # ocorrência, peça pra Reserva, troca de equipamento...)
                # — só os administradores recebem, porque não dá pra
                # saber qual técnico deveria ser avisado.
                cursor.execute(
                    "SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE matricula = ANY(%s)",
                    (list(MATRICULAS_ADM),)
                )
                inscricoes = cursor.fetchall()
                _disparar_push_para_inscricoes(inscricoes, titulo, corpo, url, dados_extra)
            else:
                # Evento COM área da oficina (atividade nova/atrasada) —
                # administrador recebe sempre + quem tiver exatamente
                # essa área cadastrada.
                # 🐛 CORRIGIDO ("Concluído no equipamento não notifica
                # ninguém da área, só o ADM"): esta query usava
                # `colaboradores.area` — a MESMA coluna morta já
                # documentada em notificar_areas_extras_atividade_oficina
                # (nunca escrita por nenhuma rota, sempre no DEFAULT
                # 'Ambos'). Na prática, `c.area = %s` NUNCA batia com
                # nada, então todo push "por área" (atividade nova,
                # atrasada, mudança de status) só chegava pros 3 ADMs —
                # o técnico da área nunca recebia nada, silenciosamente.
                # A área de verdade do colaborador mora em
                # equipe_oficina (ver _buscar_area_colaborador).
                #
                # 🆕 Título do ADM ganha o prefixo da área de origem
                # ("[Caldeiraria] ..."): o ADM recebe TODA notificação de
                # TODAS as áreas misturadas, e o mesmo texto que já é
                # claro pro técnico da área (que só vê a própria área,
                # então já sabe de onde veio) virava uma parede de texto
                # sem contexto pro ADM. O técnico da área continua
                # recebendo o título original, sem prefixo redundante.
                cursor.execute(
                    "SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE matricula = ANY(%s)",
                    (list(MATRICULAS_ADM),)
                )
                inscricoes_adm = cursor.fetchall()
                cursor.execute("""
                    SELECT ps.endpoint, ps.p256dh, ps.auth
                    FROM push_subscriptions ps
                    JOIN equipe_oficina eo ON eo.matricula = ps.matricula AND eo.ativo = TRUE
                    WHERE eo.area = %s AND ps.matricula != ALL(%s)
                """, (area, list(MATRICULAS_ADM)))
                inscricoes_area = cursor.fetchall()

                nome_area_prefixo = NOME_AREA_PUSH.get(area) or AREA_OFICINA_NOMES.get(area) or area
                titulo_adm = f"[{nome_area_prefixo}] {titulo}"
                _disparar_push_para_inscricoes(inscricoes_adm, titulo_adm, corpo, url, dados_extra)
                _disparar_push_para_inscricoes(inscricoes_area, titulo, corpo, url, dados_extra)
    except Exception as e:
        print(f"⚠️ Falha geral ao processar envio de push: {e}")


# 🆕 Avisa UMA pessoa específica (não a área toda) — usado quando a
# área Recusa ou coloca "Aguardando" numa atividade: quem PEDIU (o
# técnico do Checklist de Execução, via solicitante_matricula) precisa
# saber o motivo, não a área inteira de novo.
def enviar_push_para_matricula(matricula: str, titulo: str, corpo: str, url: str = "/app.html#notificacoes", dados_extra: Optional[dict] = None):
    if not PUSH_HABILITADO or not matricula:
        return
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE matricula = %s",
                (matricula,)
            )
            inscricoes = cursor.fetchall()
        _disparar_push_para_inscricoes(inscricoes, titulo, corpo, url, dados_extra)
    except Exception as e:
        print(f"⚠️ Falha geral ao processar envio de push (matrícula): {e}")


# 🆕 Registro PERSISTENTE de toda ação numa atividade da Oficina (criar,
# mudar status, editar, excluir, mandar mensagem) — pediu explicitamente
# que TODA ação gere notificação na Central. Antes só existia o push
# (enviar_push_para_area/matricula), que é efêmero: se ninguém estava
# com o app aberto/inscrito naquele segundo, a ação simplesmente
# desaparecia sem deixar rastro na Central de Notificações. Grava em
# log_eventos com categoria='Atividade Oficina' — uma categoria PRÓPRIA
# (não usa a mesma de Ocorrência) porque tem query e navegação dedicadas
# no feed (ver /api/notificacoes/feed, tipo 'atividade').
# Mesmo padrão de robustez do evento de mancal do Sinótico 3D: nunca
# deve derrubar a ação principal (que já foi commitada antes de chamar
# isso), só registra o log num try/except separado.
def registrar_evento_atividade_oficina(operador: str, area: str, peca_id: Optional[str], acao: str, atividade_id: Optional[int] = None, tipo_evento: str = "status"):
    """`tipo_evento` diz pro front-end pra onde o clique na notificação
    deve levar: 'mensagem' (Conversa da Atividade) ou 'status'/'criacao'/
    'edicao' (a Atividade em si) — ver comentário da coluna tipo_evento
    em log_eventos. Default 'status' porque é o caso mais comum
    (mudar_status_atividade_oficina, atraso automático)."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, categoria, area, atividade_id, tipo_evento) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (agora_brasil().strftime("%Y-%m-%d %H:%M:%S"), operador or "Sistema", peca_id, acao, "Atividade Oficina", area, atividade_id, tipo_evento)
            )
            conn.commit()
    except Exception as e:
        print(f"⚠️ Falha ao registrar evento de Atividade da Oficina na Central de Notificações: {e}")


def _buscar_area_origem_checklist_extra(cursor, oficina_atividade_id: Optional[int]):
    """Se essa atividade nasceu de um 'Registrar Atividade Extra' num
    Checklist de Execução, devolve a área de ORIGEM — o equipamento que
    estava sendo executado (ex: 'molde-mcc4') — e não a área DESTINO
    (quem vai executar a atividade extra, ex: 'caldeiraria'). None se a
    atividade foi criada direto no quadro de uma área (sem checklist
    por trás) — aí não tem 'origem' nenhuma pra notificar."""
    if not oficina_atividade_id:
        return None
    cursor.execute(
        """
        SELECT ce.tipo_equipamento
        FROM checklist_execucao_atividades_extra cea
        JOIN checklist_execucao_execucoes ce ON ce.id = cea.execucao_id
        WHERE cea.oficina_atividade_id = %s
        """,
        (oficina_atividade_id,)
    )
    linha = cursor.fetchone()
    return linha["tipo_equipamento"] if linha else None


# 🐛 CORREÇÃO ("líder da Caldeiraria respondeu, ninguém do lado de quem
# pediu viu nada"): registrar_evento_atividade_oficina acima sempre
# grava sob a ÁREA DONA da atividade (quem vai EXECUTAR — ex:
# Caldeiraria). Certo pra Caldeiraria/ADM verem, mas isso não basta:
#   1) Quem PEDIU (solicitante_matricula) tem a própria Central
#      restrita à SUA área (ver operadorTecnicoComArea no front) — um
#      evento só sob "caldeiraria" nunca aparece pra ele.
#   2) Se o pedido nasceu de um "Registrar Atividade Extra" num
#      Checklist de Execução, o solicitante gravado é só quem clicou
#      no botão NAQUELE momento — podia até ser um ADM testando, sem
#      área própria nenhuma (não aparece em equipe_oficina). O resto da
#      equipe da área de ORIGEM do checklist (ex: outros técnicos do
#      Molde MCC4) também precisa saber, não só esse indivíduo.
# Por isso notifica as DUAS áreas extras (solicitante + origem do
# checklist), sem duplicar quando coincidem entre si ou com a área dona.
def notificar_areas_extras_atividade_oficina(oficina_atividade_id: Optional[int], solicitante_matricula: Optional[str], area_dona: str, peca_id: Optional[str], acao: str, operador: Optional[str], tipo_evento: str = "status"):
    areas_extras = set()
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if solicitante_matricula:
                # 🐛 CORRIGIDO ("segunda mensagem, ainda não apareceu"): a
                # primeira versão buscava em colaboradores.area — coluna
                # que NUNCA é escrita por nenhuma rota deste backend
                # (fica parada no DEFAULT 'Ambos' pra todo mundo). A área
                # de verdade do colaborador mora em equipe_oficina (mesma
                # tabela que o login usa via _buscar_area_colaborador).
                area_sol = _buscar_area_colaborador(cursor, solicitante_matricula)
                if area_sol:
                    areas_extras.add(area_sol)
            area_origem = _buscar_area_origem_checklist_extra(cursor, oficina_atividade_id)
            if area_origem:
                areas_extras.add(area_origem)
    except Exception as e:
        print(f"⚠️ Falha ao buscar áreas extras pra notificar (atividade {oficina_atividade_id}): {e}")
        return
    # "Ambos"/vazio = sem área própria de verdade (ADM, ou matrícula não
    # cadastrada em equipe_oficina) — não sobra nada útil pra duplicar.
    areas_extras.discard(area_dona)
    areas_extras.discard("Ambos")
    for area in areas_extras:
        registrar_evento_atividade_oficina(operador=operador, area=area, peca_id=peca_id, acao=acao, atividade_id=oficina_atividade_id, tipo_evento=tipo_evento)


class PecaUpdate(BaseModel):
    id: str
    tipo: Optional[str] = None
    mcc_compat: Optional[str] = None  # 🆕 "2/3" ou "4" — agora persistido de verdade
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
    barra_transversal: Optional[str] = None
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

# 🆕 registrarHistorico() no front-end usa peca_id como uma "tag" pra
# ações de sessão/administrativas que não são de um equipamento real
# (ver comentário em registrar_evento) — essas nunca viram notificação
# nem aparecem no feed da Central, só ficam na Auditoria.
TAGS_AUDITORIA_SEM_NOTIFICACAO = ("AUTENTICAÇÃO", "SISTEMA")

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
    operador: Optional[str] = None

class HidraulicaAjuste(BaseModel):
    id: str
    local: str
    fator: float
    operador: Optional[str] = None

class PushSubscribe(BaseModel):
    matricula: str
    endpoint: str
    p256dh: str
    auth: str

class PushUnsubscribe(BaseModel):
    endpoint: str

class NotificacaoMarcarLida(BaseModel):
    tipo: str       # "evento" | "os" | "achado" | "estoque"
    evento_id: str
    matricula: str

class RegistroComFoto(BaseModel):
    peca_id: str
    acao: str
    operador: str
    categoria: str
    foto_base64: Optional[str] = None
    area: Optional[str] = None  # 🆕 chave de AREAS_OFICINA, ex: "hidraulica" — opcional


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
    data_inicio: Optional[str] = None  # data no formato "YYYY-MM-DD", opcional — quando futura, a atividade fica "programada"
    # 🆕 Matrícula de quem PEDIU essa atividade (não quem vai executar).
    # Só vem preenchido quando a atividade nasce de um "Registrar
    # Atividade Extra" no Checklist de Execução — é pra ELE que a área
    # avisa se Recusar ou colocar "Aguardando" com motivo.
    solicitante_matricula: Optional[str] = None


class OficinaStatus(BaseModel):
    id: int
    status: str  # "Pendente" | "Em Andamento" | "Concluído" | "Aguardando" | "Recusado"
    # 🆕 Obrigatório (no front) quando status vira "Aguardando" ou
    # "Recusado" — não dá pra só "passar por cima" de uma atividade
    # sem dizer por que não iniciou ou por que travou.
    motivo: Optional[str] = None
    # 🆕 Opcional pra não quebrar cliente antigo — usado só pra assinar o
    # registro na Central de Notificações (ver registrar_evento_
    # atividade_oficina); "Sistema" quando não vier.
    operador: Optional[str] = None
    # 🆕 Quem de fato vai EXECUTAR a atividade a partir de "Em Andamento"
    # — pode ser mais de um nome (mesmo modal de seleção de colaboradores
    # do Checklist de Execução, front manda os nomes já juntados numa
    # string tipo "Fulano, Ciclano"). Diferente de `operador` (sempre o
    # técnico logado que clicou o botão, usado pra assinar o log) —
    # `colaboradores` é quem realmente pegou o serviço, podendo ser um
    # grupo. Opcional: se não vier, cai no comportamento antigo (usa o
    # próprio `operador` como executor).
    colaboradores: Optional[str] = None
    # 🆕 Reabertura de atividade Concluída (volta pra "Em Andamento"):
    # marca essa transição como reabertura pra exigir motivo e gerar um
    # tipo_evento próprio na Central ("reabertura"), diferente de um
    # Iniciar normal. Sem isso, `motivo` continuaria opcional pra
    # qualquer "Em Andamento" — ver validação abaixo.
    reabertura: Optional[bool] = None


class OficinaExcluir(BaseModel):
    id: int
    # 🆕 Mesma ideia do OficinaStatus.operador acima — opcional.
    operador: Optional[str] = None


class OficinaAtividadeMensagem(BaseModel):
    atividade_id: int
    autor_matricula: Optional[str] = None
    autor_nome: str
    mensagem: str


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


class ChecklistExecucaoEtapaNova(BaseModel):
    # 🆕 IMPORTANTE: a partir de agora, equipamento_id aqui guarda o TIPO
    # de equipamento (ex: "molde-mcc4"), não mais uma tag específica (ex:
    # "M4-12"). Assim a mesma etapa vale pra TODO equipamento daquele
    # tipo, em vez de precisar recadastrar tudo pra cada peça nova.
    equipamento_id: str
    area: str
    texto: str
    operador: str  # matrícula de quem está cadastrando (checado contra ADM)
    # 🆕 Especialidade de quem executa (mecanica/eletrica/hidraulica) —
    # independente da "area" (que agora é a etapa: chegada/manutencao/
    # saida pro Molde MCC4). Permite sub-agrupar dentro de cada etapa.
    especialidade: str = "mecanica"
    # 🆕 Ponte com o Folhão: id do campo no documento oficial (ex:
    # "m4-aj-tfr") pro qual essa etapa deve jogar o valor automaticamente.
    # Opcional — etapa sem isso continua funcionando igual, só não
    # preenche folhão nenhum sozinha.
    folhao_campo: Optional[str] = None
    # 🆕 Que tipo de resposta essa etapa espera: "sim_nao" (padrão,
    # comportamento atual), "medicao" (1 valor só) ou "medicao_multipla"
    # (várias medidas de uma vez, tipo a tabela de Folga Aresta).
    tipo_resposta: str = "sim_nao"
    # 🆕 Passo a passo de referência (o "como fazer"), pra quando o
    # técnico quiser consultar o detalhe. Não é preenchido na hora da
    # execução — é texto fixo, escrito 1 vez no cadastro da etapa.
    descricao: Optional[str] = None


class ChecklistExecucaoIniciar(BaseModel):
    # 🆕 Início de uma EXECUÇÃO — 1 reparo real de 1 tag específica.
    # É esse id (execucao_id) que vai amarrar cada marcação ao reparo
    # certo, mesmo que as etapas sejam compartilhadas com outras peças
    # do mesmo tipo.
    equipamento_id: str        # tag específica, ex: "M4-12"
    tipo_equipamento: str      # ex: "molde-mcc4" — de onde vêm as etapas
    tipo_execucao: str         # "geral" ou "parcial"
    tecnico_matricula: Optional[str] = None
    tecnico_nome: str


class ChecklistExecucaoFinalizar(BaseModel):
    execucao_id: int


class ChecklistExecucaoEtapaEditar(BaseModel):
    id: int
    texto: str
    operador: str
    # 🆕 Corrige a "ponte com o Folhão" de uma etapa já criada, sem
    # precisar apagar e recadastrar (o que perderia o histórico de quem
    # já marcou/preencheu essa etapa nas execuções em andamento).
    # Opcionais: None = não mexe no que já estava salvo.
    folhao_campo: Optional[str] = None
    tipo_resposta: Optional[str] = None
    # 🆕 Move a etapa de bloco/seção (ex: "mecanica" -> "chegada", pro
    # Molde MCC4 que passou a usar Chegada/Manutenção/Saída em vez das
    # seções genéricas). Mesma lógica: None = não mexe na área atual.
    area: Optional[str] = None
    # 🆕 Especialidade (mecanica/eletrica/hidraulica) — None = não mexe.
    especialidade: Optional[str] = None


class ChecklistExecucaoEtapaExcluir(BaseModel):
    id: int
    operador: str


class ChecklistExecucaoEtapaReordenarItem(BaseModel):
    id: int
    ordem: int


class ChecklistExecucaoReordenar(BaseModel):
    itens: list[ChecklistExecucaoEtapaReordenarItem]
    operador: str


class ChecklistExecucaoMarcar(BaseModel):
    etapa_id: int
    execucao_id: int  # 🆕 substitui equipamento_id como chave da marcação
    equipamento_id: str  # mantido pra consulta/histórico rápido (tag)
    marcado: bool
    colaborador: Optional[str] = None  # quem realmente executou a etapa
    tecnico_matricula: Optional[str] = None
    tecnico_nome: str
    # 🆕 Pra etapas de medição (tipo_resposta = "medicao"): o valor
    # digitado (ex: "298" pro torque). Fica NULL pras etapas sim/não,
    # que continuam usando só o "marcado".
    valor: Optional[str] = None
    # 🆕 Só relevante quando a execução é "parcial": marca se ESSE item
    # específico foi trocado/interveio (True) ou só conferido/OK
    # (False). Em execução "geral" não precisa mandar isso — o backend
    # assume tudo como trocado.
    trocado: Optional[bool] = None


class ChecklistExecucaoAtividadeExtra(BaseModel):
    # 🆕 Registro de algo fora do checklist padrão (ex: precisou
    # envolver Caldeiraria ou Usinagem num reparo de Molde).
    execucao_id: int
    equipamento_id: str
    area: str  # chave da área (mecanica/eletrica/hidraulica/caldeiraria/usinagem/tubulacao/jato)
    descricao: str
    operador_matricula: Optional[str] = None
    operador_nome: str


class ChecklistExecucaoAtividadeExtraExcluir(BaseModel):
    id: int  # id da linha em checklist_execucao_atividades_extra (não o da oficina_atividades)


class OficinaAtividadeEditar(BaseModel):
    id: int
    equipamento_id: Optional[str] = None
    descricao: str
    responsavel: Optional[str] = None
    prioridade: Optional[str] = "Normal"
    prazo: Optional[str] = None
    data_inicio: Optional[str] = None
    foto_base64: Optional[str] = None  # null = sem foto anexada / mantém a que já tinha, ver rota
    # 🆕 Mesma ideia do OficinaStatus.operador — opcional.
    operador: Optional[str] = None


class OrdemServicoCriar(BaseModel):
    numero_os: Optional[str] = None
    descricao: Optional[str] = None
    fotos_base64: list[str] = []  # 1 OS pode ter várias páginas/fotos
    operador: str
    area: Optional[str] = None  # 🆕 chave de AREAS_OFICINA, ex: "hidraulica" — opcional


class OrdemServicoStatus(BaseModel):
    id: int
    status: str  # "Em Andamento" | "Concluído" | "Não Executada"
    operador: str
    motivo: Optional[str] = None  # obrigatório quando status = "Não Executada"


class OrdemServicoExcluir(BaseModel):
    id: int


class QualidadeAchadoInput(BaseModel):
    descricao: str
    fotos_base64: list[str] = []  # 🆕 um achado pode ter mais de 1 foto


class QualidadeCriar(BaseModel):
    peca_id: str
    observacao_entrada: Optional[str] = None
    fotos_entrada_base64: list[str] = []  # 1 registro pode ter várias fotos de entrada
    achados: list[QualidadeAchadoInput] = []  # problemas já encontrados na inspeção de entrada
    operador: str


class QualidadeSaida(BaseModel):
    observacao_saida: Optional[str] = None
    fotos_saida_base64: list[str] = []
    operador: str


class QualidadeExcluir(BaseModel):
    id: int


class QualidadeAchadoCriar(BaseModel):
    registro_id: int
    descricao: str
    fotos_base64: list[str] = []  # 🆕 um achado pode ter mais de 1 foto
    operador: str


class QualidadeAchadoEditar(BaseModel):
    id: int
    descricao: str
    operador: str


class QualidadeAchadoResolver(BaseModel):
    id: int
    foto_base64: Optional[str] = None
    operador: str


class QualidadeAchadoExcluir(BaseModel):
    id: int


class LaudoCriar(BaseModel):
    peca_id: str
    tipo: Optional[str] = None
    html: str
    operador: str


class LaudoExcluir(BaseModel):
    id: int



# Matrículas com acesso total a todas as áreas da Oficina (ADM). As
# outras matrículas só enxergam a própria área, vinda de equipe_oficina
# (ver AREA_OFICINA_NOMES acima e o mapeamento em
# importar_efetivo_oficina.py). Mesmo padrão já usado no front-end para
# MATRICULAS_TESTE_FOLHOES, em script.js.
MATRICULAS_ADM = ("CBK3574", "CSP1869", "CSP6632")

# 🆕 Nome legível de cada área — usado nas notificações push (aviso
# entre áreas e atividade extra), pra não mandar a chave crua
# ("eletrica") na mensagem. Mesmas chaves de CHECKLIST_EXECUCAO_SECOES
# no front-end (dados.js) — mantenha as duas listas em sincronia.
NOME_AREA_PUSH = {
    "mecanica": "Mecânica",
    "eletrica": "Elétrica",
    "hidraulica": "Hidráulica",
    "caldeiraria": "Caldeiraria",
    "usinagem": "Usinagem",
    "tubulacao": "Tubulação",
    "jato": "Jato/Pintura",
}


def _buscar_area_colaborador(cursor, matricula):
    """Busca a área do colaborador em equipe_oficina. Retorna None se a
    matrícula não estiver cadastrada lá (login e área vêm de planilhas
    diferentes — ver importar_colaboradores.py x
    importar_efetivo_oficina.py). None é tratado no front-end como
    'sem área definida ainda', não como erro."""
    cursor.execute(
        "SELECT area FROM equipe_oficina WHERE matricula = %s AND ativo = TRUE",
        (matricula,)
    )
    linha = cursor.fetchone()
    return linha["area"] if linha else None