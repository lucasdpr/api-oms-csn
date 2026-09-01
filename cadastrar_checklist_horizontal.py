"""
Cadastro do Checklist de Execução do Horizontal (tipo "horizontal-mcc4").

Igual pedido: o Horizontal não tinha NENHUMA etapa cadastrada ainda —
diferente do Molde MCC4/2-3, aqui não tem nada pra migrar, é cadastro
do zero. Fonte: as perguntas/tabelas já embutidas no folhaoHorizontal.js
(mesmo texto que aparece no PDF oficial "CHECK LIST GERAL SEGMENTOS
HORIZONTAL MCC#4").

COMO CLASSIFIQUEI (chegada/manutencao/saida):
  CHEGADA:     seção "1. INSPEÇÃO DE CHEGADA" (23 perguntas sim/não,
               por grupo: Lubrificação/Refrigeração/Cilindros/Porca
               Hidráulica/Estrutura) + um resumo por bloco de medição
               que só existe na fase de chegada (Gap, Cangalhas, Pass
               Line, Cilindros Hidráulicos, Rolos — todos "(CHEGADA)"
               no documento).
  MANUTENÇÃO:  seção "8. CHECKLIST DE MANUTENÇÃO" inteira (itens 1 a
               10.5) — é UMA lista contínua só no documento oficial,
               sem subdivisão de saída dentro dela, então segui a
               fonte literalmente em vez de reclassificar por conta
               própria.
  SAÍDA:       Pass Line (Saída), Cilindros Hidráulicos (Saída),
               Inspeção de Rolos (Saída) — seções 9/10/11, todas
               marcadas "(SAÍDA)" no documento.

  🔶 ÚNICA CLASSIFICAÇÃO SEM MARCAÇÃO EXPLÍCITA NO DOCUMENTO: "7.
  Inspeção de Distribuição de Graxa" fica sozinha entre a seção 6
  (Chegada) e a 8 (Manutenção), sem "(CHEGADA)"/"(SAÍDA)" no nome.
  Classifiquei como CHEGADA (última checagem antes do reparo em si
  começar) — se não fizer sentido, é só editar a área depois (ADM →
  editar etapa).

Os blocos de medição (Gap, Cangalhas, Pass Line, Cilindros, Rolos,
Graxa) viraram 1 etapa-resumo cada, não 1 etapa por célula/posição —
"etapa" aqui é passo do processo que alguém marca "feito", não campo
de medição (isso já é papel do Folhão, não do Checklist de Execução).

COMO USAR:
  1. Ajuste API_BASE e OPERADOR_MATRICULA.
  2. pip install requests (se não tiver)
  3. python cadastrar_checklist_horizontal.py
  4. Confira a saída — cada linha mostra se deu certo ou não.

Pode rodar mais de uma vez sem quebrar nada, mas vai DUPLICAR (o
backend não trava "mesmo texto já existe") — se rodar 2x sem querer,
me avisa que a gente limpa.
"""

import requests

# ⚠️ AJUSTE AQUI antes de rodar
API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR_MATRICULA = "CBK3574"

TIPO_EQUIPAMENTO = "horizontal-mcc4"


# --------------------------------------------------------------
# 1. INSPEÇÃO DE CHEGADA — 23 perguntas sim/não, por grupo
# (texto igual ao itensChegadaHorizontal do folhaoHorizontal.js)
# --------------------------------------------------------------
ITENS_CHEGADA = [
    ("Lubrificação", "Sistema de lubrificação isento de vazamentos."),
    ("Lubrificação", "Tubulação amassada."),
    ("Lubrificação", "Distribuidores de graxa funcionando corretamente sem vazamentos."),
    ("Refrigeração", "Resfriadores completos e alinhados."),
    ("Refrigeração", "Bicos obstruídos."),
    ("Refrigeração", "Flexíveis isentos de vazamentos."),
    ("Refrigeração", "Tubulações isentas de empenos."),
    ("Refrigeração", "Tubulações furadas."),
    ("Cilindros", "Isento de vazamento."),
    ("Cilindros", "Conexões completas e apertadas."),
    ("Cilindros", "Flexíveis isentos de vazamentos."),
    ("Cilindros", "Tubulações isentas de empenos."),
    ("Porca Hidráulica", "Isento de vazamento."),
    ("Porca Hidráulica", "Conexões completas e apertadas."),
    ("Porca Hidráulica", "Proteções danificadas."),
    ("Porca Hidráulica", "Tubulações isentas de vazamentos."),
    ("Estrutura", "Tubulações isentas de amassados."),
    ("Estrutura", "Proteções isentas de avarias."),
    ("Estrutura", "Estrutura com break-out."),
    ("Estrutura", "Rolamentos quebrados."),
    ("Estrutura", "Rolos travados"),
    ("Estrutura", "Mancais furados."),
    ("Estrutura", "Conexões apertadas."),
]

# Blocos de medição que só existem na fase de Chegada no documento
RESUMOS_CHEGADA = [
    "Aferição de Gap (255+0,3/-0,3)",
    "Inspeção de Cangalhas (Base Superior e Inferior)",
    "Pass Line (Chegada) — Base Inferior e Superior",
    "Cilindros Hidráulicos (Chegada) — Elevação / Clamp / Motriz",
    "Inspeção de Rolos (Chegada) — Rolamento, Teste Hidrostático e Medidas",
]

# 🔶 Sem marcação explícita de fase no documento — ver docstring
RESUMOS_CHEGADA_INCERTOS = [
    "Inspeção de Distribuição de Graxa (Base Superior e Inferior)",
]

# --------------------------------------------------------------
# 8. CHECKLIST DE MANUTENÇÃO — itens 1 a 10.5, lista contínua igual
# ao documento oficial (mesmo texto do manutencaoHorizontal do
# folhaoHorizontal.js)
# --------------------------------------------------------------
ITENS_MANUTENCAO = [
    ("1", "Lavagem e/ou Limpeza Mecânica"),
    ("2.1", "Teste Hidrostático"),
    ("2.2", "Teste Hidráulico"),
    ("2.3", "Teste de Refrigeração"),
    ("2.4", "Aferição de Gap (255mm)"),
    ("2.5", "Abrir Segmento"),
    ("3.1", "Desmontagem de proteções"),
    ("3.2", "Retirar chavetas"),
    ("3.3", "Desconectar pinos dos cilindros de elevação"),
    ("3.4", "Retirada da Barra Transversal"),
    ("3.5", "Desconectar flexíveis principais"),
    ("3.6", "Retirar parafusos de fixação das buchas"),
    ("3.7", "Transferir base para stand"),
    ("3.8", "Aferir pass-line Inf. e Sup."),
    ("3.9", "Retirar cangalhas (Inf. e Sup.)"),
    ("3.10", "Desconectar flexíveis das juntas rotativas"),
    ("3.11", "Retirar proteções de mancal"),
    ("3.12", "Desmontagem dos rolos (Destorquear e soltá-los) inferior"),
    ("3.13", "Desmontagem dos rolos (Destorquear e soltá-los) superior"),
    ("3.14", "Desmontagem da estrutura do rolo acionado"),
    ("3.15", "Retirada dos cilindros motriz"),
    ("3.16", "Desmontagem de buchas e conjuntos na base"),
    ("3.17", "Desmontagem de buchas e conjuntos"),
    ("3.18", "Preparar bases e barra para jateamento e pintura"),
    ("4.1", "Desmontagem de proteções e preparação dos calços e base Inferior"),
    ("4.2", "Troca de oring's"),
    ("4.3", "Montagem de distribuidores"),
    ("4.4", "Fixação dos distribuidores na base"),
    ("4.5", "Desobstrução das tubulações de graxa e de refrigeração"),
    ("4.6", "Preparação dos Rolos"),
    ("4.7", "Montagem de flexíveis na base"),
    ("4.8", "Preparação de pés e tulipas"),
    ("4.9", "Montagem de rolos na base"),
    ("4.10", "Torque dos parafusos dos mancais"),
    ("4.11", "Regulagem dos distribuidores"),
    ("4.12", "Teste de Lubrificação"),
    ("4.13", "Fixação dos distribuidores na base"),
    ("4.14", "Preparar hastes"),
    ("4.15", "Preparar e montar conjuntos de ajustes e buchas"),
    ("4.16", "Montagem das buchas e conjuntos na base"),
    ("4.17", "Montagem dos flexíveis principais"),
    ("4.18", "Conectar flexíveis de juntas nos rolos"),
    ("4.19", "Teste hidrostático juntas rotativas"),
    ("4.20", "Teste hidrostático Mancal"),
    ("4.21", "Aferir Pass-Line e Ajustar"),
    ("4.22", "Montagem e alinhamento das cangalhas"),
    ("5.1", "Desmontar todos os bicos"),
    ("5.2", "Realizar Limpeza das tubulações"),
    ("5.3", "Montar os bicos e flexíveis"),
    ("5.4", "Realizar teste"),
    ("6.1", "Preparação de Lines ou troca"),
    ("6.2", "Preparação dos calços e apoios"),
    ("6.3", "Troca de oring's"),
    ("6.4", "Desobstrução de tubulações de graxa e de refrigeração"),
    ("6.5", "Montagem de proteções das tubulações e de stauff"),
    ("6.6", "Verificar roscas dos parafusos M30"),
    ("6.7", "Montagem do rolo motriz"),
    ("7.1", "Preparação para receber estrutura e cilindros (Lines e mancais)"),
    ("7.2", "Montagem de Cilindros Motriz"),
    ("7.3", "Desmontagem de proteções e preparação dos calços e base Superior"),
    ("7.4", "Troca de oring's"),
    ("7.5", "Desobstruição das tubulações de graxa e de refrigeração"),
    ("7.6", "Preparação dos Rolos"),
    ("7.7", "Troca de parafusos dos calços de alinhamento pass-line"),
    ("7.8", "Montagem de rolos na base"),
    ("7.9", "Aperto de parafusos nos mancais"),
    ("7.10", "Montagem da estrutura"),
    ("7.11", "Montagem de distribuidores"),
    ("7.12", "Regulagem dos distribuidores"),
    ("7.13", "Teste de Lubrificação"),
    ("7.14", "Fixação dos distribuidores na base"),
    ("7.15", "Montagem de proteções dos mancais"),
    ("7.16", "Realização do teste hidrostático da base"),
    ("7.17", "Virar a base"),
    ("7.18", "Torque dos parafusos dos mancais"),
    ("7.19", "Montagem de flexíveis de junta rotativa"),
    ("7.20", "Aferir e ajustar pass-line"),
    ("7.21", "Troca das válvulas dos cilindros"),
    ("7.22", "Troca dos mangotes hidráulicos dos cilindros"),
    ("7.23", "Montagem de proteções sanfonadas"),
    ("7.24", "Substituição dos engates rápidos (hidráulicos)"),
    ("7.25", "Substituição dos engates rápidos (refrigeração)"),
    ("7.26", "Montagem de cangalhas na base"),
    ("8.1", "Troca de cilindros de elevação"),
    ("8.2", "Troca de cilindros clamp"),
    ("8.3", "Montagem de blocos nos cilindros clamp"),
    ("8.4", "Troca de oring's (completo)"),
    ("8.5", "Aperto de tubulações (Conferir)"),
    ("8.6", "Montagem de mangotes dos cilindros de elevação"),
    ("8.7", "Teste hidráulico da barra"),
    ("9.1", "Movimentar base sup para inf"),
    ("9.2", "Conectar flexíveis principais (graxa e água)"),
    ("9.3", "Montar parafusos das buchas"),
    ("9.4", "Preparação das hastes para receber a barra"),
    ("9.5", "Alinhamento de cangalha superior"),
    ("9.6", "Teste geral de juntas"),
    ("9.7", "Montagem da barra transversal no segmento"),
    ("9.8", "Aperto de parafusos dos cilindros clamp"),
    ("9.9", "Montagem de pinos e chavetas"),
    ("9.10", "Montagem de proteções"),
    ("9.11", "Conexão da hidráulica"),
    ("9.12", "Equalização dos cilindros motriz"),
    ("9.13", "Aferir e Ajustar Gap (255mm)"),
    ("10.1", "Teste e Liberação hidráulica"),
    ("10.2", "Teste e Liberação hidrostática"),
    ("10.3", "Retirar Segmento do Stand"),
    ("10.4", "Montagem de Acoplamentos"),
    ("10.5", "Teste de lubrificação geral"),
]

# --------------------------------------------------------------
# 9/10/11 — blocos de medição da fase de Saída (marcados "(SAÍDA)"
# no documento oficial)
# --------------------------------------------------------------
RESUMOS_SAIDA = [
    "Pass Line (Saída) — Base Inferior e Superior",
    "Cilindros Hidráulicos (Saída) — Elevação / Clamp / Motriz",
    "Inspeção de Rolos (Saída) — Rolamento, Teste Hidrostático e Medidas",
]


def cadastrar_etapa(area, texto, especialidade="mecanica"):
    payload = {
        "equipamento_id": TIPO_EQUIPAMENTO,
        "area": area,
        "texto": texto,
        "operador": OPERADOR_MATRICULA,
        "especialidade": especialidade,
        "tipo_resposta": "sim_nao",
    }
    resp = requests.post(f"{API_BASE}/api/checklist-execucao/etapas", json=payload, timeout=15)
    status = "✅" if resp.ok else f"❌ ({resp.status_code})"
    print(f"{status} [{area}] {texto}")
    if not resp.ok:
        print(f"    -> {resp.text[:200]}")


if __name__ == "__main__":
    print(f"Cadastrando etapas em: {API_BASE}")
    print(f"Tipo de equipamento: {TIPO_EQUIPAMENTO}\n")

    print("--- CHEGADA ---")
    for grupo, desc in ITENS_CHEGADA:
        cadastrar_etapa("chegada", f"{grupo} — {desc}")
    for texto in RESUMOS_CHEGADA:
        cadastrar_etapa("chegada", texto)
    for texto in RESUMOS_CHEGADA_INCERTOS:
        cadastrar_etapa("chegada", texto)

    print("\n--- MANUTENÇÃO ---")
    for item, desc in ITENS_MANUTENCAO:
        cadastrar_etapa("manutencao", f"{item} — {desc}")

    print("\n--- SAÍDA ---")
    for texto in RESUMOS_SAIDA:
        cadastrar_etapa("saida", texto)

    print("\nCadastro concluído.")
