"""
Cadastro do LOTE 2 — resto do Checklist de Execução do Molde MCC 2/3
(todas as tabelas de medição/inspeção que não são os checklists
sim/não simples já cadastrados no Lote 1).

PADRÃO USADO (mesmo do "Verificar bitola/aresta" no cadastrar_lote1_molde4.py):
  cada tabela/seção vira UMA etapa com tipo_resposta="medicao_multipla",
  guardando um JSON {rótulo: id_do_campo} no folhao_campo. Onde existia
  radio SIM/NÃO de verdade (ex: "placa afastada"), virou etapa sim_nao
  separada, igual ao padrão do Lote 1.

NÃO INCLUÍDO DE PROPÓSITO (mesmo critério do Lote 2 do Molde 4):
  - Materiais utilizados (lista livre de peças/quantidade)
  - Campos de cabeçalho da OS (líder, motivo, datas, nova meta etc. —
    são "camposProtegidos" no próprio JS, nunca viram etapa)
  - Campos de data/nome/matrícula de rodapé de cada seção (registro de
    quem preencheu, não é resultado de medição)

Todos os ids foram lidos direto de folhaoMolde23.js (funções
renderizarIdentificacao, renderizarDiametrosRolos, renderizarAlinhamentoRolos,
renderizarSensorNivel, renderizarIsolamentoSensores, renderizarTermopares,
renderizarCheckJB2, renderizarResistenciaPlacas, renderizarPeritagemPlacasLargas,
renderizarPeritagemPlacasEstreitas, renderizarAjusteChavetas,
renderizarFolgaAresta, renderizarResfriamento) e conferidos contra os
containers do app.html — todos batem, sem divergência.

DESCRIÇÃO: mesmo caso do Lote 1 — sem o Folhão físico impresso, deixei
descricao=None em tudo, exceto onde o próprio código já trazia uma
tolerância/torque explícito (esses eu copiei, não inventei).

COMO USAR: igual o Lote 1 — ajuste API_BASE/OPERADOR_MATRICULA e rode
depois do Lote 1 (são etapas diferentes, pode rodar em qualquer ordem).
"""

import json
import requests

API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR_MATRICULA = "CBK3574"

TIPO_EQUIPAMENTO = "molde-mcc2-3"


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


ETAPAS = []


def add(area, texto, tipo_resposta, folhao_campo=None, campo_json=None, descricao=None):
    ETAPAS.append((area, texto, tipo_resposta, folhao_campo, campo_json, descricao))


# ================================================================
# 1) IDENTIFICAÇÃO (placas / redutores / cilindros — saída máquina/oficina)
# ================================================================
add("mecanica", "Identificação — Placas (saída máquina/oficina)", "medicao_multipla", campo_json={
    "fixa_mq": "id-placa-fixa-mq", "fixa_of": "id-placa-fixa-of",
    "movel_mq": "id-placa-movel-mq", "movel_of": "id-placa-movel-of",
    "direita_mq": "id-placa-dir-mq", "direita_of": "id-placa-dir-of",
    "esquerda_mq": "id-placa-esq-mq", "esquerda_of": "id-placa-esq-of",
})
add("mecanica", "Identificação — Redutores (saída máquina/oficina)", "medicao_multipla", campo_json={
    "sup_direito_mq": "id-red-sup-dir-mq", "sup_direito_of": "id-red-sup-dir-of",
    "inf_direito_mq": "id-red-inf-dir-mq", "inf_direito_of": "id-red-inf-dir-of",
    "sup_esquerdo_mq": "id-red-sup-esq-mq", "sup_esquerdo_of": "id-red-sup-esq-of",
    "inf_esquerdo_mq": "id-red-inf-esq-mq", "inf_esquerdo_of": "id-red-inf-esq-of",
})
add("mecanica", "Identificação — Cilindros (saída máquina/oficina)", "medicao_multipla", campo_json={
    "sup_dir_mq": "id-cil-sup-dir-mq", "sup_dir_of": "id-cil-sup-dir-of",
    "inf_dir_mq": "id-cil-inf-dir-mq", "inf_dir_of": "id-cil-inf-dir-of",
    "sup_esq_mq": "id-cil-sup-esq-mq", "sup_esq_of": "id-cil-sup-esq-of",
    "inf_esq_mq": "id-cil-inf-esq-mq", "inf_esq_of": "id-cil-inf-esq-of",
})

# ================================================================
# 2) DIÂMETROS DOS ROLOS
# ================================================================
add("mecanica", "Diâmetros dos rolos — ao chegar na oficina", "medicao_multipla", campo_json={
    "lado_fixo": "dia-c-fixo", "lado_movel": "dia-c-movel",
    "lado_direito": "dia-c-dir", "lado_esquerdo": "dia-c-esq",
})
add("mecanica", "Diâmetros dos rolos — ao sair da oficina", "medicao_multipla", campo_json={
    "lado_fixo": "dia-s-fixo", "lado_movel": "dia-s-movel",
    "lado_direito": "dia-s-dir", "lado_esquerdo": "dia-s-esq",
})

# ================================================================
# 3) ALINHAMENTO DOS ROLOS
# ================================================================
add("mecanica", "Alinhamento dos rolos (foot roll / edge roll)", "medicao_multipla", campo_json={
    "lado_fixo": "alinh-fixo", "lado_movel": "alinh-movel",
})

# ================================================================
# 4) SENSOR DE NÍVEL — checagem (OK) e resistência (Ω)
# ================================================================
SENSOR_NIVEL_DESCRICOES = [
    "VERIFICAR TAMPA DE PROTEÇÃO;",
    "EFETUAR A TROCA DAS GAXETAS DE ISOLAÇÃO DO SENSOR",
    "VERIFICAR PARAFUSO DE FIXAÇÃO DO SUPORTE DO SENSOR, TORQUE 50 NM;",
    "VERIFICAR PARAFUSO DE FIXAÇÃO DA TAMPA DE PROTEÇÃO DO SENSOR, TORQUE 40 NM;",
    "VERIFICAR ESTADO DE CONSERVAÇÃO E LIMPEZA;",
    "TESTE DE ESTANQUIEDADE (5 BAR);",
    "CHECK NA CONEXÕES DE ALIMENTAÇÃO DE ÁGUA;",
]
add("mecanica", "Sensor de nível — checagem (itens 1 a 7)", "medicao_multipla",
    campo_json={f"item_{i+1}_{SENSOR_NIVEL_DESCRICOES[i][:20].strip()}": f"sn-{i+1}" for i in range(7)},
    descricao="Itens com torque especificado: item 3 = 50 Nm, item 4 = 40 Nm.")

RESISTENCIA_SENSOR_DESCRICOES = [
    "PINOS 1-2 (140...300 Ω)", "PINOS 3-4 (0...2 Ω)", "PINOS 1-5 (70...150 Ω)",
    "PINOS 3-5 (0...1 Ω)", "PINOS 7-8 (0...1 Ω)", "PINOS 8-9 (100...140 Ω)",
    "PINOS 15-16 (3...10 Ω)", "PINO 10 x CARCAÇA (0...1 Ω)",
]
add("mecanica", "Sensor de nível — medição de resistência (itens 8 a 15)", "medicao_multipla",
    campo_json={f"item_{8+i}_{RESISTENCIA_SENSOR_DESCRICOES[i][:20]}": f"sn-{8+i}" for i in range(8)},
    descricao="Limites de referência: " + "; ".join(RESISTENCIA_SENSOR_DESCRICOES))

# ================================================================
# 5) ISOLAÇÃO DOS SENSORES DE NÍVEL (MΩ, escala 100VCA)
# ================================================================
PARES_ISOLACAO = ["5 e 6", "5 e 8", "5 e 10", "5 e 15", "6 e 8", "6 e 10", "6 e 15", "8 e 10", "8 e 15", "10 e 15"]
add("mecanica", "Isolação dos sensores de nível (MΩ)", "medicao_multipla",
    campo_json={f"pinos_{p.replace(' ', '')}": f"iso-{i}" for i, p in enumerate(PARES_ISOLACAO)},
    descricao="Limite de referência: >10 MΩ, escala de medição de 100VCA.")

# ================================================================
# 6) TERMOPARES
# ================================================================
add("eletrica", "Termopares — identificação das caixas (placa fixa/móvel)", "medicao_multipla", campo_json={
    "placa_fixa": "termo-fixa", "placa_movel": "termo-movel",
})
add("eletrica", "Termopares — manutenção (parafusos, ar, limpeza, borrachas, travas)", "medicao_multipla", campo_json={
    "parafusos_base": "termo-cond1", "teste_ar_wamboy": "termo-cond2",
    "estado_limpeza": "termo-cond3", "borrachas_vedacoes": "termo-cond4", "travas": "termo-cond5",
})

# ================================================================
# 7) CHECK DO JB2 (painel, válvula proporcional, transdutores, bloco, cabos)
# ================================================================
add("eletrica", "JB2 — fecho painel / conectores wanboy / vedação", "medicao_multipla", campo_json={
    "fecho_painel_status": "jb2-fecho", "fecho_painel_obs": "jb2-fecho-obs",
    "conectores_wanboy_status": "jb2-wanboy", "conectores_wanboy_obs": "jb2-wanboy-obs",
    "vedacao_jb2_status": "jb2-vedacao", "vedacao_jb2_obs": "jb2-vedacao-obs",
})
add("eletrica", "JB2 — conectores da válvula proporcional (4 posições)", "medicao_multipla", campo_json={
    "sup_esq_status": "vp-se", "sup_esq_obs": "vp-se-obs",
    "sup_dir_status": "vp-sd", "sup_dir_obs": "vp-sd-obs",
    "inf_esq_status": "vp-ie", "inf_esq_obs": "vp-ie-obs",
    "inf_dir_status": "vp-id", "inf_dir_obs": "vp-id-obs",
})
add("eletrica", "JB2 — conectores dos transdutores de posição (4 posições)", "medicao_multipla", campo_json={
    "sup_esq_status": "tp-se", "sup_esq_obs": "tp-se-obs",
    "sup_dir_status": "tp-sd", "sup_dir_obs": "tp-sd-obs",
    "inf_esq_status": "tp-ie", "inf_esq_obs": "tp-ie-obs",
    "inf_dir_status": "tp-id", "inf_dir_obs": "tp-id-obs",
})
add("eletrica", "JB2 — bloco principal (vedações, válvulas, transdutores óleo/ar)", "medicao_multipla", campo_json={
    "vedacoes_status": "bp-ved", "vedacoes_obs": "bp-ved-obs",
    "valvulas_conectores_status": "bp-valv", "valvulas_conectores_obs": "bp-valv-obs",
    "transdutores_status": "bp-trans", "transdutores_obs": "bp-trans-obs",
})
add("eletrica", "JB2 — cabos do ajuste de largura do molde (4 posições + banco de válvulas)", "medicao_multipla", campo_json={
    "sup_esq_status": "cal-se", "sup_esq_obs": "cal-se-obs",
    "sup_dir_status": "cal-sd", "sup_dir_obs": "cal-sd-obs",
    "inf_esq_status": "cal-ie", "inf_esq_obs": "cal-ie-obs",
    "inf_dir_status": "cal-id", "inf_dir_obs": "cal-id-obs",
    "banco_valvulas_status": "cal-bv", "banco_valvulas_obs": "cal-bv-obs",
})

# ================================================================
# 8) TESTE DE RESISTÊNCIA DAS PLACAS
# ================================================================
add("eletrica", "Teste de resistência das placas (móvel/fixa/estreitas)", "medicao_multipla", campo_json={
    "placa_movel": "res-placa-movel", "placa_fixa": "res-placa-fixa",
    "placa_estreita_direita": "res-placa-est-dir", "placa_estreita_esquerda": "res-placa-est-esq",
})

# ================================================================
# 9) PERITAGEM DAS PLACAS LARGAS (entrada / saída)
# ================================================================
def _campos_peritagem_largas(prefix):
    campos = {}
    for face, letra in (("norte", "n"), ("sul", "s")):
        for linha in (1, 2, 3):
            for col in range(1, 8):
                campos[f"face_{face}_linha{linha}_col{col}"] = f"{prefix}-{letra}{linha}-{col}"
    campos.update({
        "alinh_face_norte_regua_leste_superior": f"{prefix}-alinh-n1",
        "alinh_face_norte_regua_leste_inferior": f"{prefix}-alinh-n2",
        "alinh_face_norte_regua_oeste_superior": f"{prefix}-alinh-n3",
        "alinh_face_norte_regua_oeste_inferior": f"{prefix}-alinh-n4",
        "alinh_face_sul_regua_leste_superior": f"{prefix}-alinh-s1",
        "alinh_face_sul_regua_leste_inferior": f"{prefix}-alinh-s2",
        "alinh_face_sul_regua_oeste_superior": f"{prefix}-alinh-s3",
        "alinh_face_sul_regua_oeste_inferior": f"{prefix}-alinh-s4",
    })
    return campos

add("mecanica", "Peritagem placas largas — ao entrar na oficina", "medicao_multipla",
    campo_json=_campos_peritagem_largas("pl-ent"),
    descricao="Tolerância do alinhamento face norte (fixa): 1,0 +/- 0,1mm. Face sul (móvel): superior 0,1mm e inferior 0,2mm.")
add("mecanica", "Peritagem placas largas — ao sair da oficina", "medicao_multipla",
    campo_json=_campos_peritagem_largas("pl-sai"),
    descricao="Tolerância do alinhamento face norte (fixa): 1,0 +/- 0,1mm. Face sul (móvel): superior 0,1mm e inferior 0,2mm.")

# ================================================================
# 10) PERITAGEM DAS PLACAS ESTREITAS (chegada / saída)
# ================================================================
add("mecanica", "Peritagem placas estreitas — placa esquerda afastada? (chegada)", "sim_nao", folhao_campo="pe-c-esq-af")
add("mecanica", "Peritagem placas estreitas — placa direita afastada? (chegada)", "sim_nao", folhao_campo="pe-c-dir-af")
add("mecanica", "Peritagem placas estreitas — pontos de medição (chegada)", "medicao_multipla", campo_json={
    "esquerda_ponto1": "pe-c-e1", "direita_ponto1": "pe-c-d1",
    "esquerda_ponto2": "pe-c-e2", "direita_ponto2": "pe-c-d2",
    "esquerda_ponto3": "pe-c-e3", "direita_ponto3": "pe-c-d3",
})
add("mecanica", "Peritagem placas estreitas — placa esquerda afastada? (saída)", "sim_nao", folhao_campo="pe-s-esq-af")
add("mecanica", "Peritagem placas estreitas — placa direita afastada? (saída)", "sim_nao", folhao_campo="pe-s-dir-af")
add("mecanica", "Peritagem placas estreitas — pontos de medição (saída)", "medicao_multipla", campo_json={
    "esquerda_ponto1": "pe-s-e1", "direita_ponto1": "pe-s-d1",
    "esquerda_ponto2": "pe-s-e2", "direita_ponto2": "pe-s-d2",
    "esquerda_ponto3": "pe-s-e3", "direita_ponto3": "pe-s-d3",
})

# ================================================================
# 11) AJUSTE DE CHAVETAS DAS PLACAS ESTREITAS
# ================================================================
add("mecanica", "Ajuste de chavetas — placa esquerda (lados A e B)", "medicao_multipla", campo_json={
    "lado_a_medida_a": "chav-esq-a-a", "lado_a_medida_b": "chav-esq-a-b",
    "lado_a_nome": "chav-esq-a-nome", "lado_a_registro": "chav-esq-a-reg",
    "lado_b_medida_a": "chav-esq-b-a", "lado_b_medida_b": "chav-esq-b-b",
    "lado_b_nome": "chav-esq-b-nome", "lado_b_registro": "chav-esq-b-reg",
})
add("mecanica", "Ajuste de chavetas — placa direita (lados A e B)", "medicao_multipla", campo_json={
    "lado_a_medida_a": "chav-dir-a-a", "lado_a_medida_b": "chav-dir-a-b",
    "lado_a_nome": "chav-dir-a-nome", "lado_a_registro": "chav-dir-a-reg",
    "lado_b_medida_a": "chav-dir-b-a", "lado_b_medida_b": "chav-dir-b-b",
    "lado_b_nome": "chav-dir-b-nome", "lado_b_registro": "chav-dir-b-reg",
})

# ================================================================
# 12) RELATÓRIO FOLGA DE ARESTA (15 larguras x 3 posições x 2 lados)
#     Mesmo padrão do MAPA_ARESTA_ESQUERDA/DIREITA do Molde 4: uma
#     etapa por lado, com todas as larguras dentro do JSON.
# ================================================================
LARGURAS_FOLGA_ARESTA = [830, 870, 950, 1030, 1100, 1180, 1230, 1300, 1380, 1460, 1500, 1530, 1550, 1580, 1620]

MAPA_FOLGA_ARESTA_ESQUERDA = {}
MAPA_FOLGA_ARESTA_DIREITA = {}
for _l in LARGURAS_FOLGA_ARESTA:
    for _pos, _sufixo in (("superior", "sup"), ("meio", "meio"), ("inferior", "inf")):
        MAPA_FOLGA_ARESTA_ESQUERDA[f"largura_{_l}_{_pos}"] = f"fa-{_l}-esq-{_sufixo}"
        MAPA_FOLGA_ARESTA_DIREITA[f"largura_{_l}_{_pos}"] = f"fa-{_l}-dir-{_sufixo}"

add("mecanica", "Folga de aresta — lado esquerdo (todas as larguras)", "medicao_multipla",
    campo_json=MAPA_FOLGA_ARESTA_ESQUERDA, descricao="Tolerância: 0,25mm por face.")
add("mecanica", "Folga de aresta — lado direito (todas as larguras)", "medicao_multipla",
    campo_json=MAPA_FOLGA_ARESTA_DIREITA, descricao="Tolerância: 0,25mm por face.")

# ================================================================
# 13) AVALIAÇÃO DO SISTEMA DE RESFRIAMENTO
# ================================================================
add("mecanica", "Avaliação do sistema de resfriamento — face norte/fixa", "medicao", folhao_campo="ref-norte")
add("mecanica", "Avaliação do sistema de resfriamento — face sul/móvel", "medicao", folhao_campo="ref-sul")


if __name__ == "__main__":
    print(f"Cadastrando etapas em: {API_BASE}")
    print(f"Tipo de equipamento: {TIPO_EQUIPAMENTO}\n")

    for area, texto, tipo_resposta, folhao_campo, campo_json, descricao in ETAPAS:
        cadastrar_etapa(area, texto, tipo_resposta, folhao_campo=folhao_campo, campo_json=campo_json, descricao=descricao)

    print(f"\nTotal: {len(ETAPAS)} etapas processadas.")
