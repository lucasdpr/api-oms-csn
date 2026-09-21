"""
Cadastro do LOTE 1 — Checklist de Execução do Molde MCC4.

O QUE ESTÁ AQUI (confirmado com você, pronto pra subir):
  - Grupo Desmontagem completo (Placa x4, Vulso, Foot Roll, Guia)
  - Grupo Chegada/Testes (lavagem, inspeção, hidrostático, hidráulico,
    bitola/aresta esquerda e direita, motivo do reparo)

O QUE FICA PRO LOTE 2 (ainda sem os sub-passos detalhados):
  - Pintura (preparação + pintura em si)
  - Montagem (preparação + início de montagem)
  - Alinhamento de foot roll/guia + medições
  - Teste Final (17 perguntas — m4-fin-0 até m4-fin-16)

COMO USAR:
  1. Preencha API_BASE e OPERADOR_MATRICULA logo abaixo.
  2. Rode: pip install requests  (se ainda não tiver)
  3. Rode: python cadastrar_lote1_molde4.py
  4. Confira a saída — cada linha mostra se deu certo ou não.

Pode rodar mais de uma vez sem medo de duplicar备份: se uma etapa com
o mesmo texto já existir, você vai só ver duas etapas iguais na lista
(o backend não tem trava de "duplicado" hoje) — se isso acontecer,
me avisa que a gente adiciona essa trava.
"""

import requests

# ⚠️ AJUSTE AQUI antes de rodar
API_BASE = "https://api-oms-csn.onrender.com"   # sem barra no final
OPERADOR_MATRICULA = "CBK3574"              # precisa estar em MATRICULAS_ADM

TIPO_EQUIPAMENTO = "molde-mcc4"  # calculado a partir de item.tipo="Molde" + mcc_compat="4"

# --------------------------------------------------------------
# DESCRIÇÕES DE REFERÊNCIA (o "como fazer" de cada tópico de
# desmontagem — igual você me passou)
# --------------------------------------------------------------
DESC_PLACA = (
    "1) Retirar parafuso da régua\n"
    "2) Retirar a régua\n"
    "3) Retirar a tampa do parafuso\n"
    "4) Prender o suporte na placa\n"
    "5) Estropar com a talha\n"
    "6) Retirar o parafuso\n"
    "7) Levar pra bancada"
)
DESC_VULSO = (
    "1) Retirar a tampa do vulso\n"
    "2) Desconectar o cabo do vulso\n"
    "3) Retirar o vulso (leva pra elétrica)"
)
DESC_FOOT_ROLL = (
    "1) Estropar com talha e cinta\n"
    "2) Desapertar o parafuso\n"
    "3) Descer o foot roll pro estande"
)
DESC_GUIA = (
    "1) Colocar o cachorro na guia\n"
    "2) Estropar com a talha\n"
    "3) Descer e levar pra bancada"
)

# --------------------------------------------------------------
# MAPAS DA TABELA "FOLGA ARESTA" (19 bitolas x 3 medidas, por lado)
# --------------------------------------------------------------
MAPA_ARESTA_ESQUERDA = {"1000-sup": "m4-fa-1000-es", "1000-meio": "m4-fa-1000-em", "1000-inf": "m4-fa-1000-ei", "1030-sup": "m4-fa-1030-es", "1030-meio": "m4-fa-1030-em", "1030-inf": "m4-fa-1030-ei", "1040-sup": "m4-fa-1040-es", "1040-meio": "m4-fa-1040-em", "1040-inf": "m4-fa-1040-ei", "1090-sup": "m4-fa-1090-es", "1090-meio": "m4-fa-1090-em", "1090-inf": "m4-fa-1090-ei", "1100-sup": "m4-fa-1100-es", "1100-meio": "m4-fa-1100-em", "1100-inf": "m4-fa-1100-ei", "1160-sup": "m4-fa-1160-es", "1160-meio": "m4-fa-1160-em", "1160-inf": "m4-fa-1160-ei", "1180-sup": "m4-fa-1180-es", "1180-meio": "m4-fa-1180-em", "1180-inf": "m4-fa-1180-ei", "1230-sup": "m4-fa-1230-es", "1230-meio": "m4-fa-1230-em", "1230-inf": "m4-fa-1230-ei", "1290-sup": "m4-fa-1290-es", "1290-meio": "m4-fa-1290-em", "1290-inf": "m4-fa-1290-ei", "1360-sup": "m4-fa-1360-es", "1360-meio": "m4-fa-1360-em", "1360-inf": "m4-fa-1360-ei", "1380-sup": "m4-fa-1380-es", "1380-meio": "m4-fa-1380-em", "1380-inf": "m4-fa-1380-ei", "1420-sup": "m4-fa-1420-es", "1420-meio": "m4-fa-1420-em", "1420-inf": "m4-fa-1420-ei", "1460-sup": "m4-fa-1460-es", "1460-meio": "m4-fa-1460-em", "1460-inf": "m4-fa-1460-ei", "1500-sup": "m4-fa-1500-es", "1500-meio": "m4-fa-1500-em", "1500-inf": "m4-fa-1500-ei", "1530-sup": "m4-fa-1530-es", "1530-meio": "m4-fa-1530-em", "1530-inf": "m4-fa-1530-ei", "1550-sup": "m4-fa-1550-es", "1550-meio": "m4-fa-1550-em", "1550-inf": "m4-fa-1550-ei", "1560-sup": "m4-fa-1560-es", "1560-meio": "m4-fa-1560-em", "1560-inf": "m4-fa-1560-ei", "1580-sup": "m4-fa-1580-es", "1580-meio": "m4-fa-1580-em", "1580-inf": "m4-fa-1580-ei", "1620-sup": "m4-fa-1620-es", "1620-meio": "m4-fa-1620-em", "1620-inf": "m4-fa-1620-ei"}
MAPA_ARESTA_DIREITA = {"1000-sup": "m4-fa-1000-ds", "1000-meio": "m4-fa-1000-dm", "1000-inf": "m4-fa-1000-di", "1030-sup": "m4-fa-1030-ds", "1030-meio": "m4-fa-1030-dm", "1030-inf": "m4-fa-1030-di", "1040-sup": "m4-fa-1040-ds", "1040-meio": "m4-fa-1040-dm", "1040-inf": "m4-fa-1040-di", "1090-sup": "m4-fa-1090-ds", "1090-meio": "m4-fa-1090-dm", "1090-inf": "m4-fa-1090-di", "1100-sup": "m4-fa-1100-ds", "1100-meio": "m4-fa-1100-dm", "1100-inf": "m4-fa-1100-di", "1160-sup": "m4-fa-1160-ds", "1160-meio": "m4-fa-1160-dm", "1160-inf": "m4-fa-1160-di", "1180-sup": "m4-fa-1180-ds", "1180-meio": "m4-fa-1180-dm", "1180-inf": "m4-fa-1180-di", "1230-sup": "m4-fa-1230-ds", "1230-meio": "m4-fa-1230-dm", "1230-inf": "m4-fa-1230-di", "1290-sup": "m4-fa-1290-ds", "1290-meio": "m4-fa-1290-dm", "1290-inf": "m4-fa-1290-di", "1360-sup": "m4-fa-1360-ds", "1360-meio": "m4-fa-1360-dm", "1360-inf": "m4-fa-1360-di", "1380-sup": "m4-fa-1380-ds", "1380-meio": "m4-fa-1380-dm", "1380-inf": "m4-fa-1380-di", "1420-sup": "m4-fa-1420-ds", "1420-meio": "m4-fa-1420-dm", "1420-inf": "m4-fa-1420-di", "1460-sup": "m4-fa-1460-ds", "1460-meio": "m4-fa-1460-dm", "1460-inf": "m4-fa-1460-di", "1500-sup": "m4-fa-1500-ds", "1500-meio": "m4-fa-1500-dm", "1500-inf": "m4-fa-1500-di", "1530-sup": "m4-fa-1530-ds", "1530-meio": "m4-fa-1530-dm", "1530-inf": "m4-fa-1530-di", "1550-sup": "m4-fa-1550-ds", "1550-meio": "m4-fa-1550-dm", "1550-inf": "m4-fa-1550-di", "1560-sup": "m4-fa-1560-ds", "1560-meio": "m4-fa-1560-dm", "1560-inf": "m4-fa-1560-di", "1580-sup": "m4-fa-1580-ds", "1580-meio": "m4-fa-1580-dm", "1580-inf": "m4-fa-1580-di", "1620-sup": "m4-fa-1620-ds", "1620-meio": "m4-fa-1620-dm", "1620-inf": "m4-fa-1620-di"}

# --------------------------------------------------------------
# LOTE 1 — lista de etapas a cadastrar
# Cada item: (area, texto, folhao_campo, tipo_resposta, descricao)
# folhao_campo = None quando a etapa não tem campo correspondente
# no documento oficial (é só controle interno do processo).
# --------------------------------------------------------------
ETAPAS_LOTE_1 = [
    # --- Chegada / Testes ---
    ("mecanica", "Lavagem do molde", None, "sim_nao", None),
    ("mecanica", "Inspeção visual", None, "sim_nao", None),
    ("mecanica", "Teste hidrostático", "m4-rec-10", "sim_nao", None),
    ("mecanica", "Teste hidráulico (movimentação do molde)", "m4-rec-9", "sim_nao", None),
    ("mecanica", "Verificar bitola/aresta — Esquerda", None, "medicao_multipla", "19 pontos de largura (1000mm a 1620mm), 3 medidas cada (superior/meio/inferior)"),
    ("mecanica", "Verificar bitola/aresta — Direita", None, "medicao_multipla", "19 pontos de largura (1000mm a 1620mm), 3 medidas cada (superior/meio/inferior)"),
    ("mecanica", "Qual a situação do molde / Observação", "molde4-motivo", "medicao", None),

    # --- Desmontagem: Placa (mesma sequência, 4 peças) ---
    ("mecanica", "Desmontagem placa larga fixa", None, "sim_nao", DESC_PLACA),
    ("mecanica", "Desmontagem placa larga móvel", None, "sim_nao", DESC_PLACA),
    ("mecanica", "Desmontagem placa estreita direita", None, "sim_nao", DESC_PLACA),
    ("mecanica", "Desmontagem placa estreita esquerda", None, "sim_nao", DESC_PLACA),

    # --- Desmontagem: demais componentes ---
    ("mecanica", "Desmontagem de vulso", None, "sim_nao", DESC_VULSO),
    ("mecanica", "Desmontagem de foot roll", None, "sim_nao", DESC_FOOT_ROLL),
    ("mecanica", "Desmontagem de guia", None, "sim_nao", DESC_GUIA),
]


def cadastrar_etapa(area, texto, folhao_campo, tipo_resposta, descricao, campo_json=None):
    payload = {
        "equipamento_id": TIPO_EQUIPAMENTO,
        "area": area,
        "texto": texto,
        "operador": OPERADOR_MATRICULA,
        "tipo_resposta": tipo_resposta,
        "descricao": descricao,
    }
    # medicao_multipla guarda o mapa de campos como JSON no folhao_campo
    if tipo_resposta == "medicao_multipla" and campo_json is not None:
        import json as _json
        payload["folhao_campo"] = _json.dumps(campo_json)
    elif folhao_campo:
        payload["folhao_campo"] = folhao_campo

    resp = requests.post(f"{API_BASE}/api/checklist-execucao/etapas", json=payload, timeout=15)
    status = "✅" if resp.ok else f"❌ ({resp.status_code})"
    print(f"{status} {texto}")
    if not resp.ok:
        print(f"    -> {resp.text[:200]}")


if __name__ == "__main__":
    print(f"Cadastrando etapas em: {API_BASE}")
    print(f"Tipo de equipamento: {TIPO_EQUIPAMENTO}\n")

    for area, texto, folhao_campo, tipo_resposta, descricao in ETAPAS_LOTE_1:
        if texto == "Verificar bitola/aresta — Esquerda":
            cadastrar_etapa(area, texto, None, tipo_resposta, descricao, campo_json=MAPA_ARESTA_ESQUERDA)
        elif texto == "Verificar bitola/aresta — Direita":
            cadastrar_etapa(area, texto, None, tipo_resposta, descricao, campo_json=MAPA_ARESTA_DIREITA)
        else:
            cadastrar_etapa(area, texto, folhao_campo, tipo_resposta, descricao)

    print(f"\nTotal: {len(ETAPAS_LOTE_1)} etapas processadas.")
