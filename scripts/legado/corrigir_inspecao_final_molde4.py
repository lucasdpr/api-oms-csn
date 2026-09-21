"""
Correção do bug: as 17 etapas de "Inspeção Final" do Molde MCC4 foram
cadastradas como tipo_resposta="medicao_multipla" (campo de texto livre),
mas no Folhão os campos m4-fin-0..16 são botões SIM/NÃO (radio) — por
isso a ponte com o Checklist de Execução não consegue autopreencher
essas respostas (o toast mostra "m4-fin-0" até "m4-fin-13" como "não
encontrados").

O QUE ESSE SCRIPT FAZ:
  Busca as etapas já cadastradas do tipo "molde-mcc4" que começam com
  "[Inspeção Final]", e edita cada uma pra tipo_resposta="sim_nao" com
  folhao_campo="m4-fin-{idx}" (na ordem em que aparecem).

  Usa o endpoint /api/checklist-execucao/etapas/editar — não apaga e
  recria, então o histórico de quem já respondeu cada etapa continua
  intacto.

CUSTO DESSA CORREÇÃO (leia antes de rodar):
  A etapa também guardava um campo de MEDIDA (m4-fin-{idx}-med), que
  vinha junto no JSON de medicao_multipla. Depois dessa correção, só o
  resultado (SIM/NÃO) volta a autopreencher — a medida não tem mais
  como vir automática dessa mesma etapa (o campo -med do Folhão
  continua existindo, só não é mais preenchido pela ponte). Se isso
  for um problema, me avise antes de rodar — dá pra fazer diferente
  (duas etapas separadas por item, uma sim_nao + uma medicao), mas aí
  o Checklist de Execução ganha o dobro de etapas nessa seção.

  Respostas HISTÓRICAS (já dadas por técnicos, no formato de texto
  livre de antes) NÃO viram SIM/NÃO magicamente — a ponte só volta a
  funcionar pras respostas dadas DAQUI PRA FRENTE, depois da correção.

COMO USAR:
  1. Preencha API_BASE e OPERADOR_MATRICULA logo abaixo (mesmos valores
     que você já usa nos outros scripts de cadastro).
  2. Rode: python corrigir_inspecao_final_molde4.py
  3. Confira a saída — precisa mostrar 17 linhas com ✅.
"""

import requests

# ⚠️ AJUSTE AQUI antes de rodar (mesmos valores do cadastrar_lote1/2)
API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR_MATRICULA = "CBK3574"

TIPO_EQUIPAMENTO = "molde-mcc4"
PREFIXO_TEXTO = "[Inspeção Final]"


def buscar_etapas_inspecao_final():
    resp = requests.get(f"{API_BASE}/api/checklist-execucao/etapas/{TIPO_EQUIPAMENTO}", timeout=15)
    resp.raise_for_status()
    todas = resp.json()
    # Mantém a ordem em que foram cadastradas (mesma ordem do
    # enumerate(INSPECAO_FINAL) original) — normalmente já vem
    # ordenado por id/criação, mas ordenamos por id pra garantir.
    encontradas = [e for e in todas if str(e.get("texto", "")).startswith(PREFIXO_TEXTO)]
    encontradas.sort(key=lambda e: e["id"])
    return encontradas


def corrigir_etapa(etapa_id, texto, idx):
    payload = {
        "id": etapa_id,
        "texto": texto,
        "operador": OPERADOR_MATRICULA,
        "tipo_resposta": "sim_nao",
        "folhao_campo": f"m4-fin-{idx}",
    }
    resp = requests.post(f"{API_BASE}/api/checklist-execucao/etapas/editar", json=payload, timeout=15)
    status = "✅" if resp.ok else f"❌ ({resp.status_code})"
    print(f"{status} [{idx}] {texto}  ->  folhao_campo=m4-fin-{idx}, tipo_resposta=sim_nao")
    if not resp.ok:
        print(f"    -> {resp.text[:200]}")


if __name__ == "__main__":
    print(f"Buscando etapas de Inspeção Final em: {API_BASE}\n")
    etapas = buscar_etapas_inspecao_final()

    if len(etapas) == 0:
        print("⚠️ Nenhuma etapa encontrada com esse prefixo. Confira TIPO_EQUIPAMENTO e PREFIXO_TEXTO.")
    elif len(etapas) != 17:
        print(f"⚠️ Esperava 17 etapas, encontrei {len(etapas)}. Confira a lista antes de continuar:")
        for e in etapas:
            print(f"   id={e['id']}  texto={e['texto']}")
        print("\nSe a lista acima estiver certa mesmo assim (ex: só 14 já existem), pode seguir.")

    print()
    for idx, etapa in enumerate(etapas):
        corrigir_etapa(etapa["id"], etapa["texto"], idx)

    print(f"\nTotal: {len(etapas)} etapa(s) corrigida(s).")
