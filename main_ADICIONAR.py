# ==============================================================
# ADICIONAR AO main.py — Sistema de Push Notification
# ==============================================================
# Instruções:
#  1. Adicione "pywebpush" no requirements.txt e rode
#     "pip install pywebpush" localmente pra testar.
#  2. Cole os imports abaixo perto do topo do main.py (junto com os
#     outros imports).
#  3. Cole o bloco "CONFIGURAÇÃO VAPID" logo depois da configuração
#     do DATABASE_URL.
#  4. Cole as duas novas tabelas (push_subscriptions e o ALTER de
#     colaboradores) dentro da função init_db(), junto das outras
#     CREATE TABLE.
#  5. Cole os modelos Pydantic novos junto dos outros modelos.
#  6. Cole as rotas novas (get_vapid_public_key, subscribe_push,
#     unsubscribe_push) junto das outras rotas.
#  7. Cole a função enviar_push_para_area(...) em qualquer lugar
#     depois da configuração VAPID.
#  8. Chame enviar_push_para_area(...) nos pontos indicados no final
#     deste arquivo (dentro de apontar_producao_geral,
#     registrar_evento, salvar_rascunho_folhao).
# ==============================================================


# --------------------------------------------------------------
# 1) IMPORTS (adicionar no topo do main.py)
# --------------------------------------------------------------
from pywebpush import webpush, WebPushException
import json as json_lib


# --------------------------------------------------------------
# 2) CONFIGURAÇÃO VAPID (adicionar depois do DATABASE_URL)
# --------------------------------------------------------------
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_EMAIL = os.environ.get("VAPID_EMAIL", "mailto:contato@exemplo.com")

# Não trava a API se as chaves ainda não estiverem configuradas —
# só desliga o push (o resto do app continua funcionando normal).
PUSH_HABILITADO = bool(VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY)
if not PUSH_HABILITADO:
    print("⚠️ VAPID_PRIVATE_KEY/VAPID_PUBLIC_KEY não configuradas — push notification desativado.")


# --------------------------------------------------------------
# 3) TABELAS NOVAS (colar dentro de init_db(), junto das outras)
# --------------------------------------------------------------
"""
        # Área do colaborador, usada pra filtrar quem recebe cada tipo de
        # notificação (ex: só "Mecânico" recebe alerta de equipamento
        # crítico da área dele; "Técnico" recebe alerta de produção).
        # Valores esperados: 'Técnico', 'Mecânico', 'Ambos'.
        cursor.execute('''
            ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS area TEXT DEFAULT 'Ambos'
        ''')

        # Inscrições de push notification (Web Push API). Cada celular/
        # navegador que aceitar receber notificação gera uma "subscription"
        # única, salva aqui vinculada à matrícula. Um colaborador pode ter
        # mais de uma inscrição (ex: logou em 2 celulares diferentes).
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
"""


# --------------------------------------------------------------
# 4) MODELOS NOVOS (colar junto dos outros modelos Pydantic)
# --------------------------------------------------------------
class PushSubscribe(BaseModel):
    matricula: str
    endpoint: str
    p256dh: str
    auth: str


class PushUnsubscribe(BaseModel):
    endpoint: str


# --------------------------------------------------------------
# 5) FUNÇÃO CENTRAL DE ENVIO (colar em qualquer lugar após a config VAPID)
# --------------------------------------------------------------
def enviar_push_para_area(titulo: str, corpo: str, area: str = "Ambos", url: str = "/"):
    """
    Manda push notification pra todo mundo inscrito que seja da área
    informada (ou 'Ambos' inscritos sempre recebem tudo).

    area: 'Técnico', 'Mecânico' ou 'Ambos' (manda pra todos, sem filtro).
    Nunca lança exceção pra fora — se o push falhar, só loga o erro;
    isso NUNCA deve derrubar a rota principal (ex: lançar produção tem
    que funcionar mesmo se a notificação falhar).
    """
    if not PUSH_HABILITADO:
        return

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if area == "Ambos":
                cursor.execute("""
                    SELECT ps.endpoint, ps.p256dh, ps.auth
                    FROM push_subscriptions ps
                """)
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
                # Erro 404/410 = a inscrição não existe mais (ex: usuário
                # desinstalou o app ou trocou de celular) — marca pra
                # limpar do banco, não precisa alarmar por isso.
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
        # Rede fora do ar, banco caído etc — nunca deixa isso quebrar
        # a rota que chamou o envio.
        print(f"⚠️ Falha geral ao processar envio de push: {e}")


# --------------------------------------------------------------
# 6) ROTAS NOVAS (colar junto das outras rotas @app.get/@app.post)
# --------------------------------------------------------------
@app.get("/api/push/vapid_public_key")
def get_vapid_public_key():
    """O front-end chama essa rota pra saber qual chave pública usar
    ao pedir permissão de notificação no navegador."""
    if not PUSH_HABILITADO:
        raise HTTPException(status_code=503, detail="Push notification não configurado no servidor.")
    return {"publicKey": VAPID_PUBLIC_KEY}


@app.post("/api/push/subscribe")
def subscribe_push(dados: PushSubscribe):
    """Registra (ou atualiza) a inscrição de push de um celular/navegador,
    vinculada à matrícula do colaborador logado."""
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
    """Remove a inscrição (ex: usuário desligou notificações nas
    configurações do app)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (dados.endpoint,))
        conn.commit()
    return {"sucesso": True}


# --------------------------------------------------------------
# 7) ONDE DISPARAR O PUSH (adicionar dentro das rotas já existentes)
# --------------------------------------------------------------

# --- Dentro de apontar_producao_geral(), logo ANTES do "return {"sucesso": True}":
"""
    enviar_push_para_area(
        titulo="📦 Produção atualizada",
        corpo=f"{dados.operador} lançou produção geral (MCC2: {dados.qtd_mcc2}t, MCC3: {dados.qtd_mcc3}t, MCC4: {dados.qtd_mcc4}t).",
        area="Ambos"
    )
"""

# --- Dentro de registrar_evento(), logo ANTES do "return {"sucesso": True}":
#     (esse é o endpoint chamado quando um registro/ação é feito num equipamento)
"""
    # Só dispara push para eventos considerados críticos — ajuste essa
    # lista de palavras-chave conforme os textos reais que o front manda
    # em "acao" (ex: alarmes, quebras, B.O.).
    PALAVRAS_CRITICAS = ["b.o", "blackout", "quebra", "fim de vida", "alarme"]
    is_critico = any(p in evento.acao.lower() for p in PALAVRAS_CRITICAS)

    enviar_push_para_area(
        titulo="🚨 Evento crítico" if is_critico else "📋 Registro no equipamento",
        corpo=f"{evento.operador} — {evento.peca_id}: {evento.acao}",
        area="Mecânico" if is_critico else "Ambos"
    )
"""
