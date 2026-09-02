#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mesma família do cadastrar_medicoes_{saida,chegada}_horizontal.py, mas
pra Manutenção — só que aqui NÃO é conversão de tipo (os 108 itens já
são "sim_nao" corretamente, é um checklist de tarefa feita/não feita).
O que faltava era a PONTE com o Folhão: cada item, no Folhão, tem
checkbox Geral/Parcial + Executante + Matrícula + Data — e nada disso
era preenchido a partir do Checklist de Execução.

Usa o novo tipo_resposta "sim_nao_assinatura" (ver main.py,
valores_folhao_checklist_execucao): ao marcar a etapa, o servidor
preenche sozinho, a partir da própria marcação:
  - o checkbox certo (Geral OU Parcial, conforme o tipo_execucao do
    reparo — não os dois, e nunca o errado);
  - Executante = colaborador (quem o técnico logado informou que fez);
  - Matrícula = matrícula de quem marcou;
  - Data = data da marcação.

Índices (hz-p-{i}/hz-g-{i}/hz-resp-{i}/hz-mat-{i}/hz-dat-{i}) batem
1:1 com a ordem de manutencaoHorizontal em folhaoHorizontal.js — a
mesma ordem/textos de ITENS_MANUTENCAO em
cadastrar_checklist_horizontal.py (conferido linha a linha, 108/108).

Roda isso NO SEU computador (a rede da sessão do Claude bloqueia a API
de produção por política). Requer só Python 3 (usa urllib) + o arquivo
mapeamentos_manutencao.json na MESMA pasta.

USO:
    python cadastrar_medicoes_manutencao_horizontal.py
"""
import json
import os
import urllib.request

API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR = "CBK3574"  # confirmado pelo usuário como a própria matrícula

PASTA = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PASTA, "mapeamentos_manutencao.json"), encoding="utf-8") as f:
    MAPEAMENTOS = json.load(f)


def chamar(path, payload=None, metodo="GET"):
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=metodo,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("Buscando etapas de 'horizontal-mcc4'...")
    etapas = chamar("/api/checklist-execucao/etapas/horizontal-mcc4")
    etapas_manutencao = [e for e in etapas if e.get("area") == "manutencao"]
    print(f"Achei {len(etapas_manutencao)} etapa(s) na área Manutenção (esperado: 108).")

    ok, faltou = 0, []
    for texto, mapa in MAPEAMENTOS.items():
        etapa = next((e for e in etapas_manutencao if e["texto"].strip() == texto.strip()), None)
        if not etapa:
            print(f"⚠️  NÃO achei uma etapa com o texto exato: {texto!r}")
            faltou.append(texto)
            continue

        payload = {
            "id": etapa["id"],
            "texto": etapa["texto"],
            "operador": OPERADOR,
            "tipo_resposta": "sim_nao_assinatura",
            "folhao_campo": json.dumps(mapa, ensure_ascii=False),
        }
        resultado = chamar("/api/checklist-execucao/etapas/editar", payload, metodo="POST")
        ok += 1 if resultado.get("sucesso") else 0
        print(f"✅ Etapa #{etapa['id']} ({texto[:55]}...) -> {resultado}")

    print(f"\n{ok}/{len(MAPEAMENTOS)} etapas editadas com sucesso.")
    if faltou:
        print(f"⚠️  {len(faltou)} não encontrada(s) — confira acentos/travessão nos textos acima.")
    print("Pronto. Recarrega o Checklist de Execução do Horizontal e confere.")


if __name__ == "__main__":
    main()
