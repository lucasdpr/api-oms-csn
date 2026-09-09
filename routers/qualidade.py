from fastapi import APIRouter, HTTPException
from app_core import (
    Optional,
    QualidadeAchadoCriar,
    QualidadeAchadoEditar,
    QualidadeAchadoExcluir,
    QualidadeAchadoResolver,
    QualidadeCriar,
    QualidadeExcluir,
    QualidadeSaida,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




# ==========================================
# 🆕 QUALIDADE (Entrada/Saída) — registro digital de como o equipamento
# chegou na oficina e como está saindo, com fotos em cada etapa.
# ==========================================
@router.get("/api/qualidade", tags=["Qualidade"], summary="Listar registros de Qualidade")
def listar_qualidade(status: Optional[str] = None, limite: int = 100):
    """Lista os registros com uma foto de "capa" de cada etapa (entrada
    e saída) — pra montar o card na lista sem precisar buscar TODAS as
    fotos de TODOS os registros de uma vez."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT
                r.*,
                (SELECT f.foto_base64 FROM qualidade_fotos f WHERE f.registro_id = r.id AND f.etapa = 'entrada' ORDER BY f.id ASC LIMIT 1) AS foto_entrada_capa,
                (SELECT f.foto_base64 FROM qualidade_fotos f WHERE f.registro_id = r.id AND f.etapa = 'saida' ORDER BY f.id ASC LIMIT 1) AS foto_saida_capa,
                (SELECT COUNT(*) FROM qualidade_achados a WHERE a.registro_id = r.id) AS achados_total,
                (SELECT COUNT(*) FROM qualidade_achados a WHERE a.registro_id = r.id AND a.status = 'Pendente') AS achados_pendentes
            FROM qualidade_registros r
        """
        if status:
            query += " WHERE r.status = %s ORDER BY r.id DESC LIMIT %s"
            cursor.execute(query, (status, limite))
        else:
            query += " ORDER BY r.id DESC LIMIT %s"
            cursor.execute(query, (limite,))
        return cursor.fetchall()




@router.get("/api/qualidade/{registro_id}/fotos", tags=["Qualidade"], summary="Listar fotos (entrada ou saída) de um registro")
def get_fotos_qualidade(registro_id: int, etapa: str):
    if etapa not in ("entrada", "saida"):
        raise HTTPException(status_code=400, detail="Etapa inválida.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, foto_base64, criado_em FROM qualidade_fotos WHERE registro_id = %s AND etapa = %s ORDER BY id ASC",
            (registro_id, etapa)
        )
        return cursor.fetchall()




@router.post("/api/qualidade", tags=["Qualidade"], summary="Registrar entrada de um equipamento na oficina")
def criar_qualidade(dados: QualidadeCriar):
    if not dados.fotos_entrada_base64:
        raise HTTPException(status_code=400, detail="É preciso pelo menos 1 foto de entrada.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO qualidade_registros (peca_id, observacao_entrada, status, criado_por, criado_em)
            VALUES (%s, %s, 'Aguardando Saída', %s, %s)
            RETURNING id
            """,
            (dados.peca_id, dados.observacao_entrada, dados.operador, agora)
        )
        registro_id = cursor.fetchone()["id"]

        cursor.executemany(
            "INSERT INTO qualidade_fotos (registro_id, etapa, foto_base64, criado_em) VALUES (%s, 'entrada', %s, %s)",
            [(registro_id, foto, agora) for foto in dados.fotos_entrada_base64]
        )

        if dados.achados:
            for a in dados.achados:
                if not a.descricao or not a.descricao.strip():
                    continue
                cursor.execute(
                    """INSERT INTO qualidade_achados (registro_id, descricao, status, criado_por, criado_em)
                       VALUES (%s, %s, 'Pendente', %s, %s)
                       RETURNING id""",
                    (registro_id, a.descricao.strip(), dados.operador, agora)
                )
                achado_id = cursor.fetchone()["id"]
                if a.fotos_base64:
                    cursor.executemany(
                        "INSERT INTO qualidade_achado_fotos (achado_id, foto_base64, criado_em) VALUES (%s, %s, %s)",
                        [(achado_id, foto, agora) for foto in a.fotos_base64]
                    )

        conn.commit()

    return {"sucesso": True, "id": registro_id}




@router.post("/api/qualidade/{registro_id}/saida", tags=["Qualidade"], summary="Registrar saída de um equipamento da oficina")
def registrar_saida_qualidade(registro_id: int, dados: QualidadeSaida):
    if not dados.fotos_saida_base64:
        raise HTTPException(status_code=400, detail="É preciso pelo menos 1 foto de saída.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE qualidade_registros
               SET status = 'Concluído', observacao_saida = %s, concluido_por = %s, concluido_em = %s
               WHERE id = %s""",
            (dados.observacao_saida, dados.operador, agora, registro_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de qualidade não encontrado.")

        cursor.executemany(
            "INSERT INTO qualidade_fotos (registro_id, etapa, foto_base64, criado_em) VALUES (%s, 'saida', %s, %s)",
            [(registro_id, foto, agora) for foto in dados.fotos_saida_base64]
        )
        conn.commit()

    return {"sucesso": True}




@router.post("/api/qualidade/excluir", tags=["Qualidade"], summary="Excluir um registro de Qualidade")
def excluir_qualidade(dados: QualidadeExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        # qualidade_fotos e qualidade_achados têm ON DELETE CASCADE —
        # apagar o registro já apaga fotos e achados junto.
        cursor.execute("DELETE FROM qualidade_registros WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de qualidade não encontrado.")
        conn.commit()

    return {"sucesso": True}


# ---- ACHADOS: cada problema encontrado pela Qualidade vira uma linha
# própria (com fotos opcionais), separada da observação geral, com
# status individual Pendente/Resolvido. ----




# ---- ACHADOS: cada problema encontrado pela Qualidade vira uma linha
# própria (com fotos opcionais), separada da observação geral, com
# status individual Pendente/Resolvido. ----
@router.get("/api/qualidade/{registro_id}/achados", tags=["Qualidade"], summary="Listar achados de um registro")
def listar_achados_qualidade(registro_id: int):
    """Traz cada achado com uma foto de "capa" (a primeira, se tiver
    mais de uma) e o total de fotos — pra montar o card na lista sem
    precisar buscar todas as fotos de todos os achados de uma vez."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                a.*,
                COALESCE(
                    (SELECT f.foto_base64 FROM qualidade_achado_fotos f WHERE f.achado_id = a.id ORDER BY f.id ASC LIMIT 1),
                    a.foto_base64
                ) AS foto_capa,
                (SELECT COUNT(*) FROM qualidade_achado_fotos f WHERE f.achado_id = a.id) AS total_fotos
            FROM qualidade_achados a
            WHERE a.registro_id = %s
            ORDER BY a.id ASC
            """,
            (registro_id,)
        )
        return cursor.fetchall()




@router.get("/api/qualidade/achados/{achado_id}/fotos", tags=["Qualidade"], summary="Listar todas as fotos de um achado")
def get_fotos_achado_qualidade(achado_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, foto_base64, criado_em FROM qualidade_achado_fotos WHERE achado_id = %s ORDER BY id ASC",
            (achado_id,)
        )
        fotos = cursor.fetchall()

        # 🔧 Achado antigo (de antes dessa mudança) só tem a foto na
        # coluna foto_base64 da própria tabela, não em
        # qualidade_achado_fotos — cai aqui como fallback pra galeria
        # não aparecer vazia pra quem já tinha achado cadastrado.
        if not fotos:
            cursor.execute("SELECT foto_base64 FROM qualidade_achados WHERE id = %s", (achado_id,))
            achado = cursor.fetchone()
            if achado and achado["foto_base64"]:
                return [{"id": None, "foto_base64": achado["foto_base64"], "criado_em": None}]

        return fotos




@router.post("/api/qualidade/achados", tags=["Qualidade"], summary="Adicionar um achado a um registro de Qualidade")
def criar_achado_qualidade(dados: QualidadeAchadoCriar):
    if not dados.descricao or not dados.descricao.strip():
        raise HTTPException(status_code=400, detail="Descreva o achado.")

    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT peca_id FROM qualidade_registros WHERE id = %s", (dados.registro_id,))
        registro = cursor.fetchone()
        if not registro:
            raise HTTPException(status_code=404, detail="Registro de qualidade não encontrado.")

        cursor.execute(
            """
            INSERT INTO qualidade_achados (registro_id, descricao, status, criado_por, criado_em)
            VALUES (%s, %s, 'Pendente', %s, %s)
            RETURNING id
            """,
            (dados.registro_id, dados.descricao.strip(), dados.operador, agora)
        )
        achado_id = cursor.fetchone()["id"]

        if dados.fotos_base64:
            cursor.executemany(
                "INSERT INTO qualidade_achado_fotos (achado_id, foto_base64, criado_em) VALUES (%s, %s, %s)",
                [(achado_id, foto, agora) for foto in dados.fotos_base64]
            )

        conn.commit()

    # 🆕 Achado de Qualidade era o único evento "problema encontrado" do
    # sistema que não avisava ninguém — a única forma de saber era abrir
    # o registro manualmente. Agora avisa como os demais eventos críticos
    # (área "Ambos": não tem área da oficina associada, só os admins).
    enviar_push_para_area(
        titulo="🔍 Achado de Qualidade",
        corpo=f"{dados.operador} — {registro['peca_id']}: {dados.descricao.strip()}",
        area="Ambos"
    )

    return {"sucesso": True, "id": achado_id}




@router.post("/api/qualidade/achados/editar", tags=["Qualidade"], summary="Editar a descrição de um achado")
def editar_achado_qualidade(dados: QualidadeAchadoEditar):
    if not dados.descricao or not dados.descricao.strip():
        raise HTTPException(status_code=400, detail="Descreva o achado.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE qualidade_achados SET descricao = %s WHERE id = %s",
            (dados.descricao.strip(), dados.id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}




@router.post("/api/qualidade/achados/resolver", tags=["Qualidade"], summary="Marcar um achado como resolvido")
def resolver_achado_qualidade(dados: QualidadeAchadoResolver):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE qualidade_achados
               SET status = 'Resolvido', foto_resolucao_base64 = %s, resolvido_por = %s, resolvido_em = %s
               WHERE id = %s""",
            (dados.foto_base64, dados.operador, agora, dados.id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}




@router.post("/api/qualidade/achados/reabrir", tags=["Qualidade"], summary="Reabrir um achado marcado como resolvido")
def reabrir_achado_qualidade(dados: QualidadeAchadoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE qualidade_achados
               SET status = 'Pendente', foto_resolucao_base64 = NULL, resolvido_por = NULL, resolvido_em = NULL
               WHERE id = %s""",
            (dados.id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}




@router.post("/api/qualidade/achados/excluir", tags=["Qualidade"], summary="Excluir um achado")
def excluir_achado_qualidade(dados: QualidadeAchadoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM qualidade_achados WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achado não encontrado.")
        conn.commit()

    return {"sucesso": True}


# ==========================================
# 🆕 LAUDOS (PDFs de folhão finalizado) — antes só existiam no
# localStorage de quem gerava; agora persistem no Neon, visíveis pra
# todo mundo na Auditoria (igual o resto do histórico).
# ==========================================
