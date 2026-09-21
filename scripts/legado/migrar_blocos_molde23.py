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
    # 🆕 Preenchido a partir do "CHECK LIST GERAL DO MOLDE MCC 2 E 3"
    # oficial (arquivo enviado por quem manja do processo) — cada seção
    # do documento oficial vira uma fase:
    #   INSPEÇÃO DE RECEBIMENTO / RECEBIMENTO ELÉTRICA -> chegada
    #   REVISÃO DOS MOLDES / CHECK LIST HIDRÁULICO      -> manutencao
    #   INSPEÇÃO FINAL DOS MOLDES                        -> saida
    # + os itens com "AO CHEGAR"/"AO SAIR"/"NA SAÍDA"/"(chegada)"/
    # "(saída)" explícito no próprio texto.

    # --- INSPEÇÃO DE RECEBIMENTO (chegada) ---
    "Os engates rápidos do sistema hidráulico e do sistema de nitrogênio estão completos e em perfeitas condições?": "chegada",
    "Os flexíveis das faces estreitas e spray estão amassados e/ou danificados?": "chegada",
    "Verificar se existe alguma tubulação hidráulica amassada e / ou danificada?": "chegada",
    "Teste de água com pressão de 10 KGF/cm2 c / tempo de 30 minutos conforme?": "chegada",
    "Verificar se todos os conectores de termopares estão em perfeitas condições e funcionando?": "chegada",
    "Sensor vuhz se encontra em perfeitas condições?": "chegada",
    "Proteções sanfonadas encontram-se em perfeitas condições?": "chegada",
    "Tampas e réguas guias das placas estão em perfeitas condições?": "chegada",
    "As cangalhas de spray estão em perfeitas condições, sem avarias?": "chegada",
    "Os foot-roll e roletes das guias laterais estão em perfeitas condições?": "chegada",
    "O sistema de lubrificação possui alguma avaria?": "chegada",
    "As placas de cobre possuem ferimentos e/ou arranhões profundos na face de trabalho?": "chegada",
    "As juntas de expansão das placas principais estão em perfeitas condições?": "chegada",
    "Parafusos de fixação do molde no stand estão completos e em perfeitas condições?": "chegada",

    # --- INSPEÇÃO DE RECEBIMENTO ELÉTRICA (chegada) ---
    "Os conectores do detector de break-out das faces larga estão tampados e em perfeitas condições?": "chegada",
    "Os cabos elétricos dos termopares do detector de break-out das faces estreitas estão em perfeitas condições?": "chegada",

    # --- REVISÃO DOS MOLDES (manutenção) ---
    "Inspeção das proteções sanfonadas dos cilindros das faces estreitas, substituindo as que estiverem danificadas.": "manutencao",
    "Inspeção das proteções sanfonadas dos fusos dos castelos quadrados, substituindo as que estiverem danificadas.": "manutencao",
    "Inspeção, reparo (se necessário) e lubrificação dos conjuntos de porcas e contra porcas.": "manutencao",
    "Inspeção, reparo (se necessário) e lubrificação dos conjuntos do castelo quadrado.": "manutencao",
    "Inspeção das hastes dos cilindros das faces estreitas, verificando se há avarias e vazamentos de óleo.": "manutencao",
    "Inspeção dos cilindros do clamp de abertura da face larga, substituindo os que estiverem com vazamento.": "manutencao",
    "Inspeção do filtro de óleo do sistema hidráulico, verificando se ele não está sujo.": "manutencao",
    "Inspeção e lubrificação nos olhais e nas chavetas de fixação das placas laterais, ajustando se necessário.": "manutencao",
    "Inspeção, revisão e lubrificação dos eixos e mancais deslizantes (caixa louca).": "manutencao",
    "Inspeção em todo sistema de lubrificação, corrigindo anomalias. Testar as válvulas de graxa na unidade hidráulica, trocas tubulações.": "manutencao",
    "Inspeção das condições dos flexíveis de água, substituindo os que estiverem danificados.": "manutencao",
    "Inspeção, revisão e lubrificação dos parafusos de fixação do molde no stand.": "manutencao",
    "Inspeção das tubulações hidráulicas (conferir aperto das conexões e trocar as que estiverem danificadas).": "manutencao",
    "Alinhar os fusos dos castelos quadrados na medida padrão de 210mm.": "manutencao",
    "Lubrificar e amaciar os fusos do ajuste mecânico.": "manutencao",
    "Inspeção das juntas de expansão (trocar se necessário).": "manutencao",

    # --- CHECK LIST HIDRÁULICO (manutenção) ---
    "CHECK DOS CILINDROS DE AJUSTE DE LARGURA DO MOLDE": "manutencao",
    "VERIFICAR VAZAMENTO DE GRAXA NAS CONEXÕES": "manutencao",
    "VERIFICAR VAZAMENTO DE ÓLEO NAS CONEXÕES": "manutencao",
    "INSPECIONAR O ELEMENTO FILTRANTE DO FILTRO DA LINHA DE PRESSÃO HIDRÁULICA E SE NECESSÁRIO EFETUAR A TROCA.": "manutencao",
    "LUBRIFICAÇÃO": "manutencao",
    "VERIFICAR VAZAMENTO EM MANGUEIRAS E DOSADOR, SUBSTITUIR SE NECESSÁRIO.": "manutencao",
    "EFETUAR A LIMPEZA DOS ENGATES HIDRÁULICOS": "manutencao",
    "EMBALAR ENGATES HIDRÁULICOS": "manutencao",

    # --- INSPEÇÃO FINAL DOS MOLDES (saída) ---
    "Indicadores de pressão de ajuste das molas da placa lado móvel, estão completos e alinhados?": "saida",
    "Tampa de proteção do molde não está tocando sobre a tubulação de sangria das placas principais?": "saida",
    "Placas de proteção estão calafetadas com fita, desempenadas alinhadas e fixadas através de parafusos?": "saida",
    "Posicionamento dos flexíveis superiores e inferiores estão conformes?": "saida",
    "Teste de água com pressão de 10 KGF/cm2 (valor referência) c/ tempo de 30 minutos, conforme?": "saida",
    "Proteções sanfonadas estão fixadas?": "saida",
    "“Foot-roll” e roletes das guias laterais estão lubrificados e girando normalmente?": "saida",
    "Alinhamento dos bicos de spray das faces largas e estreitas?": "saida",
    "Parafusos de fixação do molde na máquina estão completos e lubrificados?": "saida",
    "Sensor Vuhz está montado corretamente e testado?": "saida",
    "A precisão de movimento das faces estreitas estão conforme?": "saida",
    "Funcionamento correto das válvulas distribuidoras de graxa, conexões marcadas?": "saida",
    "Réguas do ajuste mecânico estão livres e lubrificadas corretamente?": "saida",
    "Folga na aresta das faces das placas estreitas e largas (<= 0,35mm)?": "saida",
    "Cavidade interna do molde limpa?": "saida",
    "Centro do molde está identificado na placa norte e visível ao operador?": "saida",
    "Conectores dos termopares das placas estão limpos e tampados?": "saida",
    "Teste de profundidade está conforme?": "saida",
    "Engates rápido do sistema hidráulico, sistema de nitrogênio e graxa, estão c/ as vedações completas, apertados e protegidos?": "saida",
    "Base de vedação do molde está limpa e lixada?": "saida",
    "Os conectores dos DBO estão todos tamponados e protegidos?": "saida",

    # --- Diâmetros / peritagem / avaliação, com fase no próprio texto ---
    "Diâmetros dos rolos — ao chegar na oficina": "chegada",
    "Diâmetros dos rolos — ao sair da oficina": "saida",
    "Peritagem placas largas — ao entrar na oficina": "chegada",
    "Peritagem placas largas — ao sair da oficina": "saida",
    "Peritagem placas estreitas — placa esquerda afastada? (chegada)": "chegada",
    "Peritagem placas estreitas — placa direita afastada? (chegada)": "chegada",
    "Peritagem placas estreitas — pontos de medição (chegada)": "chegada",
    "Peritagem placas estreitas — placa esquerda afastada? (saída)": "saida",
    "Peritagem placas estreitas — placa direita afastada? (saída)": "saida",
    "Peritagem placas estreitas — pontos de medição (saída)": "saida",
    "Avaliação do sistema de resfriamento — face norte/fixa": "saida",   # doc: "NA SAÍDA" explícito
    "Avaliação do sistema de resfriamento — face sul/móvel": "saida",   # doc: "NA SAÍDA" explícito

    # --- Termopares / JB2 (manutenção — tabelas "MANUTENÇÃO TERMOPARES" / "CHECK DO JB2" no doc oficial) ---
    "Termopares — identificação das caixas (placa fixa/móvel)": "manutencao",
    "Termopares — manutenção (parafusos, ar, limpeza, borrachas, travas)": "manutencao",
    "JB2 — fecho painel / conectores wanboy / vedação": "manutencao",
    "JB2 — conectores da válvula proporcional (4 posições)": "manutencao",
    "JB2 — conectores dos transdutores de posição (4 posições)": "manutencao",
    "JB2 — bloco principal (vedações, válvulas, transdutores óleo/ar)": "manutencao",
    "JB2 — cabos do ajuste de largura do molde (4 posições + banco de válvulas)": "manutencao",
    "Teste de resistência das placas (móvel/fixa/estreitas)": "manutencao",

    # --- Sensor de nível (manutenção — planilha de ajuste, sem marcação de fase no doc) ---
    "Sensor de nível — checagem (itens 1 a 7)": "manutencao",
    "Sensor de nível — medição de resistência (itens 8 a 15)": "manutencao",
    "Isolação dos sensores de nível (MΩ)": "manutencao",

    # --- Ajuste de chavetas (manutenção) ---
    "Ajuste de chavetas — placa esquerda (lados A e B)": "manutencao",
    "Ajuste de chavetas — placa direita (lados A e B)": "manutencao",

    # 🔶 CONFIANÇA MÉDIA — o doc não marca a fase explicitamente pra
    # essas 3, classifiquei pela posição delas no documento (entre um
    # ajuste/manutenção e a seção de saída). Confirme antes de aplicar
    # se tiver dúvida:
    "Alinhamento dos rolos (foot roll / edge roll)": "manutencao",
    "Folga de aresta — lado esquerdo (todas as larguras)": "saida",
    "Folga de aresta — lado direito (todas as larguras)": "saida",

    # ⚠️ DE PROPÓSITO FORA DA MIGRAÇÃO (mesma ambiguidade do Molde MCC4:
    # a MESMA etapa cobre tanto a saída da máquina do cliente — que é
    # quando a peça CHEGA na oficina — quanto a saída da oficina de
    # volta pro cliente. Não dá pra jogar numa fase só sem perder
    # metade do sentido; fica na área antiga até alguém decidir separar
    # em 2 etapas, uma só com os campos de entrada e outra só com os de
    # saída):
    #   "Identificação — Placas (saída máquina/oficina)"
    #   "Identificação — Redutores (saída máquina/oficina)"
    #   "Identificação — Cilindros (saída máquina/oficina)"
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
