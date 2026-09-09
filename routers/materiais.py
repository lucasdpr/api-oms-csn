from fastapi import APIRouter, HTTPException
from app_core import (
    MaterialAjuste,
    MaterialCadastro,
    MaterialRemover,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




@router.get("/api/materiais", tags=["Materiais (Estoque Geral)"], summary="Listar materiais do estoque geral")
def get_materiais():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE ativo = TRUE ORDER BY descricao"
        )
        return cursor.fetchall()




@router.post("/api/materiais/cadastrar", tags=["Materiais (Estoque Geral)"], summary="Cadastrar novo material")
def cadastrar_material(dados: MaterialCadastro):
    codigo = dados.codigo.strip().upper()
    descricao = dados.descricao.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT qtd FROM materiais WHERE codigo = %s", (codigo,))
        existente = cursor.fetchone()

        if existente:
            cursor.execute(
                "UPDATE materiais SET qtd = qtd + %s, ativo = TRUE WHERE codigo = %s",
                (dados.qtd, codigo)
            )
            ja_existia = True
        else:
            cursor.execute(
                "INSERT INTO materiais (codigo, descricao, qtd, local, valor_unit, ativo) "
                "VALUES (%s, %s, %s, %s, %s, TRUE)",
                (codigo, descricao, dados.qtd, dados.local, dados.valor_unit)
            )
            ja_existia = False

        cursor.execute("SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE codigo = %s", (codigo,))
        atualizado = cursor.fetchone()
        conn.commit()

    return {"sucesso": True, "ja_existia": ja_existia, "material": atualizado}




@router.post("/api/materiais/ajustar", tags=["Materiais (Estoque Geral)"], summary="Ajustar quantidade de um material")
def ajustar_material(dados: MaterialAjuste):
    codigo = dados.codigo.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT qtd FROM materiais WHERE codigo = %s AND ativo = TRUE", (codigo,))
        material = cursor.fetchone()

        if not material:
            raise HTTPException(status_code=404, detail=f"Material '{codigo}' não encontrado.")

        if material["qtd"] + dados.fator < 0:
            raise HTTPException(status_code=400, detail="O estoque não pode ficar negativo.")

        qtd_anterior = material["qtd"]

        cursor.execute(
            "UPDATE materiais SET qtd = qtd + %s WHERE codigo = %s",
            (dados.fator, codigo)
        )
        cursor.execute("SELECT codigo, descricao, qtd, local, valor_unit FROM materiais WHERE codigo = %s", (codigo,))
        atualizado = cursor.fetchone()
        conn.commit()

    # 🆕 Estoque zerando não avisava ninguém — só se percebia abrindo o
    # Almoxarifado manualmente. Notifica só na transição pra zero (não
    # dispara de novo a cada ajuste feito enquanto já está zerado).
    if qtd_anterior > 0 and atualizado["qtd"] <= 0:
        enviar_push_para_area(
            titulo="📦 Estoque zerado",
            corpo=f"{atualizado['descricao']} ({codigo}) chegou a zero no Almoxarifado.",
            area="Ambos"
        )

    return {"sucesso": True, "material": atualizado}




@router.post("/api/materiais/remover", tags=["Materiais (Estoque Geral)"], summary="Remover um material do estoque")
def remover_material(dados: MaterialRemover):
    codigo = dados.codigo.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE materiais SET ativo = FALSE WHERE codigo = %s", (codigo,))
        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail=f"Material '{codigo}' não encontrado.")
        conn.commit()

    return {"sucesso": True}
