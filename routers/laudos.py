from fastapi import APIRouter, HTTPException
from app_core import (
    LaudoCriar,
    LaudoExcluir,
    Optional,
    agora_brasil,
    get_db,
)

router = APIRouter()




# ==========================================
# 🆕 LAUDOS (PDFs de folhão finalizado) — antes só existiam no
# localStorage de quem gerava; agora persistem no Neon, visíveis pra
# todo mundo na Auditoria (igual o resto do histórico).
# ==========================================
@router.get("/api/laudos", tags=["Laudos"], summary="Listar laudos gerados")
def listar_laudos(peca_id: Optional[str] = None, limite: int = 200):
    with get_db() as conn:
        cursor = conn.cursor()
        if peca_id:
            cursor.execute(
                "SELECT * FROM laudos WHERE peca_id = %s ORDER BY id DESC LIMIT %s",
                (peca_id, limite)
            )
        else:
            cursor.execute("SELECT * FROM laudos ORDER BY id DESC LIMIT %s", (limite,))
        return cursor.fetchall()




@router.get("/api/laudos/{laudo_id}", tags=["Laudos"], summary="Consultar um laudo específico")
def get_laudo(laudo_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM laudos WHERE id = %s", (laudo_id,))
        laudo = cursor.fetchone()
        if not laudo:
            raise HTTPException(status_code=404, detail="Laudo não encontrado.")
        return laudo




@router.post("/api/laudos", tags=["Laudos"], summary="Salvar um laudo gerado")
def criar_laudo(dados: LaudoCriar):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        # 🔧 CORREÇÃO CRÍTICA (achado de auditoria de Go-Live): faltava o
        # predicado WHERE no ON CONFLICT — laudos_execucao_id_unica é um
        # índice ÚNICO PARCIAL (só onde execucao_id IS NOT NULL), e o
        # Postgres só usa um índice parcial como alvo do ON CONFLICT se a
        # cláusula repetir o mesmo predicado. Sem isso, TODO INSERT com
        # execucao_id preenchido falhava com "no unique or exclusion
        # constraint matching the ON CONFLICT specification" — ou seja,
        # nenhum Folhão com Checklist de Execução iniciado conseguia
        # salvar o laudo, um 500 em produção.
        #
        # 🔧 CORREÇÃO (mesma auditoria): também valida que a execução
        # pertence à MESMA peça informada — sem isso, mandar o
        # execucao_id de outro equipamento sobrescrevia o laudo daquele
        # reparo (IDOR com perda de dado).
        if dados.execucao_id is not None:
            cursor.execute(
                "SELECT equipamento_id FROM checklist_execucao_execucoes WHERE id = %s",
                (dados.execucao_id,)
            )
            execucao = cursor.fetchone()
            if not execucao or execucao["equipamento_id"] != dados.peca_id:
                raise HTTPException(status_code=400, detail="execucao_id não corresponde à peça informada.")
            cursor.execute(
                """
                INSERT INTO laudos (peca_id, tipo, html, criado_por, criado_em, execucao_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (execucao_id) WHERE execucao_id IS NOT NULL DO UPDATE SET
                    peca_id = EXCLUDED.peca_id,
                    tipo = EXCLUDED.tipo,
                    html = EXCLUDED.html,
                    criado_por = EXCLUDED.criado_por,
                    criado_em = EXCLUDED.criado_em
                RETURNING id
                """,
                (dados.peca_id, dados.tipo, dados.html, dados.operador, agora, dados.execucao_id)
            )
        else:
            cursor.execute(
                "INSERT INTO laudos (peca_id, tipo, html, criado_por, criado_em) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (dados.peca_id, dados.tipo, dados.html, dados.operador, agora)
            )
        laudo_id = cursor.fetchone()["id"]
        conn.commit()

    return {"sucesso": True, "id": laudo_id}




@router.post("/api/laudos/excluir", tags=["Laudos"], summary="Excluir um laudo")
def excluir_laudo(dados: LaudoExcluir):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM laudos WHERE id = %s", (dados.id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Laudo não encontrado.")
        conn.commit()

    return {"sucesso": True}
