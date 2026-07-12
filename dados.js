export const MOTIVOS_RETIRO = {
    "Molde": ["Desgaste de placa", "Ranhura de placa", "Falha no cilindro", "Fim de vida", "Trava da bender", "Alarme de B.O", "B.O", "Rolete travado", "Outros"],
    "Segmento Horizontal": ["Blackout", "Fim de vida", "Vazamento de graxa", "Placa na linha", "Transpordo", "Vazão", "Rolo travado", "Outros"],
    "Horizontal": ["Blackout", "Fim de vida", "Vazamento de graxa", "Placa na linha", "Transpordo", "Vazão", "Rolo travado", "Outros"],
    "Bow": ["Blackout", "Fim de vida", "Vazamento de graxa", "Placa na linha", "Transpordo", "Vazão", "Rolo travado", "Outros"],
    "Straightener": ["Blackout", "Fim de vida", "Vazamento de graxa", "Placa na linha", "Transpordo", "Vazão", "Rolo travado", "Outros"],
    "Bender": ["Blackout", "Fim de vida", "Vazamento de graxa", "Placa na linha", "Transpordo", "Vazão", "Rolo travado", "Outros"],
    "Segmento Zero": ["Blackout", "Fim de vida", "Vazamento de graxa", "Placa na linha", "Transpordo", "Vazão", "Rolo travado", "Outros"],
    "Cadeira Superior": ["Empeno", "Desgaste", "Rolo quebrado", "Vazamento de cilindro", "Vazamento de graxa", "Refrigeração", "Trinca", "Fim de vida", "Outros"],
    "Cadeira Inferior": ["Empeno", "Desgaste", "Rolo quebrado", "Vazamento de cilindro", "Vazamento de graxa", "Refrigeração", "Trinca", "Fim de vida", "Outros"],
    "Mesa Osciladora": ["Desgaste", "Falha mecânica", "Fim de vida", "Outros"],
    "Outros": ["Fim de vida", "Quebra", "Manutenção Preventiva", "Outros"]
};

export const CHECKLIST_RECEBIMENTO = [
    "Os engates rápidos do sistema hidráulico e nitrogênio estão completos e em perfeitas condições?",
    "Os flexíveis das faces estreitas e spray estão amassados e/ou danificados?",
    "Verificar se existe alguma tubulação hidráulica amassada e/ou danificada?",
    "Teste de água com pressão de 10 KGF/cm2 c/ tempo de 30 minutos conforme?",
    "Sensor vuhz se encontra em perfeitas condições?",
    "Verificar se todos os conectores de termopares estão em perfeitas condições e funcionando?",
    "As cangalhas de spray estão em perfeitas condições, sem avarias?",
    "Proteções sanfonadas encontram-se em perfeitas condições?",
    "Tampas e réguas guias das placas estão em perfeitas condições?",
    "Os foot-roll e roletes das guias laterais estão em perfeitas condições?",
    "O sistema de lubrificação possui alguma avaria?",
    "As placas de cobre possuem ferimentos e/ou arranhões profundos na face de trabalho?",
    "As juntas de expansão das placas principais estão em perfeitas condições?",
    "Parafusos de fixação do molde no stand estão completos e em perfeitas condições?",
    "(ELÉTRICA) Conectores do detector de break-out das faces larga estão tampados e em perfeitas condições?",
    "(ELÉTRICA) Cabos elétricos dos termopares do detector de break-out das faces estreitas estão em perfeitas condições?"
];

export const CHECKLIST_REVISAO = [
    "Inspeção das proteções sanfonadas dos cilindros das faces estreitas, substituindo as que estiverem danificadas.",
    "Inspeção das proteções sanfonadas dos fusos dos castelos quadrados, substituindo as danificadas.",
    "Inspeção, reparo (se necessário) e lubrificação dos conjuntos de porcas e contra porcas.",
    "Inspeção, reparo (se necessário) e lubrificação dos conjuntos do castelo quadrado.",
    "Inspeção das hastes dos cilindros das faces estreitas, verificando avarias e vazamentos de óleo.",
    "Inspeção dos cilindros do clamp de abertura da face larga, substituindo os com vazamento.",
    "Inspeção do filtro de óleo do sistema hidráulico, verificando se não está sujo.",
    "Inspeção e lubrificação nos olhais e nas chavetas de fixação das placas laterais.",
    "Inspeção, revisão e lubrificação dos eixos e mancais deslizantes (caixa louca).",
    "Inspeção em todo sistema de lubrificação, corrigindo anomalias. Testar válvulas de graxa.",
    "Inspeção das condições dos flexíveis de água, substituindo os danificados.",
    "Inspeção, revisão e lubrificação dos parafusos de fixação do molde no stand.",
    "Inspeção das tubulações hidráulicas (conferir aperto das conexões).",
    "Alinhar os fusos dos castelos quadrados na medida padrão de 210mm.",
    "Lubrificar e amaciar os fusos do ajuste mecânico.",
    "Inspeção das juntas de expansão (trocar se necessário)."
];

export const CHECKLIST_HIDRAULICA = [
    "Check dos cilindros de ajuste de largura do molde.",
    "Verificar vazamento de graxa nas conexões.",
    "Verificar vazamento de óleo nas conexões.",
    "Inspecionar o elemento filtrante da linha de pressão hidráulica e trocar se necessário.",
    "Lubrificação geral de componentes.",
    "Verificar vazamento em mangueiras e dosador, substituir se necessário.",
    "Efetuar a limpeza dos engates hidráulicos.",
    "Embalar engates hidráulicos."
];

export const CHECKLIST_FINAL = [
    "Indicadores de pressão de ajuste das molas da placa lado móvel estão completos e alinhados?",
    "Tampa de proteção do molde NÃO está tocando sobre a tubulação de sangria das placas?",
    "Placas de proteção estão calafetadas com fita, desempenadas, alinhadas e fixadas?",
    "Posicionamento dos flexíveis superiores e inferiores estão conformes?",
    "Teste de água com pressão de 10 KGF/cm2 c/ tempo de 30 minutos conforme?",
    "Proteções sanfonadas estão fixadas?",
    "Foot-roll e roletes das guias laterais estão lubrificados e girando normalmente?",
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
    "Engates rápidos (hidráulico, N2, graxa) com vedações completas, apertados e limpos?",
    "Base de vedação do molde está limpa e lixada?",
    "Os conectores dos DBO estão todos tamponados e protegidos?"
];
// ==========================================
// NOVOS CHECKLISTS INTELIGENTES POR EQUIPAMENTO
// ==========================================
// ==========================================
// BIBLIOTECA INTELIGENTE DE CHECKLISTS POR EQUIPAMENTO
// ==========================================
// ==========================================
// BIBLIOTECA INTELIGENTE DE CHECKLISTS E CATEGORIAS
// ==========================================
export const BIBLIOTECA_CHECKLISTS = {
    // ---- EQUIPAMENTOS DA FAMÍLIA 4 ----
    "Bender": {
        "1. INSPEÇÃO DE CHEGADA": [
            "LUBRIFICAÇÃO: Sistema isento de vazamentos.",
            "LUBRIFICAÇÃO: Tubulação amassada.",
            "LUBRIFICAÇÃO: Distribuidores funcionando corretamente.",
            "LUBRIFICAÇÃO: Flexíveis perfeitos, sem avarias.",
            "LUBRIFICAÇÃO: Tubulações Inox/Cobre danificadas.",
            "REFRIGERAÇÃO: Resfriadores completos e alinhados.",
            "REFRIGERAÇÃO: Bicos completos e desobstruídos.",
            "REFRIGERAÇÃO: Flexíveis isentos de vazamentos.",
            "REFRIGERAÇÃO: Tubulações isentas de empenos ou furos.",
            "ESTRUTURA: Rolos lubrificados, girando normalmente.",
            "ESTRUTURA: Proteções isentas de avarias.",
            "ESTRUTURA: Estrutura com break-out.",
            "ESTRUTURA: Rolamentos quebrados ou Rolos travados.",
            "ESTRUTURA: Parafusos dos mancais todos apertados.",
            "ESTRUTURA: Conexões apertadas."
        ],
        "2. CHECKLIST DE MANUTENÇÃO (EXECUÇÃO)": [
            "Limpeza e lavagem de Break Out.",
            "Soltar uniões das cangalhas, retirar chavetas e remover cangalhas.",
            "Posicionar segmento na horizontal e aferir GAP de chegada.",
            "Içar e separar a base superior da base inferior.",
            "Desconectar tubulação de graxa, parafusos e retirar conjuntos de rolos.",
            "Preparar base superior e inferior para jateamento/pintura.",
            "Preparação e Testes de refrigeração nas cangalhas.",
            "Montar válvulas de graxa nas bases e testar lubrificação.",
            "Instalar conjuntos de rolos na base, apertando os parafusos M16 (com graxa).",
            "Aferir Pass Line com régua na base inferior e superior.",
            "Conectar e testar tubos de lubrificação, montar proteções dos rolos.",
            "Transportar base superior, montar calços e fechar o segmento.",
            "Conferir o GAP de Saída e registrar.",
            "Montar cangalhas, resfriadores e mangueiras de lubrificação.",
            "Efetuar teste final de resfriadores e lubrificação."
        ]
    },
    // ---- EQUIPAMENTOS DA FAMÍLIA 2 E 3 ----
    "Molde": {
        "1. INSPEÇÃO DE RECEBIMENTO": [
            "Os engates rápidos para abertura da face móvel estão completos e em perfeitas condições?",
            "Os engates rápidos para o sistema de lubrificação estão completos e em perfeitas condições?",
            "Os flexíveis das guias laterais estão amassados e/ou danificados?",
            "As tubulações hidráulicas e de lubrificação estão em perfeitas condições?",
            "Os protetores sanfonados dos fusos e tubos telescópicos das placas laterais estão danificados?",
            "As cangalhas de spray estão 'OK' sem avarias?",
            "Há avarias nas mangueiras e tubulação de lubrificação dos foot rolls e guias laterais?",
            "As réguas de guia das placas laterais estão em perfeitas condições?",
            "Ao executar o teste de movimentação das laterais houve ruídos?",
            "Ao realizar o teste hidrostático nas placas foi identificados vazamentos?",
            "Ao realizar o teste de spray, ocorreu obstrução de bicos?"
        ],
        "2. INSPEÇÃO ELÉTRICA (RECEBIMENTO)": [
            "Os conectores do detector de break-out das faces larga estão tampados e em perfeitas condições?",
            "Os cabos elétricos dos termopares do detector de break-out das faces estreitas estão em perfeitas condições?"
        ],
        "3. REVISÃO DO MOLDE": [
            "Retirar os parafusos de fixação dos foot rolls e guias laterais; fazer acabamento e recondicionar roscas.",
            "Ajustar chavetas das guias dos rolos laterais e bases dos foot-rolls.",
            "Desmontar réguas guias das laterais, lixar, desempenar e recompor c/ solda se necessário.",
            "Calibrar com 0.40mm a folga da arruela dos parafusos de fixação da face larga móvel.",
            "Desobstruir dreno na tampa das hastes do cilindro do clamp.",
            "Ajustar as 04 porcas castelo da haste do cilindro de clamp da face larga móvel.",
            "Limpar e ajustar os parafusos de alinhamento das bases (guias laterais).",
            "Limpar faces de apoio das placas largas e estreitas e montar o'ring.",
            "Fazer inspeção visual em todo o sistema hidráulico e relatar anomalias.",
            "Verificar e reparar pinos travas dos eixos KARDANS, lubrificar, ajustar estrias e pintá-los.",
            "Desmontar proteção sanfonada dos fusos, inspecionar e lubrificar os mesmos (substituir se danificada).",
            "Limpar e ajustar calços para alinhamento dos foot roll.",
            "Ajustar e lubrificar o parafuso excêntrico de alinhamento do molde na máquina.",
            "Fixar e ajustar placa suporte do parafuso de fixação do molde na máquina, com 1mm.",
            "Inspecionar folgas nas caixas de engrenagem das placas laterais.",
            "Lubrificar total, verificando o perfeito funcionamento das válvulas distribuidoras de graxa.",
            "Fazer inspeção nas roscas para fixação das placas laterais (back up).",
            "Verificar torque de aperto dos parafusos tipo feno dos eixos cardans - 25 Nm."
        ],
        "4. INSPEÇÃO FINAL": [
            "Esquadramento das faces estreitas está na tolerância de 0.1mm?",
            "Alinhamento do molde em relação ao gabarito do stand está correto?",
            "A folga nas arruelas dos parafusos de fixação da placa móvel estão entre 0.3mm a 0.5mm?",
            "A folga máxima entre as placas laterais e largas é de 0.25mm?",
            "Os encaixes dos eixos cardans nos motores foram feitos sem interferência?",
            "As marcações dos centros das placas largas estão legíveis?",
            "Tubos telescópios sem vazamentos? (Teste de casamento com 7kgf/cm2).",
            "Os protetores sanfonados estão em bom estado de conservação?",
            "Os engates rápidos estão apertados e protegidos?",
            "Os eixos cardan estão limpos, lubrificados e protegidos?",
            "Os leques dos sprays estão corretamente alinhados e sem obstrução?",
            "Não houve vazamento durante o teste hidrostático com 10 bar durante 30min?",
            "Foot Rolls e roletes das guias laterais estão lubrificados e girando normalmente?",
            "As tampas de proteção dos parafusos do foot roll estão montadas?",
            "Os parafusos M36 alinhados (c/ contra porca) na elevação de 1640mm ~3mm a partir do pé do molde?",
            "Cavidade interna do molde e rolos limpos?",
            "Cilindros hidráulicos do sistema do clamp foi feito sangria?"
        ],
        "5. CHECK LIST HIDRÁULICO E ELÉTRICO": [
            "CHECK DOS CILINDROS DO CLAMP",
            "VERIFICAR VAZAMENTO DE GRAXA NAS CONEXÕES",
            "VERIFICAR VAZAMENTO DE ÓLEO NAS CONEXÕES",
            "INSPECIONAR ELEMENTO FILTRANTE (LINHA DE PRESSÃO) E TROCAR SE NECESSÁRIO",
            "LUBRIFICAÇÃO (Verificar mangueiras e dosador)",
            "EFETUAR LIMPEZA E EMBALAR ENGATES HIDRÁULICOS",
            "OS CONECTORES DO DBO E VUHZ ESTÃO LIMPOS, TAMPONADOS E PROTEGIDOS?"
        ]
    }
};