from fastapi import APIRouter, HTTPException
from app_core import (
    HidraulicaAjuste,
    agora_brasil,
    enviar_push_para_area,
    get_db,
)

router = APIRouter()




@router.get("/api/hidraulica", tags=["Hidráulica"], summary="Listar estoque hidráulico")
def get_hidraulica():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hidraulica ORDER BY mcc_compat, conjunto, nome")
        return cursor.fetchall()




@router.post("/api/hidraulica/ajustar", tags=["Hidráulica"], summary="Ajustar estoque hidráulico")
def ajustar_hidraulica(dados: HidraulicaAjuste):
    if dados.local not in ("aplicado", "reserva"):
        raise HTTPException(status_code=400, detail="local precisa ser 'aplicado' ou 'reserva'.")

    coluna = "qtd_aplicado" if dados.local == "aplicado" else "qtd_reserva"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT {coluna} AS saldo FROM hidraulica WHERE id = %s", (dados.id,))
        item = cursor.fetchone()

        if not item:
            raise HTTPException(status_code=404, detail=f"Item hidráulico '{dados.id}' não encontrado.")

        if item["saldo"] + dados.fator < 0:
            raise HTTPException(status_code=400, detail="O estoque não pode ficar negativo.")

        cursor.execute(f"UPDATE hidraulica SET {coluna} = {coluna} + %s WHERE id = %s", (dados.fator, dados.id))
        cursor.execute("SELECT * FROM hidraulica WHERE id = %s", (dados.id,))
        atualizado = cursor.fetchone()

        # 🆕 Mesma ideia do ajuste de Rolos acima — tag própria pra
        # aparecer em /api/notificacoes/feed (área sintética
        # "hidraulica-estoque", pra não confundir com a área de reparo
        # "hidraulica" da Central de Áreas — são coisas diferentes).
        agora = agora_brasil().strftime("%Y-%m-%d %H:%M:%S")
        operador = dados.operador or "Sistema"
        rotulo = "Aplicado na Máquina" if dados.local == "aplicado" else "Reserva (Oficina)"
        sinal = "+" if dados.fator >= 0 else ""
        acao = f"Ajuste hidráulico — {atualizado.get('nome', dados.id)} ({rotulo}): {sinal}{dados.fator:g}"
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, area) VALUES (%s, %s, %s, %s, %s)",
            (agora, operador, "ESTOQUE-HIDRAULICA", acao, "hidraulica-estoque")
        )
        conn.commit()

    enviar_push_para_area(titulo="🛢️ Estoque Hidráulico ajustado", corpo=f"{operador} — {acao}", area="Ambos")

    return {"sucesso": True, "item": atualizado}
