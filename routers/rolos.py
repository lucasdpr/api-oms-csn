from fastapi import APIRouter, HTTPException
from app_core import (
    RoloAjuste,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




@router.get("/api/rolos", tags=["Rolos"], summary="Listar estoque de rolos")
def get_rolos():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rolos ORDER BY conjunto, nome")
        return cursor.fetchall()




@router.post("/api/rolos/ajustar", tags=["Rolos"], summary="Ajustar estoque de rolos")
def ajustar_rolo(dados: RoloAjuste):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT qtd FROM rolos WHERE id = %s", (dados.id,))
        rolo = cursor.fetchone()

        if not rolo:
            raise HTTPException(status_code=404, detail=f"Rolo '{dados.id}' não encontrado.")

        if rolo["qtd"] + dados.fator < 0:
            raise HTTPException(status_code=400, detail="O estoque não pode ficar negativo.")

        cursor.execute("UPDATE rolos SET qtd = qtd + %s WHERE id = %s", (dados.fator, dados.id))
        cursor.execute("SELECT * FROM rolos WHERE id = %s", (dados.id,))
        atualizado = cursor.fetchone()

        # 🆕 "vai ter que colocar rolos, hidráulica tanto a área e tando o
        # estoque pq se for atualizado gera notificação" — grava com uma
        # tag própria (não mais via registrarHistorico do front-end, que
        # usava "ALMOXARIFADO" pra tudo e nunca aparecia na Central de
        # Notificações) pra dar pra filtrar certinho em
        # /api/notificacoes/feed.
        agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
        operador = dados.operador or "Sistema"
        sinal = "+" if dados.fator >= 0 else ""
        acao = f"Ajuste de estoque — {atualizado.get('nome', dados.id)}: {sinal}{dados.fator:g} (saldo atual: {atualizado['qtd']:g})"
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, area) VALUES (%s, %s, %s, %s, %s)",
            (agora, operador, "ESTOQUE-ROLOS", acao, "rolos")
        )
        conn.commit()

    enviar_push_para_area(titulo="🧵 Estoque de Rolos ajustado", corpo=f"{operador} — {acao}", area="Ambos")

    return {"sucesso": True, "rolo": atualizado}
