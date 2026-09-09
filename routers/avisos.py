from fastapi import APIRouter, HTTPException
from app_core import (
    AvisoCriar,
    AvisoExcluir,
    AvisoMarcarLido,
    agora_brasil,
    get_db,
)

router = APIRouter()


# ==========================================================================
# AVISOS DO SISTEMA — comunicado criado pelo ADM ("treinamento disponível",
# "novo procedimento", etc.) que aparece pra todo colaborador ao entrar no
# sistema até ele confirmar que leu. Depois de confirmado, nunca mais
# aparece de novo pra essa matrícula (ver avisos_leitura em app_core.py).
# ==========================================================================
@router.get("/api/avisos", tags=["Avisos"], summary="Listar avisos ativos não lidos por uma matrícula")
def get_avisos(matricula: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.id, a.titulo, a.mensagem, a.criado_por, a.criado_em
            FROM avisos_sistema a
            WHERE a.ativo = TRUE
              AND NOT EXISTS (
                  SELECT 1 FROM avisos_leitura l
                  WHERE l.aviso_id = a.id AND l.matricula = %s
              )
            ORDER BY a.id ASC
            """,
            (matricula,)
        )
        return cursor.fetchall()


@router.get("/api/avisos/todos", tags=["Avisos"], summary="Listar todos os avisos (ativos e arquivados) com progresso de leitura")
def get_avisos_todos():
    with get_db() as conn:
        cursor = conn.cursor()
        # Total de colaboradores ativos — denominador do "X de Y leram".
        cursor.execute("SELECT COUNT(*) AS qtd FROM colaboradores WHERE ativo = TRUE")
        total_colaboradores = cursor.fetchone()["qtd"]

        cursor.execute(
            """
            SELECT a.id, a.titulo, a.mensagem, a.criado_por, a.criado_em, a.ativo,
                   COUNT(l.matricula) AS total_leram
            FROM avisos_sistema a
            LEFT JOIN avisos_leitura l ON l.aviso_id = a.id
            GROUP BY a.id, a.titulo, a.mensagem, a.criado_por, a.criado_em, a.ativo
            ORDER BY a.id DESC
            """
        )
        avisos = cursor.fetchall()
        for aviso in avisos:
            aviso["total_colaboradores"] = total_colaboradores
        return avisos


@router.post("/api/avisos", tags=["Avisos"], summary="Criar um novo aviso do sistema")
def criar_aviso(dados: AvisoCriar):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO avisos_sistema (titulo, mensagem, criado_por, criado_em, ativo) "
            "VALUES (%s, %s, %s, %s, TRUE) RETURNING id",
            (dados.titulo, dados.mensagem, dados.criado_por, agora)
        )
        novo_id = cursor.fetchone()["id"]
        conn.commit()
    return {"sucesso": True, "id": novo_id}


@router.post("/api/avisos/marcar_lido", tags=["Avisos"], summary="Confirmar que uma matrícula leu um aviso")
def marcar_aviso_lido(dados: AvisoMarcarLido):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO avisos_leitura (aviso_id, matricula, lido_em) VALUES (%s, %s, %s) "
            "ON CONFLICT (aviso_id, matricula) DO NOTHING",
            (dados.aviso_id, dados.matricula, agora)
        )
        conn.commit()
    return {"sucesso": True}


@router.post("/api/avisos/arquivar", tags=["Avisos"], summary="Arquivar um aviso (para de aparecer pra quem ainda não leu)")
def arquivar_aviso(dados: AvisoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE avisos_sistema SET ativo = FALSE WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Aviso não encontrado.")
        conn.commit()
    return {"sucesso": True}


@router.post("/api/avisos/excluir", tags=["Avisos"], summary="Excluir definitivamente um aviso")
def excluir_aviso(dados: AvisoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM avisos_sistema WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Aviso não encontrado.")
        conn.commit()
    return {"sucesso": True}
