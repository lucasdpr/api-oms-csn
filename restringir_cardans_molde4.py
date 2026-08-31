"""
Restringe a etapa "Verificação dos cardans" do Checklist de Execução:
as 16 sub-perguntas de status (articulação, sanfonada, pino-trava,
acoplamento — 4 locais x 4 tipos) viravam campo de texto livre, e
qualquer coisa digitada ali (ex: "q", "qq") não batia com o select
OK/NOK do Folhão. As 4 datas de troca continuam texto livre (não fazem
sentido como OK/NOK).

O QUE ESSE SCRIPT FAZ:
  Busca a etapa "Verificação dos cardans" (tipo "molde-mcc4"), pega o
  JSON de mapeamento atual, e renomeia as 16 chaves de status
  adicionando o sufixo " (OK/NOK)" — é esse sufixo que o
  checklist-execucao.js (já corrigido) usa pra saber que precisa
  mostrar um seletor travado, em vez de caixa de texto.

  Ex: "esq-sup-articulacao" vira "esq-sup-articulacao (OK/NOK)"
  (o valor de destino, m4-cd-art-0, não muda — só a chave).

IMPORTANTE: precisa do checklist-execucao.js já atualizado (com o
reconhecimento do sufixo "(OK/NOK)") rodando no servidor ANTES de
rodar esse script — senão o sufixo só vira um nome de campo estranho,
sem virar seletor.

COMO USAR:
  1. Preencha API_BASE e OPERADOR_MATRICULA (mesmos valores dos outros
     scripts de cadastro/correção).
  2. Rode: python restringir_cardans_molde4.py
"""

import json
import requests

# ⚠️ AJUSTE AQUI antes de rodar
API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR_MATRICULA = "CBK3574"

TIPO_EQUIPAMENTO = "molde-mcc4"
TEXTO_ETAPA = "Verificação dos cardans"

# Sufixo dos status (todas menos "data-troca")
CHAVES_STATUS_SUFIXOS = ["articulacao", "sanfonada", "pino-trava", "acoplamento"]


def buscar_etapa_cardans():
    resp = requests.get(f"{API_BASE}/api/checklist-execucao/etapas/{TIPO_EQUIPAMENTO}", timeout=15)
    resp.raise_for_status()
    todas = resp.json()
    encontradas = [e for e in todas if e.get("texto", "").strip().lower() == TEXTO_ETAPA.lower()]
    if len(encontradas) == 0:
        return None
    if len(encontradas) > 1:
        print(f"⚠️ Encontrei {len(encontradas)} etapas com esse texto — usando a primeira (id={encontradas[0]['id']}).")
    return encontradas[0]


def restringir(etapa):
    mapa_atual = json.loads(etapa["folhao_campo"])
    mapa_novo = {}
    renomeadas = 0
    for chave, campo_real in mapa_atual.items():
        eh_status = any(chave.endswith(sufixo) for sufixo in CHAVES_STATUS_SUFIXOS)
        if eh_status and "(OK/NOK)" not in chave:
            mapa_novo[f"{chave} (OK/NOK)"] = campo_real
            renomeadas += 1
        else:
            mapa_novo[chave] = campo_real  # datas e o que já foi renomeado antes, sem mexer

    payload = {
        "id": etapa["id"],
        "texto": etapa["texto"],
        "operador": OPERADOR_MATRICULA,
        "tipo_resposta": "medicao_multipla",
        "folhao_campo": json.dumps(mapa_novo),
    }
    resp = requests.post(f"{API_BASE}/api/checklist-execucao/etapas/editar", json=payload, timeout=15)
    status = "✅" if resp.ok else f"❌ ({resp.status_code})"
    print(f"{status} {renomeadas} chave(s) de status restringida(s) pra OK/NOK.")
    if not resp.ok:
        print(f"    -> {resp.text[:200]}")


if __name__ == "__main__":
    print(f"Buscando etapa '{TEXTO_ETAPA}' em: {API_BASE}\n")
    etapa = buscar_etapa_cardans()
    if not etapa:
        print(f"⚠️ Não achei nenhuma etapa com o texto '{TEXTO_ETAPA}'. Confira TIPO_EQUIPAMENTO/TEXTO_ETAPA.")
    else:
        print(f"Achei: id={etapa['id']}")
        restringir(etapa)
