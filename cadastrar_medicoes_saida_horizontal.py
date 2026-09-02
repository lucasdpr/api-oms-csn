#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte as 3 etapas de Saída do Horizontal (Pass Line, Cilindros
Hidráulicos, Inspeção de Rolos) de "sim_nao" pra "medicao_multipla",
com o folhao_campo mapeando cada posição/medida do documento pro id
real do campo em folhaoHorizontal.js.

🔶 ISSO MUDA UMA DECISÃO REGISTRADA em cadastrar_checklist_horizontal.py:
lá diz explicitamente "campo de medição já é papel do Folhão, não do
Checklist de Execução" — por isso esses 3 itens nasceram como
"resumo" (1 checkbox marca "feito", sem preencher nada sozinho). Só
que na prática isso deixou a Saída com só 3 perguntas de sim/não pra
um passo que tem ~300 medições reais — pedido explícito do usuário foi
reverter essa decisão e puxar tudo pela ponte com o Folhão, igual já
funciona pro Molde MCC4/2-3.

Roda isso NO SEU computador (não dá pra rodar na sessão do Claude —
a rede de lá bloqueia a API de produção por política).

O que faz:
1. Busca as etapas já cadastradas pra "horizontal-mcc4".
2. Acha, pelo TEXTO, as 3 etapas de Saída (cadastradas via a tela
   "+ Etapa" do Checklist de Execução, não por este script).
3. Edita cada uma: tipo_resposta -> "medicao_multipla" e o folhao_campo
   com o JSON de mapeamento (gerado e validado campo a campo contra o
   HTML real do Folhão — ver gerar_mapeamento.mjs, no repo oficina-oms).

Já rodado 1x em produção com sucesso (etapas #351/#352/#353 — 42+60+196
campos). Fica commitado só como registro reproduzível, igual os outros
scripts cadastrar_*.py deste repo — rodar de novo é idempotente (edita
as mesmas etapas outra vez com o mesmo valor).

Requer só Python 3 (usa urllib, sem precisar instalar nada).
"""
import json
import urllib.request

API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR = "CBK3574"  # confirmado pelo usuário como a própria matrícula

MAPEAMENTOS = {
    "Pass Line (Saída) — Base Inferior e Superior": {
        "Inf 1° - Posição A": "horiz-passline-inf-saida-a-0", "Inf 1° - Posição B": "horiz-passline-inf-saida-b-0", "Inf 1° - Posição C": "horiz-passline-inf-saida-c-0",
        "Inf 2° - Posição A": "horiz-passline-inf-saida-a-1", "Inf 2° - Posição B": "horiz-passline-inf-saida-b-1", "Inf 2° - Posição C": "horiz-passline-inf-saida-c-1",
        "Inf 3° - Posição A": "horiz-passline-inf-saida-a-2", "Inf 3° - Posição B": "horiz-passline-inf-saida-b-2", "Inf 3° - Posição C": "horiz-passline-inf-saida-c-2",
        "Inf 4° - Posição A": "horiz-passline-inf-saida-a-3", "Inf 4° - Posição B": "horiz-passline-inf-saida-b-3", "Inf 4° - Posição C": "horiz-passline-inf-saida-c-3",
        "Inf 5° - Posição A": "horiz-passline-inf-saida-a-4", "Inf 5° - Posição B": "horiz-passline-inf-saida-b-4", "Inf 5° - Posição C": "horiz-passline-inf-saida-c-4",
        "Inf 6° - Posição A": "horiz-passline-inf-saida-a-5", "Inf 6° - Posição B": "horiz-passline-inf-saida-b-5", "Inf 6° - Posição C": "horiz-passline-inf-saida-c-5",
        "Inf 7° - Posição A": "horiz-passline-inf-saida-a-6", "Inf 7° - Posição B": "horiz-passline-inf-saida-b-6", "Inf 7° - Posição C": "horiz-passline-inf-saida-c-6",
        "Sup 1° - Posição A": "horiz-passline-sup-saida-a-0", "Sup 1° - Posição B": "horiz-passline-sup-saida-b-0", "Sup 1° - Posição C": "horiz-passline-sup-saida-c-0",
        "Sup 2° - Posição A": "horiz-passline-sup-saida-a-1", "Sup 2° - Posição B": "horiz-passline-sup-saida-b-1", "Sup 2° - Posição C": "horiz-passline-sup-saida-c-1",
        "Sup 3° - Posição A": "horiz-passline-sup-saida-a-2", "Sup 3° - Posição B": "horiz-passline-sup-saida-b-2", "Sup 3° - Posição C": "horiz-passline-sup-saida-c-2",
        "Sup 4° - Posição A": "horiz-passline-sup-saida-a-3", "Sup 4° - Posição B": "horiz-passline-sup-saida-b-3", "Sup 4° - Posição C": "horiz-passline-sup-saida-c-3",
        "Sup 5° - Posição A": "horiz-passline-sup-saida-a-4", "Sup 5° - Posição B": "horiz-passline-sup-saida-b-4", "Sup 5° - Posição C": "horiz-passline-sup-saida-c-4",
        "Sup 6° - Posição A": "horiz-passline-sup-saida-a-5", "Sup 6° - Posição B": "horiz-passline-sup-saida-b-5", "Sup 6° - Posição C": "horiz-passline-sup-saida-c-5",
        "Sup 7° - Posição A": "horiz-passline-sup-saida-a-6", "Sup 7° - Posição B": "horiz-passline-sup-saida-b-6", "Sup 7° - Posição C": "horiz-passline-sup-saida-c-6",
    },
    "Cilindros Hidráulicos (Saída) — Elevação / Clamp / Motriz": {
        "Elevação A - Número": "hcils-se-num-A", "Elevação A - Produção": "hcils-se-prod-A", "Elevação A - Reparado (OK/NOK)": "hcils-se-rep-A", "Elevação A - Reutilizado (OK/NOK)": "hcils-se-reu-A", "Elevação A - Novo (OK/NOK)": "hcils-se-nov-A", "Elevação A - Observação": "hcils-se-obs-A",
        "Elevação B - Número": "hcils-se-num-B", "Elevação B - Produção": "hcils-se-prod-B", "Elevação B - Reparado (OK/NOK)": "hcils-se-rep-B", "Elevação B - Reutilizado (OK/NOK)": "hcils-se-reu-B", "Elevação B - Novo (OK/NOK)": "hcils-se-nov-B", "Elevação B - Observação": "hcils-se-obs-B",
        "Elevação C - Número": "hcils-se-num-C", "Elevação C - Produção": "hcils-se-prod-C", "Elevação C - Reparado (OK/NOK)": "hcils-se-rep-C", "Elevação C - Reutilizado (OK/NOK)": "hcils-se-reu-C", "Elevação C - Novo (OK/NOK)": "hcils-se-nov-C", "Elevação C - Observação": "hcils-se-obs-C",
        "Elevação D - Número": "hcils-se-num-D", "Elevação D - Produção": "hcils-se-prod-D", "Elevação D - Reparado (OK/NOK)": "hcils-se-rep-D", "Elevação D - Reutilizado (OK/NOK)": "hcils-se-reu-D", "Elevação D - Novo (OK/NOK)": "hcils-se-nov-D", "Elevação D - Observação": "hcils-se-obs-D",
        "Clamp (Porcas Hidráulicas) A - Número": "hcils-sc-num-A", "Clamp (Porcas Hidráulicas) A - Produção": "hcils-sc-prod-A", "Clamp (Porcas Hidráulicas) A - Reparado (OK/NOK)": "hcils-sc-rep-A", "Clamp (Porcas Hidráulicas) A - Reutilizado (OK/NOK)": "hcils-sc-reu-A", "Clamp (Porcas Hidráulicas) A - Novo (OK/NOK)": "hcils-sc-nov-A", "Clamp (Porcas Hidráulicas) A - Observação": "hcils-sc-obs-A",
        "Clamp (Porcas Hidráulicas) B - Número": "hcils-sc-num-B", "Clamp (Porcas Hidráulicas) B - Produção": "hcils-sc-prod-B", "Clamp (Porcas Hidráulicas) B - Reparado (OK/NOK)": "hcils-sc-rep-B", "Clamp (Porcas Hidráulicas) B - Reutilizado (OK/NOK)": "hcils-sc-reu-B", "Clamp (Porcas Hidráulicas) B - Novo (OK/NOK)": "hcils-sc-nov-B", "Clamp (Porcas Hidráulicas) B - Observação": "hcils-sc-obs-B",
        "Clamp (Porcas Hidráulicas) C - Número": "hcils-sc-num-C", "Clamp (Porcas Hidráulicas) C - Produção": "hcils-sc-prod-C", "Clamp (Porcas Hidráulicas) C - Reparado (OK/NOK)": "hcils-sc-rep-C", "Clamp (Porcas Hidráulicas) C - Reutilizado (OK/NOK)": "hcils-sc-reu-C", "Clamp (Porcas Hidráulicas) C - Novo (OK/NOK)": "hcils-sc-nov-C", "Clamp (Porcas Hidráulicas) C - Observação": "hcils-sc-obs-C",
        "Clamp (Porcas Hidráulicas) D - Número": "hcils-sc-num-D", "Clamp (Porcas Hidráulicas) D - Produção": "hcils-sc-prod-D", "Clamp (Porcas Hidráulicas) D - Reparado (OK/NOK)": "hcils-sc-rep-D", "Clamp (Porcas Hidráulicas) D - Reutilizado (OK/NOK)": "hcils-sc-reu-D", "Clamp (Porcas Hidráulicas) D - Novo (OK/NOK)": "hcils-sc-nov-D", "Clamp (Porcas Hidráulicas) D - Observação": "hcils-sc-obs-D",
        "Motriz A - Número": "hcils-sm-num-A", "Motriz A - Produção": "hcils-sm-prod-A", "Motriz A - Reparado (OK/NOK)": "hcils-sm-rep-A", "Motriz A - Reutilizado (OK/NOK)": "hcils-sm-reu-A", "Motriz A - Novo (OK/NOK)": "hcils-sm-nov-A", "Motriz A - Observação": "hcils-sm-obs-A",
        "Motriz B - Número": "hcils-sm-num-B", "Motriz B - Produção": "hcils-sm-prod-B", "Motriz B - Reparado (OK/NOK)": "hcils-sm-rep-B", "Motriz B - Reutilizado (OK/NOK)": "hcils-sm-reu-B", "Motriz B - Novo (OK/NOK)": "hcils-sm-nov-B", "Motriz B - Observação": "hcils-sm-obs-B",
    },
    "Inspeção de Rolos (Saída) — Rolamento, Teste Hidrostático e Medidas": (
        {f"{base_nome} - Rolamento pos {i} grupo {j} (OK/NOK)": f"hrol-sa-{base_pfx}-{i}-{j}"
         for base_pfx, base_nome in [("inf", "Inferior"), ("sup", "Superior")]
         for i in range(1, 8) for j in range(1, 5)}
        | {f"{base_nome} - Teste Hidrostático pos {i} grupo {j} (OK/NOK)": f"hhid-sa-{base_pfx}-{i}-{j}"
           for base_pfx, base_nome in [("inf", "Inferior"), ("sup", "Superior")]
           for i in range(1, 8) for j in range(1, 5)}
        | {f"{base_nome} - Medidas pos {i} {campo}": f"hmed-sa-{base_pfx}-{i}-{sufixo}"
           for base_pfx, base_nome in [("inf", "Inferior"), ("sup", "Superior")]
           for i in range(1, 8)
           for campo, sufixo in [("Num 1", "n1"), ("Medida 1", "m1"), ("Num 2", "n2"), ("Medida 2", "m2"), ("Num 3", "n3"), ("Medida 3", "m3")]}
    ),
}


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
    etapas_saida = [e for e in etapas if e.get("area") == "saida"]
    print(f"Achei {len(etapas_saida)} etapa(s) na área Saída.")

    for texto, mapa in MAPEAMENTOS.items():
        etapa = next((e for e in etapas_saida if e["texto"].strip() == texto.strip()), None)
        if not etapa:
            print(f"⚠️  NÃO achei uma etapa com o texto exato: {texto!r}")
            print("    Confira se o texto cadastrado bate certinho (acentos, travessão —, etc.)")
            continue

        payload = {
            "id": etapa["id"],
            "texto": etapa["texto"],
            "operador": OPERADOR,
            "tipo_resposta": "medicao_multipla",
            "folhao_campo": json.dumps(mapa, ensure_ascii=False),
        }
        resultado = chamar("/api/checklist-execucao/etapas/editar", payload, metodo="POST")
        print(f"✅ Etapa #{etapa['id']} ({texto[:50]}...) -> {resultado} ({len(mapa)} campos)")

    print("\nPronto. Recarrega o Checklist de Execução do Horizontal e confere.")


if __name__ == "__main__":
    main()
