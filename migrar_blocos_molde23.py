"""
Migra as etapas já cadastradas do Molde MCC2/3 (tipo "molde-mcc2-3") das
áreas antigas (mecanica/eletrica/...) pros 3 blocos novos: chegada,
manutencao, saida — mesmo padrão já aplicado no Molde MCC4
(migrar_blocos_molde4.py).

IMPORTANTE — PRÉ-REQUISITOS antes de rodar isso:
  1. O backend (main.py) já precisa estar publicado com TIPOS_CHECKLIST_POR_FASE
     incluindo "molde-mcc2-3" (aviso de fase concluída) e com o campo
     `area` aceito em /api/checklist-execucao/etapas/editar (isso já
     existia, não mudou).
  2. O front-end (checklist-execucao.js e dados.js) já precisa estar
     publicado com CHECKLIST_EXECUCAO_SECOES_POR_TIPO['molde-mcc2-3'].
  Se rodar esse script antes disso, a migração vai "funcionar" (o banco
  aceita qualquer string em area), mas a tela vai continuar mostrando
  Mecânica/Elétrica/etc., porque o front-end ainda não sabe que
  "molde-mcc2-3" usa outra lista de seções.

DIFERENÇA IMPORTANTE em relação ao script do Molde MCC4:
  O Molde MCC4 tinha um prefixo de campo padronizado (m4-rec-, m4-fin-,
  m4-per-...) que deu pra classificar automaticamente por regra. O
  Molde 2/3 NÃO tem esse padrão — os campos do Folhão usam prefixos por
  GRUPO DE PEÇA (alinh-, bp-, cal-, chav-, fa-, iso-, jb2-, ref-...),
  não por FASE do reparo. Não dá pra adivinhar "chegada x manutenção x
  saída" a partir disso sem chutar — classificar errado aqui faz uma
  etapa sumir pro técnico errado ou aparecer na fase errada, o que é
  pior do que não migrar.

  Por isso este script NÃO classifica sozinho: ele só LISTA as etapas
  atuais (texto, área atual, especialidade) pra alguém que conhece o
  processo de verdade decidir. Depois de decidir, preencha o dicionário
  CLASSIFICACAO abaixo (texto exato da etapa -> "chegada"/"manutencao"/
  "saida") e rode de novo com --aplicar.

COMO USAR:
  1. Ajuste API_BASE e OPERADOR_MATRICULA.
  2. Rode sem argumento nenhum pra listar as etapas atuais:
       python migrar_blocos_molde23.py
  3. Preencha CLASSIFICACAO abaixo com a decisão de cada etapa.
  4. Rode de novo pra conferir (ainda sem aplicar) — mostra quem ficou
     de fora (sem entrada no dicionário ainda):
       python migrar_blocos_molde23.py
  5. Quando CLASSIFICACAO cobrir tudo que você quer migrar, aplica:
       python migrar_blocos_molde23.py --aplicar
"""

import sys
import requests

# ⚠️ AJUSTE AQUI antes de rodar
API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR_MATRICULA = "CBK3574"

TIPO_EQUIPAMENTO = "molde-mcc2-3"

# 🔧 PREENCHA AQUI, com o texto EXATO da etapa (copie da listagem que o
# script imprime), depois de decidir com quem conhece o processo do
# Molde 2/3 qual fase cada etapa pertence.
CLASSIFICACAO = {
    # "Texto exato da etapa": "chegada",
    # "Outro texto exato":    "manutencao",
    # "Mais um":              "saida",
}


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
    print("MODO: " + ("APLICANDO DE VERDADE" if aplicar else "SÓ LISTANDO (nada será alterado)") + "\n")

    etapas = buscar_etapas()
    print(f"Total de etapas encontradas: {len(etapas)}\n")

    if not etapas:
        print("Nenhuma etapa cadastrada pra esse tipo ainda. Nada a migrar.")
        sys.exit(0)

    pendentes = []
    classificadas = []
    for e in etapas:
        texto = (e.get("texto") or "").strip()
        bloco = CLASSIFICACAO.get(texto)
        if bloco:
            classificadas.append((e, bloco))
        else:
            pendentes.append(e)

    if classificadas:
        print(f"--- JÁ CLASSIFICADAS EM CLASSIFICACAO ({len(classificadas)}) ---")
        for e, bloco in classificadas:
            marcador = "  (já está aqui)" if e["area"] == bloco else f"  ({e['area']} -> {bloco})"
            print(f"  [{bloco}] {e['texto']}{marcador}")
        print()

    if pendentes:
        print(f"--- AINDA SEM CLASSIFICAÇÃO ({len(pendentes)}) — adicione ao dicionário CLASSIFICACAO ---")
        for e in pendentes:
            especialidade = e.get("especialidade") or "mecanica"
            print(f'  "{e["texto"]}"   (área atual: {e["area"]}, especialidade: {especialidade})')
        print()

    if not aplicar:
        print("Isso foi só listagem. Preencha CLASSIFICACAO com as etapas que faltam e rode de novo com --aplicar quando estiver completo.")
    else:
        if pendentes:
            print(f"⚠️ {len(pendentes)} etapa(s) ainda sem classificação — elas NÃO serão migradas (ficam na área antiga).")
        print("Aplicando...\n")
        for e, bloco in classificadas:
            if e["area"] != bloco:  # só chama a API pra quem realmente muda
                aplicar_migracao(e, bloco)
        print("\nMigração concluída.")
