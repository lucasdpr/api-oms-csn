from fastapi import APIRouter, HTTPException
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


@router.get("/api/mensagens_area", tags=["Mensagens Área-ADM"], summary="Listar conversa de uma área — canal 'supervisao' (área<->ADM) ou 'tecnicos' (só entre a área, supervisão só lê)")
def get_mensagens_area(area: str, canal: str = "supervisao"):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, area, de_adm, remetente, remetente_matricula, mensagem, foto_base64, canal, atividade_referencia, criado_em, lida
            FROM mensagens_area_adm
            WHERE area = %s AND canal = %s
            ORDER BY id ASC
            """,
            (area, canal)
        )
        return cursor.fetchall()


@router.get("/api/mensagens_area/resumo", tags=["Mensagens Área-ADM"], summary="Resumo por área — última mensagem e não lidas do canal 'supervisao' (visão do ADM)")
def get_mensagens_area_resumo():
    with get_db() as conn:
        cursor = conn.cursor()
        # 🆕 Só o canal 'supervisao' entra no resumo — é o que aparece como
        # badge/prévia na lista de conversas do ADM. O canal 'tecnicos' é
        # visualizado à parte (aba "Entre Técnicos" dentro da mesma
        # conversa), sem contar pra esse resumo.
        cursor.execute(
            """
            SELECT area,
                   MAX(criado_em) AS ultima_em,
                   SUM(CASE WHEN de_adm = FALSE AND lida = FALSE THEN 1 ELSE 0 END) AS nao_lidas
            FROM mensagens_area_adm
            WHERE canal = 'supervisao'
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


@router.post("/api/mensagens_area", tags=["Mensagens Área-ADM"], summary="Enviar mensagem (texto e/ou foto) na conversa área <-> ADM")
def enviar_mensagem_area(dados: MensagemAreaAdmEnviar):
    # 🆕 Com a foto virando opcional, precisa ter pelo menos UM dos dois —
    # senão seria uma mensagem completamente vazia.
    texto = (dados.mensagem or "").strip()
    if not texto and not dados.foto_base64:
        raise HTTPException(status_code=400, detail="Mande um texto ou uma foto.")

    canal = dados.canal if dados.canal in ("supervisao", "tecnicos") else "supervisao"
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mensagens_area_adm (area, de_adm, remetente, remetente_matricula, mensagem, foto_base64, canal, atividade_referencia, criado_em, lida)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            RETURNING id
            """,
            (dados.area, dados.de_adm, dados.remetente, dados.remetente_matricula, texto, dados.foto_base64, canal, dados.atividade_referencia, agora)
        )
        nova_id = cursor.fetchone()["id"]
        conn.commit()

    nome_area = AREA_OFICINA_NOMES.get(dados.area, dados.area)
    corpo_push = texto if texto else "📷 Foto enviada"
    if canal == "tecnicos":
        # 🆕 Canal "Entre Técnicos" — avisa só quem é da própria área (não
        # incomoda o ADM com push; ele pode ver quando quiser, na aba
        # "Entre Técnicos" da mesma conversa).
        enviar_push_para_area(
            titulo=f"💬 {nome_area} (entre técnicos)",
            corpo=f"{dados.remetente or 'Técnico'}: {corpo_push}",
            area=dados.area,
            url="/app.html#area-oficina",
            dados_extra={"tipo_evento": "mensagem_area_tecnicos", "area": dados.area}
        )
    elif dados.de_adm:
        # ADM respondeu -> avisa quem está na área.
        enviar_push_para_area(
            titulo=f"💬 ADM respondeu — {nome_area}",
            corpo=corpo_push,
            area=dados.area,
            url="/app.html#area-oficina",
            dados_extra={"tipo_evento": "mensagem_adm", "area": dados.area}
        )
    else:
        # Área mandou -> avisa o ADM (mesmo mecanismo de "Ambos" já usado
        # por qualquer evento sem destino de técnico específico).
        enviar_push_para_area(
            titulo=f"💬 Mensagem da {nome_area}",
            corpo=f"{dados.remetente or 'Técnico'}: {corpo_push}",
            area="Ambos",
            url="/app.html#painel-adm",
            dados_extra={"tipo_evento": "mensagem_area", "area": dados.area}
        )

    return {"sucesso": True, "id": nova_id}


@router.post("/api/mensagens_area/marcar_lida", tags=["Mensagens Área-ADM"], summary="Marcar como lidas as mensagens de um lado da conversa")
def marcar_mensagens_area_lidas(dados: MensagemAreaAdmMarcarLida):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        # Quem chama é quem LEU — então marca como lida a mensagem que
        # partiu do OUTRO lado (de_adm invertido em relação a quem pediu).
        # 🆕 canal = 'supervisao' explícito — a contagem de não lidas só
        # existe pro canal principal (área<->ADM); "Entre Técnicos" não
        # tem badge de não lida, então nunca deve ser tocado aqui.
        cursor.execute(
            "UPDATE mensagens_area_adm SET lida = TRUE WHERE area = %s AND canal = 'supervisao' AND de_adm = %s AND lida = FALSE RETURNING id",
            (dados.area, not dados.de_adm)
        )
        ids_marcados = [linha["id"] for linha in cursor.fetchall()]
        # 🐛 CORREÇÃO ("respondi no ADM e não sumiu da Central"): ler a
        # conversa aqui só marcava lida em mensagens_area_adm — a Central
        # de Notificações usa uma tabela separada (notificacoes_lidas,
        # por matrícula). Sem isso, a mensagem lida no chat continuava
        # aparecendo como não-lida na Central pra sempre.
        if dados.matricula and ids_marcados:
            matricula = dados.matricula.strip().upper()
            for msg_id in ids_marcados:
                cursor.execute(
                    """
                    INSERT INTO notificacoes_lidas (tipo, evento_id, matricula, lido_em)
                    VALUES ('mensagem_area', %s, %s, %s)
                    ON CONFLICT (tipo, evento_id, matricula) DO NOTHING
                    """,
                    (str(msg_id), matricula, agora)
                )
        conn.commit()
    return {"sucesso": True}
