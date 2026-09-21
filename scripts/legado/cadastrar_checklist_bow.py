#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cadastro do Checklist de Execução do Bow (tipo "bow-mcc4"), do ZERO —
o Bow não tinha NENHUMA etapa cadastrada ainda.

Diferente de cadastrar_checklist_horizontal.py (que cadastrou os
"resumos" de Chegada/Saída como sim_nao e precisou de scripts
separados depois pra corrigir), aqui já cadastra tudo com o tipo
CERTO desde o início:

  CHEGADA:     23 perguntas sim/não (por grupo: Lubrificação/
               Refrigeração/Cilindros/Porca Hidráulica/Estrutura)
               + 6 etapas de medição múltipla (Gap, Cangalhas,
               Pass Line, Cilindros, Rolos, Graxa — 341 campos).
  MANUTENÇÃO:  108 itens "sim_nao_assinatura" (preenchem sozinhos
               o checkbox Geral/Parcial + Executante/Matrícula/Data
               no Folhão, a partir de quem marcou).
  SAÍDA:       3 etapas de medição múltipla (Pass Line, Cilindros,
               Rolos — 298 campos).

Fonte dos textos: folhaoBow.js (itensChegadaBow, manutencaoBow) — os
mapeamentos de folhao_campo vêm dos arquivos mapeamentos_bow_*.json
(gerados e validados por tools/gerar_mapeamento.mjs, no repo
oficina-oms, campo a campo contra o HTML real do Folhão).

🔶 NOTA: manutencaoBow tem o MESMO TEXTO de manutencaoHorizontal em
folhaoHorizontal.js (parece ter sido copiado sem adaptar pro Bow de
verdade) — isso é um problema de CONTEÚDO pré-existente, não deste
script. Cadastrei o texto que está realmente no Folhão hoje; se os
passos reais de manutenção do Bow forem diferentes, é preciso corrigir
o texto em folhaoBow.js e recadastrar.

Roda isso NO SEU computador (a rede da sessão do Claude bloqueia a API
de produção por política). Requer só Python 3 (usa urllib) + os 4
arquivos mapeamentos_bow_*.json e itens_chegada_bow.json na MESMA pasta.

USO:
    python cadastrar_checklist_bow.py
"""
import json
import os
import urllib.request

API_BASE = "https://api-oms-csn.onrender.com"
TIPO_EQUIPAMENTO = "bow-mcc4"
OPERADOR = "CBK3574"  # confirmado pelo usuário como a própria matrícula

PASTA = os.path.dirname(os.path.abspath(__file__))


def carregar(nome):
    with open(os.path.join(PASTA, nome), encoding="utf-8") as f:
        return json.load(f)


ITENS_CHEGADA = carregar("itens_chegada_bow.json")               # lista de 23 textos
MAPEAMENTOS_CHEGADA = carregar("mapeamentos_bow_chegada.json")     # 6 etapas -> {label: campo}
MAPEAMENTOS_MANUTENCAO = carregar("mapeamentos_bow_manutencao.json")  # 108 etapas -> {chaves fixas}
MAPEAMENTOS_SAIDA = carregar("mapeamentos_bow_saida.json")         # 3 etapas -> {label: campo}


def chamar(path, payload=None, metodo="GET"):
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=metodo,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cadastrar_etapa(area, texto, tipo_resposta="sim_nao", folhao_campo=None, especialidade="mecanica"):
    payload = {
        "equipamento_id": TIPO_EQUIPAMENTO,
        "area": area,
        "texto": texto,
        "operador": OPERADOR,
        "especialidade": especialidade,
        "tipo_resposta": tipo_resposta,
    }
    if folhao_campo is not None:
        payload["folhao_campo"] = json.dumps(folhao_campo, ensure_ascii=False)
    resp = chamar("/api/checklist-execucao/etapas", payload, metodo="POST")
    status = "✅" if resp.get("sucesso", True) else "❌"
    print(f"{status} [{area}/{tipo_resposta}] {texto[:70]}")
    return resp


if __name__ == "__main__":
    print(f"Cadastrando etapas em: {API_BASE}")
    print(f"Tipo de equipamento: {TIPO_EQUIPAMENTO}\n")

    print(f"--- CHEGADA (23 sim/não + {len(MAPEAMENTOS_CHEGADA)} medição múltipla) ---")
    for texto in ITENS_CHEGADA:
        cadastrar_etapa("chegada", texto, tipo_resposta="sim_nao")
    for texto, mapa in MAPEAMENTOS_CHEGADA.items():
        cadastrar_etapa("chegada", texto, tipo_resposta="medicao_multipla", folhao_campo=mapa)

    print(f"\n--- MANUTENÇÃO ({len(MAPEAMENTOS_MANUTENCAO)} sim/não com assinatura) ---")
    for texto, mapa in MAPEAMENTOS_MANUTENCAO.items():
        cadastrar_etapa("manutencao", texto, tipo_resposta="sim_nao_assinatura", folhao_campo=mapa)

    print(f"\n--- SAÍDA ({len(MAPEAMENTOS_SAIDA)} medição múltipla) ---")
    for texto, mapa in MAPEAMENTOS_SAIDA.items():
        cadastrar_etapa("saida", texto, tipo_resposta="medicao_multipla", folhao_campo=mapa)

    print("\nCadastro concluído. Recarrega o Checklist de Execução do Bow e confere.")
