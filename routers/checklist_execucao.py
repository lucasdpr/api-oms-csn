from fastapi import APIRouter, HTTPException
from app_core import (
    AREA_OFICINA_NOMES,
    ChecklistExecucaoAtividadeExtra,
    ChecklistExecucaoAtividadeExtraExcluir,
    ChecklistExecucaoEtapaEditar,
    ChecklistExecucaoEtapaExcluir,
    ChecklistExecucaoEtapaNova,
    ChecklistExecucaoFinalizar,
    ChecklistExecucaoIniciar,
    ChecklistExecucaoMarcar,
    ChecklistExecucaoReordenar,
    MATRICULAS_ADM,
    NOME_AREA_PUSH,
    OficinaAtividade,
    Optional,
    agora_brasil,
    enviar_push_para_area,
    get_db,
    json_lib,
    registrar_evento_atividade_oficina,
)
# 🔧 Único ponto de dependência ENTRE módulos de rota (fora do
# app_core compartilhado): este handler chama a função de outra rota
# (POST /api/oficina/atividade) diretamente, em vez de fazer uma
# chamada HTTP nela — mesmo comportamento de sempre, só que agora
# precisa de import explícito por estarem em arquivos diferentes.
from routers.oficina import criar_atividade_oficina

router = APIRouter()



# ==========================================
# 🆕 CHECKLIST DE EXECUÇÃO — passo a passo REAL do reparo (por
# equipamento, dividido em seções: mecânica, elétrica, hidráulica,
# caldeiraria, usinagem, tubulação, jato). Diferente do "Procedimento"
# oficial (procedimentos_execucoes acima) — este é editável só pelas 3
# matrículas admin e reflete o jeito que os técnicos realmente fazem.
# ==========================================

@router.get("/api/checklist-execucao/etapas/{tipo_equipamento}", tags=["Checklist de Execução"], summary="Listar etapas de um TIPO de equipamento (com estado da execução atual)")
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




@router.get("/api/checklist-execucao/execucoes/todas", tags=["Checklist de Execução"], summary="Listar todas as execuções de checklist em andamento")
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




@router.post("/api/checklist-execucao/execucoes/iniciar", tags=["Checklist de Execução"], summary="Iniciar (ou reaproveitar) a execução de um reparo específico")
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




@router.post("/api/checklist-execucao/execucoes/finalizar", tags=["Checklist de Execução"], summary="Finalizar a execução de um reparo (fecha o ciclo)")
def finalizar_execucao_checklist(dados: ChecklistExecucaoFinalizar):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE checklist_execucao_execucoes SET status = 'concluida', concluida_em = %s WHERE id = %s",
            (agora_brasil().isoformat(), dados.execucao_id)
        )
        conn.commit()
        return {"sucesso": True}




@router.get("/api/checklist-execucao/status/{equipamento_id}", tags=["Checklist de Execução"], summary="Progresso da execução em andamento dessa tag")
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




@router.get("/api/checklist-execucao/folhao/{tipo_equipamento}", tags=["Checklist de Execução"], summary="Valores prontos pro Folhão se autopreencher")
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




@router.post("/api/checklist-execucao/etapas", tags=["Checklist de Execução"], summary="Cadastrar nova etapa (só ADM do checklist)")
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




@router.post("/api/checklist-execucao/etapas/editar", tags=["Checklist de Execução"], summary="Editar texto (e opcionalmente a ponte com o Folhão) de uma etapa (só ADM do checklist)")
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




@router.post("/api/checklist-execucao/etapas/excluir", tags=["Checklist de Execução"], summary="Excluir (desativar) uma etapa (só ADM do checklist)")
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




@router.post("/api/checklist-execucao/etapas/reordenar", tags=["Checklist de Execução"], summary="Reordenar etapas dentro de uma seção (só ADM do checklist)")
def reordenar_etapas_checklist_execucao(dados: ChecklistExecucaoReordenar):
    if dados.operador.upper() not in MATRICULAS_ADM:
        raise HTTPException(status_code=403, detail="Só as matrículas autorizadas podem reordenar etapas do checklist.")
    with get_db() as conn:
        cursor = conn.cursor()
        for item in dados.itens:
            cursor.execute("UPDATE checklist_execucao_etapas SET ordem = %s WHERE id = %s", (item.ordem, item.id))
        conn.commit()
    return {"sucesso": True}




@router.post("/api/checklist-execucao/marcar", tags=["Checklist de Execução"], summary="Marcar ou desmarcar uma etapa executada")
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




@router.post("/api/checklist-execucao/atividade-extra", tags=["Checklist de Execução"], summary="Registrar atividade fora do checklist padrão (ex: precisou de Caldeiraria/Usinagem)")
def registrar_atividade_extra_checklist_execucao(dados: ChecklistExecucaoAtividadeExtra):
    # 🐛 CORRIGIDO ("registrei pra Caldeiraria e não chegou nada lá"):
    # antes isso só gravava uma linha informativa aqui dentro — nunca
    # virava uma atividade de verdade no quadro da área (as mesmas
    # "Atividades da Oficina" com Pendente/Em Andamento/Concluído que
    # cada área já usa). Agora chama criar_atividade_oficina() de
    # verdade (mesma função do botão "+ Nova Atividade" de cada área) —
    # reaproveita o push que ela já dispara, então NÃO manda um segundo
    # aviso separado aqui.
    # 🐛 CORRIGIDO ("nome mostrado pro técnico é 'Checklist de Execução'
    # genérico, não o equipamento"): o prefixo "[Checklist de Execução]"
    # aqui virava a DESCRIÇÃO da atividade — que é o texto de destaque
    # no card (ver renderizarAtividadesArea no front). O equipamento já
    # tem campo próprio (equipamento_id, mostrado como tag no card); o
    # prefixo só duplicava informação genérica e escondia a descrição de
    # verdade atrás de um rótulo igual em toda atividade extra.
    atividade_oficina = criar_atividade_oficina(OficinaAtividade(
        area=dados.area,
        equipamento_id=dados.equipamento_id,
        descricao=dados.descricao,
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

    # 🆕 Além da área DESTINO (dados.area — quem vai executar, ex:
    # Caldeiraria) e do push pro solicitante individual (dentro de
    # criar_atividade_oficina), a área de ORIGEM do checklist (o
    # equipamento que estava sendo executado, ex: Molde MCC4) também
    # precisa saber — não só quem literalmente clicou em "Registrar
    # Atividade Extra" (pode ter sido um ADM testando, sem área própria
    # nenhuma em equipe_oficina; e mesmo pra um técnico de verdade, o
    # RESTO da equipe da área de origem também quer saber que um pedido
    # saiu do checklist deles).
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tipo_equipamento FROM checklist_execucao_execucoes WHERE id = %s",
                (dados.execucao_id,)
            )
            linha_execucao = cursor.fetchone()
        area_origem = linha_execucao["tipo_equipamento"] if linha_execucao else None
    except Exception as e:
        print(f"⚠️ Falha ao buscar área de origem da execução {dados.execucao_id}: {e}")
        area_origem = None

    if area_origem and area_origem != dados.area:
        nome_area_destino = AREA_OFICINA_NOMES.get(dados.area, dados.area)
        registrar_evento_atividade_oficina(
            operador=dados.operador_nome,
            area=area_origem,
            peca_id=dados.equipamento_id,
            acao=f"{dados.operador_nome} pediu ajuda de {nome_area_destino}: {dados.descricao}",
            atividade_id=oficina_atividade_id,
            tipo_evento="criacao"
        )

    return {"sucesso": True, "id": novo_id, "oficina_atividade_id": oficina_atividade_id}




@router.get("/api/checklist-execucao/atividades-extra/{execucao_id}", tags=["Checklist de Execução"], summary="Listar atividades extra registradas numa execução")
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




@router.post("/api/checklist-execucao/atividade-extra/excluir", tags=["Checklist de Execução"], summary="Excluir uma Atividade Extra (cancela também a atividade real na área)")
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




@router.get("/api/checklist-execucao/historico/{equipamento_id}", tags=["Checklist de Execução"], summary="Histórico completo (inclui retrabalhos)")
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
