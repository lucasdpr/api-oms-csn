from fastapi import APIRouter, HTTPException
from app_core import (
    AREA_OFICINA_NOMES,
    OficinaAtividade,
    OficinaAtividadeEditar,
    OficinaAtividadeMensagem,
    OficinaExcluir,
    OficinaMaterial,
    OficinaMaterialExcluir,
    OficinaNota,
    OficinaStatus,
    Optional,
    ProcedimentoExecucao,
    agora_brasil,
    enviar_push_para_area,
    enviar_push_para_matricula,
    get_db,
    json_lib,
    notificar_areas_extras_atividade_oficina,
    registrar_evento_atividade_oficina,
)

router = APIRouter()




# ==========================================
# OFICINA — ATIVIDADES POR ÁREA (v1)
# ==========================================
@router.get("/api/oficina/atividades", tags=["Oficina"], summary="Listar atividades da Oficina")
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
        # 🆕 CORRIGIDO ("quem pediu a atividade extra some da própria
        # área quando outra equipe assume"): "area" na tabela é sempre
        # quem EXECUTA — pra quem pediu (solicitante_matricula) ver a
        # atividade no PRÓPRIO quadro mesmo sendo executada por outra
        # área, o front precisa saber qual é a área do solicitante.
        # LEFT JOIN com equipe_oficina (mesma fonte de área usada em
        # _buscar_area_colaborador) só pra trazer esse dado a mais —
        # não filtra nada aqui, o filtro por área continua sendo feito
        # no front-end pra montar a grade (ver comentário acima).
        query = """
            SELECT oa.*, eo.area AS solicitante_area
            FROM oficina_atividades oa
            LEFT JOIN equipe_oficina eo
                ON eo.matricula = oa.solicitante_matricula AND eo.ativo = TRUE
            WHERE 1=1
        """
        params = []
        if area:
            query += " AND oa.area = %s"
            params.append(area)
        if status:
            query += " AND oa.status = %s"
            params.append(status)
        query += " ORDER BY oa.id DESC LIMIT %s"
        params.append(limite)
        cursor.execute(query, params)
        return cursor.fetchall()




@router.get("/api/oficina/atividade/{atividade_id}/reaberturas", tags=["Oficina"], summary="Histórico de reaberturas de uma atividade")
def listar_reaberturas_atividade_oficina(atividade_id: int):
    """
    Lista o histórico de reaberturas de UMA atividade (mais recente
    primeiro) — o que ela tinha (data de conclusão, motivo/observação,
    quem executou) antes de cada reabertura. Ver comentário da tabela
    oficina_atividades_reaberturas no schema.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, atividade_id, concluido_em_anterior, motivo_conclusao_anterior,
                   motivo_reabertura, reaberto_por, executado_por_anterior, data_reabertura
            FROM oficina_atividades_reaberturas
            WHERE atividade_id = %s
            ORDER BY id DESC
            """,
            (atividade_id,)
        )
        return cursor.fetchall()




@router.get("/api/oficina/atividades/mais_reabertas", tags=["Oficina"], summary="Atividades mais reabertas (retrabalho)")
def listar_atividades_mais_reabertas_oficina(limite: int = 10):
    """
    Ranking simples de retrabalho: atividades com reaberturas_count > 0,
    da maior contagem pra menor. Endpoint pronto pra alimentar uma tela/
    relatório visual no futuro — hoje não é consumido pelo front-end.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, descricao, area, equipamento_id, reaberturas_count
            FROM oficina_atividades
            WHERE reaberturas_count > 0
            ORDER BY reaberturas_count DESC, id DESC
            LIMIT %s
            """,
            (limite,)
        )
        return cursor.fetchall()




@router.post("/api/oficina/atividade", tags=["Oficina"], summary="Criar atividade da Oficina")
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
            area=dados.area,
            # 🆕 tipo_evento/atividade_id vão no payload do push pro
            # Service Worker saber pra onde navegar no notificationclick
            # (mesmo destino que o clique dentro da Central já usa).
            dados_extra={"tipo_evento": "criacao", "atividade_id": atividade_id, "area": dados.area}
        )

    # 🆕 Registro persistente na Central de Notificações — ver
    # registrar_evento_atividade_oficina. Ao contrário do push acima,
    # isso vale MESMO pra atividade programada pro futuro (o push espera
    # a data chegar, mas o registro de "isso foi criado" é imediato).
    registrar_evento_atividade_oficina(
        operador=dados.operador,
        area=dados.area,
        peca_id=dados.equipamento_id,
        acao=f"{dados.operador} criou: {dados.descricao}",
        atividade_id=atividade_id,
        tipo_evento="criacao"
    )
    # 🐛 CORRIGIDO: mudar_status/editar/excluir/mensagem já chamam
    # notificar_areas_extras_atividade_oficina (pra o solicitante de
    # outra área ver o evento na própria Central), mas a criação nunca
    # chamava — o solicitante só passava a ver a atividade a partir da
    # PRIMEIRA mudança de status, não desde que ela foi criada.
    notificar_areas_extras_atividade_oficina(
        oficina_atividade_id=atividade_id,
        solicitante_matricula=dados.solicitante_matricula,
        area_dona=dados.area,
        peca_id=dados.equipamento_id,
        acao=f"{dados.operador} criou: {dados.descricao}",
        operador=dados.operador,
        tipo_evento="criacao"
    )

    return {"sucesso": True, "id": atividade_id}





@router.post("/api/oficina/atividade/status", tags=["Oficina"], summary="Mudar status de uma atividade da Oficina")
def mudar_status_atividade_oficina(dados: OficinaStatus):
    # 🆕 "Recusado" e "Aguardando" exigem motivo — não dá pra só
    # "passar por cima" de uma atividade sem justificar por que não
    # iniciou (Recusado) ou por que travou depois de já ter começado
    # (Aguardando, ex: aguardando material chegar).
    if dados.status in ("Recusado", "Aguardando") and not (dados.motivo or "").strip():
        raise HTTPException(status_code=400, detail=f"Status \"{dados.status}\" precisa de um motivo.")
    # 🆕 Reabrir uma atividade Concluída também exige motivo — mesma
    # lógica de Recusado/Aguardando: não dá pra "passar por cima" e
    # mandar de volta pra produção sem dizer por quê (ver front em
    # window.reabrirAtividadeOficina).
    if dados.reabertura and not (dados.motivo or "").strip():
        raise HTTPException(status_code=400, detail="Reabertura precisa de um motivo.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    concluido_em = agora if dados.status == "Concluído" else None
    # 🔧 CORRIGIDO ("nem chegou notificação de que iniciou, nem o
    # motivo da recusa"): antes só guardava (e só avisava) o motivo pra
    # Recusado/Aguardando. Motivo/observação agora vale pra QUALQUER
    # status — inclusive uma nota ao Concluir ("trocado o parafuso X")
    # — se veio alguma coisa, guarda; senão fica vazio (não força
    # limpeza em transições que não vieram acompanhadas de nota).
    motivo_status = dados.motivo.strip() if (dados.motivo or "").strip() else None

    reaberturas_count_atual = 0
    with get_db() as conn:
        cursor = conn.cursor()
        # 🆕 Se é uma reabertura, ANTES de zerar concluido_em e sobrescrever
        # motivo_status (perdendo esses dados pra sempre), guarda uma
        # linha no histórico (oficina_atividades_reaberturas) com o que a
        # atividade TINHA — ver comentário da tabela no schema.
        if dados.reabertura:
            # 🐛 CORRIGIDO (corrida em reabertura dupla): sem FOR UPDATE,
            # dois cliques quase simultâneos de Reabrir na mesma
            # atividade (ex: solicitante e executor, já que o botão
            # aparece nos dois quadros) podiam ler o MESMO "anterior"
            # antes de qualquer um commitar — as duas linhas de
            # histórico ficavam com o mesmo concluido_em/motivo_status,
            # mesmo a segunda reabertura devendo refletir o que a
            # primeira já tinha gravado. FOR UPDATE trava a linha até o
            # commit desta transação, serializando as duas.
            cursor.execute(
                "SELECT concluido_em, motivo_status, executado_por FROM oficina_atividades WHERE id = %s FOR UPDATE",
                (dados.id,)
            )
            anterior = cursor.fetchone()
            if not anterior:
                raise HTTPException(status_code=404, detail="Atividade não encontrada.")
            cursor.execute(
                """
                INSERT INTO oficina_atividades_reaberturas
                    (atividade_id, concluido_em_anterior, motivo_conclusao_anterior, motivo_reabertura, reaberto_por, executado_por_anterior, data_reabertura)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (dados.id, anterior["concluido_em"], anterior["motivo_status"], (dados.motivo or "").strip(),
                 dados.operador, anterior["executado_por"], agora)
            )

        # 🆕 Se a atividade voltou a ficar aberta (reaberta depois de
        # concluída, por exemplo), reseta o aviso de atraso — se ela
        # ficar atrasada de novo, precisa poder notificar de novo.
        resetar_notificacao = dados.status != "Concluído"
        # 🆕 Guarda quem EXECUTA a atividade a partir do momento que ela
        # entra "Em Andamento" — ver comentário da coluna executado_por.
        # Não sobrescreve em Concluir/Recusar/Aguardar/Reabrir (mantém o
        # nome de quem pegou o serviço da última vez que foi iniciada).
        set_executor = ", executado_por = %s" if dados.status == "Em Andamento" else ""
        # 🆕 Reabertura incrementa o contador — ver coluna reaberturas_count.
        set_reaberturas = ", reaberturas_count = reaberturas_count + 1" if dados.reabertura else ""
        params = [dados.status, concluido_em, motivo_status]
        if set_executor:
            # 🆕 Prioriza os colaboradores escolhidos no modal (pode ser
            # mais de um nome); sem isso, mantém o comportamento antigo
            # de gravar só quem clicou (dados.operador).
            params.append((dados.colaboradores or "").strip() or dados.operador)
        params.append(dados.id)
        cursor.execute(
            "UPDATE oficina_atividades SET status = %s, concluido_em = %s, motivo_status = %s"
            + set_executor
            + set_reaberturas
            + (", notificado_atraso = FALSE" if resetar_notificacao else "")
            + " WHERE id = %s"
            + " RETURNING equipamento_id, descricao, area, solicitante_matricula, executado_por, reaberturas_count",
            params
        )
        linha = cursor.fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()
        reaberturas_count_atual = linha["reaberturas_count"] or 0

    # 🔧 CORRIGIDO ("nem chegou notificação de que ele iniciou a
    # atividade, e nem que recusou e o motivo"): antes só avisava em
    # Recusado/Aguardando — quem pediu ficava sem saber que o serviço
    # tinha começado ou terminado. Agora TODA mudança de status
    # (Iniciar, Concluir, Recusar, Aguardar) avisa quem pediu — só faz
    # sentido pra atividade que veio de um "Registrar Atividade Extra"
    # no Checklist de Execução (tem solicitante_matricula). Uma
    # atividade criada direto no quadro da área não tem "quem pediu"
    # separado de quem executa, então não notifica ninguém aqui.
    VERBOS_STATUS = {
        "Em Andamento": "iniciou",
        "Concluído": "concluiu",
        "Recusado": "recusou",
        "Aguardando": "colocou em espera",
        "Pendente": "reabriu",
    }
    verbo = "reabriu" if dados.reabertura else VERBOS_STATUS.get(dados.status, "atualizou")
    if linha["solicitante_matricula"]:
        tag = linha["equipamento_id"] or ""
        nome_area = AREA_OFICINA_NOMES.get(linha["area"], linha["area"])
        # 🐛 CORRIGIDO ("notificação de 'iniciou atividade' aparece com
        # 'sem observação' escrito literalmente"): motivo só é
        # OBRIGATÓRIO pra Recusado/Aguardando (ver validação lá em cima)
        # — pra Iniciar/Concluir/Reabrir é normal não ter nada, e antes
        # isso virava um corpo de push genérico e feio ("Sem
        # observações."). Agora, sem motivo, o corpo conta a descrição
        # da própria atividade (informação de verdade) em vez de um
        # texto vazio de preenchimento.
        corpo = f"Motivo: {motivo_status}" if motivo_status else (linha["descricao"] or f"{tag} — {nome_area}")
        enviar_push_para_matricula(
            matricula=linha["solicitante_matricula"],
            titulo=f"{nome_area} {verbo} sua atividade — {tag}",
            corpo=corpo,
            url="/",
            dados_extra={"tipo_evento": "status", "atividade_id": dados.id, "area": linha["area"]}
        )

    # 🆕 RETRABALHO REPETIDO — quando essa reabertura faz o contador
    # chegar a 2 ou mais, não é mais "reabriu uma vez, ok" — é um padrão
    # que o ADM precisa enxergar (a área pode estar concluindo cedo
    # demais, ou o problema pode não ter sido resolvido de verdade).
    # Reaproveita enviar_push_para_area (que já manda pro ADM sempre,
    # com prefixo de área — ver comentário da função) só que com um
    # título com destaque, além do aviso normal que já vai pro
    # solicitante acima.
    if dados.reabertura and reaberturas_count_atual >= 2:
        nome_area_retrabalho = AREA_OFICINA_NOMES.get(linha["area"], linha["area"])
        tag_retrabalho = linha["equipamento_id"] or ""
        enviar_push_para_area(
            titulo=f"⚠️ RETRABALHO REPETIDO — {nome_area_retrabalho}",
            corpo=f"{tag_retrabalho} — {linha['descricao']}: já reaberta {reaberturas_count_atual}x. Motivo agora: {motivo_status or '-'}",
            area=linha["area"],
            dados_extra={"tipo_evento": "reabertura", "atividade_id": dados.id, "area": linha["area"]}
        )

    # 🆕 Registro persistente na Central — TODA mudança de status, não
    # só quando tem solicitante pra avisar (o push acima é sobre avisar
    # UMA pessoa específica; isso aqui é o rastro na Central que
    # qualquer ADM/técnico da área vê depois, com ou sem solicitante).
    acao_texto = f"{dados.operador or 'Alguém'} {verbo}: {linha['descricao']}" + (f" ({motivo_status})" if motivo_status else "")
    registrar_evento_atividade_oficina(
        operador=dados.operador,
        area=linha["area"],
        peca_id=linha["equipamento_id"],
        acao=acao_texto,
        atividade_id=dados.id,
        tipo_evento="reabertura" if dados.reabertura else "status"
    )
    # 🐛 CORREÇÃO: sem isso, quem PEDIU a atividade (solicitante_
    # matricula, de outra área) e o resto da equipe da área de ORIGEM do
    # checklist (se veio de "Atividade Extra") nunca viam essa mudança
    # de status na própria Central. Ver
    # notificar_areas_extras_atividade_oficina.
    notificar_areas_extras_atividade_oficina(
        oficina_atividade_id=dados.id,
        solicitante_matricula=linha["solicitante_matricula"],
        area_dona=linha["area"],
        peca_id=linha["equipamento_id"],
        acao=acao_texto,
        operador=dados.operador,
        # 🐛 CORRIGIDO: faltava aqui — a cópia desse evento registrada
        # pra área DONA (registrar_evento_atividade_oficina acima) já
        # ficava marcada "reabertura" numa reabertura, mas a cópia pras
        # áreas EXTRAS (solicitante/origem do checklist) caía sempre no
        # default "status", classificando o mesmo evento lógico de
        # jeitos diferentes dependendo de qual área olha a Central.
        tipo_evento="reabertura" if dados.reabertura else "status"
    )

    return {"sucesso": True}


# 🆕 Verificação de atividades atrasadas — não roda sozinha (o sistema
# não tem um agendador/cron), então é chamada pelo front-end sempre que
# o app é aberto (ver DOMContentLoaded em script.js). Cada atividade só
# gera UMA notificação (controlado pela coluna notificado_atraso) —
# reabrir a atividade (ver rota de status acima) é o que permite avisar
# de novo se ela atrasar outra vez.




# 🆕 Verificação de atividades atrasadas — não roda sozinha (o sistema
# não tem um agendador/cron), então é chamada pelo front-end sempre que
# o app é aberto (ver DOMContentLoaded em script.js). Cada atividade só
# gera UMA notificação (controlado pela coluna notificado_atraso) —
# reabrir a atividade (ver rota de status acima) é o que permite avisar
# de novo se ela atrasar outra vez.
@router.post("/api/oficina/verificar_atrasos", tags=["Oficina"], summary="Verificar atividades atrasadas e notificar")
def verificar_atrasos_oficina():
    hoje_str = agora_brasil().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, area, descricao, responsavel, prazo, equipamento_id
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
            area=a["area"],
            dados_extra={"tipo_evento": "status", "atividade_id": a["id"], "area": a["area"]}
        )
        # 🆕 Registro persistente — atraso é detectado pelo sistema, não
        # por uma ação de alguém, mas ainda é algo que "aconteceu" com a
        # atividade e merece ficar marcável como lido na Central.
        registrar_evento_atividade_oficina(
            operador="Sistema",
            area=a["area"],
            peca_id=a["equipamento_id"],
            acao=f"Atrasada: {a['descricao']} (prazo era {a['prazo']})",
            atividade_id=a["id"]
        )

    return {"sucesso": True, "notificadas": len(atrasadas)}


# ==========================================================================
# 🆕 CONVERSA DA ATIVIDADE — mensagens de mão dupla numa atividade
# específica. Ver comentário da tabela oficina_atividade_mensagens
# (schema) pros casos de uso reais que isso resolve.
# ==========================================================================




# ==========================================================================
# 🆕 CONVERSA DA ATIVIDADE — mensagens de mão dupla numa atividade
# específica. Ver comentário da tabela oficina_atividade_mensagens
# (schema) pros casos de uso reais que isso resolve.
# ==========================================================================
@router.post("/api/oficina/atividade/mensagem", tags=["Oficina"], summary="Enviar mensagem na conversa de uma atividade (avisa o outro lado)")
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
            area=atividade["area"],
            dados_extra={"tipo_evento": "mensagem", "atividade_id": dados.atividade_id, "area": atividade["area"]}
        )
    elif atividade["solicitante_matricula"]:
        enviar_push_para_matricula(
            matricula=atividade["solicitante_matricula"],
            titulo=f"💬 {nome_area} respondeu — {tag}",
            corpo=f"{dados.autor_nome}: {dados.mensagem}",
            dados_extra={"tipo_evento": "mensagem", "atividade_id": dados.atividade_id, "area": atividade["area"]}
        )
    # Sem solicitante e quem escreveu não é ele: é conversa interna da
    # própria área (atividade criada direto no quadro) — não tem "outro
    # lado" fora da área pra avisar.

    # 🆕 Registro persistente na Central — diferente do push acima (que
    # só avisa "o outro lado"), isso fica visível pra qualquer ADM/
    # técnico da área depois, mensagem de qualquer um dos dois lados.
    acao_texto = f"{dados.autor_nome}: {dados.mensagem}"
    registrar_evento_atividade_oficina(
        operador=dados.autor_nome,
        area=atividade["area"],
        peca_id=atividade["equipamento_id"],
        acao=acao_texto,
        atividade_id=dados.atividade_id,
        tipo_evento="mensagem"
    )
    # 🐛 CORREÇÃO ("líder da Caldeiraria respondeu, ninguém do lado de
    # quem pediu viu a mensagem na própria Central"): sem isso, a linha
    # acima só aparece sob a área DONA da atividade (Caldeiraria) —
    # invisível pra quem pediu e pra área de origem do checklist, cada
    # um restrito à própria área. Só duplica quando quem escreveu NÃO é
    # o próprio solicitante (senão ele veria a própria mensagem
    # "chegando" pra ele mesmo).
    if not eh_o_solicitante_escrevendo:
        notificar_areas_extras_atividade_oficina(
            oficina_atividade_id=dados.atividade_id,
            solicitante_matricula=atividade["solicitante_matricula"],
            area_dona=atividade["area"],
            peca_id=atividade["equipamento_id"],
            acao=acao_texto,
            operador=dados.autor_nome,
            tipo_evento="mensagem"
        )

    return {"sucesso": True, "id": novo_id}




@router.get("/api/oficina/atividade/mensagens/{atividade_id}", tags=["Oficina"], summary="Listar mensagens da conversa de uma atividade")
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




@router.post("/api/oficina/atividade/excluir", tags=["Oficina"], summary="Excluir atividade da Oficina")
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
        cursor.execute(
            "DELETE FROM oficina_atividades WHERE id = %s RETURNING area, equipamento_id, descricao, solicitante_matricula",
            (dados.id,)
        )
        linha = cursor.fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()

    # 🆕 Registro persistente na Central — mesmo excluída, fica o rastro
    # de que existiu e foi removida (senão a atividade só "some" sem
    # explicação nenhuma pra quem não estava olhando bem na hora).
    acao_texto = f"{dados.operador or 'Alguém'} excluiu: {linha['descricao']}"
    registrar_evento_atividade_oficina(
        operador=dados.operador,
        area=linha["area"],
        peca_id=linha["equipamento_id"],
        acao=acao_texto,
        tipo_evento="edicao"
    )
    # 🐛 CORREÇÃO: mesma lacuna do mudar_status — quem pediu (de outra
    # área) e a área de origem do checklist não viam a exclusão na
    # própria Central.
    notificar_areas_extras_atividade_oficina(
        oficina_atividade_id=dados.id,
        solicitante_matricula=linha["solicitante_matricula"],
        area_dona=linha["area"],
        peca_id=linha["equipamento_id"],
        acao=acao_texto,
        operador=dados.operador,
        tipo_evento="edicao"
    )

    return {"sucesso": True}




@router.get("/api/oficina/nota/{area}", tags=["Oficina"], summary="Consultar anotações de uma área")
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




@router.post("/api/oficina/nota", tags=["Oficina"], summary="Salvar anotações de uma área")
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




@router.get("/api/oficina/equipe/{area}", tags=["Oficina"], summary="Listar equipe de uma área")
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




# ==========================================
# OFICINA — MATERIAIS POR ÁREA
# ==========================================
@router.get("/api/oficina/materiais_todos", tags=["Oficina"], summary="Catálogo geral de materiais (todas as áreas)")
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




@router.get("/api/oficina/materiais/{area}", tags=["Oficina"], summary="Listar materiais de uma área específica")
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




@router.post("/api/oficina/materiais", tags=["Oficina"], summary="Cadastrar material numa área")
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




@router.post("/api/oficina/materiais/excluir", tags=["Oficina"], summary="Excluir material de uma área")
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




# ==========================================
# OFICINA — EDITAR ATIVIDADE
# ==========================================
@router.post("/api/oficina/atividade/editar", tags=["Oficina"], summary="Editar atividade da Oficina")
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
            RETURNING area, solicitante_matricula
            """,
            (dados.equipamento_id, dados.descricao, dados.responsavel,
             dados.prioridade or "Normal", dados.prazo, dados.data_inicio, dados.foto_base64, dados.id)
        )
        linha = cursor.fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        conn.commit()

    # 🆕 Registro persistente na Central — ver registrar_evento_
    # atividade_oficina.
    acao_texto = f"{dados.operador or 'Alguém'} editou: {dados.descricao}"
    registrar_evento_atividade_oficina(
        operador=dados.operador,
        area=linha["area"],
        peca_id=dados.equipamento_id,
        acao=acao_texto,
        atividade_id=dados.id,
        tipo_evento="edicao"
    )
    # 🐛 CORREÇÃO: mesma lacuna do mudar_status — quem pediu (de outra
    # área) e a área de origem do checklist não viam a edição na própria
    # Central.
    notificar_areas_extras_atividade_oficina(
        oficina_atividade_id=dados.id,
        solicitante_matricula=linha["solicitante_matricula"],
        area_dona=linha["area"],
        peca_id=dados.equipamento_id,
        acao=acao_texto,
        operador=dados.operador,
        tipo_evento="edicao"
    )

    return {"sucesso": True}

# ==========================================
# PROCEDIMENTOS (checklist de etapas por área)
# ==========================================
# O conteúdo do procedimento (passo a passo, EPIs, ferramentas) fica
# como dado estático no front-end (procedimentosOficina.js) — aqui só
# fica o REGISTRO de cada execução: quem fez, quando, e quais etapas
# foram marcadas. Isso permite auditar depois (ex: "esse procedimento
# foi mesmo seguido por completo na última execução?").



# ==========================================
# PROCEDIMENTOS (checklist de etapas por área)
# ==========================================
# O conteúdo do procedimento (passo a passo, EPIs, ferramentas) fica
# como dado estático no front-end (procedimentosOficina.js) — aqui só
# fica o REGISTRO de cada execução: quem fez, quando, e quais etapas
# foram marcadas. Isso permite auditar depois (ex: "esse procedimento
# foi mesmo seguido por completo na última execução?").
@router.post("/api/oficina/procedimento/executar", tags=["Oficina"], summary="Registrar execução de um procedimento")
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




@router.get("/api/oficina/procedimento/historico/{area}", tags=["Oficina"], summary="Histórico de procedimentos executados numa área")
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
