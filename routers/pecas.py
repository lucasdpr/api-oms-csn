from fastapi import APIRouter, HTTPException
from app_core import (
    PecaExcluir,
    PecaUpdate,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




@router.get("/api/pecas", tags=["Peças"], summary="Listar todas as peças")
def get_pecas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipamentos")
        return cursor.fetchall()




@router.post("/api/atualizar_peca", tags=["Peças"], summary="Cadastrar ou atualizar uma peça")
def atualizar_peca(peca: PecaUpdate):
    campos = []
    valores = []

    if peca.tipo is not None:
        campos.append("tipo = %s"); valores.append(peca.tipo)
    if peca.mcc_compat is not None:
        campos.append("mcc_compat = %s"); valores.append(peca.mcc_compat)
    if peca.tonelagem is not None:
        campos.append("tonelagem = %s"); valores.append(peca.tonelagem)
    if peca.dias is not None:
        campos.append("dias = %s"); valores.append(peca.dias)
    if peca.local is not None:
        campos.append("local = %s"); valores.append(peca.local)
    if peca.status is not None:
        campos.append("status = %s"); valores.append(peca.status)
    if peca.meta is not None:
        campos.append("meta = %s"); valores.append(peca.meta)
    if peca.posicao is not None:
        campos.append("posicao = %s"); valores.append(peca.posicao)
    if peca.tag_patrimonio is not None:
        campos.append("tag_patrimonio = %s"); valores.append(peca.tag_patrimonio)
    if peca.data_entrada is not None:
        campos.append("data_entrada = %s"); valores.append(peca.data_entrada)
    if peca.data_reparo is not None:
        campos.append("data_reparo = %s"); valores.append(peca.data_reparo)
    if peca.substituido_por is not None:
        campos.append("substituido_por = %s"); valores.append(peca.substituido_por)
    if peca.observacao is not None:
        campos.append("observacao = %s"); valores.append(peca.observacao)
    if peca.rolos_travados is not None:
        campos.append("rolos_travados = %s"); valores.append(peca.rolos_travados)
    if peca.mancais_ocorrencias is not None:
        campos.append("mancais_ocorrencias = %s"); valores.append(peca.mancais_ocorrencias)
    if peca.barra_transversal is not None:
        campos.append("barra_transversal = %s"); valores.append(peca.barra_transversal)

    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar foi enviado.")

    valores.append(peca.id)
    query = f"UPDATE equipamentos SET {', '.join(campos)} WHERE id = %s"

    with get_db() as conn:
        cursor = conn.cursor()

        # 🆕 Busca o estado ANTES da atualização, só pra poder comparar
        # depois e saber se o status mudou pra "Reserva" ou se a peça foi
        # trocada (substituido_por passou a ter valor) — sem isso, toda
        # edição de peça pareceria uma troca/movimentação nova.
        cursor.execute("SELECT status, substituido_por FROM equipamentos WHERE id = %s", (peca.id,))
        estado_anterior = cursor.fetchone()
        status_anterior = estado_anterior["status"] if estado_anterior else None
        substituido_por_anterior = estado_anterior["substituido_por"] if estado_anterior else None

        cursor.execute(query, tuple(valores))
        criada = False

        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO equipamentos (id, tipo, mcc_compat, local, status, tonelagem, dias, meta, posicao, tag_patrimonio, data_entrada, data_reparo, substituido_por, observacao, rolos_travados, mancais_ocorrencias, barra_transversal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    tipo = EXCLUDED.tipo,
                    mcc_compat = EXCLUDED.mcc_compat,
                    local = EXCLUDED.local,
                    status = EXCLUDED.status,
                    tonelagem = EXCLUDED.tonelagem,
                    dias = EXCLUDED.dias,
                    meta = EXCLUDED.meta,
                    posicao = EXCLUDED.posicao,
                    tag_patrimonio = EXCLUDED.tag_patrimonio,
                    data_entrada = EXCLUDED.data_entrada,
                    data_reparo = EXCLUDED.data_reparo,
                    substituido_por = EXCLUDED.substituido_por,
                    observacao = EXCLUDED.observacao,
                    rolos_travados = EXCLUDED.rolos_travados,
                    mancais_ocorrencias = EXCLUDED.mancais_ocorrencias,
                    barra_transversal = EXCLUDED.barra_transversal
            ''', (
                peca.id, peca.tipo or "", peca.mcc_compat or "", peca.local or "", peca.status or "",
                peca.tonelagem or 0, peca.dias or 0, peca.meta or 0, peca.posicao or "",
                peca.tag_patrimonio, peca.data_entrada, peca.data_reparo,
                peca.substituido_por, peca.observacao, peca.rolos_travados, peca.mancais_ocorrencias,
                peca.barra_transversal
            ))
            criada = True

        conn.commit()

    # 🆕 Notificação push quando uma ocorrência de mancal é registrada
    # (não dispara em toda edição de peça — só quando o front-end manda
    # o texto pronto, ou seja, quando de fato marcou quebra de
    # rolamento / vazamento de graxa ou água num mancal).
    if peca.mancal_evento_corpo:
        enviar_push_para_area(
            titulo=peca.mancal_evento_titulo or "⚠️ Ocorrência em mancal",
            corpo=peca.mancal_evento_corpo,
            area="Ambos"
        )
        # 🆕 Grava em log_eventos com area="sinotico-3d" pra aparecer
        # como área própria na Central de Notificações (antes só virava
        # push — nunca ficava registrado em lugar nenhum que o feed
        # olhasse, por isso "faltou o Sinótico 3D" na Central).
        # 🐛 CORREÇÃO: sem o try/except, uma falha aqui (ex: pool de
        # conexão esgotado — já aconteceu em produção) derrubava a rota
        # inteira com 500, mesmo com a atualização REAL da peça
        # (rolos_travados/mancais_ocorrencias) já commitada mais acima —
        # o app mostraria erro pro usuário apesar do save ter funcionado.
        # Mesmo padrão de enviar_push_para_area: registrar a notificação
        # é "nice to have", nunca deve derrubar o que já foi salvo.
        try:
            with get_db() as conn2:
                cursor2 = conn2.cursor()
                cursor2.execute(
                    "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, categoria, area) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (agora_brasil().strftime("%Y-%m-%d %H:%M:%S"), "Sinótico 3D", peca.id,
                     peca.mancal_evento_corpo, None, "sinotico-3d")
                )
                conn2.commit()
        except Exception as e:
            print(f"⚠️ Falha ao gravar evento de mancal do Sinótico 3D na Central de Notificações: {e}")

    # 🆕 Notificação quando a peça vai (ou passa a ir) pra Reserva —
    # só dispara na TROCA de status, não toda vez que alguém salva a
    # peça já estando em Reserva.
    if peca.status is not None and peca.status != status_anterior and peca.status.strip().lower() == "reserva":
        enviar_push_para_area(
            titulo="📦 Equipamento movido pra Reserva",
            corpo=f"{peca.id} ({peca.tipo or 'equipamento'}) foi movido pro Estoque Reserva.",
            area="Ambos"
        )

    # 🆕 Notificação de troca de peça — dispara quando o campo
    # substituido_por passa a ter um valor novo (ou muda de valor),
    # indicando que essa peça foi substituída por outra.
    if peca.substituido_por is not None and peca.substituido_por.strip() and peca.substituido_por != substituido_por_anterior:
        enviar_push_para_area(
            titulo="🔁 Troca de equipamento",
            corpo=f"{peca.id} foi substituído por {peca.substituido_por}.",
            area="Ambos"
        )

    return {"sucesso": True, "criada": criada}




@router.post("/api/excluir_peca", tags=["Peças"], summary="Excluir uma peça")
def excluir_peca(peca: PecaExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM equipamentos WHERE id = %s", (peca.id,))
        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail=f"Peça '{peca.id}' não encontrada.")
        cursor.execute("DELETE FROM folhoes_rascunho WHERE equipamento_id = %s", (peca.id,))
        conn.commit()

    return {"sucesso": True}




@router.get("/api/fotos/{peca_id}", tags=["Peças"], summary="Listar fotos registradas de uma peça")
def get_fotos_da_peca(peca_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, f.foto_base64, f.criado_em, e.data_hora, e.operador, e.acao, e.categoria
            FROM fotos_registro f
            JOIN log_eventos e ON e.id = f.evento_id
            WHERE f.peca_id = %s
            ORDER BY f.id DESC
        """, (peca_id,))
        return cursor.fetchall()
