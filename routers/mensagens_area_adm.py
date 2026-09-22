import time

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app_core import (
    MensagemAreaAdmEnviar,
    MensagemAreaAdmMarcarLida,
    MensagemAreaAdmDigitando,
    AREA_OFICINA_NOMES,
    agora_brasil,
    enviar_push_para_area,
    exigir_login,
    get_db,
)

router = APIRouter()

# 🆕 "Está digitando..." no canal Entre Técnicos (área<->área) — pedido
# do usuário, igual WhatsApp. É estado EFÊMERO (só importa por poucos
# segundos), por isso fica em memória do processo, não no banco — não
# faz sentido gastar linha de tabela/gravação persistente pra isso.
# Chave: (area_de_quem_digita, area_destino). Valor: timestamp (epoch)
# do último "ping" de digitação. Uma entrada mais velha que
# DIGITANDO_TTL_SEGUNDOS é tratada como "parou de digitar".
# ⚠️ Só funciona certo com 1 worker/processo (Render free tier já roda
# assim) — com múltiplos workers cada um teria sua própria cópia deste
# dicionário, e o ping podia cair num worker diferente da consulta.
_DIGITANDO: dict[tuple[str, str], float] = {}
DIGITANDO_TTL_SEGUNDOS = 4

# ==========================================================================
# CHAT ÁREA <-> ADM — pedido do usuário: "as áreas podem enviar mensagem
# pra área de adm?". Antes disso, nenhuma área tinha canal formal pra
# avisar o ADM de algo — o ADM só via tudo passivamente pelos eventos
# automáticos (nova atividade, atraso, etc). Aqui é uma conversa
# persistente por área, igual um chat: qualquer lado manda mensagem, o
# outro lado recebe push, e dá pra ver o histórico depois.
#
# 🆕 canal 'tecnicos' virou ÁREA-A-ÁREA (pedido do usuário, com exemplo:
# "caldeiraria tem que ter chat com o molde, bender, zero etc, tem que
# ter com todos, e o molde tem que ter com bender, zero etc e todas as
# áreas"). Cada mensagem tem `area` (quem mandou) e `area_destino` (a
# área alvo daquela mensagem); a conversa entre X e Y é a união das
# linhas nos dois sentidos. `area_destino` é sempre NULL no canal
# 'supervisao' (o alvo ali é sempre o ADM).
# ==========================================================================


@router.get("/api/mensagens_area", tags=["Mensagens Área-ADM"], summary="Listar conversa — canal 'supervisao' (área<->ADM) ou 'tecnicos' (área<->área, exige area_destino)")
def get_mensagens_area(area: str, canal: str = "supervisao", area_destino: Optional[str] = None, _matricula: str = Depends(exigir_login)):
    with get_db() as conn:
        cursor = conn.cursor()
        if canal == "tecnicos":
            if not area_destino:
                raise HTTPException(status_code=400, detail="area_destino é obrigatório no canal 'tecnicos'.")
            cursor.execute(
                """
                SELECT id, area, area_destino, de_adm, remetente, remetente_matricula, mensagem, foto_base64, canal, atividade_referencia, criado_em, lida
                FROM mensagens_area_adm
                WHERE canal = 'tecnicos' AND (
                    (area = %s AND area_destino = %s) OR (area = %s AND area_destino = %s)
                )
                ORDER BY id ASC
                """,
                (area, area_destino, area_destino, area)
            )
        else:
            cursor.execute(
                """
                SELECT id, area, area_destino, de_adm, remetente, remetente_matricula, mensagem, foto_base64, canal, atividade_referencia, criado_em, lida
                FROM mensagens_area_adm
                WHERE area = %s AND canal = %s
                ORDER BY id ASC
                """,
                (area, canal)
            )
        return cursor.fetchall()


@router.get("/api/mensagens_area/resumo", tags=["Mensagens Área-ADM"], summary="Resumo por área — última mensagem e não lidas do canal 'supervisao' (visão do ADM)")
def get_mensagens_area_resumo(_matricula: str = Depends(exigir_login)):
    with get_db() as conn:
        cursor = conn.cursor()
        # 🆕 Só o canal 'supervisao' entra aqui — é o que aparece como
        # badge/prévia na lista de conversas do ADM. O canal 'tecnicos'
        # (área-a-área) tem seu próprio resumo, ver /resumo_tecnicos.
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


@router.get("/api/mensagens_area/resumo_tecnicos", tags=["Mensagens Área-ADM"], summary="Resumo das conversas área-a-área (canal 'tecnicos') de uma área, com todas as outras")
def get_mensagens_area_resumo_tecnicos(area: str, _matricula: str = Depends(exigir_login)):
    with get_db() as conn:
        cursor = conn.cursor()
        # Pega toda mensagem onde a área é qualquer um dos dois lados do
        # par, normaliza "quem é a OUTRA área" num CASE, e agrupa por ela.
        # Não-lida = mensagem que a área não mandou (veio do outro lado)
        # e ainda não foi marcada lida — não depende de qual dos dois
        # lados fisicamente escreveu na coluna `area`.
        cursor.execute(
            """
            SELECT
                CASE WHEN area = %s THEN area_destino ELSE area END AS outra_area,
                MAX(criado_em) AS ultima_em,
                SUM(CASE WHEN area != %s AND lida = FALSE THEN 1 ELSE 0 END) AS nao_lidas
            FROM mensagens_area_adm
            WHERE canal = 'tecnicos' AND (area = %s OR area_destino = %s)
            GROUP BY outra_area
            ORDER BY ultima_em DESC
            """,
            (area, area, area, area)
        )
        linhas = cursor.fetchall()
        for linha in linhas:
            linha["nome_area"] = AREA_OFICINA_NOMES.get(linha["outra_area"], linha["outra_area"])
        return linhas


@router.post("/api/mensagens_area/digitando", tags=["Mensagens Área-ADM"], summary="Avisa que está digitando no canal Entre Técnicos (efêmero, sem gravar no banco)")
def marcar_digitando(dados: MensagemAreaAdmDigitando):
    _DIGITANDO[(dados.area, dados.area_destino)] = time.time()
    return {"sucesso": True}


@router.get("/api/mensagens_area/digitando", tags=["Mensagens Área-ADM"], summary="Verifica se a OUTRA área está digitando pra mim agora")
def get_digitando(area: str, area_destino: str, _matricula: str = Depends(exigir_login)):
    """`area` = minha área (quem pergunta), `area_destino` = a área do
    outro lado da conversa — mesma convenção usada no resto deste
    arquivo. Retorna True só se o PING mais recente do outro lado pra
    mim ainda está dentro da janela (DIGITANDO_TTL_SEGUNDOS)."""
    ultimo_ping = _DIGITANDO.get((area_destino, area))
    digitando = bool(ultimo_ping and (time.time() - ultimo_ping) <= DIGITANDO_TTL_SEGUNDOS)
    return {"digitando": digitando}


@router.get("/api/mensagens_area/nao_lidas", tags=["Mensagens Área-ADM"], summary="Quantidade de mensagens não lidas de uma área (ADM->área + área<->área)")
def get_mensagens_area_nao_lidas(area: str, _matricula: str = Depends(exigir_login)):
    """🔧 CORREÇÃO ("mandei mensagem no Entre Técnicos e não chegou nem
    notificação pro outro lado"): esta rota só contava não lidas do
    canal 'supervisao' (ADM -> área) — o canal 'tecnicos' (área<->área)
    nunca somava aqui, e é ESTE número que window.atualizarBadgeChatAreaAdm
    usa pro badge do nav "Chats" e da Central de Áreas de quem não é
    ADM. Resultado: mesmo com a mensagem gravada certinho no banco (área
    de origem/destino corretos), quem recebia não tinha NENHUM sinal
    visual persistente — só o push, que falha em qualquer teste sem
    notificação já autorizada no navegador. Agora soma as duas coisas:
    supervisao (ADM -> esta área) + tecnicos (mensagem que a OUTRA área
    mandou pra esta, ainda não lida)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM mensagens_area_adm
                 WHERE area = %s AND canal = 'supervisao' AND de_adm = TRUE AND lida = FALSE)
                +
                (SELECT COUNT(*) FROM mensagens_area_adm
                 WHERE canal = 'tecnicos' AND area_destino = %s AND area != %s AND lida = FALSE)
                AS qtd
            """,
            (area, area, area)
        )
        return {"nao_lidas": cursor.fetchone()["qtd"]}


@router.post("/api/mensagens_area", tags=["Mensagens Área-ADM"], summary="Enviar mensagem (texto e/ou foto) — área<->ADM ou área<->área")
def enviar_mensagem_area(dados: MensagemAreaAdmEnviar):
    # 🆕 Com a foto virando opcional, precisa ter pelo menos UM dos dois —
    # senão seria uma mensagem completamente vazia.
    texto = (dados.mensagem or "").strip()
    if not texto and not dados.foto_base64:
        raise HTTPException(status_code=400, detail="Mande um texto ou uma foto.")

    canal = dados.canal if dados.canal in ("supervisao", "tecnicos") else "supervisao"
    area_destino = None
    if canal == "tecnicos":
        if not dados.area_destino or dados.area_destino == dados.area:
            raise HTTPException(status_code=400, detail="área_destino é obrigatória e precisa ser diferente da área de origem no canal 'tecnicos'.")
        area_destino = dados.area_destino

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mensagens_area_adm (area, area_destino, de_adm, remetente, remetente_matricula, mensagem, foto_base64, canal, atividade_referencia, criado_em, lida)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            RETURNING id
            """,
            (dados.area, area_destino, dados.de_adm, dados.remetente, dados.remetente_matricula, texto, dados.foto_base64, canal, dados.atividade_referencia, agora)
        )
        nova_id = cursor.fetchone()["id"]
        conn.commit()

    nome_area = AREA_OFICINA_NOMES.get(dados.area, dados.area)
    corpo_push = texto if texto else "📷 Foto enviada"
    if canal == "tecnicos":
        # 🆕 Área-a-área — avisa só a área DESTINO dessa mensagem.
        nome_area_destino = AREA_OFICINA_NOMES.get(area_destino, area_destino)
        enviar_push_para_area(
            titulo=f"💬 {nome_area} → {nome_area_destino}",
            corpo=f"{dados.remetente or 'Técnico'}: {corpo_push}",
            area=area_destino,
            url="/app.html#area-oficina",
            dados_extra={"tipo_evento": "mensagem_area_tecnicos", "area": dados.area, "area_destino": area_destino}
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
        if dados.canal == "tecnicos":
            if not dados.area_destino:
                raise HTTPException(status_code=400, detail="area_destino é obrigatório pra marcar lido no canal 'tecnicos'.")
            # Marca como lida toda mensagem do par (área, area_destino) em
            # QUALQUER sentido que não tenha partido de quem está chamando
            # (dados.area) — ou seja, a mensagem que ele ainda não leu.
            cursor.execute(
                """
                UPDATE mensagens_area_adm SET lida = TRUE
                WHERE canal = 'tecnicos' AND area != %s AND lida = FALSE AND (
                    (area = %s AND area_destino = %s) OR (area = %s AND area_destino = %s)
                )
                RETURNING id
                """,
                (dados.area, dados.area, dados.area_destino, dados.area_destino, dados.area)
            )
        else:
            # Quem chama é quem LEU — então marca como lida a mensagem que
            # partiu do OUTRO lado (de_adm invertido em relação a quem pediu).
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
