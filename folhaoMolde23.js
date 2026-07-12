// folhaoMolde23.js - VERSÃO FINAL COM TODOS OS CAMPOS E FALLBACK DE CONTAINERS


let ID_FOLHAO_MOLDE23_ATUAL = null;

// ==============================================================
// 1. DADOS DAS TABELAS (transcritos do documento)
// ==============================================================
const recebimentoMecanica = [
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
    "Parafusos de fixação do molde no stand estão completos e em perfeitas condições?"
];

const recebimentoEletrica = [
    "Os conectores do detector de break-out das faces larga estão tampados e em perfeitas condições?",
    "Os cabos elétricos dos termopares do detector de break-out das faces estreitas estão em perfeitas condições?"
];

const revisaoMoldes = [
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
    "Inspeção das juntas de expansão (trocar se necessário)."
];

const inspecaoFinal = [
    "Indicadores de pressão de ajuste das molas da placa lado móvel, estão completos e alinhados?",
    "Tampa de proteção do molde não está tocando sobre a tubulação de sangria das placas principais?",
    "Placas de proteção estão calafetadas com fita, desempenadas alinhadas e fixadas através de parafusos?",
    "Posicionamento dos flexíveis superiores e inferiores estão conformes?",
    "Teste de água com pressão de 10 KGF/cm2 (valor referência) c/ tempo de 30 minutos, conforme?",
    "Proteções sanfonadas estão fixadas?",
    "“Foot-roll” e roletes das guias laterais estão lubrificados e girando normalmente?",
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
    "Os conectores dos DBO estão todos tamponados e protegidos?"
];

const checkHidraulico = [
    "CHECK DOS CILINDROS DE AJUSTE DE LARGURA DO MOLDE",
    "VERIFICAR VAZAMENTO DE GRAXA NAS CONEXÕES",
    "VERIFICAR VAZAMENTO DE ÓLEO NAS CONEXÕES",
    "INSPECIONAR O ELEMENTO FILTRANTE DO FILTRO DA LINHA DE PRESSÃO HIDRÁULICA E SE NECESSÁRIO EFETUAR A TROCA.",
    "LUBRIFICAÇÃO",
    "VERIFICAR VAZAMENTO EM MANGUEIRAS E DOSADOR, SUBSTITUIR SE NECESSÁRIO.",
    "EFETUAR A LIMPEZA DOS ENGATES HIDRÁULICOS",
    "EMBALAR ENGATES HIDRÁULICOS"
];

// ==============================================================
// 2. FUNÇÕES AUXILIARES
// ==============================================================
function getV(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
}

function getRadioValue(name) {
    const radios = document.getElementsByName(name);
    for (let r of radios) if (r.checked) return r.value;
    return 'NÃO';
}

function getCheckboxValue(id) {
    const el = document.getElementById(id);
    return el && el.checked ? 'OK' : '';
}

// ==============================================================
// 3. GARANTIR QUE OS CONTAINERS EXISTAM (FALLBACK)
// ==============================================================
function garantirContainer(id) {
    let container = document.getElementById(id);
    if (!container) {
        // Cria o container dentro do corpo do modal (procura a aba correspondente)
        const aba = document.querySelector(`#aba-m23-${id.split('-')[2] || 'identificacao'}`);
        if (aba) {
            container = document.createElement('div');
            container.id = id;
            aba.appendChild(container);
        } else {
            // Fallback: coloca no final do body do modal
            const body = document.querySelector('.folhao-body');
            if (body) {
                container = document.createElement('div');
                container.id = id;
                body.appendChild(container);
            }
        }
    }
    return container;
}

// ==============================================================
// 4. RENDERIZAR TABELAS DE CHECKLIST (RECEBIMENTO, REVISÃO, etc.)
// ==============================================================
function renderizarChecklist(containerId, array, prefix, isMatricula = false) {
    const container = garantirContainer(containerId);
    if (!container) return;
    let html = `<table class="premium-table" style="font-size:10px; width:100%; border-collapse:collapse;">
        <thead><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th>`;
    if (isMatricula) {
        html += `<th style="width:15%;">NOME</th><th style="width:12%;">MATRÍCULA</th>`;
    } else {
        html += `<th style="width:8%;">SIM</th><th style="width:8%;">NÃO</th>`;
    }
    html += `</tr></thead><tbody>`;
    array.forEach((desc, i) => {
        const name = `${prefix}-${i}`;
        html += `<tr><td style="text-align:center;">${i+1}</td><td>${desc}</td>`;
        if (isMatricula) {
            html += `<td><input id="${name}-nome" class="w-100"></td><td><input id="${name}-mat" class="w-100"></td>`;
        } else {
            html += `<td style="text-align:center;"><input type="radio" name="${name}" value="SIM" checked></td>
                     <td style="text-align:center;"><input type="radio" name="${name}" value="NÃO"></td>`;
        }
        html += `</tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

// ==============================================================
// 5. RENDERIZAR IDENTIFICAÇÃO
// ==============================================================
function renderizarIdentificacao() {
    const container = garantirContainer('molde23-identificacao');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">IDENTIFICAÇÃO</h3>
        <table class="premium-table" style="font-size:10px;">
            <thead><tr><th>PLACAS</th><th>SAÍDA MÁQUINA</th><th>SAÍDA OFICINA</th>
                <th>REDUTORES</th><th>SAIR MÁQUINA</th><th>SAIR OFICINA</th>
                <th>CILINDROS</th><th>SAIR MÁQUINA</th><th>SAIR OFICINA</th></tr></thead>
            <tbody>
                <tr><td>FIXA:</td><td><input id="id-placa-fixa-mq"></td><td><input id="id-placa-fixa-of"></td>
                    <td>SUP DIREITO</td><td><input id="id-red-sup-dir-mq"></td><td><input id="id-red-sup-dir-of"></td>
                    <td>SUP DIR</td><td><input id="id-cil-sup-dir-mq"></td><td><input id="id-cil-sup-dir-of"></td></tr>
                <tr><td>MÓVEL</td><td><input id="id-placa-movel-mq"></td><td><input id="id-placa-movel-of"></td>
                    <td>INF. DIREITO</td><td><input id="id-red-inf-dir-mq"></td><td><input id="id-red-inf-dir-of"></td>
                    <td>INF. DIR</td><td><input id="id-cil-inf-dir-mq"></td><td><input id="id-cil-inf-dir-of"></td></tr>
                <tr><td>DIREITA:</td><td><input id="id-placa-dir-mq"></td><td><input id="id-placa-dir-of"></td>
                    <td>SUP. ESQ</td><td><input id="id-red-sup-esq-mq"></td><td><input id="id-red-sup-esq-of"></td>
                    <td>SUP. ESQ</td><td><input id="id-cil-sup-esq-mq"></td><td><input id="id-cil-sup-esq-of"></td></tr>
                <tr><td>ESQUERDA:</td><td><input id="id-placa-esq-mq"></td><td><input id="id-placa-esq-of"></td>
                    <td>INF. ESQ</td><td><input id="id-red-inf-esq-mq"></td><td><input id="id-red-inf-esq-of"></td>
                    <td>INF. ESQ</td><td><input id="id-cil-inf-esq-mq"></td><td><input id="id-cil-inf-esq-of"></td></tr>
            </tbody>
        </table>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 6. DIÂMETROS DOS ROLOS (CHEGADA e SAÍDA)
// ==============================================================
function renderizarDiametrosRolos(tipo) {
    const idContainer = tipo === 'chegada' ? 'molde23-diametros-chegada' : 'molde23-diametros-saida';
    const container = garantirContainer(idContainer);
    if (!container) return;
    const titulo = tipo === 'chegada' ? 'AO CHEGAR NA OFICINA' : 'AO SAIR DA OFICINA';
    const prefix = tipo === 'chegada' ? 'dia-c' : 'dia-s';
    const html = `
        <h4 style="color:var(--text-heading);">VERIFICAÇÃO DOS DIÂMETROS DOS ROLOS DO FOOT ROLL E EDGE ROLL ${titulo}</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>LADO FIXO</th><td><input id="${prefix}-fixo"></td>
                <th>LADO MÓVEL</th><td><input id="${prefix}-movel"></td></tr>
            <tr><th>LADO DIREITO</th><td><input id="${prefix}-dir"></td>
                <th>LADO ESQUERDO</th><td><input id="${prefix}-esq"></td></tr>
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="${prefix}-data"></div>
            <div><label>NOME: </label><input id="${prefix}-nome"></div>
            <div><label>MATRÍCULA: </label><input id="${prefix}-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 7. ALINHAMENTO DOS ROLOS
// ==============================================================
function renderizarAlinhamentoRolos() {
    const container = garantirContainer('molde23-alinhamento-rolos');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">VERIFICAÇÃO DO ALINHAMENTO DOS ROLOS</h3>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>LADO FIXO</th><td><input id="alinh-fixo"></td>
                <th>LADO MÓVEL</th><td><input id="alinh-movel"></td></tr>
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="alinh-data"></div>
            <div><label>NOME: </label><input id="alinh-nome"></div>
            <div><label>MATRÍCULA: </label><input id="alinh-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 8. SENSOR DE NÍVEL (PLANILHA E RESISTÊNCIA)
// ==============================================================
function renderizarSensorNivel() {
    const container = garantirContainer('molde23-sensor-nivel');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">PLANILHA DE AJUSTE E MEDIDAS DO SENSOR DE NÍVEL</h3>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>ITEM</th><th>DESCRIÇÃO</th><th>OK</th></tr>
            ${[1,2,3,4,5,6,7].map(i => `
                <tr><td>${i}</td><td>${['VERIFICAR TAMPA DE PROTEÇÃO;','EFETUAR A TROCA DAS GAXETAS DE ISOLAÇÃO DO SENSOR','VERIFICAR PARAFUSO DE FIXAÇÃO DO SUPORTE DO SENSOR, TORQUE 50 NM;','VERIFICAR PARAFUSO DE FIXAÇÃO DA TAMPA DE PROTEÇÃO DO SENSOR, TORQUE 40 NM;','VERIFICAR ESTADO DE CONSERVAÇÃO E LIMPEZA;','TESTE DE ESTANQUIEDADE (5 BAR);','CHECK NA CONEXÕES DE ALIMENTAÇÃO DE ÁGUA;'][i-1]}</td>
                    <td style="text-align:center;"><input type="checkbox" id="sn-${i}"></td></tr>
            `).join('')}
        </table>
        <h4>MEDIÇÃO RESISTÊNCIA NO SENSOR DE NÍVEL</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>ITEM</th><th>DESCRIÇÃO</th><th>VALOR</th></tr>
            ${[8,9,10,11,12,13,14,15].map(i => `
                <tr><td>${i}</td><td>${['VERIFICAR RESISTÊNCIA ENTRE OS PINOS 1-2 LIMITES DE Ω (140...300)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 3-4 LIMITES DE Ω (0...2)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 1-5 LIMITES DE Ω (70...150)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 3-5 LIMITES DE Ω (0...1)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 7-8 LIMITES DE Ω (0...1)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 8-9 LIMITES DE Ω (100...140)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 15-16 LIMITES DE Ω (3...10)','VERIFICAR RESISTÊNCIA NO PINO 10 E A CARCAÇA DO SENSOR LIMITE DE Ω (0...1)'][i-8]}</td>
                    <td><input id="sn-${i}"></td></tr>
            `).join('')}
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="sn-data"></div>
            <div><label>NOME: </label><input id="sn-nome"></div>
            <div><label>MATRÍCULA: </label><input id="sn-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 9. ISOLAÇÃO DOS SENSORES DE NÍVEL
// ==============================================================
function renderizarIsolamentoSensores() {
    const container = garantirContainer('molde23-isolamento');
    if (!container) return;
    const pinos = ["5 e 6","5 e 8","5 e 10","5 e 15","6 e 8","6 e 10","6 e 15","8 e 10","8 e 15","10 e 15"];
    let rows = '';
    pinos.forEach((p, i) => {
        rows += `<tr><td>${p}</td><td>>10 MΩ</td><td><input id="iso-${i}"></td></tr>`;
    });
    const html = `
        <h3 style="color:var(--text-heading);">ISOLAÇÃO DOS SENSORES DE NÍVEL DO MOLDE (MΩ)</h3>
        <p>OBS: ESCALA DE MEDIÇÃO DE 100VCA</p>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>PINO CONECTOR</th><th>LIMITE (MΩ)</th><th>VALOR MEDIDO</th></tr>
            ${rows}
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="iso-data"></div>
            <div><label>NOME: </label><input id="iso-nome"></div>
            <div><label>MATRÍCULA: </label><input id="iso-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 10. TERMOPARES
// ==============================================================
function renderizarTermopares() {
    const container = garantirContainer('molde23-termopares');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">IDENTIFICAÇÃO DAS CAIXAS DOS TERMOPARES</h3>
        <div style="display:flex; gap:20px; flex-wrap:wrap;">
            <div><h4>PLACA FIXA</h4><input id="termo-fixa" style="width:200px;"></div>
            <div><h4>PLACA MÓVEL</h4><input id="termo-movel" style="width:200px;"></div>
        </div>
        <h4>MANUTENÇÃO TERMOPARES DO MOLDE</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>DESCRIÇÃO</th><th>CONDIÇÃO</th></tr>
            <tr><td>VERIFICAR PARAFUSOS DA BASE DAS CAIXAS DOS TERMOPARES</td><td><input id="termo-cond1"></td></tr>
            <tr><td>TESTE DE AR (INDICAÇÃO WAMBOY)</td><td><input id="termo-cond2"></td></tr>
            <tr><td>ESTADO/LIMPEZA</td><td><input id="termo-cond3"></td></tr>
            <tr><td>BORRACHAS E VEDAÇÕES</td><td><input id="termo-cond4"></td></tr>
            <tr><td>TRAVAS</td><td><input id="termo-cond5"></td></tr>
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="termo-data"></div>
            <div><label>NOME: </label><input id="termo-nome"></div>
            <div><label>MATRÍCULA: </label><input id="termo-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 11. CHECK DO JB 2
// ==============================================================
function renderizarCheckJB2() {
    const container = garantirContainer('molde23-checkjb2');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">CHECK DO JB 2</h3>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>DESCRIÇÃO</th><th>STATUS</th><th>OBSERVAÇÕES</th></tr>
            <tr><td>FECHO PAINEL</td><td><select id="jb2-fecho"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="jb2-fecho-obs"></td></tr>
            <tr><td>CONECTORES DO WANBOY COM MOLDE</td><td><select id="jb2-wanboy"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="jb2-wanboy-obs"></td></tr>
            <tr><td>VEDAÇÃO DO JB 2</td><td><select id="jb2-vedacao"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="jb2-vedacao-obs"></td></tr>
        </table>
        <h4>CHECK CONECTORES DA VÁLVULA PROPORCIONAL</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>DESCRIÇÃO</th><th>STATUS</th><th>OBSERVAÇÕES</th></tr>
            <tr><td>SUPERIOR ESQUERDO</td><td><select id="vp-se"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="vp-se-obs"></td></tr>
            <tr><td>SUPERIOR DIREITO</td><td><select id="vp-sd"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="vp-sd-obs"></td></tr>
            <tr><td>INFERIOR ESQUERDO</td><td><select id="vp-ie"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="vp-ie-obs"></td></tr>
            <tr><td>INFERIOR DIREITO</td><td><select id="vp-id"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="vp-id-obs"></td></tr>
        </table>
        <h4>CHECK CONECTORES DOS TRANSDUTORES DE POSIÇÃO</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>DESCRIÇÃO</th><th>STATUS</th><th>OBSERVAÇÕES</th></tr>
            <tr><td>SUPERIOR ESQUERDO</td><td><select id="tp-se"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="tp-se-obs"></td></tr>
            <tr><td>SUPERIOR DIREITO</td><td><select id="tp-sd"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="tp-sd-obs"></td></tr>
            <tr><td>INFERIOR ESQUERDO</td><td><select id="tp-ie"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="tp-ie-obs"></td></tr>
            <tr><td>INFERIOR DIREITO</td><td><select id="tp-id"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="tp-id-obs"></td></tr>
        </table>
        <h4>BLOCO PRINCIPAL</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>DESCRIÇÃO</th><th>STATUS</th><th>OBSERVAÇÕES</th></tr>
            <tr><td>VEDAÇÕES</td><td><select id="bp-ved"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="bp-ved-obs"></td></tr>
            <tr><td>VÁLVULAS E CONECTORES</td><td><select id="bp-valv"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="bp-valv-obs"></td></tr>
            <tr><td>TRANSDUTORES (ÓLEO/AR)</td><td><select id="bp-trans"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="bp-trans-obs"></td></tr>
        </table>
        <h4>CHECK CABOS DO AJUSTE DE LARGURA DO MOLDE</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>DESCRIÇÃO</th><th>STATUS</th><th>OBSERVAÇÕES</th></tr>
            <tr><td>SUPERIOR ESQUERDO</td><td><select id="cal-se"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="cal-se-obs"></td></tr>
            <tr><td>SUPERIOR DIREITO</td><td><select id="cal-sd"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="cal-sd-obs"></td></tr>
            <tr><td>INFERIOR ESQUERDO</td><td><select id="cal-ie"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="cal-ie-obs"></td></tr>
            <tr><td>INFERIOR DIREITO</td><td><select id="cal-id"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="cal-id-obs"></td></tr>
            <tr><td>BANCO DE VÁLVULAS</td><td><select id="cal-bv"><option>NORMAL</option><option>ANORMAL</option></select></td><td><input id="cal-bv-obs"></td></tr>
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="jb2-data"></div>
            <div><label>NOME: </label><input id="jb2-nome"></div>
            <div><label>MATRÍCULA: </label><input id="jb2-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 12. RESISTÊNCIA DAS PLACAS
// ==============================================================
function renderizarResistenciaPlacas() {
    const container = garantirContainer('molde23-resistencia-placas');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">TESTE DE RESISTÊNCIA DAS PLACAS</h3>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
            <div><h4>PLACA MÓVEL</h4><input id="res-placa-movel" style="width:100%;"></div>
            <div><h4>PLACA FIXA</h4><input id="res-placa-fixa" style="width:100%;"></div>
            <div><h4>PLACA ESTREITA DIREITA</h4><input id="res-placa-est-dir" style="width:100%;"></div>
            <div><h4>PLACA ESTREITA ESQUERDA</h4><input id="res-placa-est-esq" style="width:100%;"></div>
        </div>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="res-data"></div>
            <div><label>NOME: </label><input id="res-nome"></div>
            <div><label>MATRÍCULA: </label><input id="res-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 13. PERITAGEM DAS PLACAS LARGAS (ENTRADA E SAÍDA)
// ==============================================================
function renderizarPeritagemPlacasLargas(tipo) {
    const idContainer = tipo === 'entrada' ? 'molde23-peritagem-largas-entrada' : 'molde23-peritagem-largas-saida';
    const container = garantirContainer(idContainer);
    if (!container) return;
    const titulo = tipo === 'entrada' ? 'AO ENTRAR NA OFICINA' : 'AO SAIR DA OFICINA';
    const prefix = tipo === 'entrada' ? 'pl-ent' : 'pl-sai';
    const html = `
        <h3 style="color:var(--text-heading);">PERITAGEM DAS PLACAS LARGAS ${titulo}</h3>
        <h4>FACE NORTE</h4>
        <table class="premium-table" style="font-size:9px;">
            <tr><th>1600</th><th>1300</th><th>1000</th><th>LINHA CENTRO</th><th>1000</th><th>1300</th><th>1600</th></tr>
            ${[1,2,3].map(linha => `
                <tr>${[1,2,3,4,5,6,7].map(col => `<td><input id="${prefix}-n${linha}-${col}"></td>`).join('')}</tr>
            `).join('')}
        </table>
        <h4>FACE SUL</h4>
        <table class="premium-table" style="font-size:9px;">
            <tr><th>1600</th><th>1300</th><th>1000</th><th>LINHA CENTRO</th><th>1000</th><th>1300</th><th>1600</th></tr>
            ${[1,2,3].map(linha => `
                <tr>${[1,2,3,4,5,6,7].map(col => `<td><input id="${prefix}-s${linha}-${col}"></td>`).join('')}</tr>
            `).join('')}
        </table>
        <h4>RESULTADO DO ALINHAMENTO FACE PRINCIPAL NORTE (FIXA)</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>RÉGUA LESTE</th><th>RÉGUA OESTE</th></tr>
            <tr><td>SUPERIOR (1): <input id="${prefix}-alinh-n1"></td><td>SUPERIOR (3): <input id="${prefix}-alinh-n3"></td></tr>
            <tr><td>INFERIOR (2): <input id="${prefix}-alinh-n2"></td><td>INFERIOR (4): <input id="${prefix}-alinh-n4"></td></tr>
            <tr><td colspan="2">TOLERÂNCIA (1,0+/-0,1)</td></tr>
        </table>
        <h4>RESULTADO DO ALINHAMENTO FACE PRINCIPAL SUL (MÓVEL)</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>RÉGUA LESTE</th><th>RÉGUA OESTE</th></tr>
            <tr><td>SUPERIOR (1): <input id="${prefix}-alinh-s1"></td><td>SUPERIOR (3): <input id="${prefix}-alinh-s3"></td></tr>
            <tr><td>INFERIOR (2): <input id="${prefix}-alinh-s2"></td><td>INFERIOR (4): <input id="${prefix}-alinh-s4"></td></tr>
            <tr><td colspan="2">SUPERIOR 0.1 mm E INFERIOR 0.2 mm</td></tr>
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="${prefix}-data"></div>
            <div><label>NOME: </label><input id="${prefix}-nome"></div>
            <div><label>MATRÍCULA: </label><input id="${prefix}-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 14. PERITAGEM DAS PLACAS ESTREITAS (CHEGADA E SAÍDA)
// ==============================================================
function renderizarPeritagemPlacasEstreitas(tipo) {
    const idContainer = tipo === 'chegada' ? 'molde23-peritagem-estreitas-chegada' : 'molde23-peritagem-estreitas-saida';
    const container = garantirContainer(idContainer);
    if (!container) return;
    const titulo = tipo === 'chegada' ? 'AO CHEGAR DA OFICINA' : 'AO SAIR DA OFICINA';
    const prefix = tipo === 'chegada' ? 'pe-c' : 'pe-s';
    const html = `
        <h3 style="color:var(--text-heading);">PERITAGEM DAS PLACAS ESTREITAS ${titulo}</h3>
        <div>
            <label>PLACA ESQUERDA AFASTADA: <input type="radio" name="${prefix}-esq-af" value="SIM"> SIM <input type="radio" name="${prefix}-esq-af" value="NÃO" checked> NÃO</label>
        </div>
        <div>
            <label>PLACA DIREITA AFASTADA: <input type="radio" name="${prefix}-dir-af" value="SIM"> SIM <input type="radio" name="${prefix}-dir-af" value="NÃO" checked> NÃO</label>
        </div>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>PONTO</th><th>ESQUERDA</th><th>DIREITA</th></tr>
            ${[1,2,3].map(i => `
                <tr><td>${i}</td><td><input id="${prefix}-e${i}"></td><td><input id="${prefix}-d${i}"></td></tr>
            `).join('')}
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="${prefix}-data"></div>
            <div><label>NOME: </label><input id="${prefix}-nome"></div>
            <div><label>MATRÍCULA: </label><input id="${prefix}-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 15. AJUSTE DE CHAVETAS
// ==============================================================
function renderizarAjusteChavetas() {
    const container = garantirContainer('molde23-ajuste-chavetas');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">AJUSTE DE CHAVETAS DAS PLACAS ESTREITAS</h3>
        <h4>PLACA ESQUERDA</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>Posição</th><th>LADO A</th><th>LADO B</th><th>NOME</th><th>REG</th></tr>
            <tr><td>Lado A</td><td><input id="chav-esq-a-a"></td><td><input id="chav-esq-a-b"></td><td><input id="chav-esq-a-nome"></td><td><input id="chav-esq-a-reg"></td></tr>
            <tr><td>Lado B</td><td><input id="chav-esq-b-a"></td><td><input id="chav-esq-b-b"></td><td><input id="chav-esq-b-nome"></td><td><input id="chav-esq-b-reg"></td></tr>
        </table>
        <h4>PLACA DIREITA</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>Posição</th><th>LADO A</th><th>LADO B</th><th>NOME</th><th>REG</th></tr>
            <tr><td>Lado A</td><td><input id="chav-dir-a-a"></td><td><input id="chav-dir-a-b"></td><td><input id="chav-dir-a-nome"></td><td><input id="chav-dir-a-reg"></td></tr>
            <tr><td>Lado B</td><td><input id="chav-dir-b-a"></td><td><input id="chav-dir-b-b"></td><td><input id="chav-dir-b-nome"></td><td><input id="chav-dir-b-reg"></td></tr>
        </table>
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="chav-data"></div>
            <div><label>NOME: </label><input id="chav-nome"></div>
            <div><label>MATRÍCULA: </label><input id="chav-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 16. RELATÓRIO FOLGA DE ARESTA (TODAS AS LARGURAS)
// ==============================================================
function renderizarFolgaAresta() {
    const container = garantirContainer('molde23-folga-aresta');
    if (!container) return;
    const larguras = [830,870,950,1030,1100,1180,1230,1300,1380,1460,1500,1530,1550,1580,1620];
    let html = `<h3 style="color:var(--text-heading);">RELATÓRIO FOLGA DE ARESTA</h3><p>Tolerância -- 0.25 por face.</p>`;
    larguras.forEach(l => {
        html += `
            <h4>LARGURA ${l}</h4>
            <table class="premium-table" style="font-size:9px;">
                <tr><th>POSIÇÃO</th><th>ESQUERDA</th><th>DIREITA</th></tr>
                <tr><td>SUPERIOR</td><td><input id="fa-${l}-esq-sup"></td><td><input id="fa-${l}-dir-sup"></td></tr>
                <tr><td>MEIO</td><td><input id="fa-${l}-esq-meio"></td><td><input id="fa-${l}-dir-meio"></td></tr>
                <tr><td>INFERIOR</td><td><input id="fa-${l}-esq-inf"></td><td><input id="fa-${l}-dir-inf"></td></tr>
            </table>
        `;
    });
    html += `
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="fa-data"></div>
            <div><label>NOME: </label><input id="fa-nome"></div>
            <div><label>MATRÍCULA: </label><input id="fa-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 17. AVALIAÇÃO DO SISTEMA DE RESFRIAMENTO
// ==============================================================
function renderizarResfriamento() {
    const container = garantirContainer('molde23-resfriamento');
    if (!container) return;
    const html = `
        <h3 style="color:var(--text-heading);">AVALIAÇÃO DO SISTEMA DE RESFRIAMENTO NA SAÍDA</h3>
        <h4>FACE NORTE / FIXA</h4>
        <input id="ref-norte" style="width:100%;">
        <h4>FACE SUL / MÓVEL</h4>
        <input id="ref-sul" style="width:100%;">
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin:10px 0;">
            <div><label>DATA: </label><input type="date" id="ref-data"></div>
            <div><label>NOME: </label><input id="ref-nome"></div>
            <div><label>MATRÍCULA: </label><input id="ref-matricula"></div>
        </div>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 18. MATERIAIS UTILIZADOS
// ==============================================================
function renderizarMateriais() {
    const container = garantirContainer('molde23-materiais');
    if (!container) return;
    let rows = '';
    for (let i = 1; i <= 20; i++) {
        rows += `<tr><td><input id="mat-desc-${i}" style="width:100%;"></td><td><input id="mat-qtd-${i}" style="width:60px;"></td></tr>`;
    }
    const html = `
        <h3 style="color:var(--text-heading);">MATERIAIS UTILIZADOS NA MANUTENÇÃO</h3>
        <table class="premium-table" style="font-size:10px;">
            <thead><tr><th style="width:80%;">DESCRIÇÃO DO MATERIAL / SKU</th><th style="width:20%;">QUANTIDADE</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
    `;
    container.innerHTML = html;
}

// ==============================================================
// 19. FUNÇÃO PRINCIPAL DE ABRIR O FOLHÃO
// ==============================================================
window.abrirFolhaoMolde23 = function(id) {
    ID_FOLHAO_MOLDE23_ATUAL = id;
    const modal = document.getElementById('modal-folhao-molde23');
    if (!modal) {
        console.error("Modal #modal-folhao-molde23 não encontrado!");
        alert("Erro: Modal do Molde 2/3 não encontrado. Verifique o HTML.");
        return;
    }

    // Preenche cabeçalho
    const tagNameEl = document.getElementById('molde23-tag-name');
    if (tagNameEl) tagNameEl.innerText = id;
    const dataInicio = document.getElementById('molde23-data-inicio');
    const dataFim = document.getElementById('molde23-data-fim');
    if (dataInicio) dataInicio.valueAsDate = new Date();
    if (dataFim) dataFim.valueAsDate = new Date();

    // Renderiza todas as seções (com fallback de containers)
    renderizarIdentificacao();
    renderizarChecklist('container-check-recebimento-m23', recebimentoMecanica, 'rec');
    renderizarChecklist('container-check-eletrica-m23', recebimentoEletrica, 'ele');
    renderizarChecklist('container-check-revisao-m23', revisaoMoldes, 'rev');
    renderizarChecklist('container-check-hidraulica-m23', checkHidraulico, 'hid', true);
    renderizarChecklist('container-check-final-m23', inspecaoFinal, 'fin');
    renderizarDiametrosRolos('chegada');
    renderizarDiametrosRolos('saida');
    renderizarAlinhamentoRolos();
    renderizarSensorNivel();
    renderizarIsolamentoSensores();
    renderizarTermopares();
    renderizarCheckJB2();
    renderizarResistenciaPlacas();
    renderizarPeritagemPlacasLargas('entrada');
    renderizarPeritagemPlacasLargas('saida');
    renderizarPeritagemPlacasEstreitas('chegada');
    renderizarPeritagemPlacasEstreitas('saida');
    renderizarAjusteChavetas();
    renderizarFolgaAresta();
    renderizarResfriamento();
    renderizarMateriais();

    modal.classList.remove('hidden');
};

// ==============================================================
// 20. GERAR PDF E SALVAR NO BANCO (NUVEM + PDF NATIVO) - MOLDE 2/3
// ==============================================================
window.salvarEImprimirFolhaoMolde23 = async function() {
    if (!window.verificarAcesso || !window.verificarAcesso()) { alert("Acesso negado."); return; }
    if (!ID_FOLHAO_MOLDE23_ATUAL) { alert("Nenhuma TAG carregada."); return; }

    const tag = ID_FOLHAO_MOLDE23_ATUAL;

    // 1. COLETA DADOS DO CABEÇALHO
    const lider = getV('molde23-lider') || '_______________';
    const dataInicio = getV('molde23-data-inicio') || new Date().toLocaleDateString('pt-BR');
    const dataFim = getV('molde23-data-fim') || new Date().toLocaleDateString('pt-BR');
    const numMolde = getV('molde23-num-molde') || '______';
    const motivo = getV('molde23-motivo') || '_______________';
    const tipoExec = document.getElementById('molde23-tipo-exec')?.value || 'GERAL';
    const desempenho = getV('molde23-desempenho') || '_______________';
    const novaMeta = getV('molde23-nova-meta') || 'Manter Atual'; // 🔥 PEGA A NOVA META

    // 2. PREPARA OS DADOS PARA A NUVEM
    const dadosFolhao = {
        id_peca: tag,
        tipo_equipamento: "Molde",
        tecnico: window.OPERADOR_LOGADO ? window.OPERADOR_LOGADO.nome : "Técnico",
        nova_meta: parseFloat(novaMeta) || 0,
        tipo_manutencao: tipoExec,
        dados_chegada: "{}", 
        dados_saida: "{}",
        status_reparo: "Concluido",
        pdf_base64: "" 
    };

    // 3. 🔥 OBRIGA O NAVEGADOR A ESPERAR O BANCO DE DADOS 🔥
    try {
        const resposta = await fetch("http://localhost:8000/api/salvar_folhao", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dadosFolhao)
        });
        
        const resultado = await resposta.json();
        
        if (resultado.status === "erro") {
            alert("❌ Erro no Banco de Dados: " + resultado.mensagem);
            return; 
        }
        console.log("✅ Salvo com sucesso no SQLite!");
    } catch(e) {
        console.error("Erro na Nuvem:", e);
        alert("❌ Erro de comunicação. O Python está rodando?");
        return;
    }

    // FUNÇÃO AUXILIAR PARA CHECKLISTS DO PDF
    function gerarLinhasChecklist(prefix, array, isMatricula = false) {
        let html = '';
        array.forEach((desc, i) => {
            const name = `${prefix}-${i}`;
            html += `<tr><td style="text-align:center;">${i+1}</td><td>${desc}</td>`;
            if (isMatricula) {
                html += `<td>${getV(`${name}-nome`)}</td><td>${getV(`${name}-mat`)}</td>`;
            } else {
                const val = getRadioValue(name);
                html += `<td style="text-align:center;font-weight:bold;">${val === 'SIM' ? 'X' : ''}</td><td style="text-align:center;font-weight:bold;">${val === 'NÃO' ? 'X' : ''}</td>`;
            }
            html += `</tr>`;
        });
        return html;
    }

    // 4. MONTA O HTML DO PDF
    let htmlPDF = `
    <style>
        .pdf-base { font-family: Arial, sans-serif; font-size: 9px; color: #000; }
        .pdf-base table { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
        .pdf-base th, .pdf-base td { border: 1px solid #000; padding: 3px; }
        .pdf-base th { background: #e0e0e0; text-align: center; font-weight: bold; font-size: 9px; }
        .pdf-base .titulo-secao { background: #002b5e; color: #fff; font-weight: bold; padding: 4px; text-align: left; margin: 12px 0 4px 0; border: 1px solid #000; font-size: 10px; text-transform: uppercase; }
        @media print { .quebra-pagina { break-before: page; page-break-before: always; margin-top: 10px; } }
    </style>
    <div class="pdf-base">
        <!-- Cabeçalho -->
        <div style="display: flex; border: 2px solid #000; border-bottom: 5px solid #002b5e; margin-bottom: 8px; align-items: center; background: #fff;">
            <div style="width: 20%; text-align: center; border-right: 2px solid #000; padding: 8px;"><span style="font-weight: 900; font-size: 28px; color: #002b5e; letter-spacing: -2px;">CSN</span></div>
            <div style="width: 60%; text-align: center; padding: 8px;">
                <h2 style="margin: 0; font-size: 13px; color: #000;">CHECK LIST GERAL DO MOLDE MCC 2 E 3</h2>
                <p style="margin: 4px 0 0 0; font-size: 8px; color: #333; font-weight: bold;">DATA INÍCIO: ${dataInicio} | DATA FIM: ${dataFim}</p>
            </div>
            <div style="width: 20%; font-size: 9px; border-left: 2px solid #000; padding: 8px; line-height: 1.4; font-weight: bold;">
                <div style="color: #002b5e;">MOLDE TAG: <span style="color:#000;">${tag}</span></div>
            </div>
        </div>

        <!-- 🔥 TABELA CORRIGIDA COM A NOVA META E EXECUÇÃO 🔥 -->
        <table style="margin-bottom: 15px; border: 2px solid #000;">
            <tr>
                <td style="width: 25%;"><strong>Nº MOLDE:</strong> ${numMolde}</td>
                <td style="width: 30%;"><strong>MOTIVO:</strong> ${motivo}</td>
                <td style="width: 25%; color: #002b5e;"><strong>EXECUÇÃO:</strong> ${tipoExec}</td>
                <td style="width: 20%; background-color: #f0f0f0; text-align: center;"><strong>NOVA META:</strong> ${novaMeta}</td>
            </tr>
            <tr>
                <td colspan="2"><strong>LÍDER RESPONSÁVEL:</strong> ${lider}</td>
                <td colspan="2"><strong>DESEMPENHO:</strong> ${desempenho}</td>
            </tr>
        </table>

        <!-- IDENTIFICAÇÃO -->
        <div class="titulo-secao">IDENTIFICAÇÃO</div>
        <table>
            <tr><th>PLACAS</th><th>SAÍDA MÁQUINA</th><th>SAÍDA OFICINA</th>
                <th>REDUTORES</th><th>SAIR MÁQUINA</th><th>SAIR OFICINA</th>
                <th>CILINDROS</th><th>SAIR MÁQUINA</th><th>SAIR OFICINA</th></tr>
            <tr><td>FIXA:</td><td style="text-align:center;">${getV('id-placa-fixa-mq')}</td><td style="text-align:center;">${getV('id-placa-fixa-of')}</td>
                <td>SUP DIREITO</td><td style="text-align:center;">${getV('id-red-sup-dir-mq')}</td><td style="text-align:center;">${getV('id-red-sup-dir-of')}</td>
                <td>SUP DIR</td><td style="text-align:center;">${getV('id-cil-sup-dir-mq')}</td><td style="text-align:center;">${getV('id-cil-sup-dir-of')}</td></tr>
            <tr><td>MÓVEL</td><td style="text-align:center;">${getV('id-placa-movel-mq')}</td><td style="text-align:center;">${getV('id-placa-movel-of')}</td>
                <td>INF. DIREITO</td><td style="text-align:center;">${getV('id-red-inf-dir-mq')}</td><td style="text-align:center;">${getV('id-red-inf-dir-of')}</td>
                <td>INF. DIR</td><td style="text-align:center;">${getV('id-cil-inf-dir-mq')}</td><td style="text-align:center;">${getV('id-cil-inf-dir-of')}</td></tr>
            <tr><td>DIREITA:</td><td style="text-align:center;">${getV('id-placa-dir-mq')}</td><td style="text-align:center;">${getV('id-placa-dir-of')}</td>
                <td>SUP. ESQ</td><td style="text-align:center;">${getV('id-red-sup-esq-mq')}</td><td style="text-align:center;">${getV('id-red-sup-esq-of')}</td>
                <td>SUP. ESQ</td><td style="text-align:center;">${getV('id-cil-sup-esq-mq')}</td><td style="text-align:center;">${getV('id-cil-sup-esq-of')}</td></tr>
            <tr><td>ESQUERDA:</td><td style="text-align:center;">${getV('id-placa-esq-mq')}</td><td style="text-align:center;">${getV('id-placa-esq-of')}</td>
                <td>INF. ESQ</td><td style="text-align:center;">${getV('id-red-inf-esq-mq')}</td><td style="text-align:center;">${getV('id-red-inf-esq-of')}</td>
                <td>INF. ESQ</td><td style="text-align:center;">${getV('id-cil-inf-esq-mq')}</td><td style="text-align:center;">${getV('id-cil-inf-esq-of')}</td></tr>
        </table>

        <!-- INSPEÇÃO DE RECEBIMENTO -->
        <div class="titulo-secao">1. INSPEÇÃO DE RECEBIMENTO MECÂNICA</div>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:8%;">SIM</th><th style="width:8%;">NÃO</th></tr>${gerarLinhasChecklist('rec', recebimentoMecanica)}</table>

        <div class="titulo-secao">2. INSPEÇÃO DE RECEBIMENTO ELÉTRICA</div>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:8%;">SIM</th><th style="width:8%;">NÃO</th></tr>${gerarLinhasChecklist('ele', recebimentoEletrica)}</table>

        <div class="quebra-pagina"></div>

        <!-- REVISÃO DOS MOLDES -->
        <div class="titulo-secao">3. REVISÃO DOS MOLDES</div>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:8%;">SIM</th><th style="width:8%;">NÃO</th></tr>${gerarLinhasChecklist('rev', revisaoMoldes)}</table>

        <!-- CHECK LIST HIDRÁULICO -->
        <div class="titulo-secao">4. CHECK LIST HIDRÁULICO</div>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:15%;">NOME</th><th style="width:12%;">MATRÍCULA</th></tr>${gerarLinhasChecklist('hid', checkHidraulico, true)}</table>

        <div class="quebra-pagina"></div>

        <!-- INSPEÇÃO FINAL -->
        <div class="titulo-secao">5. INSPEÇÃO FINAL DOS MOLDES</div>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:8%;">SIM</th><th style="width:8%;">NÃO</th></tr>${gerarLinhasChecklist('fin', inspecaoFinal)}</table>

        <!-- DIÂMETROS DOS ROLOS (CHEGADA) -->
        <div class="titulo-secao">6. DIÂMETROS DOS ROLOS - CHEGADA</div>
        <table><tr><th>LADO FIXO</th><td style="text-align:center;">${getV('dia-c-fixo')}</td><th>LADO MÓVEL</th><td style="text-align:center;">${getV('dia-c-movel')}</td></tr>
            <tr><th>LADO DIREITO</th><td style="text-align:center;">${getV('dia-c-dir')}</td><th>LADO ESQUERDO</th><td style="text-align:center;">${getV('dia-c-esq')}</td></tr>
        </table>
        
        <div class="titulo-secao">6.1 DIÂMETROS DOS ROLOS - SAÍDA</div>
        <table><tr><th>LADO FIXO</th><td style="text-align:center;">${getV('dia-s-fixo')}</td><th>LADO MÓVEL</th><td style="text-align:center;">${getV('dia-s-movel')}</td></tr>
            <tr><th>LADO DIREITO</th><td style="text-align:center;">${getV('dia-s-dir')}</td><th>LADO ESQUERDO</th><td style="text-align:center;">${getV('dia-s-esq')}</td></tr>
        </table>
        
        <!-- ALINHAMENTO DOS ROLOS -->
        <div class="titulo-secao">7. ALINHAMENTO DOS ROLOS</div>
        <table><tr><th>LADO FIXO</th><td style="text-align:center;">${getV('alinh-fixo')}</td><th>LADO MÓVEL</th><td style="text-align:center;">${getV('alinh-movel')}</td></tr></table>

        <div class="quebra-pagina"></div>

        <!-- SENSOR DE NÍVEL -->
        <div class="titulo-secao">8. SENSOR DE NÍVEL</div>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:8%;">OK</th></tr>
            ${[1,2,3,4,5,6,7].map(i => `<tr><td style="text-align:center;">${i}</td><td>${['VERIFICAR TAMPA DE PROTEÇÃO;','EFETUAR A TROCA DAS GAXETAS DE ISOLAÇÃO DO SENSOR','VERIFICAR PARAFUSO DE FIXAÇÃO DO SUPORTE DO SENSOR, TORQUE 50 NM;','VERIFICAR PARAFUSO DE FIXAÇÃO DA TAMPA DE PROTEÇÃO DO SENSOR, TORQUE 40 NM;','VERIFICAR ESTADO DE CONSERVAÇÃO E LIMPEZA;','TESTE DE ESTANQUIEDADE (5 BAR);','CHECK NA CONEXÕES DE ALIMENTAÇÃO DE ÁGUA;'][i-1]}</td><td style="text-align:center;">${getCheckboxValue(`sn-${i}`)==='OK'?'X':''}</td></tr>`).join('')}
        </table>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th>VALOR</th></tr>
            ${[8,9,10,11,12,13,14,15].map(i => `<tr><td style="text-align:center;">${i}</td><td>${['VERIFICAR RESISTÊNCIA ENTRE OS PINOS 1-2 LIMITES DE Ω (140...300)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 3-4 LIMITES DE Ω (0...2)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 1-5 LIMITES DE Ω (70...150)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 3-5 LIMITES DE Ω (0...1)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 7-8 LIMITES DE Ω (0...1)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 8-9 LIMITES DE Ω (100...140)','VERIFICAR RESISTÊNCIA ENTRE OS PINOS 15-16 LIMITES DE Ω (3...10)','VERIFICAR RESISTÊNCIA NO PINO 10 E A CARCAÇA DO SENSOR LIMITE DE Ω (0...1)'][i-8]}</td><td style="text-align:center;">${getV(`sn-${i}`)}</td></tr>`).join('')}
        </table>

        <!-- ISOLAÇÃO DOS SENSORES -->
        <div class="titulo-secao">9. ISOLAÇÃO DOS SENSORES DE NÍVEL</div>
        <table><tr><th>PINO CONECTOR</th><th>LIMITE</th><th>VALOR</th></tr>
            ${["5 e 6","5 e 8","5 e 10","5 e 15","6 e 8","6 e 10","6 e 15","8 e 10","8 e 15","10 e 15"].map((p,i) => `<tr><td style="text-align:center;">${p}</td><td style="text-align:center;">>10 MΩ</td><td style="text-align:center;">${getV(`iso-${i}`)}</td></tr>`).join('')}
        </table>

        <div class="quebra-pagina"></div>

        <!-- TERMOPARES -->
        <div class="titulo-secao">10. TERMOPARES</div>
        <table><tr><th>DESCRIÇÃO</th><th>CONDIÇÃO</th></tr>
            <tr><td>VERIFICAR PARAFUSOS DA BASE DAS CAIXAS DOS TERMOPARES</td><td style="text-align:center;">${getV('termo-cond1')}</td></tr>
            <tr><td>TESTE DE AR (INDICAÇÃO WAMBOY)</td><td style="text-align:center;">${getV('termo-cond2')}</td></tr>
            <tr><td>ESTADO/LIMPEZA</td><td style="text-align:center;">${getV('termo-cond3')}</td></tr>
            <tr><td>BORRACHAS E VEDAÇÕES</td><td style="text-align:center;">${getV('termo-cond4')}</td></tr>
            <tr><td>TRAVAS</td><td style="text-align:center;">${getV('termo-cond5')}</td></tr>
        </table>

        <!-- CHECK JB2 -->
        <div class="titulo-secao">11. CHECK DO JB 2 E VÁLVULAS</div>
        <table><tr><th>DESCRIÇÃO (VÁLVULA PROPORCIONAL)</th><th>STATUS</th><th>OBS</th></tr>
            <tr><td>SUPERIOR ESQUERDO</td><td style="text-align:center;">${getV('vp-se')}</td><td>${getV('vp-se-obs')}</td></tr>
            <tr><td>SUPERIOR DIREITO</td><td style="text-align:center;">${getV('vp-sd')}</td><td>${getV('vp-sd-obs')}</td></tr>
            <tr><td>INFERIOR ESQUERDO</td><td style="text-align:center;">${getV('vp-ie')}</td><td>${getV('vp-ie-obs')}</td></tr>
            <tr><td>INFERIOR DIREITO</td><td style="text-align:center;">${getV('vp-id')}</td><td>${getV('vp-id-obs')}</td></tr>
        </table>

        <!-- RESISTÊNCIA DAS PLACAS -->
        <div class="titulo-secao">12. TESTE DE RESISTÊNCIA DAS PLACAS</div>
        <table><tr><th>PLACA MÓVEL</th><th>PLACA FIXA</th><th>ESTREITA DIR</th><th>ESTREITA ESQ</th></tr>
            <tr><td style="text-align:center;">${getV('res-placa-movel')}</td><td style="text-align:center;">${getV('res-placa-fixa')}</td><td style="text-align:center;">${getV('res-placa-est-dir')}</td><td style="text-align:center;">${getV('res-placa-est-esq')}</td></tr>
        </table>

        <div class="quebra-pagina"></div>

        <!-- PERITAGEM LARGAS - ENTRADA -->
        <div class="titulo-secao">13. PERITAGEM PLACAS LARGAS - ENTRADA / SAÍDA</div>
        <table><tr><th colspan="7">FACE NORTE - ENTRADA</th></tr><tr><th>1600</th><th>1300</th><th>1000</th><th>LINHA CENTRO</th><th>1000</th><th>1300</th><th>1600</th></tr>
            ${[1,2,3].map(l => `<tr>${[1,2,3,4,5,6,7].map(c => `<td style="text-align:center;">${getV(`pl-ent-n${l}-${c}`)}</td>`).join('')}</tr>`).join('')}
        </table>
        
        <!-- PERITAGEM ESTREITAS -->
        <div class="titulo-secao">14. PERITAGEM PLACAS ESTREITAS - CHEGADA / SAÍDA</div>
        <div>ESQ AFASTADA: ${getRadioValue('pe-c-esq-af')} | DIR AFASTADA: ${getRadioValue('pe-c-dir-af')}</div>
        <table><tr><th>PONTO</th><th>ESQUERDA</th><th>DIREITA</th></tr>
            ${[1,2,3].map(i => `<tr><td style="text-align:center;">${i}</td><td style="text-align:center;">${getV(`pe-c-e${i}`)}</td><td style="text-align:center;">${getV(`pe-c-d${i}`)}</td></tr>`).join('')}
        </table>

        <!-- AJUSTE DE CHAVETAS E RESFRIAMENTO -->
        <div class="titulo-secao">15. AJUSTE DE CHAVETAS</div>
        <table><tr><th>PLACA</th><th>LADO</th><th>A</th><th>B</th><th>NOME</th><th>REG</th></tr>
            <tr><td rowspan="2" style="text-align:center;font-weight:bold;">ESQUERDA</td><td style="text-align:center;">A</td><td style="text-align:center;">${getV('chav-esq-a-a')}</td><td style="text-align:center;">${getV('chav-esq-a-b')}</td><td style="text-align:center;">${getV('chav-esq-a-nome')}</td><td style="text-align:center;">${getV('chav-esq-a-reg')}</td></tr>
            <tr><td style="text-align:center;">B</td><td style="text-align:center;">${getV('chav-esq-b-a')}</td><td style="text-align:center;">${getV('chav-esq-b-b')}</td><td style="text-align:center;">${getV('chav-esq-b-nome')}</td><td style="text-align:center;">${getV('chav-esq-b-reg')}</td></tr>
            <tr><td rowspan="2" style="text-align:center;font-weight:bold;">DIREITA</td><td style="text-align:center;">A</td><td style="text-align:center;">${getV('chav-dir-a-a')}</td><td style="text-align:center;">${getV('chav-dir-a-b')}</td><td style="text-align:center;">${getV('chav-dir-a-nome')}</td><td style="text-align:center;">${getV('chav-dir-a-reg')}</td></tr>
            <tr><td style="text-align:center;">B</td><td style="text-align:center;">${getV('chav-dir-b-a')}</td><td style="text-align:center;">${getV('chav-dir-b-b')}</td><td style="text-align:center;">${getV('chav-dir-b-nome')}</td><td style="text-align:center;">${getV('chav-dir-b-reg')}</td></tr>
        </table>
        
        <div class="titulo-secao">16. AVALIAÇÃO DO SISTEMA DE RESFRIAMENTO</div>
        <div><strong>FACE NORTE / FIXA:</strong> ${getV('ref-norte')}</div>
        <div><strong>FACE SUL / MÓVEL:</strong> ${getV('ref-sul')}</div>

        <!-- ASSINATURAS -->
        <div style="margin-top:40px; display:flex; justify-content:space-around; text-align:center; font-size:10px; font-weight:bold;">
            <div><p>___________________________________</p><p>Assinatura Mecânica</p></div>
            <div><p>___________________________________</p><p>Assinatura Elétrica</p></div>
            <div><p>___________________________________</p><p>Inspetor de Qualidade</p></div>
        </div>
    </div>`;

    // 5. IMPRIME E ATUALIZA A INTERFACE (SÓ DEPOIS DO BANCO SALVAR)
    const printDiv = document.getElementById('print-content');
    if (!printDiv) { alert("Div 'print-content' não encontrada!"); return; }
    printDiv.innerHTML = htmlPDF;
    
    window.fecharFolhaoMolde23();
    if (typeof renderReparos === 'function') renderReparos();
    if (typeof renderReservas === 'function') renderReservas();
    if (typeof renderAtivos === 'function') renderAtivos();
    if (typeof window.calcularKpisGlobais === 'function') window.calcularKpisGlobais();
    
    setTimeout(() => window.print(), 500);
};

// ==============================================================
// 21. FUNÇÕES DE FECHAR E TROCAR ABA
// ==============================================================
window.fecharFolhaoMolde23 = function() {
    const modal = document.getElementById('modal-folhao-molde23');
    if (modal) modal.classList.add('hidden');
    ID_FOLHAO_MOLDE23_ATUAL = null;
};

window.trocarAbaMolde23 = function(evt, abaId) {
    const modal = document.getElementById('modal-folhao-molde23');
    if (!modal) return;
    modal.querySelectorAll('.folhao-content').forEach(c => c.classList.add('hidden'));
    modal.querySelectorAll('.folhao-tab').forEach(b => b.classList.remove('active'));
    const aba = document.getElementById(abaId);
    if (aba) aba.classList.remove('hidden');
    if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');
};

console.log("✅ folhaoMolde23.js carregado com todas as seções e campos.");