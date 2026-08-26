"""
Cadastro do LOTE 2 — resto do folhão do Molde MCC4 (elétrica, hidráulica,
e o restante de mecânica que ainda não tinha etapa).

NÃO INCLUÍDO DE PROPÓSITO (você disse que vai adicionar manual):
  - Materiais utilizados (lista livre de peças/quantidade)
  - Observações gerais (texto livre)

COMO USAR: igual o Lote 1 — ajuste API_BASE/OPERADOR_MATRICULA e rode.
Pode rodar depois do Lote 1 sem problema (são etapas diferentes).
"""

import json
import requests

API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR_MATRICULA = "CBK3574"

TIPO_EQUIPAMENTO = "molde-mcc4"


def cadastrar_etapa(area, texto, tipo_resposta, folhao_campo=None, campo_json=None, descricao=None):
    payload = {
        "equipamento_id": TIPO_EQUIPAMENTO,
        "area": area,
        "texto": texto,
        "operador": OPERADOR_MATRICULA,
        "tipo_resposta": tipo_resposta,
        "descricao": descricao,
    }
    if tipo_resposta == "medicao_multipla" and campo_json is not None:
        payload["folhao_campo"] = json.dumps(campo_json)
    elif folhao_campo:
        payload["folhao_campo"] = folhao_campo

    resp = requests.post(f"{API_BASE}/api/checklist-execucao/etapas", json=payload, timeout=15)
    status = "✅" if resp.ok else f"❌ ({resp.status_code})"
    print(f"{status} [{area}] {texto}")
    if not resp.ok:
        print(f"    -> {resp.text[:200]}")


# ================================================================
# 1) RECEBIMENTO MECÂNICA — itens que faltaram do Lote 1
#    (índices 9 e 10 já foram cadastrados como "Teste hidráulico" e
#    "Teste hidrostático" no Lote 1 — não repete aqui)
# ================================================================
RECEBIMENTO_MECANICA_RESTANTE = {
    0: "Os engates rápidos para abertura da face móvel estão completos e em perfeitas condições?",
    1: "Os engates rápidos para o sistema de lubrificação estão completos e em perfeitas condições?",
    2: "Os flexíveis das guias laterais estão amassados e/ou danificados?",
    4: "As tubulações hidráulicas e de lubrificação estão em perfeitas condições?",
    5: "Os protetores sanfonados dos fusos e tubos telescópicos das placas laterais estão danificados?",
    6: "As cangalhas de spray estão 'OK' sem avarias?",
    7: "Há avarias nas mangueiras e tubulação de lubrificação dos foot rolls e guias laterais?",
    8: "As réguas de guia das placas laterais estão em perfeitas condições?",
    11: "Ao realizar o teste de spray, ocorreu obstrução de bicos?",
    # índice 3 é um item duplicado no documento original — não cadastrado.
}

# ================================================================
# 2) RECEBIMENTO ELÉTRICA
# ================================================================
RECEBIMENTO_ELETRICA = {
    0: "Os conectores do detector de break-out das faces larga estão tampados e em perfeitas condições?",
    1: "Os cabos elétricos dos termopares do detector de break-out das faces estreitas estão em perfeitas condições?",
}

# ================================================================
# 3) REVISÃO (21 itens)
# ================================================================
REVISAO = [
    "Retirar os parafusos de fixação dos foot rolls e guias laterais",
    "Fazer acabamento e recondicionar roscas",
    "Ajustar chavetas das guias dos rolos laterais e bases dos foot-rolls",
    "Desmontar réguas guias das laterais, lixar, desempenar e recompor c/ solda se necessário",
    "Calibrar com 0.40mm a folga da arruela dos parafusos de fixação da face larga móvel",
    "Desobstruir dreno na tampa das hastes do cilindro do clamp",
    "Ajustar as 04 porcas castelo da haste do cilindro de clamp da face larga móvel",
    "Limpar e ajustar os parafusos de alinhamento das bases (guias laterais)",
    "Limpar faces de apoio das placas largas e estreitas e montar o'ring",
    "Fazer inspeção visual em todo o sistema hidráulico e relatar anomalias",
    "Verificar e reparar pinos travas dos eixos KARDANS, lubrificar, ajustar estrias e pintá-los",
    "Desmontar proteção sanfonada dos fusos, inspecionar e lubrificar os mesmos",
    "Substituir proteção sanfonada danificada",
    "Limpar e ajustar calços para alinhamento dos foot roll",
    "Ajustar e lubrificar o parafuso excêntrico de alinhamento do molde na máquina",
    "Fixar e ajustar placa suporte do parafuso de fixação do molde na máquina, com 1mm de folga entre a placa e a estrutura do molde",
    "Inspecionar folgas nas caixas de engrenagem das placas laterais",
    "Lubrificar total, verificando o perfeito funcionamento das válvulas distribuidoras de graxa",
    "Fazer inspeção nas roscas para fixação das placas laterais (back up)",
    "Verificar torque de aperto dos parafusos tipo feno dos eixos cardans - 25 Nm",
]

# ================================================================
# 4) INSPEÇÃO FINAL (17 itens — cada um vira "resultado" + "medida")
# ================================================================
INSPECAO_FINAL = [
    "Esquadramento das faces estreitas está na tolerância de 0.1mm?",
    "Alinhamento do molde em relação ao gabarito do stand está correto?",
    "A folga nas arruelas dos parafusos de fixação da placa móvel estão entre 0.3mm a 0.5mm?",
    "A folga máxima entre as placas laterais e largas é de 0.25mm?",
    "Os encaixes dos eixos cardans nos motores foram feitos sem interferência?",
    "As marcações dos centros das placas largas estão legíveis?",
    "Tubos telescópios sem vazamentos? (Analisado com 7kgf/cm2)",
    "Os protetores sanfonados estão em bom estado de conservação?",
    "Os engates rápidos estão apertados e protegidos?",
    "Os eixos cardan estão limpos, lubrificados e protegidos?",
    "Os leques dos sprays estão corretamente alinhados e sem obstrução?",
    "Não houve vazamento durante o teste hidrostático com 10 bar de pressão durante 30min",
    "Foot Rolls e roletes das guias laterais estão lubrificados e girando normalmente?",
    "As tampas de proteção dos parafusos do foot roll estão montadas?",
    "Os parafusos M36 alinhados na elevação de 1640mm ~3mm a partir do pé do molde?",
    "Cavidade interna do molde e rolos limpos?",
    "Cilindros hidráulicos do sistema do clamp foi feito sangria?",
]

# ================================================================
# 5) CHECK LIST HIDRÁULICO (quem fez cada item — nome + matrícula)
# ================================================================
HIDRAULICO = [
    "CHECK DOS CILINDROS DO CLAMP",
    "VERIFICAR VAZAMENTO DE GRAXA NAS CONEXÕES",
    "VERIFICAR VAZAMENTO DE ÓLEO NAS CONEXÕES",
    "INSPECIONAR O ELEMENTO FILTRANTE DA LINHA DE PRESSÃO HIDRÁULICA",
    "LUBRIFICAÇÃO",
    "VERIFICAR VAZAMENTO EM MANGUEIRAS E DOSADOR, SUBSTITUIR SE NECESSÁRIO",
    "EFETUAR A LIMPEZA DOS ENGATES HIDRÁULICOS",
    "EMBALAR ENGATES HIDRÁULICOS",
]

# ================================================================
# 6) SENSOR DE NÍVEL — checklist simples (7 itens)
# ================================================================
SENSOR_NIVEL_CHECKLIST = [
    "Verificar tampa de proteção",
    "Efetuar a troca das gaxetas de isolação do sensor",
    "Verificar parafuso de fixação do suporte do sensor, torque 50 Nm",
    "Verificar parafuso de fixação da tampa de proteção do sensor, torque 40 Nm",
    "Verificar estado de conservação e limpeza",
    "Teste de estanqueidade (5 bar)",
    "Check nas conexões de alimentação de água",
]

SENSOR_RESISTENCIA_PINOS = ["1-2", "3-4", "1-5", "3-5", "7-8", "8-9", "15-16", "Pino 10 / Carcaça"]
SENSOR_ISOLACAO_PINOS = ["5 e 6", "5 e 8", "5 e 10", "5 e 15", "6 e 8", "6 e 10", "6 e 15", "8 e 10", "8 e 15", "10 e 15"]

LARGURAS_ARESTA = [1000, 1030, 1040, 1090, 1100, 1160, 1180, 1230, 1290, 1360, 1380, 1420, 1460, 1500, 1530, 1550, 1560, 1580, 1620]

PERITAGEM_ESTREITAS_MEDIDAS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H1', 'H2', 'H3', 'H4', 'L', 'M']


def rodar():
    print(f"Cadastrando LOTE 2 em: {API_BASE}\n")

    # --- Recebimento Mecânica (restante) ---
    for idx, texto in RECEBIMENTO_MECANICA_RESTANTE.items():
        cadastrar_etapa("mecanica", texto, "sim_nao", folhao_campo=f"m4-rec-{idx}")

    # --- Recebimento Elétrica ---
    for idx, texto in RECEBIMENTO_ELETRICA.items():
        cadastrar_etapa("eletrica", texto, "sim_nao", folhao_campo=f"m4-ele-{idx}")

    # --- Revisão (21 itens) ---
    for idx, texto in enumerate(REVISAO):
        cadastrar_etapa("mecanica", texto, "sim_nao", folhao_campo=f"m4-rev-{idx}")

    # --- Inspeção Final (17 itens, resultado + medida) ---
    for idx, texto in enumerate(INSPECAO_FINAL):
        cadastrar_etapa("mecanica", f"[Inspeção Final] {texto}", "medicao_multipla",
                         campo_json={"resultado": f"m4-fin-{idx}", "medida": f"m4-fin-{idx}-med"})

    # --- Check Hidráulico (quem fez cada item) ---
    for idx, texto in enumerate(HIDRAULICO):
        cadastrar_etapa("hidraulica", texto, "medicao_multipla",
                         campo_json={"nome": f"m4-hid-nome-{idx}", "matricula": f"m4-hid-mat-{idx}"})

    # --- Ajustes / Medidas Nominais ---
    cadastrar_etapa("mecanica", "Aperto do parafuso excêntrico (Dir/Esq)", "medicao_multipla",
                     campo_json={"dir": "m4-aj-exc-dir", "esq": "m4-aj-exc-esq"})
    cadastrar_etapa("mecanica", "Torque parafuso fixação foot roll (nominal: 300 ± 5 Nm)", "medicao", folhao_campo="m4-aj-tfr")
    cadastrar_etapa("mecanica", "Torque parafuso fixação placa lateral (nominal: 200 ± 5 Nm)", "medicao", folhao_campo="m4-aj-tpl")
    cadastrar_etapa("mecanica", "Tirante fixação guias laterais (nominal: 100 Nm)", "medicao", folhao_campo="m4-aj-tir")
    cadastrar_etapa("mecanica", "Folga gabarito clamp Sup/Inf - Ø250 (nominal: 1,60 ± 0,15mm)", "medicao_multipla",
                     campo_json={"sup": "m4-aj-clp-sup", "inf": "m4-aj-clp-inf"})

    # --- Check Elétrico (conectores DBO/VUHZ) ---
    cadastrar_etapa("eletrica", "Os conectores do DBO e VUHZ estão limpos, tamponados e protegidos?", "medicao_multipla",
                     campo_json={"nome": "m4-ele-nome", "matricula": "m4-ele-mat"})

    # --- Rolos: diâmetros e afastamento ---
    for prefixo, rotulo in [("dia-c", "Chegada na oficina"), ("dia-s", "Saída da oficina")]:
        cadastrar_etapa("mecanica", f"Diâmetros dos rolos — {rotulo}", "medicao_multipla",
                         campo_json={"fixo": f"m4-{prefixo}-fixo", "movel": f"m4-{prefixo}-movel",
                                     "dir": f"m4-{prefixo}-dir", "esq": f"m4-{prefixo}-esq"})
        cadastrar_etapa("mecanica", f"Lado esquerdo afastado — {rotulo}", "sim_nao", folhao_campo=f"m4-{prefixo}-esq-af")
        cadastrar_etapa("mecanica", f"Lado direito afastado — {rotulo}", "sim_nao", folhao_campo=f"m4-{prefixo}-dir-af")

    # --- Alinhamento dos rolos (F1/F2/F3) ---
    cadastrar_etapa("mecanica", "Alinhamento dos rolos — Face Fixa (F1/F2/F3, tolerância ±0.1mm)", "medicao_multipla",
                     campo_json={"f1": "m4-alinh-fixa-f1", "f2": "m4-alinh-fixa-f2", "f3": "m4-alinh-fixa-f3"})
    cadastrar_etapa("mecanica", "Alinhamento dos rolos — Face Móvel (F1/F2/F3, tolerância ±0.1mm)", "medicao_multipla",
                     campo_json={"f1": "m4-alinh-mov-f1", "f2": "m4-alinh-mov-f2", "f3": "m4-alinh-mov-f3"})

    # --- Sensor de Nível: checklist simples ---
    for idx, texto in enumerate(SENSOR_NIVEL_CHECKLIST, start=1):
        cadastrar_etapa("eletrica", texto, "sim_nao", folhao_campo=f"m4-sn-{idx}")

    # --- Sensor de Nível: resistência ---
    cadastrar_etapa("eletrica", "Medição de resistência no sensor de nível", "medicao_multipla",
                     campo_json={pino: f"m4-sn-res-{i+8}" for i, pino in enumerate(SENSOR_RESISTENCIA_PINOS)})

    # --- Sensor de Nível: isolação ---
    cadastrar_etapa("eletrica", "Isolação dos sensores (> 10 MΩ)", "medicao_multipla",
                     campo_json={pino: f"m4-sn-iso-{i}" for i, pino in enumerate(SENSOR_ISOLACAO_PINOS)})

    # --- Termopares ---
    mapa_termopares = {}
    for i in range(1, 13):
        mapa_termopares[f"T{i}-fixa"] = f"m4-termo-f-{i}"
        mapa_termopares[f"T{i}-movel"] = f"m4-termo-m-{i}"
    cadastrar_etapa("eletrica", "Teste de resistência das placas (termopares, 10-30 Ω)", "medicao_multipla", campo_json=mapa_termopares)

    cadastrar_etapa("eletrica", "Teste de resistência — Placas estreitas (10-30 Ω)", "medicao_multipla",
                     campo_json={"dir-t1": "m4-termo-ed-1", "dir-t2": "m4-termo-ed-2",
                                 "esq-t1": "m4-termo-ee-1", "esq-t2": "m4-termo-ee-2"})

    cadastrar_etapa("eletrica", "Verificação das caixas de termopares", "medicao_multipla",
                     campo_json={"parafusos-base": "m4-tc-1", "teste-ar": "m4-tc-2", "estado-limpeza": "m4-tc-3",
                                 "borrachas-ved": "m4-tc-4", "travas": "m4-tc-5"})

    # --- Peritagem Placas Largas ---
    for prefixo, rotulo in [("m4-per-ent", "Entrada na oficina"), ("m4-per-sai", "Saída da oficina")]:
        cadastrar_etapa("mecanica", f"Placa fixa afastada — {rotulo}", "sim_nao", folhao_campo=f"{prefixo}-fixa-afast")
        cadastrar_etapa("mecanica", f"Placa móvel afastada — {rotulo}", "sim_nao", folhao_campo=f"{prefixo}-movel-afast")
        cadastrar_etapa("mecanica", f"Peritagem placas largas — {rotulo}", "medicao_multipla", campo_json={
            "planicidade-vertical-fixa": f"{prefixo}-fv-fixa", "planicidade-vertical-movel": f"{prefixo}-fv-movel",
            "planicidade-horizontal-fixa": f"{prefixo}-fh-fixa", "planicidade-horizontal-movel": f"{prefixo}-fh-movel",
            "profundidade-ranhuras-fixa": f"{prefixo}-pr-fixa", "profundidade-ranhuras-movel": f"{prefixo}-pr-movel",
            "desgaste-fixa": f"{prefixo}-da-fixa", "desgaste-movel": f"{prefixo}-da-movel",
        })

    # --- Peritagem Placas Estreitas ---
    for prefixo, rotulo in [("pe-cheg", "Chegada na oficina"), ("pe-sai", "Saída da oficina")]:
        mapa = {}
        for i, medida in enumerate(PERITAGEM_ESTREITAS_MEDIDAS):
            mapa[f"{medida}-sul"] = f"{prefixo}-sul-{i}"
            mapa[f"{medida}-norte"] = f"{prefixo}-nor-{i}"
        cadastrar_etapa("mecanica", f"Peritagem placas estreitas — {rotulo}", "medicao_multipla", campo_json=mapa)

    # --- Caixas de Engrenagem, Chavetas e Resfriamento ---
    cadastrar_etapa("mecanica", "Folgas nas caixas de engrenagem (bitola 1300 ± 1mm)", "medicao_multipla", campo_json={
        "fuso-esq-sup": "m4-eng-fuso-es", "fuso-esq-inf": "m4-eng-fuso-ei",
        "fuso-dir-sup": "m4-eng-fuso-ds", "fuso-dir-inf": "m4-eng-fuso-di",
        "placa-esq-sup": "m4-eng-placa-es", "placa-esq-inf": "m4-eng-placa-ei",
        "placa-dir-sup": "m4-eng-placa-ds", "placa-dir-inf": "m4-eng-placa-di",
    })
    cadastrar_etapa("mecanica", "Ajuste de chavetas das placas estreitas", "medicao_multipla", campo_json={
        "esq-a-a": "m4-chav-esq-a-a", "esq-a-b": "m4-chav-esq-a-b", "esq-a-nome": "m4-chav-esq-a-nome", "esq-a-reg": "m4-chav-esq-a-reg",
        "esq-b-a": "m4-chav-esq-b-a", "esq-b-b": "m4-chav-esq-b-b", "esq-b-nome": "m4-chav-esq-b-nome", "esq-b-reg": "m4-chav-esq-b-reg",
        "dir-a-a": "m4-chav-dir-a-a", "dir-a-b": "m4-chav-dir-a-b", "dir-a-nome": "m4-chav-dir-a-nome", "dir-a-reg": "m4-chav-dir-a-reg",
        "dir-b-a": "m4-chav-dir-b-a", "dir-b-b": "m4-chav-dir-b-b", "dir-b-nome": "m4-chav-dir-b-nome", "dir-b-reg": "m4-chav-dir-b-reg",
    })
    cadastrar_etapa("mecanica", "Avaliação do sistema de resfriamento na saída", "medicao_multipla",
                     campo_json={"face-fixa": "m4-resf-fixa", "face-movel": "m4-resf-movel"})

    # --- Identificação de Componentes ---
    cadastrar_etapa("mecanica", "Identificação de componentes — Placas (saída máquina/oficina)", "medicao_multipla", campo_json={
        "fixa-mq": "m4-id-pl-fixa-mq", "fixa-of": "m4-id-pl-fixa-of",
        "movel-mq": "m4-id-pl-movel-mq", "movel-of": "m4-id-pl-movel-of",
        "dir-mq": "m4-id-pl-dir-mq", "dir-of": "m4-id-pl-dir-of",
        "esq-mq": "m4-id-pl-esq-mq", "esq-of": "m4-id-pl-esq-of",
    })
    cadastrar_etapa("mecanica", "Identificação de componentes — Redutores (saída máquina/oficina)", "medicao_multipla", campo_json={
        "sup-dir-mq": "m4-id-red-sd-mq", "sup-dir-of": "m4-id-red-sd-of",
        "inf-dir-mq": "m4-id-red-id-mq", "inf-dir-of": "m4-id-red-id-of",
        "sup-esq-mq": "m4-id-red-se-mq", "sup-esq-of": "m4-id-red-se-of",
        "inf-esq-mq": "m4-id-red-ie-mq", "inf-esq-of": "m4-id-red-ie-of",
    })
    cadastrar_etapa("mecanica", "Identificação de componentes — Cilindros (saída máquina/oficina)", "medicao_multipla", campo_json={
        "sup-dir-mq": "m4-id-cil-sd-mq", "sup-dir-of": "m4-id-cil-sd-of",
        "inf-dir-mq": "m4-id-cil-id-mq", "inf-dir-of": "m4-id-cil-id-of",
        "sup-esq-mq": "m4-id-cil-se-mq", "sup-esq-of": "m4-id-cil-se-of",
        "inf-esq-mq": "m4-id-cil-ie-mq", "inf-esq-of": "m4-id-cil-ie-of",
    })

    # --- Mecânica: eixo excêntrico e bucha ---
    cotas = ["a", "b", "c", "d", "e", "f", "sw"]
    mapa_ex = {f"{cota}-dir": f"m4-ex-{cota}-d" for cota in cotas}
    mapa_ex.update({f"{cota}-esq": f"m4-ex-{cota}-e" for cota in cotas})
    mapa_ex["bucha-dir"] = "m4-ex-buc-d"
    mapa_ex["bucha-esq"] = "m4-ex-buc-e"
    cadastrar_etapa("mecanica", "Aferição eixo excêntrico e bucha", "medicao_multipla", campo_json=mapa_ex)

    # --- Mecânica: cardans ---
    mapa_cardans = {}
    for i, loc in enumerate(["esq-sup", "dir-sup", "esq-inf", "dir-inf"]):
        mapa_cardans[f"{loc}-articulacao"] = f"m4-cd-art-{i}"
        mapa_cardans[f"{loc}-sanfonada"] = f"m4-cd-sanf-{i}"
        mapa_cardans[f"{loc}-pino-trava"] = f"m4-cd-pino-{i}"
        mapa_cardans[f"{loc}-acoplamento"] = f"m4-cd-acop-{i}"
        mapa_cardans[f"{loc}-data-troca"] = f"m4-cd-data-{i}"
    cadastrar_etapa("mecanica", "Verificação dos cardans", "medicao_multipla", campo_json=mapa_cardans)

    # --- Mecânica: parafusos de fixação das transmissões ---
    mapa_transm = {}
    for i, loc in enumerate(["sup-dir", "sup-esq", "inf-dir", "inf-esq"]):
        mapa_transm[f"{loc}-benzler"] = f"m4-tr-bz-{i}"
        mapa_transm[f"{loc}-transmi"] = f"m4-tr-tr-{i}"
        for p in [1, 2, 3, 4]:
            mapa_transm[f"{loc}-p{p}"] = f"m4-tr-p{p}-{i}"
    cadastrar_etapa("mecanica", "Parafusos de fixação das transmissões", "medicao_multipla", campo_json=mapa_transm)

    print("\nLote 2 processado.")


if __name__ == "__main__":
    rodar()
