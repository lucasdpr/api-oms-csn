from fastapi import APIRouter, HTTPException
from app_core import (
    NotificacaoMarcarLida,
    PUSH_HABILITADO,
    PushSubscribe,
    PushUnsubscribe,
    VAPID_PUBLIC_KEY,
    agora_brasil,
    get_db,
)

router = APIRouter()




@router.get("/api/notificacoes/feed", tags=["Notificações Push"], summary="Feed unificado da Central de Notificações (com lido/não-lido por matrícula)")
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
            WHERE e.categoria IS NOT NULL AND e.categoria != 'Atividade Oficina'
            ORDER BY e.id DESC
            LIMIT %s
        """, (matricula, limite))
        eventos = cursor.fetchall()

        # 🆕 Toda ação numa atividade da Oficina (criar/mudar status/
        # editar/excluir/mensagem) — ver registrar_evento_atividade_
        # oficina. Categoria própria (não entra na query de Ocorrência
        # acima) porque clicar nisso no front abre a "Conversa da
        # Atividade" direto (via atividade_id, quando presente) em vez
        # de ir pro Registro de Ocorrência.
        cursor.execute("""
            SELECT 'atividade' AS tipo, e.id::text AS evento_id, e.area, e.peca_id AS referencia,
                   e.acao AS descricao, e.operador AS autor, e.data_hora, e.atividade_id,
                   COALESCE(e.tipo_evento, 'status') AS tipo_evento,
                   (l.matricula IS NOT NULL) AS lida
            FROM log_eventos e
            LEFT JOIN notificacoes_lidas l
                ON l.tipo = 'atividade' AND l.evento_id = e.id::text AND l.matricula = %s
            WHERE e.categoria = 'Atividade Oficina'
            ORDER BY e.id DESC
            LIMIT %s
        """, (matricula, limite))
        atividades_evt = cursor.fetchall()

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

    todos = list(eventos) + list(ordens) + list(achados) + list(estoque) + list(sinotico) + list(atividades_evt)
    todos.sort(key=lambda x: x["data_hora"] or "", reverse=True)
    return todos[:limite]




@router.post("/api/notificacoes/marcar_lido", tags=["Notificações Push"], summary="Marcar uma notificação do feed como lida por uma matrícula")
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




@router.get("/api/push/vapid_public_key", tags=["Notificações Push"], summary="Obter a chave pública VAPID")
def get_vapid_public_key():
    if not PUSH_HABILITADO:
        raise HTTPException(status_code=503, detail="Push notification não configurado no servidor.")
    return {"publicKey": VAPID_PUBLIC_KEY}




@router.post("/api/push/subscribe", tags=["Notificações Push"], summary="Inscrever dispositivo pra notificações push")
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




@router.post("/api/push/unsubscribe", tags=["Notificações Push"], summary="Cancelar inscrição de notificações push")
def unsubscribe_push(dados: PushUnsubscribe):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (dados.endpoint,))
        conn.commit()
    return {"sucesso": True}


# ==========================================
# 📸 REGISTRO COM FOTO E CATEGORIA
# ==========================================
