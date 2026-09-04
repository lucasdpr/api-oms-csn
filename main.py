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


tags_metadata = [
    {"name": "Sistema", "description": "Verificações de saúde do servidor e do banco de dados."},
    {"name": "Peças", "description": "Cadastro, edição, exclusão e histórico de fotos das peças/equipamentos."},
    {"name": "Produção", "description": "Apontamento de produção geral e de moldes, com histórico e opção de desfazer."},
    {"name": "Auditoria", "description": "Registro de eventos e consulta do histórico completo de ações do sistema."},
    {"name": "Colaboradores", "description": "Login, cadastro, cargo e controle de acesso dos colaboradores."},
    {"name": "Materiais (Estoque Geral)", "description": "Estoque geral de materiais (cadastro, ajuste de quantidade, remoção)."},
    {"name": "Rolos", "description": "Estoque de rolos."},
    {"name": "Hidráulica", "description": "Estoque hidráulico."},
    {"name": "Folhões", "description": "Rascunho de progresso dos folhões de manutenção (salvar, carregar, finalizar)."},
    {"name": "Notificações Push", "description": "Inscrição e envio de notificações push (Web Push / VAPID)."},
    {"name": "Registros e Ocorrências", "description": "Intervenções, melhorias, comentários e ocorrências registradas com foto."},
    {"name": "Oficina", "description": "Atividades, materiais por área, equipe, notas e procedimentos de cada área da Oficina."},
    {"name": "Ordens de Serviço (OS)", "description": "Registro digital de OS em papel (foto por página) com status Em Andamento / Concluído / Não Executada."},
    {"name": "Laudos", "description": "Laudos (PDFs) gerados ao finalizar um folhão."},
]

app = FastAPI(
    title="API - Oficina de Moldes CSN",
    description="Backend do sistema OMS (Oficina de Moldes e Segmentos) da CSN — gerencia peças, produção, "
                 "oficina, colaboradores e ordens de serviço, com persistência no PostgreSQL (Neon).",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

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


def _disparar_push_para_inscricoes(inscricoes, titulo: str, corpo: str, url: str):
    """Núcleo comum de envio — usado tanto por área (enviar_push_para_area)
    quanto por matrícula específica (enviar_push_para_matricula). Fica
    num lugar só pra não duplicar a limpeza de endpoint morto."""
    if not inscricoes:
        return
    corpo = limpar_texto_para_notificacao(corpo)
    titulo = limpar_texto_para_notificacao(titulo)
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


def enviar_push_para_area(titulo: str, corpo: str, area: str = "Ambos", url: str = "/app.html#notificacoes"):
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
            else:
                # Evento COM área da oficina (atividade nova/atrasada) —
                # administrador recebe sempre + quem tiver exatamente
                # essa área cadastrada.
                cursor.execute("""
                    SELECT ps.endpoint, ps.p256dh, ps.auth
                    FROM push_subscriptions ps
                    JOIN colaboradores c ON c.matricula = ps.matricula
                    WHERE c.matricula = ANY(%s) OR c.area = %s
                """, (list(MATRICULAS_ADM), area))
            inscricoes = cursor.fetchall()
        _disparar_push_para_inscricoes(inscricoes, titulo, corpo, url)
    except Exception as e:
        print(f"⚠️ Falha geral ao processar envio de push: {e}")


# 🆕 Avisa UMA pessoa específica (não a área toda) — usado quando a
# área Recusa ou coloca "Aguardando" numa atividade: quem PEDIU (o
# técnico do Checklist de Execução, via solicitante_matricula) precisa
# saber o motivo, não a área inteira de novo.
def enviar_push_para_matricula(matricula: str, titulo: str, corpo: str, url: str = "/app.html#notificacoes"):
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
        _disparar_push_para_inscricoes(inscricoes, titulo, corpo, url)
    except Exception as e:
        print(f"⚠️ Falha geral ao processar envio de push (matrícula): {e}")


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


class OficinaExcluir(BaseModel):
    id: int


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


@app.get("/api/pecas", tags=["Peças"], summary="Listar todas as peças")
def get_pecas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipamentos")
        return cursor.fetchall()


@app.post("/api/atualizar_peca", tags=["Peças"], summary="Cadastrar ou atualizar uma peça")
def atualizar_peca(peca: PecaUpdate):
    campos = []
    valores = []

    if peca.tipo is not None:
        campos.append("tipo = %s"); valores.append(peca.tipo)
    if peca.mcc_compat is not None:
        campos.append("mcc_compat = %s"); valores.append(peca.mcc_compat)
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
    if peca.barra_transversal is not None:
        campos.append("barra_transversal = %s"); valores.append(peca.barra_transversal)

    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar foi enviado.")

    valores.append(peca.id)
    query = f"UPDATE equipamentos SET {', '.join(campos)} WHERE id = %s"

    with get_db() as conn:
        cursor = conn.cursor()

        # 🆕 Busca o estado ANTES da atualização, só pra poder comparar
        # depois e saber se o status mudou pra "Reserva" ou se a peça foi
        # trocada (substituido_por passou a ter valor) — sem isso, toda
        # edição de peça pareceria uma troca/movimentação nova.
        cursor.execute("SELECT status, substituido_por FROM equipamentos WHERE id = %s", (peca.id,))
        estado_anterior = cursor.fetchone()
        status_anterior = estado_anterior["status"] if estado_anterior else None
        substituido_por_anterior = estado_anterior["substituido_por"] if estado_anterior else None

        cursor.execute(query, tuple(valores))
        criada = False

        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO equipamentos (id, tipo, mcc_compat, local, status, tonelagem, dias, meta, posicao, tag_patrimonio, data_entrada, data_reparo, substituido_por, observacao, rolos_travados, mancais_ocorrencias, barra_transversal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    tipo = EXCLUDED.tipo,
                    mcc_compat = EXCLUDED.mcc_compat,
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
                    mancais_ocorrencias = EXCLUDED.mancais_ocorrencias,
                    barra_transversal = EXCLUDED.barra_transversal
            ''', (
                peca.id, peca.tipo or "", peca.mcc_compat or "", peca.local or "", peca.status or "",
                peca.tonelagem or 0, peca.dias or 0, peca.meta or 0, peca.posicao or "",
                peca.tag_patrimonio, peca.data_entrada, peca.data_reparo,
                peca.substituido_por, peca.observacao, peca.rolos_travados, peca.mancais_ocorrencias,
                peca.barra_transversal
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
        # 🆕 Grava em log_eventos com area="sinotico-3d" pra aparecer
        # como área própria na Central de Notificações (antes só virava
        # push — nunca ficava registrado em lugar nenhum que o feed
        # olhasse, por isso "faltou o Sinótico 3D" na Central).
        with get_db() as conn2:
            cursor2 = conn2.cursor()
            cursor2.execute(
                "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, categoria, area) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (agora_brasil().strftime("%Y-%m-%d %H:%M:%S"), "Sinótico 3D", peca.id,
                 peca.mancal_evento_corpo, None, "sinotico-3d")
            )
            conn2.commit()

    # 🆕 Notificação quando a peça vai (ou passa a ir) pra Reserva —
    # só dispara na TROCA de status, não toda vez que alguém salva a
    # peça já estando em Reserva.
    if peca.status is not None and peca.status != status_anterior and peca.status.strip().lower() == "reserva":
        enviar_push_para_area(
            titulo="📦 Equipamento movido pra Reserva",
            corpo=f"{peca.id} ({peca.tipo or 'equipamento'}) foi movido pro Estoque Reserva.",
            area="Ambos"
        )

    # 🆕 Notificação de troca de peça — dispara quando o campo
    # substituido_por passa a ter um valor novo (ou muda de valor),
    # indicando que essa peça foi substituída por outra.
    if peca.substituido_por is not None and peca.substituido_por.strip() and peca.substituido_por != substituido_por_anterior:
        enviar_push_para_area(
            titulo="🔁 Troca de equipamento",
            corpo=f"{peca.id} foi substituído por {peca.substituido_por}.",
            area="Ambos"
        )

    return {"sucesso": True, "criada": criada}


@app.post("/api/excluir_peca", tags=["Peças"], summary="Excluir uma peça")
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


@app.post("/api/apontar_producao_geral", tags=["Produção"], summary="Apontar produção (geral)")
def apontar_producao_geral(dados: ProducaoGeral):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")

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


@app.post("/api/apontar_moldes", tags=["Produção"], summary="Apontar produção de moldes")
def apontar_moldes(dados: ApontamentoMoldes):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")

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


@app.get("/api/historico_apontamentos_geral", tags=["Produção"], summary="Histórico de apontamentos (geral)")
def get_historico_geral():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_apontamento_geral ORDER BY id DESC LIMIT 50")
        return cursor.fetchall()


@app.get("/api/historico_apontamentos_moldes", tags=["Produção"], summary="Histórico de apontamentos de moldes")
def get_historico_moldes():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_apontamento_moldes ORDER BY id DESC LIMIT 50")
        return cursor.fetchall()


@app.post("/api/desfazer_apontamento_geral", tags=["Produção"], summary="Desfazer apontamento (geral)")
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


@app.post("/api/desfazer_apontamento_moldes", tags=["Produção"], summary="Desfazer apontamento de moldes")
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


@app.get("/", tags=["Sistema"], summary="Verificar se o servidor está no ar")
def root():
    return {"message": "API - Oficina de Moldes CSN Online!"}


@app.get("/api/ping_db", tags=["Sistema"], summary="Verificar conexão com o banco de dados")
def ping_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return {"status": "ok", "banco": "acordado"}


@app.post("/api/registrar_evento", tags=["Auditoria"], summary="Registrar um evento na Auditoria")
def registrar_evento(evento: EventoLog):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao) VALUES (%s, %s, %s, %s)",
            (agora, evento.operador, evento.peca_id, evento.acao)
        )
        conn.commit()

    # 🔧 CORREÇÃO ("não quero notificação de login" + Central de
    # Notificações "mudando toda hora"): registrarHistorico() no
    # front-end reaproveita esse mesmo endpoint pra ações de sessão
    # (login, logout, acesso visitante) usando peca_id como uma tag
    # genérica, não um equipamento de verdade. Isso disparava push E
    # entrava na Central toda vez que QUALQUER PESSOA logava — puro
    # ruído, sem nenhuma ação real da oficina por trás. Essas tags
    # continuam gravadas em log_eventos (auditoria não perde nada),
    # só não viram notificação nem aparecem no feed (ver
    # /api/notificacoes/feed).
    if evento.peca_id not in TAGS_AUDITORIA_SEM_NOTIFICACAO:
        PALAVRAS_CRITICAS = ["b.o", "blackout", "quebra", "fim de vida", "alarme"]
        is_critico = any(p in evento.acao.lower() for p in PALAVRAS_CRITICAS)

        enviar_push_para_area(
            titulo="🚨 Evento crítico" if is_critico else "📋 Registro no equipamento",
            corpo=f"{evento.operador} — {evento.peca_id}: {evento.acao}",
            area="Mecânico" if is_critico else "Ambos"
        )

    return {"sucesso": True}


@app.get("/api/historico_eventos", tags=["Auditoria"], summary="Consultar o histórico completo de eventos")
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


@app.get("/api/colaboradores", tags=["Colaboradores"], summary="Listar colaboradores ativos")
def get_colaboradores():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, primeiro_acesso FROM colaboradores WHERE ativo = TRUE ORDER BY nome"
        )
        return cursor.fetchall()


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


@app.post("/api/colaboradores/login", tags=["Colaboradores"], summary="Autenticar colaborador (login)")
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

        is_adm = matricula in MATRICULAS_ADM
        # ADM não depende de equipe_oficina — acesso total sempre.
        area = None if is_adm else _buscar_area_colaborador(cursor, matricula)

        if colaborador["primeiro_acesso"]:
            if dados.senha.strip().upper() != matricula:
                raise HTTPException(status_code=401, detail="No primeiro acesso, a senha é a sua própria matrícula.")
            return {
                "sucesso": True,
                "nome": colaborador["nome"],
                "cargo": colaborador["cargo"],
                "area": area,
                "is_adm": is_adm,
                "precisa_definir_senha": True
            }

        if not colaborador["senha_hash"] or not bcrypt.checkpw(dados.senha.encode(), colaborador["senha_hash"].encode()):
            raise HTTPException(status_code=401, detail="Senha incorreta.")

        return {
            "sucesso": True,
            "nome": colaborador["nome"],
            "cargo": colaborador["cargo"],
            "area": area,
            "is_adm": is_adm,
            "precisa_definir_senha": False
        }


@app.post("/api/colaboradores/definir_senha", tags=["Colaboradores"], summary="Definir senha no primeiro acesso")
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
@app.get("/api/colaboradores/todos", tags=["Colaboradores"], summary="Listar todos os colaboradores (ativos e inativos)")
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


@app.post("/api/colaboradores/mudar_cargo", tags=["Colaboradores"], summary="Trocar o cargo de um colaborador")
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


@app.post("/api/colaboradores/alternar_ativo", tags=["Colaboradores"], summary="Ativar ou desativar acesso de um colaborador")
def alternar_ativo_colaborador(dados: ColaboradorAlternarAtivo):
    matricula = dados.matricula.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE colaboradores SET ativo = %s WHERE matricula = %s", (dados.ativo, matricula))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
        conn.commit()

    return {"sucesso": True, "ativo": dados.ativo}


@app.post("/api/colaboradores/resetar_senha", tags=["Colaboradores"], summary="Resetar senha de um colaborador")
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


@app.get("/api/materiais", tags=["Materiais (Estoque Geral)"], summary="Listar materiais do estoque geral")
def get_materiais():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE ativo = TRUE ORDER BY descricao"
        )
        return cursor.fetchall()


@app.post("/api/materiais/cadastrar", tags=["Materiais (Estoque Geral)"], summary="Cadastrar novo material")
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


@app.post("/api/materiais/ajustar", tags=["Materiais (Estoque Geral)"], summary="Ajustar quantidade de um material")
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

        qtd_anterior = material["qtd"]

        cursor.execute(
            "UPDATE materiais SET qtd = qtd + %s WHERE codigo = %s",
            (dados.fator, codigo)
        )
        cursor.execute("SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE codigo = %s", (codigo,))
        atualizado = cursor.fetchone()
        conn.commit()

    # 🆕 Estoque zerando não avisava ninguém — só se percebia abrindo o
    # Almoxarifado manualmente. Notifica só na transição pra zero (não
    # dispara de novo a cada ajuste feito enquanto já está zerado).
    if qtd_anterior > 0 and atualizado["qtd"] <= 0:
        enviar_push_para_area(
            titulo="📦 Estoque zerado",
            corpo=f"{atualizado['descricao']} ({codigo}) chegou a zero no Almoxarifado.",
            area="Ambos"
        )

    return {"sucesso": True, "material": atualizado}


@app.post("/api/materiais/remover", tags=["Materiais (Estoque Geral)"], summary="Remover um material do estoque")
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


@app.get("/api/rolos", tags=["Rolos"], summary="Listar estoque de rolos")
def get_rolos():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rolos ORDER BY conjunto, nome")
        return cursor.fetchall()


@app.post("/api/rolos/ajustar", tags=["Rolos"], summary="Ajustar estoque de rolos")
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

        # 🆕 "vai ter que colocar rolos, hidráulica tanto a área e tando o
        # estoque pq se for atualizado gera notificação" — grava com uma
        # tag própria (não mais via registrarHistorico do front-end, que
        # usava "ALMOXARIFADO" pra tudo e nunca aparecia na Central de
        # Notificações) pra dar pra filtrar certinho em
        # /api/notificacoes/feed.
        agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
        operador = dados.operador or "Sistema"
        sinal = "+" if dados.fator >= 0 else ""
        acao = f"Ajuste de estoque — {atualizado.get('nome', dados.id)}: {sinal}{dados.fator:g} (saldo atual: {atualizado['qtd']:g})"
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, area) VALUES (%s, %s, %s, %s, %s)",
            (agora, operador, "ESTOQUE-ROLOS", acao, "rolos")
        )
        conn.commit()

    enviar_push_para_area(titulo="🧵 Estoque de Rolos ajustado", corpo=f"{operador} — {acao}", area="Ambos")

    return {"sucesso": True, "rolo": atualizado}


@app.get("/api/hidraulica", tags=["Hidráulica"], summary="Listar estoque hidráulico")
def get_hidraulica():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hidraulica ORDER BY mcc_compat, conjunto, nome")
        return cursor.fetchall()


@app.post("/api/hidraulica/ajustar", tags=["Hidráulica"], summary="Ajustar estoque hidráulico")
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

        # 🆕 Mesma ideia do ajuste de Rolos acima — tag própria pra
        # aparecer em /api/notificacoes/feed (área sintética
        # "hidraulica-estoque", pra não confundir com a área de reparo
        # "hidraulica" da Central de Áreas — são coisas diferentes).
        agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
        operador = dados.operador or "Sistema"
        rotulo = "Aplicado na Máquina" if dados.local == "aplicado" else "Reserva (Oficina)"
        sinal = "+" if dados.fator >= 0 else ""
        acao = f"Ajuste hidráulico — {atualizado.get('nome', dados.id)} ({rotulo}): {sinal}{dados.fator:g}"
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, area) VALUES (%s, %s, %s, %s, %s)",
            (agora, operador, "ESTOQUE-HIDRAULICA", acao, "hidraulica-estoque")
        )
        conn.commit()

    enviar_push_para_area(titulo="🛢️ Estoque Hidráulico ajustado", corpo=f"{operador} — {acao}", area="Ambos")

    return {"sucesso": True, "item": atualizado}


@app.get("/api/folhao/rascunhos/todos", tags=["Folhões"], summary="Listar todos os folhões em andamento (rascunhos salvos)")
def listar_todos_rascunhos_folhao():
    """Usado na tela 'Em andamento' do Painel do Técnico: lista todo
    folhão que tem progresso salvo na nuvem, pra qualquer um (técnico
    da área certa, ou ADM) continuar de onde parou. O front-end filtra
    por área cruzando equipamento_id com o tipo do equipamento — aqui
    devolve tudo, sem filtro, igual as outras rotas de listagem."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT equipamento_id, tipo_folhao, etapa, atualizado_em, criado_em FROM folhoes_rascunho ORDER BY atualizado_em DESC"
        )
        return cursor.fetchall()


@app.get("/api/folhao/{equipamento_id}", tags=["Folhões"], summary="Carregar rascunho salvo de um folhão")
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


@app.post("/api/folhao/salvar", tags=["Folhões"], summary="Salvar progresso de um folhão")
def salvar_rascunho_folhao(dados: FolhaoRascunhoSalvar):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")

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


@app.post("/api/folhao/finalizar", tags=["Folhões"], summary="Finalizar (limpar rascunho de) um folhão")
def finalizar_rascunho_folhao(dados: FolhaoRascunhoFinalizar):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM folhoes_rascunho WHERE equipamento_id = %s",
            (dados.equipamento_id,)
        )
        conn.commit()

    return {"sucesso": True}


@app.get("/api/notificacoes/feed", tags=["Notificações Push"], summary="Feed unificado da Central de Notificações (com lido/não-lido por matrícula)")
def get_notificacoes_feed(matricula: str, limite: int = 30):
    """Junta os eventos gerais da Auditoria (log_eventos — inclui coisas
    como "rolo travado" no Sinótico 3D, que não têm categoria de
    Ocorrência e por isso nunca apareciam na Central de Notificações),
    OS em aberto e achados de Qualidade pendentes, num feed só,
    marcando pra CADA MATRÍCULA o que ela já viu ou não — ver/marcar
    como lido é individual: um ADM ver não marca como visto pra
    ninguém além dele mesmo."""
    matricula = matricula.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()

        # 🔧 CORREÇÃO ("não foi isso que pedi"): a primeira versão trazia
        # TODO log_eventos (menos login/logout) — inclui coisas como
        # "Peça cadastrada no Estoque Reserva", apontamento, troca de
        # peça... puro ruído de auditoria, não notificação de verdade.
        # Restrito a `categoria IS NOT NULL` = só Ocorrência de verdade
        # (Intervenção/Melhoria/Comentário/Atividade Pendente, criadas em
        # /api/registro_com_foto) — mesmo filtro que /api/registros_
        # ocorrencia sempre usou. Eventos de Auditoria geral (rolo
        # travado incluso) ficam de fora da Central por decisão do
        # usuário — continuam só na Auditoria/Registro Recente.
        cursor.execute("""
            SELECT 'evento' AS tipo, e.id::text AS evento_id, e.area, e.peca_id AS referencia,
                   e.acao AS descricao, e.operador AS autor, e.data_hora,
                   (l.matricula IS NOT NULL) AS lida
            FROM log_eventos e
            LEFT JOIN notificacoes_lidas l
                ON l.tipo = 'evento' AND l.evento_id = e.id::text AND l.matricula = %s
            WHERE e.categoria IS NOT NULL
            ORDER BY e.id DESC
            LIMIT %s
        """, (matricula, limite))
        eventos = cursor.fetchall()

        cursor.execute("""
            SELECT 'os' AS tipo, o.id::text AS evento_id, o.area, COALESCE(o.numero_os, o.id::text) AS referencia,
                   COALESCE(o.descricao, 'OS sem descrição') AS descricao, o.criado_por AS autor, o.criado_em AS data_hora,
                   (l.matricula IS NOT NULL) AS lida
            FROM ordens_servico o
            LEFT JOIN notificacoes_lidas l
                ON l.tipo = 'os' AND l.evento_id = o.id::text AND l.matricula = %s
            WHERE o.status != 'Concluído'
            ORDER BY o.id DESC
            LIMIT %s
        """, (matricula, limite))
        ordens = cursor.fetchall()

        cursor.execute("""
            SELECT 'achado' AS tipo, a.id::text AS evento_id, 'qualidade' AS area, r.peca_id AS referencia,
                   a.descricao, a.criado_por AS autor, a.criado_em AS data_hora,
                   (l.matricula IS NOT NULL) AS lida
            FROM qualidade_achados a
            JOIN qualidade_registros r ON r.id = a.registro_id
            LEFT JOIN notificacoes_lidas l
                ON l.tipo = 'achado' AND l.evento_id = a.id::text AND l.matricula = %s
            WHERE a.status = 'Pendente'
            ORDER BY a.id DESC
            LIMIT %s
        """, (matricula, limite))
        achados = cursor.fetchall()

        # 🆕 Ocorrências de mancal no Sinótico 3D — antes só viravam push,
        # agora também ficam em log_eventos (area="sinotico-3d") pra
        # aparecerem como área própria em vez de sumir/virar "Outros".
        cursor.execute("""
            SELECT 'sinotico' AS tipo, e.id::text AS evento_id, e.area, e.peca_id AS referencia,
                   e.acao AS descricao, e.operador AS autor, e.data_hora,
                   (l.matricula IS NOT NULL) AS lida
            FROM log_eventos e
            LEFT JOIN notificacoes_lidas l
                ON l.tipo = 'sinotico' AND l.evento_id = e.id::text AND l.matricula = %s
            WHERE e.area = 'sinotico-3d'
            ORDER BY e.id DESC
            LIMIT %s
        """, (matricula, limite))
        sinotico = cursor.fetchall()

        # 🆕 Ajustes de Estoque de Rolos/Hidráulica — gravados com tag
        # própria em log_eventos (ver ajustar_rolo/ajustar_hidraulica),
        # com "area" sintética ("rolos"/"hidraulica-estoque") pra
        # aparecerem como área própria na Central de Notificações.
        cursor.execute("""
            SELECT 'estoque' AS tipo, e.id::text AS evento_id, e.area, e.peca_id AS referencia,
                   e.acao AS descricao, e.operador AS autor, e.data_hora,
                   (l.matricula IS NOT NULL) AS lida
            FROM log_eventos e
            LEFT JOIN notificacoes_lidas l
                ON l.tipo = 'estoque' AND l.evento_id = e.id::text AND l.matricula = %s
            WHERE e.peca_id IN ('ESTOQUE-ROLOS', 'ESTOQUE-HIDRAULICA')
            ORDER BY e.id DESC
            LIMIT %s
        """, (matricula, limite))
        estoque = cursor.fetchall()

    todos = list(eventos) + list(ordens) + list(achados) + list(estoque) + list(sinotico)
    todos.sort(key=lambda x: x["data_hora"] or "", reverse=True)
    return todos[:limite]


@app.post("/api/notificacoes/marcar_lido", tags=["Notificações Push"], summary="Marcar uma notificação do feed como lida por uma matrícula")
def marcar_notificacao_lida(dados: NotificacaoMarcarLida):
    matricula = dados.matricula.strip().upper()
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notificacoes_lidas (tipo, evento_id, matricula, lido_em)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (tipo, evento_id, matricula) DO NOTHING
        """, (dados.tipo, dados.evento_id, matricula, agora))
        conn.commit()
    return {"sucesso": True}


@app.get("/api/push/vapid_public_key", tags=["Notificações Push"], summary="Obter a chave pública VAPID")
def get_vapid_public_key():
    if not PUSH_HABILITADO:
        raise HTTPException(status_code=503, detail="Push notification não configurado no servidor.")
    return {"publicKey": VAPID_PUBLIC_KEY}


@app.post("/api/push/subscribe", tags=["Notificações Push"], summary="Inscrever dispositivo pra notificações push")
def subscribe_push(dados: PushSubscribe):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
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


@app.post("/api/push/unsubscribe", tags=["Notificações Push"], summary="Cancelar inscrição de notificações push")
def unsubscribe_push(dados: PushUnsubscribe):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (dados.endpoint,))
        conn.commit()
    return {"sucesso": True}


# ==========================================
# 📸 REGISTRO COM FOTO E CATEGORIA
# ==========================================
@app.post("/api/registro_com_foto", tags=["Registros e Ocorrências"], summary="Registrar Intervenção/Melhoria/Comentário/Ocorrência com foto")
def registrar_com_foto(dados: RegistroComFoto):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, categoria, area) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (agora, dados.operador, dados.peca_id, dados.acao, dados.categoria, dados.area)
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


@app.get("/api/fotos/{peca_id}", tags=["Peças"], summary="Listar fotos registradas de uma peça")
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


@app.get("/api/registros_ocorrencia", tags=["Registros e Ocorrências"], summary="Listar ocorrências registradas")
def get_registros_ocorrencia(categoria: Optional[str] = None, limite: int = 100):
    with get_db() as conn:
        cursor = conn.cursor()
        if categoria:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria, e.area,
                       f.foto_base64
                FROM log_eventos e
                LEFT JOIN fotos_registro f ON f.evento_id = e.id
                WHERE e.categoria = %s
                ORDER BY e.id DESC
                LIMIT %s
            """, (categoria, limite))
        else:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria, e.area,
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
@app.get("/api/oficina/atividades", tags=["Oficina"], summary="Listar atividades da Oficina")
def listar_atividades_oficina(area: Optional[str] = None, status: Optional[str] = None, limite: int = 1000):
    """
    Lista as atividades da oficina. Sem filtro, traz TUDO — a grade de
    áreas no front-end filtra por área no próprio navegador (evita uma
    chamada de API por card). Os filtros opcionais ficam disponíveis
    caso precise no futuro (ex: um relatório só de pendências).

    O "limite" aqui é bem mais alto que nas outras listagens (Ocorrência,
    OS, Qualidade) DE PROPÓSITO — o front-end depende de receber tudo de
    uma vez pra montar a grade de todas as áreas. É só um teto de
    segurança pra não buscar um histórico infinito, não um paginado de
    verdade como as outras.
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
        query += " ORDER BY id DESC LIMIT %s"
        params.append(limite)
        cursor.execute(query, params)
        return cursor.fetchall()


@app.post("/api/oficina/atividade", tags=["Oficina"], summary="Criar atividade da Oficina")
def criar_atividade_oficina(dados: OficinaAtividade):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO oficina_atividades
                (area, equipamento_id, descricao, responsavel, prioridade, status, criado_por, criado_em, foto_base64, prazo, data_inicio, solicitante_matricula)
            VALUES (%s, %s, %s, %s, %s, 'Pendente', %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (dados.area, dados.equipamento_id, dados.descricao, dados.responsavel,
             dados.prioridade or "Normal", dados.operador, agora, dados.foto_base64, dados.prazo, dados.data_inicio, dados.solicitante_matricula)
        )
        atividade_id = cursor.fetchone()["id"]
        conn.commit()

    # 📲 Avisa quem estiver com push ativado que uma atividade nova
    # entrou na oficina. Como push_subscriptions hoje só existe pra quem
    # FAZ LOGIN no sistema (não pra equipe_oficina, que é só roster de
    # exibição), o alvo é "Ambos" — todo mundo logado com notificação
    # ligada. Se no futuro os líderes de área tiverem login vinculado à
    # área, dá pra refinar esse filtro.
    # 🆕 Se a atividade tem Data de Início futura, ela ainda não é "pra
    # fazer agora" — não faz sentido avisar hoje algo que só vale daqui
    # a X dias, então o push fica pra quando ela realmente começar.
    hoje_str = agora_brasil().strftime("%Y-%m-%d")
    eh_programada_pro_futuro = bool(dados.data_inicio) and dados.data_inicio > hoje_str
    if not eh_programada_pro_futuro:
        nome_area = AREA_OFICINA_NOMES.get(dados.area, dados.area)
        is_alta_prioridade = (dados.prioridade or "Normal") == "Alta"
        enviar_push_para_area(
            titulo="🔴 Atividade prioritária na Oficina" if is_alta_prioridade else f"🧰 Nova atividade — {nome_area}",
            corpo=f"{dados.operador} — {nome_area}: {dados.descricao}",
            area=dados.area
        )

    return {"sucesso": True, "id": atividade_id}



@app.post("/api/oficina/atividade/status", tags=["Oficina"], summary="Mudar status de uma atividade da Oficina")
def mudar_status_atividade_oficina(dados: OficinaStatus):
    # 🆕 "Recusado" e "Aguardando" exigem motivo — não dá pra só
    # "passar por cima" de uma atividade sem justificar por que não
    # iniciou (Recusado) ou por que travou depois de já ter começado
    # (Aguardando, ex: aguardando material chegar).
    if dados.status in ("Recusado", "Aguardando") and not (dados.motivo or "").strip():
        raise HTTPException(status_code=400, detail=f"Status \"{dados.status}\" precisa de um motivo.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    concluido_em = agora if dados.status == "Concluído" else None
    # 🔧 CORRIGIDO ("nem chegou notificação de que iniciou, nem o
    # motivo da recusa"): antes só guardava (e só avisava) o motivo pra
    # Recusado/Aguardando. Motivo/observação agora vale pra QUALQUER
    # status — inclusive uma nota ao Concluir ("trocado o parafuso X")
    # — se veio alguma coisa, guarda; senão fica vazio (não força
    # limpeza em transições que não vieram acompanhadas de nota).
    motivo_status = dados.motivo.strip() if (dados.motivo or "").strip() else None

    with get_db() as conn:
        cursor = conn.cursor()
        # 🆕 Se a atividade voltou a ficar aberta (reaberta depois de
        # concluída, por exemplo), reseta o aviso de atraso — se ela
        # ficar atrasada de novo, precisa poder notificar de novo.
        resetar_notificacao = dados.status != "Concluído"
        cursor.execute(
            "UPDATE oficina_atividades SET status = %s, concluido_em = %s, motivo_status = %s"
            + (", notificado_atraso = FALSE" if resetar_notificacao else "")
            + " WHERE id = %s"
            + " RETURNING equipamento_id, descricao, area, solicitante_matricula",
            (dados.status, concluido_em, motivo_status, dados.id)
        )
        linha = cursor.fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()

    # 🔧 CORRIGIDO ("nem chegou notificação de que ele iniciou a
    # atividade, e nem que recusou e o motivo"): antes só avisava em
    # Recusado/Aguardando — quem pediu ficava sem saber que o serviço
    # tinha começado ou terminado. Agora TODA mudança de status
    # (Iniciar, Concluir, Recusar, Aguardar) avisa quem pediu — só faz
    # sentido pra atividade que veio de um "Registrar Atividade Extra"
    # no Checklist de Execução (tem solicitante_matricula). Uma
    # atividade criada direto no quadro da área não tem "quem pediu"
    # separado de quem executa, então não notifica ninguém aqui.
    if linha["solicitante_matricula"]:
        tag = linha["equipamento_id"] or ""
        nome_area = AREA_OFICINA_NOMES.get(linha["area"], linha["area"])
        VERBOS_STATUS = {
            "Em Andamento": "iniciou",
            "Concluído": "concluiu",
            "Recusado": "recusou",
            "Aguardando": "colocou em espera",
            "Pendente": "reabriu",
        }
        verbo = VERBOS_STATUS.get(dados.status, "atualizou")
        enviar_push_para_matricula(
            matricula=linha["solicitante_matricula"],
            titulo=f"{nome_area} {verbo} sua atividade — {tag}",
            corpo=(f"Motivo: {motivo_status}" if motivo_status else "Sem observações."),
            url="/"
        )
    return {"sucesso": True}


# 🆕 Verificação de atividades atrasadas — não roda sozinha (o sistema
# não tem um agendador/cron), então é chamada pelo front-end sempre que
# o app é aberto (ver DOMContentLoaded em script.js). Cada atividade só
# gera UMA notificação (controlado pela coluna notificado_atraso) —
# reabrir a atividade (ver rota de status acima) é o que permite avisar
# de novo se ela atrasar outra vez.
@app.post("/api/oficina/verificar_atrasos", tags=["Oficina"], summary="Verificar atividades atrasadas e notificar")
def verificar_atrasos_oficina():
    hoje_str = agora_brasil().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, area, descricao, responsavel, prazo
            FROM oficina_atividades
            WHERE status != 'Concluído'
              AND prazo IS NOT NULL AND prazo != '' AND prazo < %s
              AND (data_inicio IS NULL OR data_inicio = '' OR data_inicio <= %s)
              AND notificado_atraso = FALSE
            """,
            (hoje_str, hoje_str)
        )
        atrasadas = cursor.fetchall()

        if not atrasadas:
            return {"sucesso": True, "notificadas": 0}

        ids = [a["id"] for a in atrasadas]
        cursor.execute(
            "UPDATE oficina_atividades SET notificado_atraso = TRUE WHERE id = ANY(%s)",
            (ids,)
        )
        conn.commit()

    for a in atrasadas:
        nome_area = AREA_OFICINA_NOMES.get(a["area"], a["area"])
        enviar_push_para_area(
            titulo="⏰ Atividade atrasada",
            corpo=f"{nome_area} — {a['descricao']} (prazo era {a['prazo']}, ainda não concluída).",
            area=a["area"]
        )

    return {"sucesso": True, "notificadas": len(atrasadas)}


# ==========================================================================
# 🆕 CONVERSA DA ATIVIDADE — mensagens de mão dupla numa atividade
# específica. Ver comentário da tabela oficina_atividade_mensagens
# (schema) pros casos de uso reais que isso resolve.
# ==========================================================================
@app.post("/api/oficina/atividade/mensagem", tags=["Oficina"], summary="Enviar mensagem na conversa de uma atividade (avisa o outro lado)")
def criar_mensagem_atividade_oficina(dados: OficinaAtividadeMensagem):
    agora = agora_brasil().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT area, equipamento_id, solicitante_matricula FROM oficina_atividades WHERE id = %s",
            (dados.atividade_id,)
        )
        atividade = cursor.fetchone()
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")

        cursor.execute(
            """
            INSERT INTO oficina_atividade_mensagens (atividade_id, autor_matricula, autor_nome, mensagem, criado_em)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (dados.atividade_id, dados.autor_matricula, dados.autor_nome, dados.mensagem, agora)
        )
        novo_id = cursor.fetchone()["id"]
        conn.commit()

    # 📲 Avisa o OUTRO LADO — nunca quem mandou a própria mensagem.
    # "Outro lado" depende de quem escreveu:
    #   - Se foi o solicitante (quem pediu a atividade) -> avisa a
    #     área toda (mesmo alvo que uma atividade nova usa).
    #   - Se foi alguém da área (ou a atividade não tem solicitante
    #     identificado, ex: tarefa criada direto no quadro) -> avisa
    #     especificamente o solicitante, se tiver um.
    tag = atividade["equipamento_id"] or ""
    nome_area = AREA_OFICINA_NOMES.get(atividade["area"], atividade["area"])
    eh_o_solicitante_escrevendo = bool(dados.autor_matricula) and dados.autor_matricula == atividade["solicitante_matricula"]

    if eh_o_solicitante_escrevendo:
        enviar_push_para_area(
            titulo=f"💬 {dados.autor_nome} — {tag or nome_area}",
            corpo=dados.mensagem,
            area=atividade["area"]
        )
    elif atividade["solicitante_matricula"]:
        enviar_push_para_matricula(
            matricula=atividade["solicitante_matricula"],
            titulo=f"💬 {nome_area} respondeu — {tag}",
            corpo=f"{dados.autor_nome}: {dados.mensagem}"
        )
    # Sem solicitante e quem escreveu não é ele: é conversa interna da
    # própria área (atividade criada direto no quadro) — não tem "outro
    # lado" fora da área pra avisar.

    return {"sucesso": True, "id": novo_id}


@app.get("/api/oficina/atividade/mensagens/{atividade_id}", tags=["Oficina"], summary="Listar mensagens da conversa de uma atividade")
def listar_mensagens_atividade_oficina(atividade_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, autor_matricula, autor_nome, mensagem, criado_em
            FROM oficina_atividade_mensagens
            WHERE atividade_id = %s
            ORDER BY id ASC
            """,
            (atividade_id,)
        )
        return cursor.fetchall()


@app.post("/api/oficina/atividade/excluir", tags=["Oficina"], summary="Excluir atividade da Oficina")
def excluir_atividade_oficina(dados: OficinaExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        # 🐛 CORRIGIDO ("excluí na área e continuou aparecendo no
        # Checklist de Execução"): a exclusão só tinha sido resolvida
        # no sentido Checklist -> Área (ver
        # excluir_atividade_extra_checklist_execucao). Excluindo por
        # aqui (direto no quadro da área, o caminho mais comum de
        # quem trabalha na área) o registro em
        # checklist_execucao_atividades_extra ficava órfão pra sempre
        # — o LEFT JOIN só perdia o status, o registro em si nunca
        # sumia de lá. Agora as duas pontas se apagam juntas,
        # não importa por qual lado a exclusão começa.
        cursor.execute("DELETE FROM checklist_execucao_atividades_extra WHERE oficina_atividade_id = %s", (dados.id,))
        cursor.execute("DELETE FROM oficina_atividades WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()
    return {"sucesso": True}


@app.get("/api/oficina/nota/{area}", tags=["Oficina"], summary="Consultar anotações de uma área")
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


@app.post("/api/oficina/nota", tags=["Oficina"], summary="Salvar anotações de uma área")
def salvar_nota_area_oficina(dados: OficinaNota):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
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


@app.get("/api/oficina/equipe/{area}", tags=["Oficina"], summary="Listar equipe de uma área")
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
@app.get("/api/oficina/materiais_todos", tags=["Oficina"], summary="Catálogo geral de materiais (todas as áreas)")
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


@app.get("/api/oficina/materiais/{area}", tags=["Oficina"], summary="Listar materiais de uma área específica")
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


@app.post("/api/oficina/materiais", tags=["Oficina"], summary="Cadastrar material numa área")
def criar_material_area_oficina(dados: OficinaMaterial):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
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


@app.post("/api/oficina/materiais/excluir", tags=["Oficina"], summary="Excluir material de uma área")
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
@app.post("/api/oficina/atividade/editar", tags=["Oficina"], summary="Editar atividade da Oficina")
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
                prioridade = %s, prazo = %s, data_inicio = %s, foto_base64 = %s
            WHERE id = %s
            """,
            (dados.equipamento_id, dados.descricao, dados.responsavel,
             dados.prioridade or "Normal", dados.prazo, dados.data_inicio, dados.foto_base64, dados.id)
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
@app.post("/api/oficina/procedimento/executar", tags=["Oficina"], summary="Registrar execução de um procedimento")
def registrar_execucao_procedimento(dados: ProcedimentoExecucao):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
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


@app.get("/api/oficina/procedimento/historico/{area}", tags=["Oficina"], summary="Histórico de procedimentos executados numa área")
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
# 🆕 CHECKLIST DE EXECUÇÃO — passo a passo REAL do reparo (por
# equipamento, dividido em seções: mecânica, elétrica, hidráulica,
# caldeiraria, usinagem, tubulação, jato). Diferente do "Procedimento"
# oficial (procedimentos_execucoes acima) — este é editável só pelas 3
# matrículas admin e reflete o jeito que os técnicos realmente fazem.
# ==========================================

@app.get("/api/checklist-execucao/etapas/{tipo_equipamento}", tags=["Checklist de Execução"], summary="Listar etapas de um TIPO de equipamento (com estado da execução atual)")
def listar_etapas_checklist_execucao(tipo_equipamento: str, execucao_id: Optional[int] = None):
    """🆕 Agora busca por TIPO de equipamento (ex: "molde-mcc4"), não mais
    por tag específica — assim a mesma etapa vale pra todo molde MCC4.
    `execucao_id` (opcional, vem de /execucoes/iniciar ou do /status) diz
    de QUAL reparo puxar o estado marcado/valor — sem isso, todas as
    etapas voltam como não marcadas (só a "receita", sem progresso)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.id, e.area, e.especialidade, e.texto, e.ordem, e.folhao_campo, e.tipo_resposta, e.descricao,
                   COALESCE(m.marcado, FALSE) AS marcado,
                   m.colaborador, m.tecnico_matricula, m.tecnico_nome, m.data_hora,
                   m.valor, m.trocado
            FROM checklist_execucao_etapas e
            LEFT JOIN checklist_execucao_marcacoes m
                   ON m.etapa_id = e.id AND m.execucao_id = %s
            WHERE e.equipamento_id = %s AND e.ativo = TRUE
            ORDER BY e.area, e.ordem, e.id
            """,
            (execucao_id, tipo_equipamento)
        )
        return cursor.fetchall()


@app.get("/api/checklist-execucao/execucoes/todas", tags=["Checklist de Execução"], summary="Listar todas as execuções de checklist em andamento")
def listar_execucoes_checklist_em_andamento():
    """🆕 Usado pela sub-aba 'Reparo em Andamento': antes, ela só sabia
    de um reparo em andamento se já existisse um RASCUNHO DE FOLHÃO
    salvo (folhoes_rascunho) — um técnico que iniciasse só o Checklist
    de Execução (sem nunca ter aberto/salvo o Folhão ainda) ficava
    "invisível" pro sistema: não aparecia nem em 'Iniciar Reparo' nem em
    'Reparo em Andamento'. Esta rota devolve toda execução com
    status='em_andamento', pra cruzar com folhoes_rascunho e formar a
    lista completa de quem já começou o reparo de alguma forma."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, equipamento_id, tipo_equipamento, tipo_execucao,
                   tecnico_matricula, tecnico_nome, iniciada_em
            FROM checklist_execucao_execucoes
            WHERE status = 'em_andamento'
            ORDER BY id DESC
            """
        )
        return cursor.fetchall()


@app.post("/api/checklist-execucao/execucoes/iniciar", tags=["Checklist de Execução"], summary="Iniciar (ou reaproveitar) a execução de um reparo específico")
def iniciar_execucao_checklist(dados: ChecklistExecucaoIniciar):
    """🆕 Cria 1 registro de 'reparo real' pra essa tag. Se já existir um
    em andamento pra ela, reaproveita em vez de duplicar (evita 2
    execuções abertas em paralelo pro mesmo equipamento)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM checklist_execucao_execucoes WHERE equipamento_id = %s AND status = 'em_andamento' ORDER BY id DESC LIMIT 1",
            (dados.equipamento_id,)
        )
        existente = cursor.fetchone()
        if existente:
            return {"execucao_id": existente["id"], "reaproveitada": True}

        cursor.execute(
            """
            INSERT INTO checklist_execucao_execucoes
                (equipamento_id, tipo_equipamento, tipo_execucao, tecnico_matricula, tecnico_nome, iniciada_em, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'em_andamento') RETURNING id
            """,
            (dados.equipamento_id, dados.tipo_equipamento, dados.tipo_execucao, dados.tecnico_matricula, dados.tecnico_nome, agora_brasil().isoformat())
        )
        novo_id = cursor.fetchone()["id"]
        conn.commit()
        return {"execucao_id": novo_id, "reaproveitada": False}


@app.post("/api/checklist-execucao/execucoes/finalizar", tags=["Checklist de Execução"], summary="Finalizar a execução de um reparo (fecha o ciclo)")
def finalizar_execucao_checklist(dados: ChecklistExecucaoFinalizar):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE checklist_execucao_execucoes SET status = 'concluida', concluida_em = %s WHERE id = %s",
            (agora_brasil().isoformat(), dados.execucao_id)
        )
        conn.commit()
        return {"sucesso": True}


@app.get("/api/checklist-execucao/status/{equipamento_id}", tags=["Checklist de Execução"], summary="Progresso da execução em andamento dessa tag")
def status_checklist_execucao(equipamento_id: str):
    """Usado pra decidir se o botão 'Concluir' pode ser liberado, e
    também devolve o `execucao_id` pra usar nas chamadas de /marcar.
    🆕 Agora resolve automaticamente qual é a execução 'em_andamento'
    dessa tag, em vez de olhar etapas por tag direto (que não existe
    mais — etapas agora são por tipo)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM checklist_execucao_execucoes WHERE equipamento_id = %s AND status = 'em_andamento' ORDER BY id DESC LIMIT 1",
            (equipamento_id,)
        )
        execucao = cursor.fetchone()
        if not execucao:
            return {
                "execucao_id": None, "tipo_equipamento": None, "tipo_execucao": None,
                "total": 0, "marcadas": 0, "percentual": 0, "completo": False,
                "iniciada_em": None, "concluida_em": None,
                "tecnico_matricula": None, "tecnico_nome": None
            }

        cursor.execute(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE m.marcado = TRUE) AS marcadas
            FROM checklist_execucao_etapas e
            LEFT JOIN checklist_execucao_marcacoes m
                   ON m.etapa_id = e.id AND m.execucao_id = %s
            WHERE e.equipamento_id = %s AND e.ativo = TRUE
            """,
            (execucao["id"], execucao["tipo_equipamento"])
        )
        row = cursor.fetchone()
        total = row["total"] or 0
        marcadas = row["marcadas"] or 0
        percentual = round((marcadas / total) * 100, 1) if total > 0 else 0
        return {
            "execucao_id": execucao["id"],
            "tipo_equipamento": execucao["tipo_equipamento"],
            "tipo_execucao": execucao["tipo_execucao"],
            "total": total,
            "marcadas": marcadas,
            "percentual": percentual,
            "completo": total > 0 and marcadas == total,
            # 🆕 Início/fim REAIS do reparo (gravados pelo servidor em
            # /execucoes/iniciar e /execucoes/finalizar) + quem iniciou —
            # o Folhão usa isso pra travar DATA INÍCIO/FIM e LÍDER
            # RESPONSÁVEL em vez de deixar o técnico digitar/reeditar.
            "iniciada_em": execucao["iniciada_em"],
            "concluida_em": execucao["concluida_em"],
            "tecnico_matricula": execucao["tecnico_matricula"],
            "tecnico_nome": execucao["tecnico_nome"]
        }


@app.get("/api/checklist-execucao/folhao/{tipo_equipamento}", tags=["Checklist de Execução"], summary="Valores prontos pro Folhão se autopreencher")
def valores_folhao_checklist_execucao(tipo_equipamento: str, execucao_id: Optional[int] = None):
    """🆕 PONTE COM O FOLHÃO. Devolve um dicionário { folhao_campo: valor }
    só com as etapas que têm folhao_campo preenchido e já foram
    respondidas NAQUELA execução (reparo) específica. O front-end
    (folhaoMolde4.js) chama isso em vez de ler <input> da tela — assim o
    técnico nunca precisa preencher o mesmo dado duas vezes.

    4 tipos de etapa:
    - "sim_nao": 🆕 agora usa a resposta REAL guardada em "valor" ('SIM'
      ou 'NÃO' — ver /marcar, que passou a perguntar isso antes de só
      assumir 'feito = SIM'). Etapas antigas, marcadas antes dessa
      mudança, não têm valor salvo — pra essas, cai no comportamento de
      antes ('OK' se marcado) só como compatibilidade.
    - "medicao": devolve o valor bruto digitado num único campo.
    - "medicao_multipla": pra etapas tipo "Folga Aresta — Esquerda", que
      preenchem várias dezenas de campos de uma vez. Aqui folhao_campo
      guarda um JSON { "1000-sup": "m4-fa-1000-es", ... } e valor guarda
      outro JSON { "1000-sup": "0.12", ... } com a mesma chave — os dois
      são cruzados e cada um vira uma entrada solta no resultado final.
    - 🆕 "sim_nao_assinatura": pra listas de tarefas tipo "Checklist de
      Manutenção" do Horizontal, que no Folhão pedem, por item, um
      checkbox (Geral OU Parcial, conforme o tipo de execução do
      reparo) + Executante + Matrícula + Data — dados que a marcação já
      tem (colaborador/tecnico_matricula/data_hora), sem o técnico
      precisar digitar de novo. Aqui folhao_campo guarda um JSON
      { "checkbox_geral": "hz-g-3", "checkbox_parcial": "hz-p-3",
        "executante": "hz-resp-3", "matricula": "hz-mat-3",
        "data": "hz-dat-3" } — todas as chaves opcionais."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.folhao_campo, e.tipo_resposta,
                   COALESCE(m.marcado, FALSE) AS marcado, m.valor,
                   m.colaborador, m.tecnico_matricula, m.tecnico_nome, m.data_hora
            FROM checklist_execucao_etapas e
            LEFT JOIN checklist_execucao_marcacoes m
                   ON m.etapa_id = e.id AND m.execucao_id = %s
            WHERE e.equipamento_id = %s AND e.ativo = TRUE AND e.folhao_campo IS NOT NULL
            """,
            (execucao_id, tipo_equipamento)
        )
        linhas = cursor.fetchall()

        tipo_execucao_exec = None
        if execucao_id is not None:
            cursor.execute(
                "SELECT tipo_execucao FROM checklist_execucao_execucoes WHERE id = %s",
                (execucao_id,)
            )
            row_exec = cursor.fetchone()
            tipo_execucao_exec = (row_exec["tipo_execucao"] or "").upper() if row_exec else None

    valores = {}
    for l in linhas:
        if l["tipo_resposta"] == "medicao_multipla":
            try:
                mapa_campos = json_lib.loads(l["folhao_campo"])
                mapa_valores = json_lib.loads(l["valor"]) if l["valor"] else {}
            except (TypeError, ValueError):
                continue  # JSON mal formado — pula essa etapa sem derrubar o resto
            for chave, campo_real in mapa_campos.items():
                valores[campo_real] = mapa_valores.get(chave, "")
        elif l["tipo_resposta"] == "medicao":
            valores[l["folhao_campo"]] = l["valor"] or ""
        elif l["tipo_resposta"] == "sim_nao_assinatura":
            if not l["marcado"]:
                continue  # nada marcado ainda — não preenche nada (nem checkbox errado)
            try:
                mapa = json_lib.loads(l["folhao_campo"])
            except (TypeError, ValueError):
                continue
            campo_checkbox = mapa.get("checkbox_parcial") if tipo_execucao_exec == "PARCIAL" else mapa.get("checkbox_geral")
            if campo_checkbox:
                valores[campo_checkbox] = "OK"
            if mapa.get("executante"):
                valores[mapa["executante"]] = l["colaborador"] or l["tecnico_nome"] or ""
            if mapa.get("matricula") and l["tecnico_matricula"]:
                valores[mapa["matricula"]] = l["tecnico_matricula"]
            if mapa.get("data") and l["data_hora"]:
                valores[mapa["data"]] = l["data_hora"][:10]
        else:
            # 🆕 "SIM"/"NÃO" bate direto com o value="" dos radios do
            # Folhão (ver preencherFolhaoComChecklistExecucao no
            # front-end) — não precisa de tradução nenhuma. Só cai no
            # "OK" (=SIM) por padrão se a etapa foi marcada ANTES dessa
            # mudança e não tem valor salvo ainda.
            if l["valor"] in ("SIM", "NÃO"):
                valores[l["folhao_campo"]] = l["valor"]
            else:
                valores[l["folhao_campo"]] = "OK" if l["marcado"] else ""
    return valores


@app.post("/api/checklist-execucao/etapas", tags=["Checklist de Execução"], summary="Cadastrar nova etapa (só ADM do checklist)")
def criar_etapa_checklist_execucao(dados: ChecklistExecucaoEtapaNova):
    if dados.operador.upper() not in MATRICULAS_ADM:
        raise HTTPException(status_code=403, detail="Só as matrículas autorizadas podem cadastrar etapas do checklist.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(MAX(ordem), 0) + 1 AS proxima FROM checklist_execucao_etapas WHERE equipamento_id = %s AND area = %s",
            (dados.equipamento_id, dados.area)
        )
        proxima_ordem = cursor.fetchone()["proxima"]
        cursor.execute(
            """
            INSERT INTO checklist_execucao_etapas (equipamento_id, area, especialidade, texto, ordem, criado_por, criado_em, folhao_campo, tipo_resposta, descricao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (dados.equipamento_id, dados.area, dados.especialidade, dados.texto, proxima_ordem, dados.operador, agora_brasil().isoformat(), dados.folhao_campo, dados.tipo_resposta, dados.descricao)
        )
        novo_id = cursor.fetchone()["id"]
        conn.commit()
        return {"sucesso": True, "id": novo_id}


@app.post("/api/checklist-execucao/etapas/editar", tags=["Checklist de Execução"], summary="Editar texto (e opcionalmente a ponte com o Folhão) de uma etapa (só ADM do checklist)")
def editar_etapa_checklist_execucao(dados: ChecklistExecucaoEtapaEditar):
    if dados.operador.upper() not in MATRICULAS_ADM:
        raise HTTPException(status_code=403, detail="Só as matrículas autorizadas podem editar etapas do checklist.")

    # 🆕 Se veio um novo folhao_campo pra uma etapa de medição múltipla,
    # confere que é um JSON válido ANTES de gravar — um JSON quebrado
    # aqui faria a ponte com o Folhão simplesmente parar de preencher
    # tudo (igual o mapeamento errado que causou esse bug em primeiro
    # lugar), sem erro nenhum avisando o ADM na hora.
    if dados.folhao_campo is not None and (dados.tipo_resposta or "").strip() == "medicao_multipla":
        try:
            mapa = json_lib.loads(dados.folhao_campo)
            if not isinstance(mapa, dict):
                raise ValueError("não é um objeto JSON")
        except (TypeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"O mapeamento (folhao_campo) precisa ser um JSON válido no formato {{\"chave\": \"id_do_campo_no_folhao\"}}. Erro: {e}")

    campos = ["texto = %s"]
    valores = [dados.texto]
    if dados.folhao_campo is not None:
        campos.append("folhao_campo = %s")
        valores.append(dados.folhao_campo)
    if dados.tipo_resposta is not None:
        campos.append("tipo_resposta = %s")
        valores.append(dados.tipo_resposta)
    if dados.area is not None:
        campos.append("area = %s")
        valores.append(dados.area)
    if dados.especialidade is not None:
        campos.append("especialidade = %s")
        valores.append(dados.especialidade)
    valores.append(dados.id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE checklist_execucao_etapas SET {', '.join(campos)} WHERE id = %s", tuple(valores))
        conn.commit()
    return {"sucesso": True}


@app.post("/api/checklist-execucao/etapas/excluir", tags=["Checklist de Execução"], summary="Excluir (desativar) uma etapa (só ADM do checklist)")
def excluir_etapa_checklist_execucao(dados: ChecklistExecucaoEtapaExcluir):
    if dados.operador.upper() not in MATRICULAS_ADM:
        raise HTTPException(status_code=403, detail="Só as matrículas autorizadas podem excluir etapas do checklist.")
    with get_db() as conn:
        cursor = conn.cursor()
        # Desativa em vez de apagar de verdade — preserva o histórico
        # (checklist_execucao_historico) de quem já executou essa etapa.
        cursor.execute("UPDATE checklist_execucao_etapas SET ativo = FALSE WHERE id = %s", (dados.id,))
        conn.commit()
    return {"sucesso": True}


@app.post("/api/checklist-execucao/etapas/reordenar", tags=["Checklist de Execução"], summary="Reordenar etapas dentro de uma seção (só ADM do checklist)")
def reordenar_etapas_checklist_execucao(dados: ChecklistExecucaoReordenar):
    if dados.operador.upper() not in MATRICULAS_ADM:
        raise HTTPException(status_code=403, detail="Só as matrículas autorizadas podem reordenar etapas do checklist.")
    with get_db() as conn:
        cursor = conn.cursor()
        for item in dados.itens:
            cursor.execute("UPDATE checklist_execucao_etapas SET ordem = %s WHERE id = %s", (item.ordem, item.id))
        conn.commit()
    return {"sucesso": True}


@app.post("/api/checklist-execucao/marcar", tags=["Checklist de Execução"], summary="Marcar ou desmarcar uma etapa executada")
def marcar_etapa_checklist_execucao(dados: ChecklistExecucaoMarcar):
    """Marca/desmarca uma etapa DENTRO de uma execução (reparo) específica.
    Qualquer técnico logado pode marcar (não só os 3 ADM — essa checagem
    é só pra CADASTRAR etapa nova). Desmarcar uma etapa já feita =
    retrabalho: o histórico completo fica registrado em
    checklist_execucao_historico, mesmo que o estado atual mude.

    🆕 A chave agora é (execucao_id, etapa_id), não mais só etapa_id —
    assim a mesma etapa pode estar marcada num molde e não marcada em
    outro, cada um na sua própria execução."""
    agora = agora_brasil().isoformat()
    acao = "marcou" if dados.marcado else "desmarcou (retrabalho)"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO checklist_execucao_marcacoes (etapa_id, execucao_id, equipamento_id, marcado, colaborador, tecnico_matricula, tecnico_nome, data_hora, valor, trocado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (execucao_id, etapa_id) DO UPDATE SET
                marcado = EXCLUDED.marcado,
                colaborador = EXCLUDED.colaborador,
                tecnico_matricula = EXCLUDED.tecnico_matricula,
                tecnico_nome = EXCLUDED.tecnico_nome,
                data_hora = EXCLUDED.data_hora,
                valor = EXCLUDED.valor,
                trocado = EXCLUDED.trocado
            """,
            (dados.etapa_id, dados.execucao_id, dados.equipamento_id, dados.marcado, dados.colaborador, dados.tecnico_matricula, dados.tecnico_nome, agora, dados.valor, dados.trocado)
        )
        cursor.execute(
            """
            INSERT INTO checklist_execucao_historico (etapa_id, equipamento_id, acao, colaborador, tecnico_matricula, tecnico_nome, data_hora)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (dados.etapa_id, dados.equipamento_id, acao, dados.colaborador, dados.tecnico_matricula, dados.tecnico_nome, agora)
        )

        # 🆕 AVISO POR LOTE/FASE: em vez de avisar só Elétrica/Hidráulica
        # quando falta a última etapa de Mecânica (versão anterior),
        # agora avisa TODO MUNDO ENVOLVIDO (Mecânica + Elétrica +
        # Hidráulica) sempre que uma FASE inteira (Chegada ou
        # Manutenção) fecha 100% — é o momento de virada real: Chegada
        # concluída = Manutenção pode começar; Manutenção concluída =
        # Saída pode começar (todo mundo já sabe que precisa ir lá
        # fechar a parte dele). Saída concluída não tem aviso aqui — é
        # o próprio fim do reparo, já tratado pelo fluxo de "Concluir".
        #
        # Só se aplica a tipos de equipamento que separam fase
        # (chegada/manutencao/saida) de especialidade. Nos outros tipos
        # "area" já É a especialidade, então uma "fase" com várias
        # especialidades dentro não existe.
        # 🆕 Precisa bater com CHECKLIST_EXECUCAO_SECOES_POR_TIPO do
        # front (JS/Core/dados.js) — qualquer tipo novo que ganhar essa
        # divisão por fase entra nos dois lugares. Faltavam aqui:
        # bow-mcc4, straightener-r1/r2-mcc4, bender-mcc4,
        # segmento-zero-mcc2-3, cadeira-mcc2-3, segmento-grupo-mcc2-3 —
        # cadastrados no front mas nunca propagados pra cá, então essas
        # áreas nunca disparavam o aviso de "fase completa" pra
        # Mecânica/Elétrica/Hidráulica.
        TIPOS_CHECKLIST_POR_FASE = {
            "molde-mcc4", "molde-mcc2-3", "horizontal-mcc4", "bow-mcc4",
            "straightener-r1-mcc4", "straightener-r2-mcc4", "bender-mcc4",
            "segmento-zero-mcc2-3", "cadeira-mcc2-3", "segmento-grupo-mcc2-3",
        }
        PROXIMA_FASE_APOS = {"chegada": "Manutenção", "manutencao": "Saída"}
        if dados.marcado:
            cursor.execute("SELECT area FROM checklist_execucao_etapas WHERE id = %s", (dados.etapa_id,))
            etapa_marcada = cursor.fetchone()
            aba = etapa_marcada["area"] if etapa_marcada else None
            if aba in PROXIMA_FASE_APOS:
                cursor.execute("SELECT tipo_equipamento FROM checklist_execucao_execucoes WHERE id = %s", (dados.execucao_id,))
                execucao_row = cursor.fetchone()
                tipo_equipamento = execucao_row["tipo_equipamento"] if execucao_row else None
                if tipo_equipamento in TIPOS_CHECKLIST_POR_FASE:
                    cursor.execute(
                        """
                        SELECT e.especialidade, COALESCE(m.marcado, FALSE) AS marcado
                        FROM checklist_execucao_etapas e
                        LEFT JOIN checklist_execucao_marcacoes m
                               ON m.etapa_id = e.id AND m.execucao_id = %s
                        WHERE e.equipamento_id = %s AND e.area = %s AND e.ativo = TRUE
                        """,
                        (dados.execucao_id, tipo_equipamento, aba)
                    )
                    linhas_fase = cursor.fetchall()
                    fase_completa = bool(linhas_fase) and all(r["marcado"] for r in linhas_fase)
                    if fase_completa:
                        # 1 linha só por (execução, fase) — dedupe do LOTE
                        # inteiro, não por área, porque é 1 evento só
                        # ("fase virou") que avisa todo mundo de uma vez.
                        cursor.execute(
                            """
                            INSERT INTO checklist_execucao_avisos_area (execucao_id, aba, area_avisada, criado_em)
                            VALUES (%s, %s, 'fase_completa', %s)
                            ON CONFLICT (execucao_id, aba, area_avisada) DO NOTHING
                            RETURNING id
                            """,
                            (dados.execucao_id, aba, agora)
                        )
                        if cursor.fetchone():  # só dispara se inseriu de fato (nunca avisado antes pra essa fase)
                            especialidades_envolvidas = sorted({(r["especialidade"] or "mecanica") for r in linhas_fase})
                            nome_aba = NOME_AREA_PUSH.get(aba, aba)
                            nome_proxima_fase = PROXIMA_FASE_APOS[aba]
                            for especialidade in especialidades_envolvidas:
                                enviar_push_para_area(
                                    titulo=f"Molde {dados.equipamento_id} — {nome_aba} concluída",
                                    corpo=f"\"{nome_aba}\" 100% concluída. {nome_proxima_fase} pode começar — todo mundo envolvido, bora fechar a parte de vocês.",
                                    area=especialidade,
                                    url="/"
                                )

        conn.commit()
    return {"sucesso": True}


@app.post("/api/checklist-execucao/atividade-extra", tags=["Checklist de Execução"], summary="Registrar atividade fora do checklist padrão (ex: precisou de Caldeiraria/Usinagem)")
def registrar_atividade_extra_checklist_execucao(dados: ChecklistExecucaoAtividadeExtra):
    # 🐛 CORRIGIDO ("registrei pra Caldeiraria e não chegou nada lá"):
    # antes isso só gravava uma linha informativa aqui dentro — nunca
    # virava uma atividade de verdade no quadro da área (as mesmas
    # "Atividades da Oficina" com Pendente/Em Andamento/Concluído que
    # cada área já usa). Agora chama criar_atividade_oficina() de
    # verdade (mesma função do botão "+ Nova Atividade" de cada área) —
    # reaproveita o push que ela já dispara, então NÃO manda um segundo
    # aviso separado aqui.
    atividade_oficina = criar_atividade_oficina(OficinaAtividade(
        area=dados.area,
        equipamento_id=dados.equipamento_id,
        descricao=f"[Checklist de Execução] {dados.descricao}",
        operador=dados.operador_nome,
        solicitante_matricula=dados.operador_matricula,
    ))
    oficina_atividade_id = atividade_oficina["id"]

    agora = agora_brasil().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO checklist_execucao_atividades_extra
                (execucao_id, equipamento_id, area, descricao, operador_matricula, operador_nome, criado_em, oficina_atividade_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (dados.execucao_id, dados.equipamento_id, dados.area, dados.descricao, dados.operador_matricula, dados.operador_nome, agora, oficina_atividade_id)
        )
        novo_id = cursor.fetchone()["id"]
        conn.commit()

    return {"sucesso": True, "id": novo_id, "oficina_atividade_id": oficina_atividade_id}


@app.get("/api/checklist-execucao/atividades-extra/{execucao_id}", tags=["Checklist de Execução"], summary="Listar atividades extra registradas numa execução")
def listar_atividades_extra_checklist_execucao(execucao_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        # 🆕 JOIN com oficina_atividades pra trazer o status ATUAL (o
        # que a área marcou no quadro dela: Pendente/Em Andamento/
        # Concluído) — sem isso o Checklist de Execução nunca sabia se
        # a área já tinha resolvido ou não.
        cursor.execute(
            """
            SELECT ce.id, ce.area, ce.descricao, ce.operador_matricula, ce.operador_nome, ce.criado_em,
                   ce.oficina_atividade_id,
                   oa.status AS status_atividade, oa.concluido_em AS concluido_em, oa.motivo_status AS motivo_status
            FROM checklist_execucao_atividades_extra ce
            LEFT JOIN oficina_atividades oa ON oa.id = ce.oficina_atividade_id
            WHERE ce.execucao_id = %s
            ORDER BY ce.id DESC
            """,
            (execucao_id,)
        )
        return cursor.fetchall()


@app.post("/api/checklist-execucao/atividade-extra/excluir", tags=["Checklist de Execução"], summary="Excluir uma Atividade Extra (cancela também a atividade real na área)")
def excluir_atividade_extra_checklist_execucao(dados: ChecklistExecucaoAtividadeExtraExcluir):
    """Exclui a linha aqui E a atividade de verdade que ela criou no
    quadro da área (oficina_atividades) — as duas nascem juntas
    (ver registrar_atividade_extra_checklist_execucao), então excluir
    só uma e deixar a outra pra trás confundiria: a área continuaria
    vendo uma atividade pendente que, pro Checklist de Execução, nunca
    existiu."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT oficina_atividade_id FROM checklist_execucao_atividades_extra WHERE id = %s",
            (dados.id,)
        )
        linha = cursor.fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail="Atividade extra não encontrada.")

        cursor.execute("DELETE FROM checklist_execucao_atividades_extra WHERE id = %s", (dados.id,))
        if linha["oficina_atividade_id"]:
            cursor.execute("DELETE FROM oficina_atividades WHERE id = %s", (linha["oficina_atividade_id"],))
        conn.commit()
    return {"sucesso": True}


@app.get("/api/checklist-execucao/historico/{equipamento_id}", tags=["Checklist de Execução"], summary="Histórico completo (inclui retrabalhos)")
def historico_checklist_execucao(equipamento_id: str, limite: int = 200):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT h.id, h.etapa_id, e.area, e.texto, h.acao, h.colaborador,
                   h.tecnico_matricula, h.tecnico_nome, h.data_hora
            FROM checklist_execucao_historico h
            JOIN checklist_execucao_etapas e ON e.id = h.etapa_id
            WHERE h.equipamento_id = %s
            ORDER BY h.id DESC LIMIT %s
            """,
            (equipamento_id, limite)
        )
        return cursor.fetchall()


# ==========================================
# 🆕 ORDENS DE SERVIÇO (OS) — registro digital de OS em papel (várias
# fotos por OS, uma por página), com acompanhamento de status (Em
# Andamento / Concluído).
# ==========================================
@app.get("/api/ordens_servico", tags=["Ordens de Serviço (OS)"], summary="Listar Ordens de Serviço")
def listar_ordens_servico(status: Optional[str] = None, limite: int = 100):
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
            query += " WHERE o.status = %s ORDER BY o.id DESC LIMIT %s"
            cursor.execute(query, (status, limite))
        else:
            query += " ORDER BY o.id DESC LIMIT %s"
            cursor.execute(query, (limite,))
        return cursor.fetchall()


@app.get("/api/ordens_servico/{os_id}/fotos", tags=["Ordens de Serviço (OS)"], summary="Listar páginas (fotos) de uma OS")
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


@app.post("/api/ordens_servico", tags=["Ordens de Serviço (OS)"], summary="Registrar nova Ordem de Serviço")
def criar_ordem_servico(dados: OrdemServicoCriar):
    if not dados.fotos_base64:
        raise HTTPException(status_code=400, detail="É preciso pelo menos 1 foto da OS.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ordens_servico (numero_os, descricao, status, criado_por, criado_em, area)
            VALUES (%s, %s, 'Em Andamento', %s, %s, %s)
            RETURNING id
            """,
            (dados.numero_os, dados.descricao, dados.operador, agora, dados.area)
        )
        os_id = cursor.fetchone()["id"]

        cursor.executemany(
            "INSERT INTO os_fotos (os_id, foto_base64, criado_em) VALUES (%s, %s, %s)",
            [(os_id, foto, agora) for foto in dados.fotos_base64]
        )
        conn.commit()

    # 🆕 Notificação de nova OS cadastrada.
    enviar_push_para_area(
        titulo="🆕 Nova OS cadastrada",
        corpo=f"{dados.operador} registrou {dados.numero_os and f'a OS {dados.numero_os}' or f'a OS #{os_id}'}" + (f": {dados.descricao}" if dados.descricao else "."),
        area="Ambos"
    )

    return {"sucesso": True, "id": os_id}


@app.post("/api/ordens_servico/status", tags=["Ordens de Serviço (OS)"], summary="Mudar status de uma Ordem de Serviço")
def mudar_status_ordem_servico(dados: OrdemServicoStatus):
    if dados.status not in ("Em Andamento", "Concluído", "Não Executada"):
        raise HTTPException(status_code=400, detail="Status inválido.")
    if dados.status == "Não Executada" and not (dados.motivo and dados.motivo.strip()):
        raise HTTPException(status_code=400, detail="Informe o motivo/justificativa pra marcar como Não Executada.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        if dados.status == "Concluído":
            cursor.execute(
                """UPDATE ordens_servico
                   SET status = %s, concluido_por = %s, concluido_em = %s,
                       motivo_nao_executada = NULL, encerrado_por = NULL, encerrado_em = NULL
                   WHERE id = %s""",
                (dados.status, dados.operador, agora, dados.id)
            )
        elif dados.status == "Não Executada":
            cursor.execute(
                """UPDATE ordens_servico
                   SET status = %s, motivo_nao_executada = %s, encerrado_por = %s, encerrado_em = %s,
                       concluido_por = NULL, concluido_em = NULL
                   WHERE id = %s""",
                (dados.status, dados.motivo.strip(), dados.operador, agora, dados.id)
            )
        else:
            # Voltando pra "Em Andamento" — limpa qualquer marcação de
            # conclusão ou de não-execução, já que deixou de valer.
            cursor.execute(
                """UPDATE ordens_servico
                   SET status = %s, concluido_por = NULL, concluido_em = NULL,
                       motivo_nao_executada = NULL, encerrado_por = NULL, encerrado_em = NULL
                   WHERE id = %s""",
                (dados.status, dados.id)
            )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada.")

        cursor.execute("SELECT numero_os FROM ordens_servico WHERE id = %s", (dados.id,))
        os_atual = cursor.fetchone()
        conn.commit()

    # 🆕 Notificação quando a OS é marcada como "Não Executada" (a
    # "atividade não foi concluída" do jeito que ela fica registrada
    # no sistema hoje).
    if dados.status == "Não Executada":
        rotulo_os = f"OS {os_atual['numero_os']}" if os_atual and os_atual["numero_os"] else f"OS #{dados.id}"
        enviar_push_para_area(
            titulo="🚫 OS não executada",
            corpo=f"{dados.operador} marcou {rotulo_os} como não executada. Motivo: {dados.motivo.strip()}",
            area="Ambos"
        )

    return {"sucesso": True}


@app.post("/api/ordens_servico/excluir", tags=["Ordens de Serviço (OS)"], summary="Excluir uma Ordem de Serviço")
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


# ==========================================
# 🆕 QUALIDADE (Entrada/Saída) — registro digital de como o equipamento
# chegou na oficina e como está saindo, com fotos em cada etapa.
# ==========================================
@app.get("/api/qualidade", tags=["Qualidade"], summary="Listar registros de Qualidade")
def listar_qualidade(status: Optional[str] = None, limite: int = 100):
    """Lista os registros com uma foto de "capa" de cada etapa (entrada
    e saída) — pra montar o card na lista sem precisar buscar TODAS as
    fotos de TODOS os registros de uma vez."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT
                r.*,
                (SELECT f.foto_base64 FROM qualidade_fotos f WHERE f.registro_id = r.id AND f.etapa = 'entrada' ORDER BY f.id ASC LIMIT 1) AS foto_entrada_capa,
                (SELECT f.foto_base64 FROM qualidade_fotos f WHERE f.registro_id = r.id AND f.etapa = 'saida' ORDER BY f.id ASC LIMIT 1) AS foto_saida_capa,
                (SELECT COUNT(*) FROM qualidade_achados a WHERE a.registro_id = r.id) AS achados_total,
                (SELECT COUNT(*) FROM qualidade_achados a WHERE a.registro_id = r.id AND a.status = 'Pendente') AS achados_pendentes
            FROM qualidade_registros r
        """
        if status:
            query += " WHERE r.status = %s ORDER BY r.id DESC LIMIT %s"
            cursor.execute(query, (status, limite))
        else:
            query += " ORDER BY r.id DESC LIMIT %s"
            cursor.execute(query, (limite,))
        return cursor.fetchall()


@app.get("/api/qualidade/{registro_id}/fotos", tags=["Qualidade"], summary="Listar fotos (entrada ou saída) de um registro")
def get_fotos_qualidade(registro_id: int, etapa: str):
    if etapa not in ("entrada", "saida"):
        raise HTTPException(status_code=400, detail="Etapa inválida.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, foto_base64, criado_em FROM qualidade_fotos WHERE registro_id = %s AND etapa = %s ORDER BY id ASC",
            (registro_id, etapa)
        )
        return cursor.fetchall()


@app.post("/api/qualidade", tags=["Qualidade"], summary="Registrar entrada de um equipamento na oficina")
def criar_qualidade(dados: QualidadeCriar):
    if not dados.fotos_entrada_base64:
        raise HTTPException(status_code=400, detail="É preciso pelo menos 1 foto de entrada.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO qualidade_registros (peca_id, observacao_entrada, status, criado_por, criado_em)
            VALUES (%s, %s, 'Aguardando Saída', %s, %s)
            RETURNING id
            """,
            (dados.peca_id, dados.observacao_entrada, dados.operador, agora)
        )
        registro_id = cursor.fetchone()["id"]

        cursor.executemany(
            "INSERT INTO qualidade_fotos (registro_id, etapa, foto_base64, criado_em) VALUES (%s, 'entrada', %s, %s)",
            [(registro_id, foto, agora) for foto in dados.fotos_entrada_base64]
        )

        if dados.achados:
            for a in dados.achados:
                if not a.descricao or not a.descricao.strip():
                    continue
                cursor.execute(
                    """INSERT INTO qualidade_achados (registro_id, descricao, status, criado_por, criado_em)
                       VALUES (%s, %s, 'Pendente', %s, %s)
                       RETURNING id""",
                    (registro_id, a.descricao.strip(), dados.operador, agora)
                )
                achado_id = cursor.fetchone()["id"]
                if a.fotos_base64:
                    cursor.executemany(
                        "INSERT INTO qualidade_achado_fotos (achado_id, foto_base64, criado_em) VALUES (%s, %s, %s)",
                        [(achado_id, foto, agora) for foto in a.fotos_base64]
                    )

        conn.commit()

    return {"sucesso": True, "id": registro_id}


@app.post("/api/qualidade/{registro_id}/saida", tags=["Qualidade"], summary="Registrar saída de um equipamento da oficina")
def registrar_saida_qualidade(registro_id: int, dados: QualidadeSaida):
    if not dados.fotos_saida_base64:
        raise HTTPException(status_code=400, detail="É preciso pelo menos 1 foto de saída.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE qualidade_registros
               SET status = 'Concluído', observacao_saida = %s, concluido_por = %s, concluido_em = %s
               WHERE id = %s""",
            (dados.observacao_saida, dados.operador, agora, registro_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de qualidade não encontrado.")

        cursor.executemany(
            "INSERT INTO qualidade_fotos (registro_id, etapa, foto_base64, criado_em) VALUES (%s, 'saida', %s, %s)",
            [(registro_id, foto, agora) for foto in dados.fotos_saida_base64]
        )
        conn.commit()

    return {"sucesso": True}


@app.post("/api/qualidade/excluir", tags=["Qualidade"], summary="Excluir um registro de Qualidade")
def excluir_qualidade(dados: QualidadeExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        # qualidade_fotos e qualidade_achados têm ON DELETE CASCADE —
        # apagar o registro já apaga fotos e achados junto.
        cursor.execute("DELETE FROM qualidade_registros WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de qualidade não encontrado.")
        conn.commit()

    return {"sucesso": True}


# ---- ACHADOS: cada problema encontrado pela Qualidade vira uma linha
# própria (com fotos opcionais), separada da observação geral, com
# status individual Pendente/Resolvido. ----
@app.get("/api/qualidade/{registro_id}/achados", tags=["Qualidade"], summary="Listar achados de um registro")
def listar_achados_qualidade(registro_id: int):
    """Traz cada achado com uma foto de "capa" (a primeira, se tiver
    mais de uma) e o total de fotos — pra montar o card na lista sem
    precisar buscar todas as fotos de todos os achados de uma vez."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                a.*,
                COALESCE(
                    (SELECT f.foto_base64 FROM qualidade_achado_fotos f WHERE f.achado_id = a.id ORDER BY f.id ASC LIMIT 1),
                    a.foto_base64
                ) AS foto_capa,
                (SELECT COUNT(*) FROM qualidade_achado_fotos f WHERE f.achado_id = a.id) AS total_fotos
            FROM qualidade_achados a
            WHERE a.registro_id = %s
            ORDER BY a.id ASC
            """,
            (registro_id,)
        )
        return cursor.fetchall()


@app.get("/api/qualidade/achados/{achado_id}/fotos", tags=["Qualidade"], summary="Listar todas as fotos de um achado")
def get_fotos_achado_qualidade(achado_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, foto_base64, criado_em FROM qualidade_achado_fotos WHERE achado_id = %s ORDER BY id ASC",
            (achado_id,)
        )
        fotos = cursor.fetchall()

        # 🔧 Achado antigo (de antes dessa mudança) só tem a foto na
        # coluna foto_base64 da própria tabela, não em
        # qualidade_achado_fotos — cai aqui como fallback pra galeria
        # não aparecer vazia pra quem já tinha achado cadastrado.
        if not fotos:
            cursor.execute("SELECT foto_base64 FROM qualidade_achados WHERE id = %s", (achado_id,))
            achado = cursor.fetchone()
            if achado and achado["foto_base64"]:
                return [{"id": None, "foto_base64": achado["foto_base64"], "criado_em": None}]

        return fotos


@app.post("/api/qualidade/achados", tags=["Qualidade"], summary="Adicionar um achado a um registro de Qualidade")
def criar_achado_qualidade(dados: QualidadeAchadoCriar):
    if not dados.descricao or not dados.descricao.strip():
        raise HTTPException(status_code=400, detail="Descreva o achado.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT peca_id FROM qualidade_registros WHERE id = %s", (dados.registro_id,))
        registro = cursor.fetchone()
        if not registro:
            raise HTTPException(status_code=404, detail="Registro de qualidade não encontrado.")

        cursor.execute(
            """
            INSERT INTO qualidade_achados (registro_id, descricao, status, criado_por, criado_em)
            VALUES (%s, %s, 'Pendente', %s, %s)
            RETURNING id
            """,
            (dados.registro_id, dados.descricao.strip(), dados.operador, agora)
        )
        achado_id = cursor.fetchone()["id"]

        if dados.fotos_base64:
            cursor.executemany(
                "INSERT INTO qualidade_achado_fotos (achado_id, foto_base64, criado_em) VALUES (%s, %s, %s)",
                [(achado_id, foto, agora) for foto in dados.fotos_base64]
            )

        conn.commit()

    # 🆕 Achado de Qualidade era o único evento "problema encontrado" do
    # sistema que não avisava ninguém — a única forma de saber era abrir
    # o registro manualmente. Agora avisa como os demais eventos críticos
    # (área "Ambos": não tem área da oficina associada, só os admins).
    enviar_push_para_area(
        titulo="🔍 Achado de Qualidade",
        corpo=f"{dados.operador} — {registro['peca_id']}: {dados.descricao.strip()}",
        area="Ambos"
    )

    return {"sucesso": True, "id": achado_id}


@app.post("/api/qualidade/achados/editar", tags=["Qualidade"], summary="Editar a descrição de um achado")
def editar_achado_qualidade(dados: QualidadeAchadoEditar):
    if not dados.descricao or not dados.descricao.strip():
        raise HTTPException(status_code=400, detail="Descreva o achado.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE qualidade_achados SET descricao = %s WHERE id = %s",
            (dados.descricao.strip(), dados.id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}


@app.post("/api/qualidade/achados/resolver", tags=["Qualidade"], summary="Marcar um achado como resolvido")
def resolver_achado_qualidade(dados: QualidadeAchadoResolver):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE qualidade_achados
               SET status = 'Resolvido', foto_resolucao_base64 = %s, resolvido_por = %s, resolvido_em = %s
               WHERE id = %s""",
            (dados.foto_base64, dados.operador, agora, dados.id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}


@app.post("/api/qualidade/achados/reabrir", tags=["Qualidade"], summary="Reabrir um achado marcado como resolvido")
def reabrir_achado_qualidade(dados: QualidadeAchadoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE qualidade_achados
               SET status = 'Pendente', foto_resolucao_base64 = NULL, resolvido_por = NULL, resolvido_em = NULL
               WHERE id = %s""",
            (dados.id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}


@app.post("/api/qualidade/achados/excluir", tags=["Qualidade"], summary="Excluir um achado")
def excluir_achado_qualidade(dados: QualidadeAchadoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM qualidade_achados WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}


# ==========================================
# 🆕 LAUDOS (PDFs de folhão finalizado) — antes só existiam no
# localStorage de quem gerava; agora persistem no Neon, visíveis pra
# todo mundo na Auditoria (igual o resto do histórico).
# ==========================================
@app.get("/api/laudos", tags=["Laudos"], summary="Listar laudos gerados")
def listar_laudos(peca_id: Optional[str] = None, limite: int = 200):
    with get_db() as conn:
        cursor = conn.cursor()
        if peca_id:
            cursor.execute(
                "SELECT * FROM laudos WHERE peca_id = %s ORDER BY id DESC LIMIT %s",
                (peca_id, limite)
            )
        else:
            cursor.execute("SELECT * FROM laudos ORDER BY id DESC LIMIT %s", (limite,))
        return cursor.fetchall()


@app.get("/api/laudos/{laudo_id}", tags=["Laudos"], summary="Consultar um laudo específico")
def get_laudo(laudo_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM laudos WHERE id = %s", (laudo_id,))
        laudo = cursor.fetchone()
        if not laudo:
            raise HTTPException(status_code=404, detail="Laudo não encontrado.")
        return laudo


@app.post("/api/laudos", tags=["Laudos"], summary="Salvar um laudo gerado")
def criar_laudo(dados: LaudoCriar):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO laudos (peca_id, tipo, html, criado_por, criado_em) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (dados.peca_id, dados.tipo, dados.html, dados.operador, agora)
        )
        laudo_id = cursor.fetchone()["id"]
        conn.commit()

    return {"sucesso": True, "id": laudo_id}


@app.post("/api/laudos/excluir", tags=["Laudos"], summary="Excluir um laudo")
def excluir_laudo(dados: LaudoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM laudos WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Laudo não encontrado.")
        conn.commit()

    return {"sucesso": True}