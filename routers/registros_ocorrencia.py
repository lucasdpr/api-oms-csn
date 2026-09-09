from fastapi import APIRouter
from app_core import (
    Optional,
    RegistroComFoto,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




# ==========================================
# 📸 REGISTRO COM FOTO E CATEGORIA
# ==========================================
@router.post("/api/registro_com_foto", tags=["Registros e Ocorrências"], summary="Registrar Intervenção/Melhoria/Comentário/Ocorrência com foto")
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




@router.get("/api/registros_ocorrencia", tags=["Registros e Ocorrências"], summary="Listar ocorrências registradas")
def get_registros_ocorrencia(categoria: Optional[str] = None, limite: int = 100):
    with get_db() as conn:
        cursor = conn.cursor()
        # 🔧 CORREÇÃO ("Registro de Ocorrência mostra atividade de área e
        # conversa junto"): esta rota nunca excluía categoria='Atividade
        # Oficina' — apesar de um comentário em /api/notificacoes/feed
        # (a Central de Notificações) já afirmar "mesmo filtro que
        # /api/registros_ocorrencia sempre usou". Não usava: qualquer
        # evento de Atividade da Oficina (criar/mudar status/mensagem —
        # ver registrar_evento_atividade_oficina) grava em log_eventos
        # com essa categoria própria, e como `categoria IS NOT NULL`
        # também é verdade pra ela, esses eventos entravam aqui junto
        # com as ocorrências de verdade (Intervenção/Melhoria/Comentário/
        # Atividade Pendente, criadas em /api/registro_com_foto).
        # Replicado o mesmo filtro que a Central de Notificações usa.
        if categoria:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria, e.area,
                       f.foto_base64
                FROM log_eventos e
                LEFT JOIN fotos_registro f ON f.evento_id = e.id
                WHERE e.categoria = %s AND e.categoria != 'Atividade Oficina'
                ORDER BY e.id DESC
                LIMIT %s
            """, (categoria, limite))
        else:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria, e.area,
                       f.foto_base64
                FROM log_eventos e
                LEFT JOIN fotos_registro f ON f.evento_id = e.id
                WHERE e.categoria IS NOT NULL AND e.categoria != 'Atividade Oficina'
                ORDER BY e.id DESC
                LIMIT %s
            """, (limite,))
        return cursor.fetchall()


# ==========================================
# OFICINA — ATIVIDADES POR ÁREA (v1)
# ==========================================
