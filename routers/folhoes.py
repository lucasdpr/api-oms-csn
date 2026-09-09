from fastapi import APIRouter, HTTPException
from app_core import (
    FolhaoRascunhoFinalizar,
    FolhaoRascunhoSalvar,
    agora_brasil,
    get_db,
)

router = APIRouter()




@router.get("/api/folhao/rascunhos/todos", tags=["Folhões"], summary="Listar todos os folhões em andamento (rascunhos salvos)")
def listar_todos_rascunhos_folhao():
    """Usado na tela 'Em andamento' do Painel do Técnico: lista todo
    folhão que tem progresso salvo na nuvem, pra qualquer um (técnico
    da área certa, ou ADM) continuar de onde parou. O front-end filtra
    por área cruzando equipamento_id com o tipo do equipamento — aqui
    devolve tudo, sem filtro, igual as outras rotas de listagem."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT equipamento_id, tipo_folhao, etapa, atualizado_em, criado_em FROM folhoes_rascunho ORDER BY atualizado_em DESC"
        )
        return cursor.fetchall()




@router.get("/api/folhao/{equipamento_id}", tags=["Folhões"], summary="Carregar rascunho salvo de um folhão")
def get_rascunho_folhao(equipamento_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM folhoes_rascunho WHERE equipamento_id = %s",
            (equipamento_id,)
        )
        rascunho = cursor.fetchone()

    if not rascunho:
        raise HTTPException(status_code=404, detail="Nenhum rascunho salvo para este equipamento.")

    return rascunho




@router.post("/api/folhao/salvar", tags=["Folhões"], summary="Salvar progresso de um folhão")
def salvar_rascunho_folhao(dados: FolhaoRascunhoSalvar):
    agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO folhoes_rascunho (equipamento_id, tipo_folhao, dados, etapa, atualizado_em, criado_em)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (equipamento_id) DO UPDATE SET
                tipo_folhao = EXCLUDED.tipo_folhao,
                dados = EXCLUDED.dados,
                etapa = EXCLUDED.etapa,
                atualizado_em = EXCLUDED.atualizado_em
            """,
            (dados.equipamento_id, dados.tipo_folhao, dados.dados, dados.etapa, agora, agora)
        )
        conn.commit()

    return {"sucesso": True}




@router.post("/api/folhao/finalizar", tags=["Folhões"], summary="Finalizar (limpar rascunho de) um folhão")
def finalizar_rascunho_folhao(dados: FolhaoRascunhoFinalizar):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM folhoes_rascunho WHERE equipamento_id = %s",
            (dados.equipamento_id,)
        )
        conn.commit()

    return {"sucesso": True}
