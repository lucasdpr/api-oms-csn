"""
Cadastro do LOTE 1 — Checklist de Execução do Molde MCC 2/3.

O QUE ESTÁ AQUI (confirmado lendo folhaoMolde23.js linha a linha +
cruzado com app.html — nenhum campo chutado):
  - Grupo "1. Inspeção de Recebimento Mecânica" (14 itens, prefixo rec)
  - Grupo "2. Inspeção de Recebimento Elétrica" (2 itens, prefixo ele)
  - Grupo "3. Revisão dos Moldes" (16 itens, prefixo rev)
  - Grupo "5. Inspeção Final dos Moldes" (21 itens, prefixo fin)
  - Grupo "4. Check List Hidráulico" (8 itens, prefixo hid)

⚠️ ATENÇÃO — "hid" NÃO é sim/não, mesmo o texto parecendo checklist:
  Em folhaoMolde23.js, renderizarChecklist(..., checkHidraulico, 'hid', true)
  é chamado com isMatricula=true. Isso gera, pra cada item, DOIS campos
  de texto: id="hid-{i}-nome" e id="hid-{i}-mat" (nome + matrícula de
  quem verificou) — não existe radio SIM/NÃO pra esse grupo no HTML.
  Por instrução sua, cadastrei como tipo_resposta="medicao_multipla",
  guardando os dois ids (nome/mat) no folhao_campo, no mesmo padrão que
  o Molde 4 usa pra tabela de folga de aresta.

NÃO INCLUÍDO NESTE LOTE (fica pro Lote 2, 3... — são as ~18 abas de
medição livre do formulário, não itens de checklist):
  - Identificação (placas/redutores/cilindros)
  - Diâmetros dos rolos (chegada/saída) + Alinhamento dos rolos
  - Sensor de nível (7 itens OK + 8 medições de resistência) + Isolação (10 medições)
  - Termopares (5 condições) + Check JB2 (16 status/obs)
  - Resistência das placas (4 valores)
  - Peritagem placas largas (entrada/saída, ~50 pontos cada)
  - Peritagem placas estreitas (chegada/saída)
  - Ajuste de chavetas
  - Folga de aresta (15 larguras x 3 posições x 2 lados = 90 campos)
  - Resfriamento + Materiais utilizados (lista livre)

DESCRIÇÃO ("como fazer"): você não anexou o Folhão físico impresso
nesta conversa, só os .js/.html/.py. Por isso, segui a instrução #5
do seu prompt (não inventar) e deixei descricao=None em todos os itens
deste lote — o texto da pergunta já vem literal do sistema, não é
palpite meu, mas o "passo a passo" de como executar cada item eu não
tenho de onde tirar sem o documento físico. Se você tiver o PDF/foto,
me manda que eu completo as descrições depois.

TIPO_EQUIPAMENTO: confirmado em checklistFolhaoPonte.js
  (resolverTipoEquipamento): item.tipo="Molde" + mcc_compat="2/3" ->
  slug vira "molde-mcc2-3" (barra troca por hífen, tipo em minúsculo).
  NÃO é um chute — está na função que o próprio sistema usa pra
  calcular isso, e é a mesma função usada pela ponte Checklist<->Folhão.

COMO USAR:
  1. Preencha API_BASE e OPERADOR_MATRICULA logo abaixo.
  2. Rode: pip install requests  (se ainda não tiver)
  3. Rode: python cadastrar_etapas_molde23_lote1.py
  4. Confira a saída — cada linha mostra se deu certo ou não.

Pode rodar mais de uma vez sem medo de duplicar: se uma etapa com o
mesmo texto já existir, você só vai ver duas etapas iguais na lista
(o backend não tem trava de duplicado hoje).
"""

import json
import requests

# ⚠️ AJUSTE AQUI antes de rodar
API_BASE = "https://api-oms-csn.onrender.com"   # sem barra no final
OPERADOR_MATRICULA = "CBK3574"              # precisa estar em MATRICULAS_ADM

TIPO_EQUIPAMENTO = "molde-mcc2-3"  # ver nota acima — calculado a partir de item.tipo="Molde" + mcc_compat="2/3"


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
# 1) INSPEÇÃO DE RECEBIMENTO MECÂNICA — 14 itens, prefixo "rec"
# ================================================================
RECEBIMENTO_MECANICA = [
    "Os engates rápidos do sistema hidráulico e do sistema de nitrogênio estão completos e em perfeitas condições?",
    "Os flexíveis das faces estreitas e spray estão amassados e/ou danificados?",
    "Verificar se existe alguma tubulação hidráulica amassada e / ou danificada?",
    "Teste de água com pressão de 10 KGF/cm2 c / tempo de 30 minutos conforme?",
    "Verificar se todos os conectores de termopares estão em perfeitas condições e funcionando?",
    "Sensor vuhz se encontra em perfeitas condições?",
    "Proteções sanfonadas encontram-se em perfeitas condições?",
    "Tampas e réguas guias das placas estão em perfeitas condições?",
    "As cangalhas de spray estão em perfeitas condições, sem avarias?",
    "Os foot-roll e roletes das guias laterais estão em perfeitas condições?",
    "O sistema de lubrificação possui alguma avaria?",
    "As placas de cobre possuem ferimentos e/ou arranhões profundos na face de trabalho?",
    "As juntas de expansão das placas principais estão em perfeitas condições?",
    "Parafusos de fixação do molde no stand estão completos e em perfeitas condições?",
]

# ================================================================
# 2) INSPEÇÃO DE RECEBIMENTO ELÉTRICA — 2 itens, prefixo "ele"
# ================================================================
RECEBIMENTO_ELETRICA = [
    "Os conectores do detector de break-out das faces larga estão tampados e em perfeitas condições?",
    "Os cabos elétricos dos termopares do detector de break-out das faces estreitas estão em perfeitas condições?",
]

# ================================================================
# 3) REVISÃO DOS MOLDES — 16 itens, prefixo "rev"
# ================================================================
REVISAO_MOLDES = [
    "Inspeção das proteções sanfonadas dos cilindros das faces estreitas, substituindo as que estiverem danificadas.",
    "Inspeção das proteções sanfonadas dos fusos dos castelos quadrados, substituindo as que estiverem danificadas.",
    "Inspeção, reparo (se necessário) e lubrificação dos conjuntos de porcas e contra porcas.",
    "Inspeção, reparo (se necessário) e lubrificação dos conjuntos do castelo quadrado.",
    "Inspeção das hastes dos cilindros das faces estreitas, verificando se há avarias e vazamentos de óleo.",
    "Inspeção dos cilindros do clamp de abertura da face larga, substituindo os que estiverem com vazamento.",
    "Inspeção do filtro de óleo do sistema hidráulico, verificando se ele não está sujo.",
    "Inspeção e lubrificação nos olhais e nas chavetas de fixação das placas laterais, ajustando se necessário.",
    "Inspeção, revisão e lubrificação dos eixos e mancais deslizantes (caixa louca).",
    "Inspeção em todo sistema de lubrificação, corrigindo anomalias. Testar as válvulas de graxa na unidade hidráulica, trocas tubulações.",
    "Inspeção das condições dos flexíveis de água, substituindo os que estiverem danificados.",
    "Inspeção, revisão e lubrificação dos parafusos de fixação do molde no stand.",
    "Inspeção das tubulações hidráulicas (conferir aperto das conexões e trocar as que estiverem danificadas).",
    "Alinhar os fusos dos castelos quadrados na medida padrão de 210mm.",
    "Lubrificar e amaciar os fusos do ajuste mecânico.",
    "Inspeção das juntas de expansão (trocar se necessário).",
]

# ================================================================
# 4) CHECK LIST HIDRÁULICO — 8 itens, prefixo "hid"
#    NÃO é sim/não — cada item tem campo de nome + matrícula (ver nota
#    no topo do arquivo). Cadastrado como medicao_multipla.
# ================================================================
CHECK_HIDRAULICO = [
    "CHECK DOS CILINDROS DE AJUSTE DE LARGURA DO MOLDE",
    "VERIFICAR VAZAMENTO DE GRAXA NAS CONEXÕES",
    "VERIFICAR VAZAMENTO DE ÓLEO NAS CONEXÕES",
    "INSPECIONAR O ELEMENTO FILTRANTE DO FILTRO DA LINHA DE PRESSÃO HIDRÁULICA E SE NECESSÁRIO EFETUAR A TROCA.",
    "LUBRIFICAÇÃO",
    "VERIFICAR VAZAMENTO EM MANGUEIRAS E DOSADOR, SUBSTITUIR SE NECESSÁRIO.",
    "EFETUAR A LIMPEZA DOS ENGATES HIDRÁULICOS",
    "EMBALAR ENGATES HIDRÁULICOS",
]

# ================================================================
# 5) INSPEÇÃO FINAL DOS MOLDES — 21 itens, prefixo "fin"
# ================================================================
INSPECAO_FINAL = [
    "Indicadores de pressão de ajuste das molas da placa lado móvel, estão completos e alinhados?",
    "Tampa de proteção do molde não está tocando sobre a tubulação de sangria das placas principais?",
    "Placas de proteção estão calafetadas com fita, desempenadas alinhadas e fixadas através de parafusos?",
    "Posicionamento dos flexíveis superiores e inferiores estão conformes?",
    "Teste de água com pressão de 10 KGF/cm2 (valor referência) c/ tempo de 30 minutos, conforme?",
    "Proteções sanfonadas estão fixadas?",
    "\u201cFoot-roll\u201d e roletes das guias laterais estão lubrificados e girando normalmente?",
    "Alinhamento dos bicos de spray das faces largas e estreitas?",
    "Parafusos de fixação do molde na máquina estão completos e lubrificados?",
    "Sensor Vuhz está montado corretamente e testado?",
    "A precisão de movimento das faces estreitas estão conforme?",
    "Funcionamento correto das válvulas distribuidoras de graxa, conexões marcadas?",
    "Réguas do ajuste mecânico estão livres e lubrificadas corretamente?",
    "Folga na aresta das faces das placas estreitas e largas (<= 0,35mm)?",
    "Cavidade interna do molde limpa?",
    "Centro do molde está identificado na placa norte e visível ao operador?",
    "Conectores dos termopares das placas estão limpos e tampados?",
    "Teste de profundidade está conforme?",
    "Engates rápido do sistema hidráulico, sistema de nitrogênio e graxa, estão c/ as vedações completas, apertados e protegidos?",
    "Base de vedação do molde está limpa e lixada?",
    "Os conectores dos DBO estão todos tamponados e protegidos?",
]


if __name__ == "__main__":
    print(f"Cadastrando etapas em: {API_BASE}")
    print(f"Tipo de equipamento: {TIPO_EQUIPAMENTO}\n")

    total = 0

    for i, texto in enumerate(RECEBIMENTO_MECANICA):
        cadastrar_etapa("mecanica", texto, "sim_nao", folhao_campo=f"rec-{i}")
        total += 1

    for i, texto in enumerate(RECEBIMENTO_ELETRICA):
        cadastrar_etapa("eletrica", texto, "sim_nao", folhao_campo=f"ele-{i}")
        total += 1

    for i, texto in enumerate(REVISAO_MOLDES):
        cadastrar_etapa("mecanica", texto, "sim_nao", folhao_campo=f"rev-{i}")
        total += 1

    for i, texto in enumerate(CHECK_HIDRAULICO):
        cadastrar_etapa(
            "hidraulica", texto, "medicao_multipla",
            campo_json={"nome": f"hid-{i}-nome", "mat": f"hid-{i}-mat"}
        )
        total += 1

    for i, texto in enumerate(INSPECAO_FINAL):
        cadastrar_etapa("mecanica", texto, "sim_nao", folhao_campo=f"fin-{i}")
        total += 1

    print(f"\nTotal: {total} etapas processadas.")
