"""
Migra as etapas já cadastradas do Molde MCC4 (tipo "molde-mcc4") das
áreas antigas (mecanica/eletrica) pros 3 blocos novos: chegada,
manutencao, saida.

IMPORTANTE — PRÉ-REQUISITOS antes de rodar isso:
  1. O backend (main.py) já precisa estar publicado com o campo `area`
     aceito em /api/checklist-execucao/etapas/editar.
  2. O front-end (checklist-execucao.js e dados.js) já precisa estar
     publicado com CHECKLIST_EXECUCAO_SECOES_POR_TIPO.
  Se rodar esse script antes disso, a migração vai "funcionar" (o
  banco aceita qualquer string em area), mas a tela vai continuar
  mostrando Mecânica/Elétrica/etc, porque o front-end ainda não sabe
  que "molde-mcc4" usa outra lista de seções.

COMO CLASSIFIQUEI (baseado no prefixo do folhao_campo, que eu conheço
dos scripts cadastrar_lote1/lote2 — não é chute por palavra-chave):
  CHEGADA:     m4-rec-* (recebimento mecânica), m4-ele-* (recebimento
               elétrica), m4-per-ent-* (peritagem entrada na oficina)
  SAÍDA:       m4-fin-* (inspeção final), m4-per-sai-* (peritagem saída
               da oficina)
  MANUTENÇÃO:  tudo mais (revisão, ajustes, rolos, sensor de nível,
               termopares, engrenagem/chavetas, excêntrico, cardans,
               transmissões) — é o grosso do reparo em si.

  AMBÍGUO (fica de fora da migração automática, você decide na mão):
    "Identificação de componentes — Placas/Redutores/Cilindros"
    (m4-id-*) — essa tabela tem colunas de SAÍDA MÁQUINA (quando a
    peça chega na oficina) E SAÍDA OFICINA (quando sai) na MESMA
    etapa. Não dá pra jogar automaticamente num bloco só sem perder
    metade do sentido. Ou fica em Manutenção mesmo (mais neutro), ou
    alguém duplica essa etapa em duas (uma só com os campos -mq pra
    Chegada, outra só com os campos -of pra Saída) — isso eu não faço
    sozinho, é decisão de conteúdo, não de código.

COMO USAR:
  1. Ajuste API_BASE e OPERADOR_MATRICULA.
  2. Rode primeiro SEM o --aplicar (dry run) pra conferir a
     classificação antes de mexer em produção:
       python migrar_blocos_molde4.py
  3. Se a lista impressa fizer sentido, roda de verdade:
       python migrar_blocos_molde4.py --aplicar
"""

import sys
import json
import requests

# ⚠️ AJUSTE AQUI antes de rodar
API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR_MATRICULA = "CBK3574"

TIPO_EQUIPAMENTO = "molde-mcc4"


def extrair_prefixo_campo(etapa):
    """Pega um 'representante' do folhao_campo pra decidir o prefixo —
    se for medicao_multipla (JSON), usa o primeiro valor do dict."""
    bruto = etapa.get("folhao_campo") or ""
    if (etapa.get("tipo_resposta") or "") == "medicao_multipla":
        try:
            mapa = json.loads(bruto)
            valores = list(mapa.values())
            return valores[0] if valores else ""
        except (TypeError, ValueError, IndexError):
            return ""
    return bruto


# 🆕 Alguns itens não têm folhao_campo (etapas puramente de controle,
# sem ponte com o Folhão) ou usam um prefixo que o classificador por
# prefixo não cobre (ex: peritagem de placas estreitas, "pe-cheg-"/
# "pe-sai-", diferente de "m4-per-" das placas largas). Pra esses,
# classifico pelo TEXTO exato — conferido item a item, não é chute.
TEXTO_OVERRIDES = {
    "inspecao de chegada": "chegada",
    "qual a situação do molde / observação": "chegada",
    "lavagem": "chegada",
    "liberacao": "saida",
    "desmontagem placa larga fixa": "manutencao",
    "desmontagem placa larga móvel": "manutencao",
    "desmontagem placa estreita direita": "manutencao",
    "desmontagem placa estreita esquerda": "manutencao",
    "desmontagem de vulso": "manutencao",
    "desmontagem de foot roll": "manutencao",
    "desmontagem de guia": "manutencao",
}


def classificar(etapa):
    texto_norm = (etapa.get("texto") or "").strip().lower()
    if texto_norm in TEXTO_OVERRIDES:
        return TEXTO_OVERRIDES[texto_norm]

    campo = extrair_prefixo_campo(etapa)

    # Peritagem placas estreitas usa "pe-cheg-"/"pe-sai-", não "m4-per-"
    if campo.startswith("pe-cheg-"):
        return "chegada"
    if campo.startswith("pe-sai-"):
        return "saida"

    if campo.startswith("m4-rec-") or campo.startswith("m4-ele-"):
        return "chegada"
    if campo.startswith("m4-fin-"):
        return "saida"
    if campo.startswith("m4-per-ent"):
        return "chegada"
    if campo.startswith("m4-per-sai"):
        return "saida"
    if campo.startswith("m4-id-"):
        return None  # ambíguo — ver docstring
    if campo.startswith("m4-"):
        return "manutencao"
    return None  # não reconheci — melhor não adivinhar (ex: "teste do vulso")


def buscar_etapas():
    resp = requests.get(f"{API_BASE}/api/checklist-execucao/etapas/{TIPO_EQUIPAMENTO}", timeout=15)
    resp.raise_for_status()
    return resp.json()


def aplicar_migracao(etapa, novo_bloco):
    payload = {
        "id": etapa["id"],
        "texto": etapa["texto"],
        "operador": OPERADOR_MATRICULA,
        "area": novo_bloco,
    }
    resp = requests.post(f"{API_BASE}/api/checklist-execucao/etapas/editar", json=payload, timeout=15)
    status = "✅" if resp.ok else f"❌ ({resp.status_code})"
    print(f"{status} [{etapa['area']} -> {novo_bloco}] {etapa['texto']}")
    if not resp.ok:
        print(f"    -> {resp.text[:200]}")


if __name__ == "__main__":
    aplicar = "--aplicar" in sys.argv
    print(f"Buscando etapas de '{TIPO_EQUIPAMENTO}' em: {API_BASE}")
    print("MODO: " + ("APLICANDO DE VERDADE" if aplicar else "SIMULAÇÃO (dry run) — nada será alterado") + "\n")

    etapas = buscar_etapas()
    print(f"Total de etapas encontradas: {len(etapas)}\n")

    classificadas = {"chegada": [], "manutencao": [], "saida": []}
    ambiguas = []
    nao_reconhecidas = []

    for etapa in etapas:
        bloco = classificar(etapa)
        if bloco is None:
            campo = extrair_prefixo_campo(etapa)
            if campo.startswith("m4-id-"):
                ambiguas.append(etapa)
            else:
                nao_reconhecidas.append(etapa)
        else:
            classificadas[bloco].append(etapa)

    for bloco, lista in classificadas.items():
        print(f"--- {bloco.upper()} ({len(lista)} etapas) ---")
        for e in lista:
            marcador = "  (já está aqui)" if e["area"] == bloco else f"  ({e['area']} -> {bloco})"
            print(f"  {e['texto']}{marcador}")
        print()

    if ambiguas:
        print(f"--- AMBÍGUAS, NÃO MIGRADAS ({len(ambiguas)}) — decida na mão ---")
        for e in ambiguas:
            print(f"  {e['texto']}")
        print()

    if nao_reconhecidas:
        print(f"--- PREFIXO NÃO RECONHECIDO, NÃO MIGRADAS ({len(nao_reconhecidas)}) ---")
        for e in nao_reconhecidas:
            print(f"  {e['texto']}  (folhao_campo: {e.get('folhao_campo')})")
        print()

    if not aplicar:
        print("Isso foi só simulação. Se a classificação acima fizer sentido, rode de novo com --aplicar.")
    else:
        print("Aplicando...\n")
        for bloco, lista in classificadas.items():
            for e in lista:
                if e["area"] != bloco:  # só chama a API pra quem realmente muda
                    aplicar_migracao(e, bloco)
        print("\nMigração concluída. Etapas ambíguas/não reconhecidas continuam na área antiga.")