from fastapi import APIRouter, HTTPException
from app_core import (
    Optional,
    OrdemServicoCriar,
    OrdemServicoExcluir,
    OrdemServicoStatus,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




# ==========================================
# 🆕 ORDENS DE SERVIÇO (OS) — registro digital de OS em papel (várias
# fotos por OS, uma por página), com acompanhamento de status (Em
# Andamento / Concluído).
# ==========================================
@router.get("/api/ordens_servico", tags=["Ordens de Serviço (OS)"], summary="Listar Ordens de Serviço")
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




@router.get("/api/ordens_servico/{os_id}/fotos", tags=["Ordens de Serviço (OS)"], summary="Listar páginas (fotos) de uma OS")
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




@router.post("/api/ordens_servico", tags=["Ordens de Serviço (OS)"], summary="Registrar nova Ordem de Serviço")
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




@router.post("/api/ordens_servico/status", tags=["Ordens de Serviço (OS)"], summary="Mudar status de uma Ordem de Serviço")
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




@router.post("/api/ordens_servico/excluir", tags=["Ordens de Serviço (OS)"], summary="Excluir uma Ordem de Serviço")
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
