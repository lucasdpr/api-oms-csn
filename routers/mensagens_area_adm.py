from fastapi import APIRouter
from app_core import (
    MensagemAreaAdmEnviar,
    MensagemAreaAdmMarcarLida,
    AREA_OFICINA_NOMES,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()

# ==========================================================================
# CHAT ÁREA <-> ADM — pedido do usuário: "as áreas podem enviar mensagem
# pra área de adm?". Antes disso, nenhuma área tinha canal formal pra
# avisar o ADM de algo — o ADM só via tudo passivamente pelos eventos
# automáticos (nova atividade, atraso, etc). Aqui é uma conversa
# persistente por área, igual um chat: qualquer lado manda mensagem, o
# outro lado recebe push, e dá pra ver o histórico depois.
# ==========================================================================


@router.get("/api/mensagens_area", tags=["Mensagens Área-ADM"], summary="Listar conversa de uma área com o ADM")
def get_mensagens_area(area: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, area, de_adm, remetente, remetente_matricula, mensagem, criado_em, lida
            FROM mensagens_area_adm
            WHERE area = %s
            ORDER BY id ASC
            """,
            (area,)
        )
        return cursor.fetchall()


@router.get("/api/mensagens_area/resumo", tags=["Mensagens Área-ADM"], summary="Resumo por área — última mensagem e não lidas (visão do ADM)")
def get_mensagens_area_resumo():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT area,
                   MAX(criado_em) AS ultima_em,
                   SUM(CASE WHEN de_adm = FALSE AND lida = FALSE THEN 1 ELSE 0 END) AS nao_lidas
            FROM mensagens_area_adm
            GROUP BY area
            ORDER BY ultima_em DESC
            """
        )
        linhas = cursor.fetchall()
        for linha in linhas:
            linha["nome_area"] = AREA_OFICINA_NOMES.get(linha["area"], linha["area"])
        return linhas


@router.get("/api/mensagens_area/nao_lidas", tags=["Mensagens Área-ADM"], summary="Quantidade de mensagens do ADM não lidas por uma área")
def get_mensagens_area_nao_lidas(area: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS qtd FROM mensagens_area_adm WHERE area = %s AND de_adm = TRUE AND lida = FALSE",
            (area,)
        )
        return {"nao_lidas": cursor.fetchone()["qtd"]}


@router.post("/api/mensagens_area", tags=["Mensagens Área-ADM"], summary="Enviar mensagem na conversa área <-> ADM")
def enviar_mensagem_area(dados: MensagemAreaAdmEnviar):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mensagens_area_adm (area, de_adm, remetente, remetente_matricula, mensagem, criado_em, lida)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
            RETURNING id
            """,
            (dados.area, dados.de_adm, dados.remetente, dados.remetente_matricula, dados.mensagem, agora)
        )
        nova_id = cursor.fetchone()["id"]
        conn.commit()

    nome_area = AREA_OFICINA_NOMES.get(dados.area, dados.area)
    if dados.de_adm:
        # ADM respondeu -> avisa quem está na área.
        enviar_push_para_area(
            titulo=f"💬 ADM respondeu — {nome_area}",
            corpo=dados.mensagem,
            area=dados.area,
            url="/app.html#area-oficina",
            dados_extra={"tipo_evento": "mensagem_adm", "area": dados.area}
        )
    else:
        # Área mandou -> avisa o ADM (mesmo mecanismo de "Ambos" já usado
        # por qualquer evento sem destino de técnico específico).
        enviar_push_para_area(
            titulo=f"💬 Mensagem da {nome_area}",
            corpo=f"{dados.remetente or 'Técnico'}: {dados.mensagem}",
            area="Ambos",
            url="/app.html#painel-adm",
            dados_extra={"tipo_evento": "mensagem_area", "area": dados.area}
        )

    return {"sucesso": True, "id": nova_id}


@router.post("/api/mensagens_area/marcar_lida", tags=["Mensagens Área-ADM"], summary="Marcar como lidas as mensagens de um lado da conversa")
def marcar_mensagens_area_lidas(dados: MensagemAreaAdmMarcarLida):
    with get_db() as conn:
        cursor = conn.cursor()
        # Quem chama é quem LEU — então marca como lida a mensagem que
        # partiu do OUTRO lado (de_adm invertido em relação a quem pediu).
        cursor.execute(
            "UPDATE mensagens_area_adm SET lida = TRUE WHERE area = %s AND de_adm = %s AND lida = FALSE",
            (dados.area, not dados.de_adm)
        )
        conn.commit()
    return {"sucesso": True}
