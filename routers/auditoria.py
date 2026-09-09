from fastapi import APIRouter
from app_core import (
    EventoLog,
    Optional,
    TAGS_AUDITORIA_SEM_NOTIFICACAO,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




@router.post("/api/registrar_evento", tags=["Auditoria"], summary="Registrar um evento na Auditoria")
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




@router.get("/api/historico_eventos", tags=["Auditoria"], summary="Consultar o histórico completo de eventos")
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
