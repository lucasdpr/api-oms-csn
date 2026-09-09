from fastapi import APIRouter, HTTPException
from app_core import (
    ColaboradorAlternarAtivo,
    ColaboradorMudarCargo,
    ColaboradorResetarSenha,
    DefinirSenhaColaborador,
    LoginColaborador,
    MATRICULAS_ADM,
    _buscar_area_colaborador,
    bcrypt,
    get_db,
)

router = APIRouter()




@router.get("/api/colaboradores", tags=["Colaboradores"], summary="Listar colaboradores ativos")
def get_colaboradores():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, primeiro_acesso FROM colaboradores WHERE ativo = TRUE ORDER BY nome"
        )
        return cursor.fetchall()




@router.post("/api/colaboradores/login", tags=["Colaboradores"], summary="Autenticar colaborador (login)")
def login_colaborador(dados: LoginColaborador):
    matricula = dados.matricula.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, senha_hash, primeiro_acesso FROM colaboradores WHERE matricula = %s AND ativo = TRUE",
            (matricula,)
        )
        colaborador = cursor.fetchone()

        if not colaborador:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

        is_adm = matricula in MATRICULAS_ADM
        # ADM não depende de equipe_oficina — acesso total sempre.
        area = None if is_adm else _buscar_area_colaborador(cursor, matricula)

        if colaborador["primeiro_acesso"]:
            if dados.senha.strip().upper() != matricula:
                raise HTTPException(status_code=401, detail="No primeiro acesso, a senha é a sua própria matrícula.")
            return {
                "sucesso": True,
                "nome": colaborador["nome"],
                "cargo": colaborador["cargo"],
                "area": area,
                "is_adm": is_adm,
                "precisa_definir_senha": True
            }

        if not colaborador["senha_hash"] or not bcrypt.checkpw(dados.senha.encode(), colaborador["senha_hash"].encode()):
            raise HTTPException(status_code=401, detail="Senha incorreta.")

        return {
            "sucesso": True,
            "nome": colaborador["nome"],
            "cargo": colaborador["cargo"],
            "area": area,
            "is_adm": is_adm,
            "precisa_definir_senha": False
        }




@router.post("/api/colaboradores/definir_senha", tags=["Colaboradores"], summary="Definir senha no primeiro acesso")
def definir_senha_colaborador(dados: DefinirSenhaColaborador):
    matricula = dados.matricula.strip().upper()

    if len(dados.nova_senha.strip()) < 4:
        raise HTTPException(status_code=400, detail="A nova senha precisa ter pelo menos 4 caracteres.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, senha_hash, primeiro_acesso FROM colaboradores WHERE matricula = %s AND ativo = TRUE",
            (matricula,)
        )
        colaborador = cursor.fetchone()

        if not colaborador:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

        if colaborador["primeiro_acesso"]:
            if dados.senha_atual.strip().upper() != matricula:
                raise HTTPException(status_code=401, detail="Senha atual inválida.")
        else:
            if not colaborador["senha_hash"] or not bcrypt.checkpw(dados.senha_atual.encode(), colaborador["senha_hash"].encode()):
                raise HTTPException(status_code=401, detail="Senha atual inválida.")

        novo_hash = bcrypt.hashpw(dados.nova_senha.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "UPDATE colaboradores SET senha_hash = %s, primeiro_acesso = FALSE WHERE matricula = %s",
            (novo_hash, matricula)
        )
        conn.commit()

    return {"sucesso": True}


# ==========================================
# ADMINISTRAÇÃO DE COLABORADORES (Área Restrita — só as 2 matrículas
# admin, checagem feita no front-end igual ao resto da Área Restrita;
# essas rotas não têm autenticação própria, seguindo o mesmo padrão do
# resto da API neste sistema).
# ==========================================




# ==========================================
# ADMINISTRAÇÃO DE COLABORADORES (Área Restrita — só as 2 matrículas
# admin, checagem feita no front-end igual ao resto da Área Restrita;
# essas rotas não têm autenticação própria, seguindo o mesmo padrão do
# resto da API neste sistema).
# ==========================================
@router.get("/api/colaboradores/todos", tags=["Colaboradores"], summary="Listar todos os colaboradores (ativos e inativos)")
def get_colaboradores_todos():
    """Lista TODOS os colaboradores, ativos e inativos — usado só no
    painel de administração (a rota /api/colaboradores normal, usada
    pelo login e por outras telas, continua trazendo só quem está
    ativo)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT matricula, nome, cargo, ativo, primeiro_acesso FROM colaboradores ORDER BY ativo DESC, nome"
        )
        return cursor.fetchall()




@router.post("/api/colaboradores/mudar_cargo", tags=["Colaboradores"], summary="Trocar o cargo de um colaborador")
def mudar_cargo_colaborador(dados: ColaboradorMudarCargo):
    matricula = dados.matricula.strip().upper()
    cargo = dados.cargo.strip()
    if not cargo:
        raise HTTPException(status_code=400, detail="Informe um cargo.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE colaboradores SET cargo = %s WHERE matricula = %s", (cargo, matricula))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
        conn.commit()

    return {"sucesso": True}




@router.post("/api/colaboradores/alternar_ativo", tags=["Colaboradores"], summary="Ativar ou desativar acesso de um colaborador")
def alternar_ativo_colaborador(dados: ColaboradorAlternarAtivo):
    matricula = dados.matricula.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE colaboradores SET ativo = %s WHERE matricula = %s", (dados.ativo, matricula))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
        conn.commit()

    return {"sucesso": True, "ativo": dados.ativo}




@router.post("/api/colaboradores/resetar_senha", tags=["Colaboradores"], summary="Resetar senha de um colaborador")
def resetar_senha_colaborador(dados: ColaboradorResetarSenha):
    """Zera a senha do colaborador e marca como 'primeiro acesso' de
    novo — a senha temporária volta a ser a própria matrícula, igual
    faz o resetar_colaboradores.py no terminal, mas só pra UMA pessoa
    por vez em vez de apagar todo mundo."""
    matricula = dados.matricula.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE colaboradores SET senha_hash = NULL, primeiro_acesso = TRUE WHERE matricula = %s",
            (matricula,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
        conn.commit()

    return {"sucesso": True}
