from fastapi import APIRouter, Depends, HTTPException
from app_core import (
    ColaboradorAlternarAtivo,
    ColaboradorCriar,
    ColaboradorEditar,
    ColaboradorHeartbeat,
    ColaboradorMudarCargo,
    ColaboradorResetarSenha,
    DefinirSenhaColaborador,
    LoginColaborador,
    MATRICULAS_ADM,
    _buscar_area_colaborador,
    agora_brasil,
    bcrypt,
    exigir_admin,
    gerar_token,
    get_db,
)

router = APIRouter()


# 🆕 Auditoria das ações admin sobre colaboradores (pedido do usuário:
# "quem me bloqueou e por quê" não tinha resposta nenhuma até aqui).
# Reaproveita 100% a infraestrutura de log_eventos que já existe pro
# Prontuário das peças — peca_id vira a MATRÍCULA do colaborador
# afetado, então GET /api/historico_eventos?peca_id=<matricula> já
# devolve pronto o "evento de cada funcionário separado" que o usuário
# pediu, sem precisar de tabela nova. Insert direto (sem passar pela
# rota /api/registrar_evento) pra não disparar push com o título
# "Registro no equipamento", que não faz sentido pra uma ação admin.
def _registrar_evento_colaborador(cursor, matricula_alvo, acao, admin_matricula):
    cursor.execute("SELECT nome FROM colaboradores WHERE matricula = %s", (admin_matricula,))
    row = cursor.fetchone()
    operador = f"{row['nome']} (ADM)" if row else admin_matricula
    cursor.execute(
        "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, categoria) VALUES (%s, %s, %s, %s, %s)",
        (agora_brasil().strftime("%Y-%m-%d %H:%M:%S"), operador, matricula_alvo, acao, "Colaboradores")
    )




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

        # 🆕 Marca presença já no login — o front também manda heartbeat
        # periódico depois disso pra manter "Online" enquanto o app fica
        # aberto (ver /api/colaboradores/heartbeat, mais abaixo).
        cursor.execute(
            "UPDATE colaboradores SET ultimo_acesso = %s WHERE matricula = %s",
            (agora_brasil().strftime("%Y-%m-%d %H:%M:%S"), matricula)
        )
        conn.commit()

        return {
            "sucesso": True,
            "nome": colaborador["nome"],
            "cargo": colaborador["cargo"],
            "area": area,
            "is_adm": is_adm,
            "precisa_definir_senha": False,
            "token": gerar_token(matricula),  # 🆕 usado pelo front nas rotas admin (Authorization: Bearer <token>)
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

    return {"sucesso": True, "token": gerar_token(matricula)}


# ==========================================
# ADMINISTRAÇÃO DE COLABORADORES (Área Restrita — só as 3 matrículas
# ADM). 🔧 As 3 rotas de escrita abaixo (mudar_cargo/alternar_ativo/
# resetar_senha) agora exigem Depends(exigir_admin) — antes a checagem
# era só visual no front-end (achado numa revisão de segurança: dava
# pra chamar essas rotas direto, sem estar logado nem ser admin). A de
# listagem (get_colaboradores_todos) continua aberta — é só leitura de
# nome/cargo/matrícula, sem dado sensível (sem senha_hash).
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
            "SELECT matricula, nome, cargo, ativo, primeiro_acesso, ultimo_acesso, area FROM colaboradores ORDER BY ativo DESC, nome"
        )
        return cursor.fetchall()




@router.post("/api/colaboradores/heartbeat", tags=["Colaboradores"], summary="Sinal de vida — mantém o colaborador \"Online\" na Administração")
def heartbeat_colaborador(dados: ColaboradorHeartbeat):
    """Chamado pelo front a cada ~60s enquanto alguém está logado e com
    o app aberto (ver window.iniciarHeartbeatColaborador em script.js).
    Não exige admin — é o próprio colaborador reportando presença."""
    matricula = dados.matricula.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE colaboradores SET ultimo_acesso = %s WHERE matricula = %s",
            (agora_brasil().strftime("%Y-%m-%d %H:%M:%S"), matricula)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
        conn.commit()
    return {"sucesso": True}




@router.post("/api/colaboradores/mudar_cargo", tags=["Colaboradores"], summary="Trocar o cargo de um colaborador")
def mudar_cargo_colaborador(dados: ColaboradorMudarCargo, admin: str = Depends(exigir_admin)):
    matricula = dados.matricula.strip().upper()
    cargo = dados.cargo.strip()
    if not cargo:
        raise HTTPException(status_code=400, detail="Informe um cargo.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cargo FROM colaboradores WHERE matricula = %s", (matricula,))
        atual = cursor.fetchone()
        if not atual:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

        cursor.execute("UPDATE colaboradores SET cargo = %s WHERE matricula = %s", (cargo, matricula))
        _registrar_evento_colaborador(cursor, matricula, f"🆔 Cargo alterado de \"{atual['cargo'] or '-'}\" para \"{cargo}\".", admin)
        conn.commit()

    return {"sucesso": True}




@router.post("/api/colaboradores/alternar_ativo", tags=["Colaboradores"], summary="Ativar ou desativar acesso de um colaborador")
def alternar_ativo_colaborador(dados: ColaboradorAlternarAtivo, admin: str = Depends(exigir_admin)):
    matricula = dados.matricula.strip().upper()

    # 🆕 Motivo obrigatório só ao BLOQUEAR — reativar não precisa
    # (pedido do usuário: "daqui 3 meses ninguém lembra por que fulano
    # foi bloqueado" sem isso registrado).
    if not dados.ativo and not (dados.motivo and dados.motivo.strip()):
        raise HTTPException(status_code=400, detail="Informe o motivo do bloqueio.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE colaboradores SET ativo = %s WHERE matricula = %s", (dados.ativo, matricula))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

        acao = f"🔴 Acesso bloqueado. Motivo: {dados.motivo.strip()}" if not dados.ativo else "🟢 Acesso reativado."
        _registrar_evento_colaborador(cursor, matricula, acao, admin)
        conn.commit()

    return {"sucesso": True, "ativo": dados.ativo}




@router.post("/api/colaboradores/resetar_senha", tags=["Colaboradores"], summary="Resetar senha de um colaborador")
def resetar_senha_colaborador(dados: ColaboradorResetarSenha, admin: str = Depends(exigir_admin)):
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

        _registrar_evento_colaborador(cursor, matricula, "🔑 Senha resetada pelo administrador (volta a ser a própria matrícula).", admin)
        conn.commit()

    return {"sucesso": True}




@router.post("/api/colaboradores/criar", tags=["Colaboradores"], summary="Cadastrar novo colaborador")
def criar_colaborador(dados: ColaboradorCriar, admin: str = Depends(exigir_admin)):
    """Antes só dava pra dar acesso a alguém novo rodando script no
    servidor (importar_colaboradores.py) — maior buraco de "controle
    real" da tela de Administração. Nasce com a senha padrão (a própria
    matrícula) e primeiro_acesso=TRUE, igual todo colaborador novo."""
    matricula = dados.matricula.strip().upper()
    nome = dados.nome.strip()
    if not matricula or not nome:
        raise HTTPException(status_code=400, detail="Matrícula e nome são obrigatórios.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT matricula FROM colaboradores WHERE matricula = %s", (matricula,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Já existe um colaborador com essa matrícula.")

        cursor.execute(
            "INSERT INTO colaboradores (matricula, nome, cargo, area, ativo, primeiro_acesso) VALUES (%s, %s, %s, %s, TRUE, TRUE)",
            (matricula, nome, (dados.cargo or "Colaborador").strip(), dados.area or "Ambos")
        )
        _registrar_evento_colaborador(cursor, matricula, f"🆕 Colaborador cadastrado (cargo: {dados.cargo or 'Colaborador'}).", admin)
        conn.commit()

    return {"sucesso": True}




@router.post("/api/colaboradores/editar", tags=["Colaboradores"], summary="Editar nome/área de um colaborador")
def editar_colaborador(dados: ColaboradorEditar, admin: str = Depends(exigir_admin)):
    matricula = dados.matricula.strip().upper()
    campos, valores, mudancas = [], [], []

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, area FROM colaboradores WHERE matricula = %s", (matricula,))
        atual = cursor.fetchone()
        if not atual:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

        if dados.nome is not None and dados.nome.strip() and dados.nome.strip() != atual["nome"]:
            campos.append("nome = %s"); valores.append(dados.nome.strip())
            mudancas.append(f"nome: \"{atual['nome']}\" → \"{dados.nome.strip()}\"")
        if dados.area is not None and dados.area != atual["area"]:
            campos.append("area = %s"); valores.append(dados.area)
            mudancas.append(f"área: \"{atual['area'] or '-'}\" → \"{dados.area or '-'}\"")

        if not campos:
            return {"sucesso": True}  # nada mudou, não é erro

        valores.append(matricula)
        cursor.execute(f"UPDATE colaboradores SET {', '.join(campos)} WHERE matricula = %s", valores)
        _registrar_evento_colaborador(cursor, matricula, f"✏️ Dados editados — {'; '.join(mudancas)}.", admin)
        conn.commit()

    return {"sucesso": True}
