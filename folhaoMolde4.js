// ==============================================================
// folhaoMolde4.js - Módulo completo para BENDER e MOLDE MCC 4
// ==============================================================

import { BANCO_ATIVOS } from './banco.js';
import { renderAtivos, renderReparos, renderReservas } from './ui.js';
import { gerarTelasBenderHTML, imprimirPDFBender } from './folhao_bender.js';

let ID_FOLHAO_ATUAL = null;

// ==============================================================
// FUNÇÕES AUXILIARES
// ==============================================================
export function getV(id) {
    let el = document.getElementById(id);
    return el ? el.value : '';
}

export function getRadioValue(name) {
    const radios = document.getElementsByName(name);
    for (let r of radios) if (r.checked) return r.value;
    return 'NÃO';
}

export function getCheckboxValue(id) {
    const el = document.getElementById(id);
    return el && el.checked ? 'OK' : '';
}

export function fecharFolhaoMCC4() {
    const modal = document.getElementById("modal-folhao-mcc4");
    if (modal) modal.classList.add("hidden");
    ID_FOLHAO_ATUAL = null;
}

export function fecharFolhaoMolde4() {
    const modal = document.getElementById("modal-folhao-molde4");
    if (modal) modal.classList.add("hidden");
    ID_FOLHAO_ATUAL = null;
}

export function trocarAbaFolhao(event, idAba) {
    const modal = document.getElementById("modal-folhao-mcc4");
    if (!modal) return;
    modal.querySelectorAll('.folhao-content').forEach(c => c.classList.add('hidden'));
    modal.querySelectorAll('.folhao-tab').forEach(t => t.classList.remove('active'));
    let aba = document.getElementById(idAba);
    if (aba) aba.classList.remove('hidden');
    if (event) event.currentTarget.classList.add('active');
}

export function trocarAbaMolde4(event, idAba) {
    const modal = document.getElementById('modal-folhao-molde4');
    if (!modal) return;
    modal.querySelectorAll('.folhao-content').forEach(c => c.classList.add('hidden'));
    modal.querySelectorAll('.folhao-tab').forEach(t => t.classList.remove('active'));
    let aba = document.getElementById(idAba);
    if (aba) aba.classList.remove('hidden');
    if (event) event.currentTarget.classList.add('active');
}

export function renderizarChecklist(categoriasObj, containerId, prefix) {
    const container = document.getElementById(containerId);
    if (!container) return;
    let html = "", groupIndex = 0;
    for (const [cat, perguntas] of Object.entries(categoriasObj)) {
        html += `<h4 style="margin:20px 0 10px; color:var(--text-accent); border-bottom:1px dashed var(--border-color);">${cat}</h4><div class="checklist-container">`;
        perguntas.forEach((p, idx) => {
            let name = `${prefix}-g${groupIndex}-q${idx}`;
            html += `<div class="check-item"><p>${idx + 1}. ${p}</p><div class="check-options"><label><input type="radio" name="${name}" value="SIM" checked> SIM</label><label><input type="radio" name="${name}" value="NÃO"> NÃO</label></div></div>`;
        });
        html += `</div>`;
        groupIndex++;
    }
    container.innerHTML = html;
}

// ==============================================================
// PREPARAR ABAS DINÂMICAS PARA O BENDER
// ==============================================================
function prepararAbasDinamicamente(tipoUpper) {
    const modal = document.getElementById("modal-folhao-mcc4");
    if (!modal) {
        console.error("Modal MCC4 não encontrado para adicionar abas dinâmicas.");
        return;
    }
    let tabsContainer = modal.querySelector('.folhao-tabs');
    let bodyContainer = modal.querySelector('.folhao-body');
    if (!tabsContainer || !bodyContainer) return;

    // Remove abas e conteúdos antigos (para evitar duplicação)
    modal.querySelectorAll('.tab-dinamica, .content-dinamico').forEach(el => el.remove());

    if (tipoUpper === "BENDER") {
        tabsContainer.innerHTML += `
            <button class="folhao-tab tab-dinamica" onclick="window.trocarAbaFolhao(event, 'bender-chegada')">3. Chegada</button>
            <button class="folhao-tab tab-dinamica" onclick="window.trocarAbaFolhao(event, 'bender-execucao')">4. Execução</button>
            <button class="folhao-tab tab-dinamica" onclick="window.trocarAbaFolhao(event, 'bender-saida')">5. Saída</button>
            <button class="folhao-tab tab-dinamica" onclick="window.trocarAbaFolhao(event, 'aba-materiais-geral')">6. Materiais</button>
        `;
        bodyContainer.innerHTML += gerarTelasBenderHTML();
    }
}

// ==============================================================
// DADOS DOS CHECKLISTS - MOLDE MCC 4 (IDÊNTICO AO DOCUMENTO)
// ==============================================================
const checklistsM4 = {
    recebimentoMecanica: [
        "Os engates rápidos para abertura da face móvel estão completos e em perfeitas condições?",
        "Os engates rápidos para o sistema de lubrificação estão completos e em perfeitas condições?",
        "Os flexíveis das guias laterais estão amassados e/ou danificados?",
        "Os flexíveis das guias laterais estão amassados e/ou danificados? (Duplicado doc original)",
        "As tubulações hidráulicas e de lubrificação estão em perfeitas condições?",
        "Os protetores sanfonados dos fusos e tubos telescópicos das placas laterais estão danificados?",
        "As cangalhas de spray estão 'OK' sem avarias?",
        "Há avarias nas mangueiras e tubulação de lubrificação dos foot rolls e guias laterais?",
        "As réguas de guia das placas laterais estão em perfeitas condições?",
        "Ao executar o teste de movimentação das laterais houve ruídos?",
        "Ao realizar o teste hidrostático nas placas foi identificados vazamentos?",
        "Ao realizar o teste de spray, ocorreu obstrução de bicos?"
    ],
    recebimentoEletrica: [
        "Os conectores do detector de break-out das faces larga estão tampados e em perfeitas condições?",
        "Os cabos elétricos dos termopares do detector de break-out das faces estreitas estão em perfeitas condições?"
    ],
    revisao: [
        "Retirar os parafusos de fixação dos foot rolls e guias laterais;",
        "Fazer acabamento e recondicionar roscas.",
        "Ajustar chavetas das guias dos rolos laterais e bases dos foot-rolls.",
        "Desmontar réguas guias das laterais, lixar, desempenar e recompor c/ solda se necessário",
        "Calibrar com 0.40mm a folga da arruela dos parafusos de fixação da face larga móvel.",
        "Desobstruir dreno na tampa das hastes do cilindro do clamp",
        "Ajustar as 04 porcas castelo da haste do cilindro de clamp da face larga móvel.",
        "Limpar e ajustar os parafusos de alinhamento das bases (guias laterais).",
        "Limpar faces de apoio das placas largas e estreitas e montar o'ring.",
        "Fazer inspeção visual em todo o sistema hidráulico e relatar anomalias.",
        "Verificar e reparar pinos travas dos eixos KARDANS, lubrificar, ajustar estrias e pintá-los.",
        "Desmontar proteção sanfonada dos fusos, inspecionar e lubrificar os mesmos.",
        "Substituir proteção sanfonada danificada.",
        "Limpar e ajustar calços para alinhamento dos foot roll.",
        "Ajustar e lubrificar o parafuso excêntrico de alinhamento do molde na máquina.",
        "Fixar e ajustar placa suporte do parafuso de fixação do molde na máquina, com 1mm.",
        "folga entre a placa e a estrutura do molde.",
        "Inspecionar folgas nas caixas de engrenagem das placas laterais.",
        "Lubrificar total, verificando o perfeito funcionamento das válvulas distribuidoras de graxa.",
        "Fazer inspeção nas roscas para fixação das placas laterais (back up)",
        "Verificar torque de aperto dos parafusos tipo feno dos eixos cardans - 25 Nm"
    ],
    inspecaoFinal: [
        {num: 1, text: "Esquadramento das faces estreitas está na tolerância de 0.1mm?"},
        {num: 2, text: "Alinhamento do molde em relação ao gabarito do stand está correto?"},
        {num: 3, text: "A folga nas arruelas dos parafusos de fixação da placa móvel estão entre 0.3mm a 0.5mm?"},
        {num: 4, text: "A folga máxima entre as placas laterais e largas é de 0.25mm?"},
        {num: 5, text: "Os encaixes dos eixos cardans nos motores foram feitos sem interferência?"},
        {num: 6, text: "As marcações dos centros das placas largas estão legíveis?"},
        {num: 7, text: "Tubos telescópios sem vazamentos? (Analisado com 7kgf/cm2)."},
        {num: 8, text: "Os protetores sanfonados estão em bom estado de conservação?"},
        {num: 9, text: "Os engates rápidos estão apertados e protegidos?"},
        {num: 11, text: "Os eixos cardan estão limpos, lubrificados e protegidos?"},
        {num: 12, text: "Os leques dos sprays estão corretamente alinhados e sem obstrução?"},
        {num: 13, text: "Não houve vazamento durante o teste hidrostático com 10 bar de pressão durante 30min."},
        {num: 14, text: "Foot Rolls e roletes das guias laterais estão lubrificados e girando normalmente?"},
        {num: 15, text: "As tampas de proteção dos parafusos do foot roll estão montadas?"},
        {num: 16, text: "Os parafusos M36 alinhados na elevação de 1640mm ~3mm a partir do pé do molde?"},
        {num: 17, text: "Cavidade interna do molde e rolos limpos?"},
        {num: 18, text: "Cilindros hidráulicos do sistema do clamp foi feito sangria?"}
    ],
    hidraulico: [
        "CHECK DOS CILINDROS DO CLAMP",
        "VERIFICAR VAZAMENTO DE GRAXA NAS CONEXÕES",
        "VERIFICAR VAZAMENTO DE ÓLEO NAS CONEXÕES",
        "INSPECIONAR O ELEMENTO FILTRANTE DA LINHA DE PRESSÃO HIDRÁULICA.",
        "LUBRIFICAÇÃO",
        "VERIFICAR VAZAMENTO EM MANGUEIRAS E DOSADOR, SUBSTITUIR SE NECESSÁRIO.",
        "EFETUAR A LIMPEZA DOS ENGATES HIDRÁULICOS",
        "EMBALAR ENGATES HIDRÁULICOS"
    ]
};

// ==============================================================
// FUNÇÕES DE RENDERIZAÇÃO - MOLDE MCC 4
// ==============================================================
function renderizarTabelaSimNaoM4(containerId, array, prefix, isFinal = false) {
    const container = document.getElementById(containerId);
    if (!container) return;
    let html = `<table class="premium-table" style="font-size:10px;">
        <thead><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th>`;
    if (isFinal) html += `<th style="width:15%;">MEDIDA ENCONTRADA</th>`;
    html += `<th style="width:8%;">SIM</th><th style="width:8%;">NÃO</th></tr></thead><tbody>`;
    array.forEach((item, i) => {
        const desc = isFinal ? item.text : item;
        const num = isFinal ? item.num : (i + 1);
        const name = `${prefix}-${i}`;
        html += `<tr><td style="text-align:center;font-weight:bold;">${num}</td><td>${desc}</td>`;
        if (isFinal) html += `<td><input id="${name}-med" class="w-100"></td>`;
        html += `<td style="text-align:center;"><input type="radio" name="${name}" value="SIM" checked></td>
                 <td style="text-align:center;"><input type="radio" name="${name}" value="NÃO"></td></tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML += html;
}

function renderizarM4Identificacao() {
    const container = document.getElementById('container-m4-identificacao');
    if (!container) return;
    container.innerHTML = `
        <h3 style="color:var(--text-heading);">IDENTIFICAÇÃO DE COMPONENTES</h3>
        <table class="premium-table" style="font-size:10px;">
            <thead><tr><th>PLACAS</th><th>SAÍDA MÁQUINA</th><th>SAÍDA OFICINA</th>
                <th>REDUTORES</th><th>SAIR MÁQUINA</th><th>SAIR OFICINA</th>
                <th>CILINDROS</th><th>SAIR MÁQUINA</th><th>SAIR OFICINA</th></tr></thead>
            <tbody>
                <tr><td>FIXA:</td><td><input id="m4-id-pl-fixa-mq"></td><td><input id="m4-id-pl-fixa-of"></td>
                    <td>SUP DIREITO</td><td><input id="m4-id-red-sd-mq"></td><td><input id="m4-id-red-sd-of"></td>
                    <td>SUP DIR</td><td><input id="m4-id-cil-sd-mq"></td><td><input id="m4-id-cil-sd-of"></td></tr>
                <tr><td>MÓVEL</td><td><input id="m4-id-pl-movel-mq"></td><td><input id="m4-id-pl-movel-of"></td>
                    <td>INF DIREITO</td><td><input id="m4-id-red-id-mq"></td><td><input id="m4-id-red-id-of"></td>
                    <td>INF DIR</td><td><input id="m4-id-cil-id-mq"></td><td><input id="m4-id-cil-id-of"></td></tr>
                <tr><td>DIREITA:</td><td><input id="m4-id-pl-dir-mq"></td><td><input id="m4-id-pl-dir-of"></td>
                    <td>SUP ESQ</td><td><input id="m4-id-red-se-mq"></td><td><input id="m4-id-red-se-of"></td>
                    <td>SUP ESQ</td><td><input id="m4-id-cil-se-mq"></td><td><input id="m4-id-cil-se-of"></td></tr>
                <tr><td>ESQUERDA:</td><td><input id="m4-id-pl-esq-mq"></td><td><input id="m4-id-pl-esq-of"></td>
                    <td>INF ESQ</td><td><input id="m4-id-red-ie-mq"></td><td><input id="m4-id-red-ie-of"></td>
                    <td>INF ESQ</td><td><input id="m4-id-cil-ie-mq"></td><td><input id="m4-id-cil-ie-of"></td></tr>
            </tbody>
        </table>
    `;
}

function renderizarM4AjustesHidraulica() {
    const container = document.getElementById('container-m4-ajustes');
    if (!container) return;
    
    let htmlHidr = `<table class="premium-table" style="font-size:10px;"><thead><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO (HIDRÁULICA)</th><th>NOME</th><th>MATRÍCULA</th></tr></thead><tbody>`;
    checklistsM4.hidraulico.forEach((desc, i) => {
        htmlHidr += `<tr><td style="text-align:center;">${i+1}</td><td>${desc}</td><td><input id="m4-hid-nome-${i}" class="w-100"></td><td><input id="m4-hid-mat-${i}" class="w-100"></td></tr>`;
    });
    htmlHidr += `</tbody></table>`;

    container.innerHTML = `
        <h3 style="color:var(--text-heading);">PLANILHA DE AJUSTE E MEDIDAS NOMINAIS</h3>
        <table class="premium-table" style="font-size:10px;">
            <thead><tr><th>ITEM</th><th>DESCRIÇÃO</th><th>NOMINAL</th><th>REAL</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>APERTO DO PARAFUSO EXCÊNTRICO (DIR/ESQ)</td><td>-</td><td>Dir: <input id="m4-aj-exc-dir" style="width:80px;"> Esq: <input id="m4-aj-exc-esq" style="width:80px;"></td></tr>
                <tr><td>2</td><td>TORQUE PARAFUSO FIXAÇÃO FOOT ROLL</td><td>300 + 5 Nm</td><td><input id="m4-aj-tfr"></td></tr>
                <tr><td>3</td><td>TORQUE PARAFUSO FIXAÇÃO PLACA LATERAL</td><td>200 + 5 Nm</td><td><input id="m4-aj-tpl"></td></tr>
                <tr><td>4</td><td>TIRANTE FIXAÇÃO GUIAS LATERAIS</td><td>100 Nm</td><td><input id="m4-aj-tir"></td></tr>
                <tr><td>5</td><td>FOLGA GABARITO CLAMP (SUP/INF) - Ø250</td><td>1,60 ± 0,15 mm</td><td>Sup: <input id="m4-aj-clp-sup" style="width:80px;"> Inf: <input id="m4-aj-clp-inf" style="width:80px;"></td></tr>
            </tbody>
        </table>
        <h3 style="color:var(--text-heading); margin-top:20px;">CHECK LIST HIDRÁULICO E ELÉTRICO</h3>
        ${htmlHidr}
        <div style="margin-top:10px;">
            <strong>CHECK ELÉTRICO:</strong> OS CONECTORES DO DBO E VUHZ ESTÃO LIMPOS, TAMPONADOS E PROTEGIDOS? 
            <input id="m4-ele-nome" placeholder="Nome" style="margin-left:10px;"> <input id="m4-ele-mat" placeholder="Matrícula">
        </div>
    `;
}

function renderizarM4Rolos() {
    const container = document.getElementById('container-m4-rolos');
    if (!container) return;
    
    const secRolos = (titulo, prefix) => `
        <h4 style="margin-top:15px; color:var(--text-accent);">${titulo}</h4>
        <div style="display:flex; gap:20px; align-items:center; margin-bottom:5px;">
            <label>Lado Esq Afastado: <input type="radio" name="m4-${prefix}-esq-af" value="SIM"> SIM <input type="radio" name="m4-${prefix}-esq-af" value="NÃO" checked> NÃO</label>
            <label>Lado Dir Afastado: <input type="radio" name="m4-${prefix}-dir-af" value="SIM"> SIM <input type="radio" name="m4-${prefix}-dir-af" value="NÃO" checked> NÃO</label>
        </div>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>LADO FIXO</th><td><input id="m4-${prefix}-fixo"></td><th>LADO MÓVEL</th><td><input id="m4-${prefix}-movel"></td></tr>
            <tr><th>LADO DIREITO</th><td><input id="m4-${prefix}-dir"></td><th>LADO ESQUERDO</th><td><input id="m4-${prefix}-esq"></td></tr>
        </table>
    `;

    const secAlinhamento = `
        <h4 style="margin-top:20px; color:var(--text-accent);">ALINHAMENTO DOS ROLOS (F1, F2, F3 - Tolerância ±0.1mm)</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>FACE</th><th>F1 (0,00mm)</th><th>F2 (0,00mm)</th><th>F3 (0,00mm)</th></tr>
            <tr><td>FIXA</td><td><input id="m4-alinh-fixa-f1"></td><td><input id="m4-alinh-fixa-f2"></td><td><input id="m4-alinh-fixa-f3"></td></tr>
            <tr><td>MÓVEL</td><td><input id="m4-alinh-mov-f1"></td><td><input id="m4-alinh-mov-f2"></td><td><input id="m4-alinh-mov-f3"></td></tr>
        </table>
    `;

    container.innerHTML = `
        <h3 style="color:var(--text-heading);">DIÂMETROS E ALINHAMENTO (FOOT ROLL E EDGE ROLL)</h3>
        ${secRolos('DIÂMETROS - CHEGADA NA OFICINA', 'dia-c')}
        ${secRolos('DIÂMETROS - SAÍDA DA OFICINA', 'dia-s')}
        ${secAlinhamento}
    `;
}

function renderizarM4SensorResist() {
    const containerSn = document.getElementById('container-m4-sensor');
    const containerRes = document.getElementById('container-m4-resist');
    if (!containerSn || !containerRes) return;

    containerSn.innerHTML = `
        <h3 style="color:var(--text-heading);">PLANILHA DE AJUSTE SENSOR DE NÍVEL</h3>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>ITEM</th><th>DESCRIÇÃO</th><th>OK</th></tr>
            ${[1,2,3,4,5,6,7].map(i => `<tr><td style="text-align:center;">${i}</td><td>${['VERIFICAR TAMPA DE PROTEÇÃO;','EFETUAR A TROCA DAS GAXETAS DE ISOLAÇÃO DO SENSOR','VERIFICAR PARAFUSO DE FIXAÇÃO DO SUPORTE DO SENSOR, TORQUE 50 NM;','VERIFICAR PARAFUSO DE FIXAÇÃO DA TAMPA DE PROTEÇÃO DO SENSOR, TORQUE 40 NM;','VERIFICAR ESTADO DE CONSERVAÇÃO E LIMPEZA;','TESTE DE ESTANQUIEDADE (5 BAR);','CHECK NA CONEXÕES DE ALIMENTAÇÃO DE ÁGUA;'][i-1]}</td><td style="text-align:center;"><input type="checkbox" id="m4-sn-${i}"></td></tr>`).join('')}
        </table>
        <h4 style="margin-top:15px;">MEDIÇÃO RESISTÊNCIA NO SENSOR</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>ITEM</th><th>PINOS</th><th>LIMITES (Ω)</th><th>VALOR</th></tr>
            ${[['1-2','140...300'],['3-4','0...2'],['1-5','70...150'],['3-5','0...1'],['7-8','0...1'],['8-9','100...140'],['15-16','3...10'],['Pino 10 / Carcaça','0...1']].map((p,i) => `<tr><td style="text-align:center;">${i+8}</td><td>${p[0]}</td><td>${p[1]}</td><td><input id="m4-sn-res-${i+8}"></td></tr>`).join('')}
        </table>
        <h4 style="margin-top:15px;">ISOLAÇÃO DOS SENSORES (MΩ)</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>PINOS</th><th>>10 MΩ</th><th>VALOR MEDIDO</th></tr>
            ${["5 e 6","5 e 8","5 e 10","5 e 15","6 e 8","6 e 10","6 e 15","8 e 10","8 e 15","10 e 15"].map((p,i) => `<tr><td style="text-align:center;">${p}</td><td>>10 MΩ</td><td><input id="m4-sn-iso-${i}"></td></tr>`).join('')}
        </table>
    `;

    let htmlTermopares = `<table class="premium-table" style="font-size:10px; width:100%;"><tr><th>TERMOPAR</th><th>FACE FIXA (10-30 Ω)</th><th>FACE MÓVEL (10-30 Ω)</th></tr>`;
    for(let i=1; i<=12; i++) {
        htmlTermopares += `<tr><td style="text-align:center;font-weight:bold;">T${i}</td><td><input id="m4-termo-f-${i}" class="w-100"></td><td><input id="m4-termo-m-${i}" class="w-100"></td></tr>`;
    }
    htmlTermopares += `</table>`;

    containerRes.innerHTML = `
        <h3 style="color:var(--text-heading);">TESTE DE RESISTÊNCIA DAS PLACAS (TERMOPARES)</h3>
        <div style="display:flex; gap:20px; justify-content:space-between; flex-wrap:wrap;">
            <div style="width:48%; min-width:300px;">
                ${htmlTermopares}
            </div>
            <div style="width:48%; min-width:300px;">
                <h4 style="margin-bottom:10px;">PLACAS ESTREITAS</h4>
                <table class="premium-table" style="font-size:10px;">
                    <tr><th>LADO</th><th>T1 (10-30 Ω)</th><th>T2 (10-30 Ω)</th></tr>
                    <tr><td>DIREITA</td><td><input id="m4-termo-ed-1" class="w-100"></td><td><input id="m4-termo-ed-2" class="w-100"></td></tr>
                    <tr><td>ESQUERDA</td><td><input id="m4-termo-ee-1" class="w-100"></td><td><input id="m4-termo-ee-2" class="w-100"></td></tr>
                </table>
                <h4 style="margin-top:20px; margin-bottom:10px;">VERIFICAÇÃO CAIXAS TERMOPARES</h4>
                <table class="premium-table" style="font-size:10px;">
                    <tr><th>DESCRIÇÃO</th><th>CONDIÇÃO</th></tr>
                    <tr><td>PARAFUSOS BASE</td><td><input id="m4-tc-1" class="w-100"></td></tr>
                    <tr><td>TESTE DE AR</td><td><input id="m4-tc-2" class="w-100"></td></tr>
                    <tr><td>ESTADO/LIMPEZA</td><td><input id="m4-tc-3" class="w-100"></td></tr>
                    <tr><td>BORRACHAS/VED.</td><td><input id="m4-tc-4" class="w-100"></td></tr>
                    <tr><td>TRAVAS</td><td><input id="m4-tc-5" class="w-100"></td></tr>
                </table>
            </div>
        </div>
    `;
}

function renderizarM4PeritagemLargas() {
    const container = document.getElementById('container-m4-peritagem-l');
    if (!container) return;
    
    const renderTable = (titulo, prefix) => `
        <h4 style="margin-top:15px; color:var(--text-accent);">${titulo}</h4>
        <div style="margin-bottom:10px;">
            <label style="margin-right:15px;">PLACA FIXA AFASTADA: <input type="radio" name="${prefix}-fixa-afast" value="SIM"> SIM <input type="radio" name="${prefix}-fixa-afast" value="NÃO" checked> NÃO</label>
            <label>PLACA MÓVEL AFASTADA: <input type="radio" name="${prefix}-movel-afast" value="SIM"> SIM <input type="radio" name="${prefix}-movel-afast" value="NÃO" checked> NÃO</label>
        </div>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>DESCRIÇÃO</th><th>TOLERÂNCIA</th><th>PLACA FIXA</th><th>PLACA MÓVEL</th></tr>
            <tr><td>PLANICIDADE VERTICAL (F)</td><td>< 0,2mm</td><td><input id="${prefix}-fv-fixa"></td><td><input id="${prefix}-fv-movel"></td></tr>
            <tr><td>PLANICIDADE HORIZONTAL (G)</td><td>< 0,2mm</td><td><input id="${prefix}-fh-fixa"></td><td><input id="${prefix}-fh-movel"></td></tr>
            <tr><td>PROFUNDIDADE DE RANHURAS (P)</td><td>< 1mm</td><td><input id="${prefix}-pr-fixa"></td><td><input id="${prefix}-pr-movel"></td></tr>
            <tr><td>DESGASTE (A)</td><td>< 1mm</td><td><input id="${prefix}-da-fixa"></td><td><input id="${prefix}-da-movel"></td></tr>
        </table>
    `;

    container.innerHTML = `
        <h3 style="color:var(--text-heading);">PERITAGEM PLACAS LARGAS</h3>
        ${renderTable('AO ENTRAR NA OFICINA', 'm4-per-ent')}
        ${renderTable('AO SAIR DA OFICINA', 'm4-per-sai')}
    `;
}

function renderizarM4PeritagemEstreitas() {
    const container = document.getElementById('container-m4-peritagem-e');
    if (!container) return;
    
    const secEstreitas = (titulo, prefix) => `
        <h4 style="margin-top:15px; color:var(--text-accent);">${titulo}</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>MEDIDA</th><th>FACE SUL (ESQ)</th><th>FACE NORTE (DIR)</th></tr>
            ${['A (Desgaste topo)','B (Desgaste base)','C (Comprimento)','D (Comprimento)','E (Chanfro)','F (Chanfro)','G (Meio)','H 1(0,0mm +/-0,1mm)','H 2(0,5mm +/-0,1mm)','H 3(1,0mm +/-0,1mm)','H 4(1,5mm +/-0,1mm)','L (Largura topo)','M (Largura base)'].map((p,i) => `
                <tr><td>${p}</td><td><input id="${prefix}-sul-${i}"></td><td><input id="${prefix}-nor-${i}"></td></tr>
            `).join('')}
        </table>
    `;

    container.innerHTML = `
        <h3 style="color:var(--text-heading);">PERITAGEM PLACAS ESTREITAS</h3>
        <p style="font-size:10px; color:var(--text-muted);">TOLERÂNCIAS: B <= 1,0mm | E/F <= 2,0mm</p>
        <div style="display:flex; gap:20px; flex-wrap:wrap;">
            <div style="width:48%; min-width:300px;">
                ${secEstreitas('CHEGADA NA OFICINA', 'pe-cheg')}
            </div>
            <div style="width:48%; min-width:300px;">
                ${secEstreitas('SAÍDA DA OFICINA', 'pe-sai')}
            </div>
        </div>
    `;
}

function renderizarM4ChavetasEngrenagem() {
    const container = document.getElementById('container-m4-chavetas');
    if (!container) return;

    let htmlFolga = `<table class="premium-table" style="font-size:10px;"><tr><th>LARGURA</th><th>ESQUERDA</th><th>DIREITA</th></tr>`;
    [1000, 1030, 1040, 1090, 1100, 1160, 1180, 1230, 1290, 1360, 1380, 1420, 1460, 1500, 1530, 1550, 1560, 1580, 1620].forEach(l => {
        htmlFolga += `<tr><td style="font-weight:bold;">${l}</td>
            <td>Sup:<input id="m4-fa-${l}-es" style="width:40px;"> Mei:<input id="m4-fa-${l}-em" style="width:40px;"> Inf:<input id="m4-fa-${l}-ei" style="width:40px;"></td>
            <td>Sup:<input id="m4-fa-${l}-ds" style="width:40px;"> Mei:<input id="m4-fa-${l}-dm" style="width:40px;"> Inf:<input id="m4-fa-${l}-di" style="width:40px;"></td>
        </tr>`;
    });
    htmlFolga += `</table>`;

    container.innerHTML = `
        <h3 style="color:var(--text-heading);">CAIXAS DE ENGRENAGEM, CHAVETAS E FOLGA ARESTA</h3>
        
        <h4 style="margin-top:15px;">FOLGAS NAS CAIXAS DE ENGRENAGEM (BITOLA 1300 ± 1MM)</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>COMPONENTE</th><th>ESQ SUP (ES)</th><th>ESQ INF (EI)</th><th>DIR SUP (DS)</th><th>DIR INF (DI)</th></tr>
            <tr><td>FUSO (mm)</td><td><input id="m4-eng-fuso-es"></td><td><input id="m4-eng-fuso-ei"></td><td><input id="m4-eng-fuso-ds"></td><td><input id="m4-eng-fuso-di"></td></tr>
            <tr><td>PLACA (mm)</td><td><input id="m4-eng-placa-es"></td><td><input id="m4-eng-placa-ei"></td><td><input id="m4-eng-placa-ds"></td><td><input id="m4-eng-placa-di"></td></tr>
        </table>

        <h4 style="margin-top:15px;">AJUSTE DE CHAVETAS DAS PLACAS ESTREITAS</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>PLACA</th><th>LADO</th><th>A</th><th>B</th><th>NOME</th><th>REG</th></tr>
            <tr><td rowspan="2" style="text-align:center;font-weight:bold;">ESQUERDA</td><td style="text-align:center;">A</td><td><input id="m4-chav-esq-a-a"></td><td><input id="m4-chav-esq-a-b"></td><td><input id="m4-chav-esq-a-nome"></td><td><input id="m4-chav-esq-a-reg"></td></tr>
            <tr><td style="text-align:center;">B</td><td><input id="m4-chav-esq-b-a"></td><td><input id="m4-chav-esq-b-b"></td><td><input id="m4-chav-esq-b-nome"></td><td><input id="m4-chav-esq-b-reg"></td></tr>
            <tr><td rowspan="2" style="text-align:center;font-weight:bold;">DIREITA</td><td style="text-align:center;">A</td><td><input id="m4-chav-dir-a-a"></td><td><input id="m4-chav-dir-a-b"></td><td><input id="m4-chav-dir-a-nome"></td><td><input id="m4-chav-dir-a-reg"></td></tr>
            <tr><td style="text-align:center;">B</td><td><input id="m4-chav-dir-b-a"></td><td><input id="m4-chav-dir-b-b"></td><td><input id="m4-chav-dir-b-nome"></td><td><input id="m4-chav-dir-b-reg"></td></tr>
        </table>

        <h4 style="margin-top:15px;">AVALIAÇÃO DO SISTEMA DE RESFRIAMENTO NA SAÍDA</h4>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>FACE FIXA</th><td><input id="m4-resf-fixa" class="w-100"></td></tr>
            <tr><th>FACE MÓVEL</th><td><input id="m4-resf-movel" class="w-100"></td></tr>
        </table>

        <h4 style="margin-top:15px;">RELATÓRIO FOLGA DE ARESTA (Tolerância = 0.25mm)</h4>
        ${htmlFolga}
    `;
}

function renderizarM4Mecanica() {
    const container = document.getElementById('container-m4-mecanica');
    if (!container) return;

    let htmlCardans = `<table class="premium-table" style="font-size:10px;"><tr><th>LOCAL</th><th>ARTICULAÇÃO</th><th>SANFONADA</th><th>PINO TRAVA</th><th>ACOPLAMENTO</th><th>DATA ÚLTIMA TROCA</th></tr>`;
    ['Esq Sup', 'Dir Sup', 'Esq Inf', 'Dir Inf'].forEach((loc, i) => {
        htmlCardans += `<tr><td style="font-weight:bold;">${loc}</td>
            <td style="text-align:center;"><select id="m4-cd-art-${i}"><option>OK</option><option>NOK</option></select></td>
            <td style="text-align:center;"><select id="m4-cd-sanf-${i}"><option>OK</option><option>NOK</option></select></td>
            <td style="text-align:center;"><select id="m4-cd-pino-${i}"><option>OK</option><option>NOK</option></select></td>
            <td style="text-align:center;"><select id="m4-cd-acop-${i}"><option>OK</option><option>NOK</option></select></td>
            <td><input type="date" id="m4-cd-data-${i}" class="w-100"></td>
        </tr>`;
    });
    htmlCardans += `</table>`;

    let htmlTransm = `<table class="premium-table" style="font-size:10px;"><tr><th>LOCAL</th><th>Nº BENZLER</th><th>Nº TRANSMI</th><th>P1</th><th>P2</th><th>P3</th><th>P4</th></tr>`;
    ['Sup Dir', 'Sup Esq', 'Inf Dir', 'Inf Esq'].forEach((loc, i) => {
        htmlTransm += `<tr><td style="font-weight:bold;">${loc}</td>
            <td><input id="m4-tr-bz-${i}" style="width:70px;"></td><td><input id="m4-tr-tr-${i}" style="width:70px;"></td>
            ${[1,2,3,4].map(p => `<td style="text-align:center;"><input type="checkbox" id="m4-tr-p${p}-${i}"></td>`).join('')}
        </tr>`;
    });
    htmlTransm += `</table>`;

    container.innerHTML = `
        <h3 style="color:var(--text-heading);">AFERIÇÃO EIXO EXCÊNTRICO E BUCHA</h3>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>COTA</th><th>DESENHO</th><th>LADO DIREITO</th><th>LADO ESQUERDO</th></tr>
            <tr><td>A</td><td>70 (0 / +0,1)</td><td><input id="m4-ex-a-d"></td><td><input id="m4-ex-a-e"></td></tr>
            <tr><td>B</td><td>45,00</td><td><input id="m4-ex-b-d"></td><td><input id="m4-ex-b-e"></td></tr>
            <tr><td>C</td><td>90 d9 (-0,12/-0,20)</td><td><input id="m4-ex-c-d"></td><td><input id="m4-ex-c-e"></td></tr>
            <tr><td>D</td><td>31,00</td><td><input id="m4-ex-d-d"></td><td><input id="m4-ex-d-e"></td></tr>
            <tr><td>E</td><td>70 h7 (0 / -0,03)</td><td><input id="m4-ex-e-d"></td><td><input id="m4-ex-e-e"></td></tr>
            <tr><td>F</td><td>12,00</td><td><input id="m4-ex-f-d"></td><td><input id="m4-ex-f-e"></td></tr>
            <tr><td>SW</td><td>55,00</td><td><input id="m4-ex-sw-d"></td><td><input id="m4-ex-sw-e"></td></tr>
            <tr><td colspan="4" style="background:#ddd;text-align:center;font-weight:bold;">BUCHA DO EXCÊNTRICO</td></tr>
            <tr><td>DIA INT.</td><td>70 H8 (0 / +0,046)</td><td><input id="m4-ex-buc-d"></td><td><input id="m4-ex-buc-e"></td></tr>
        </table>

        <h3 style="color:var(--text-heading); margin-top:20px;">VERIFICAÇÃO DOS CARDANS</h3>
        ${htmlCardans}

        <h3 style="color:var(--text-heading); margin-top:20px;">PARAFUSOS DE FIXAÇÃO DAS TRANSMISSÕES</h3>
        ${htmlTransm}
    `;
}

function renderizarM4Materiais() {
    const container = document.getElementById('container-m4-materiais');
    if (!container) return;
    let rows = '';
    for (let i = 1; i <= 20; i++) {
        rows += `<tr><td><input id="m4-mat-desc-${i}" class="w-100" placeholder="Material"></td><td><input id="m4-mat-qtd-${i}" style="width:80px;" placeholder="Qtd"></td></tr>`;
    }
    container.innerHTML = `
        <h3 style="color:var(--text-heading);">MATERIAIS UTILIZADOS NA MANUTENÇÃO</h3>
        <table class="premium-table" style="font-size:10px;">
            <thead><tr><th style="width:80%;">DESCRIÇÃO DO MATERIAL / SKU</th><th style="width:20%;">QUANTIDADE</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
        <div style="margin-top:15px;">
            <label style="font-size:11px; font-weight:bold; color:var(--text-muted);">OBSERVAÇÕES GERAIS</label>
            <textarea id="m4-observacoes-gerais" class="premium-textarea" rows="3"></textarea>
        </div>
    `;
}

// ==============================================================
// FUNÇÃO PRINCIPAL - ABRIR FOLHÃO (DISPATCHER)
// ==============================================================
export function abrirFolhaoMCC4(id) {
    ID_FOLHAO_ATUAL = id;
    let item = BANCO_ATIVOS.find(a => a.id === id);
    if (!item) return alert('Equipamento não encontrado!');

    let tipoPeca = item.tipo.trim();
    console.log('Tipo detectado:', tipoPeca);

    // ---- STRAIGHTENER R2 ----
    if (tipoPeca.toLowerCase().includes('straightener r2') || tipoPeca.toLowerCase().includes('straightener r-ii')) {
        console.log('Abrindo Straightener R2...');
        if (typeof window.abrirFolhaoR2 === 'function') {
            window.abrirFolhaoR2(id);
            return;
        } else {
            alert('Função abrirFolhaoR2 não encontrada. Verifique se folhaoR2.js foi carregado.');
            return;
        }
    }

    // ---- BENDER ----
    if (tipoPeca.toUpperCase() === 'BENDER') {
        console.log('Abrindo BENDER...');
        const modal = document.getElementById("modal-folhao-mcc4");
        if (!modal) {
            alert('Modal do Bender (modal-folhao-mcc4) não encontrado no HTML!');
            return;
        }

        const tagInput = document.getElementById("mcc4-tag-name");
        if (tagInput) tagInput.innerText = id;
        const dataInicio = document.getElementById("mcc4-data-inicio");
        if (dataInicio) dataInicio.valueAsDate = new Date();
        const dataFim = document.getElementById("mcc4-data-fim");
        if (dataFim) dataFim.valueAsDate = new Date();

        prepararAbasDinamicamente("BENDER");
        
        let objChecklistBender = {
            "LUBRIFICAÇÃO": [
                "Sistema de lubrificação isento de vazamentos.",
                "Tubulação amassada.",
                "Distribuidores de graxa funcionando corretamente sem vazamentos.",
                "Flexíveis estão perfeitos, sem avarias",
                "Tubulações Inox ou Cobre danificadas"
            ],
            "REFRIGERAÇÃO": [
                "Resfriadores completos e alinhados.",
                "Bicos completos e obstruídos.",
                "Flexíveis isentos de vazamentos.",
                "Tubulações isentas de empenos.",
                "Tubulações furadas."
            ],
            "ESTRUTURA": [
                "Rolos Lubrificados, girando normalmente",
                "Proteções isentas de avarias.",
                "Estrutura com break-out.",
                "Rolamentos quebrados.",
                "Rolos travados",
                "Parafusos de fixação dos mancais todos apertados",
                "Conexões apertadas."
            ]
        };
        renderizarChecklist(objChecklistBender, "container-check-recebimento", "geral");
        
        const firstTab = modal.querySelector('.folhao-tab');
        if (firstTab) firstTab.click();
        
        modal.classList.remove("hidden");
        return;
    }

    // ---- MOLDE MCC 4 ----
    if (tipoPeca.toUpperCase() === 'MOLDE') {
        console.log('Abrindo MOLDE MCC 4...');
        const modalM4 = document.getElementById("modal-folhao-molde4");
        if (!modalM4) {
            alert("Modal do Molde 4 (modal-folhao-molde4) não encontrado no HTML!");
            return;
        }

        const tagInput = document.getElementById("molde4-tag-name");
        if (tagInput) tagInput.value = id;
        const dataInicio = document.getElementById("molde4-data-inicio");
        if (dataInicio) dataInicio.valueAsDate = new Date();
        const dataFim = document.getElementById("molde4-data-fim");
        if (dataFim) dataFim.valueAsDate = new Date();

        // Limpa as divs vitais
        const recebDiv = document.getElementById('m4-aba-receb');
        if (recebDiv) recebDiv.innerHTML = '<div id="container-m4-recebimento"></div><div id="container-m4-eletrica"></div>';
        const revisaoDiv = document.getElementById('m4-aba-revisao');
        if (revisaoDiv) revisaoDiv.innerHTML = '<div id="container-m4-revisao"></div><div id="container-m4-final"></div>';

        // Renderiza tudo
        renderizarM4Identificacao();
        renderizarTabelaSimNaoM4('container-m4-recebimento', checklistsM4.recebimentoMecanica, 'm4-rec');
        renderizarTabelaSimNaoM4('container-m4-eletrica', checklistsM4.recebimentoEletrica, 'm4-ele');
        renderizarTabelaSimNaoM4('container-m4-revisao', checklistsM4.revisao, 'm4-rev');
        renderizarTabelaSimNaoM4('container-m4-final', checklistsM4.inspecaoFinal, 'm4-fin', true);
        renderizarM4AjustesHidraulica();
        renderizarM4Rolos();
        renderizarM4SensorResist();
        renderizarM4PeritagemLargas();
        renderizarM4PeritagemEstreitas();
        renderizarM4ChavetasEngrenagem();
        renderizarM4Mecanica();
        renderizarM4Materiais();

        const firstTabM4 = modalM4.querySelector('.folhao-tab');
        if (firstTabM4) firstTabM4.click();
        modalM4.classList.remove("hidden");
        return;
    }

    alert('Tipo de equipamento sem folhão definido: ' + tipoPeca);
}

// ==============================================================
// SALVAR E IMPRIMIR - MOLDE MCC 4 (PDF NATIVO + NUVEM)
// ==============================================================
export async function salvarEImprimirFolhaoMolde4() {
    if (!ID_FOLHAO_ATUAL) return alert("Nenhuma TAG carregada.");
    let tag = ID_FOLHAO_ATUAL;

    // 1. CAPTURA OS DADOS DA TELA
    const dtIni = getV('molde4-data-inicio') || new Date().toLocaleDateString('pt-BR');
    const dtFim = getV('molde4-data-fim') || new Date().toLocaleDateString('pt-BR');
    const num = getV('molde4-num-molde');
    const mot = getV('molde4-motivo');
    const tipoE = getV('molde4-tipo-exec'); 
    const novaMeta = getV('molde4-nova-meta') || 'Manter Atual';

    // 2. PREPARA OS DADOS PARA A NUVEM
    const dadosFolhao = {
        id_peca: tag,
        tipo_equipamento: "Molde",
        tecnico: window.OPERADOR_LOGADO ? window.OPERADOR_LOGADO.nome : "Técnico",
        nova_meta: parseFloat(novaMeta) || 0,
        tipo_manutencao: tipoE,
        dados_chegada: "{}", 
        dados_saida: "{}",
        status_reparo: "Concluido",
        pdf_base64: "" 
    };

    // 🔥 A CORREÇÃO MÁGICA: Obriga o navegador a ESPERAR o Python terminar de salvar! 🔥
    try {
        const resposta = await fetch("http://localhost:8000/api/salvar_folhao", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dadosFolhao)
        });
        
        const resultado = await resposta.json();
        
        // Se der algum erro no Python, o sistema avisa na tela e cancela a impressão
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

    // 3. FUNÇÃO AUXILIAR DA TABELA DO PDF
    function gerarTabelaCheckPDF(prefix, arr, isFinal = false) {
        let h = `<table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th>`;
        if (isFinal) h += `<th style="width:15%;">MEDIDA ENCONTRADA</th>`;
        h += `<th style="width:8%;">SIM</th><th style="width:8%;">NÃO</th></tr>`;
        arr.forEach((item, i) => {
            const desc = isFinal ? item.text : item;
            const numVal = isFinal ? item.num : (i + 1);
            const v = getRadioValue(`${prefix}-${i}`);
            h += `<tr><td style="text-align:center;">${numVal}</td><td>${desc}</td>`;
            if (isFinal) h += `<td style="text-align:center;">${getV(`${prefix}-${i}-med`)}</td>`;
            h += `<td style="text-align:center;font-weight:bold;">${v==='SIM'?'X':''}</td><td style="text-align:center;font-weight:bold;">${v==='NÃO'?'X':''}</td></tr>`;
        });
        h += `</table>`;
        return h;
    }

    // 4. DESENHA O SEU PDF PERFEITO DA CSN
    let htmlPDF = `
    <style>
        .pdf-base { font-family: Arial, sans-serif; font-size: 9px; color: #000; }
        .pdf-base table { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
        .pdf-base th, .pdf-base td { border: 1px solid #000; padding: 3px; }
        .pdf-base th { background: #e0e0e0; text-align: center; font-weight: bold; font-size: 9px; }
        .pdf-base .titulo-secao { background: #002b5e; color: #fff; font-weight: bold; padding: 4px; text-align: left; margin: 10px 0 4px 0; border: 1px solid #000; font-size: 10px; text-transform: uppercase; }
        .pdf-base .assinatura-box { margin-top:2px; font-size:8px; font-weight:bold; }
        @media print { .quebra-pagina { break-before: page; page-break-before: always; margin-top: 10px; } }
    </style>
    <div class="pdf-base">
        <!-- CABEÇALHO -->
        <div style="display: flex; border: 2px solid #000; border-bottom: 5px solid #002b5e; margin-bottom: 8px; align-items: center;">
            <div style="width: 20%; text-align: center; border-right: 2px solid #000; padding: 8px;"><span style="font-weight: 900; font-size: 28px; color: #002b5e; letter-spacing: -2px;">CSN</span></div>
            <div style="width: 60%; text-align: center; padding: 8px;">
                <h2 style="margin: 0; font-size: 12px; color: #000;">CHECK LIST GERAL DO MOLDE MCC 4</h2>
                <p style="margin: 4px 0 0 0; font-size: 8px; font-weight: bold;">DATA INÍCIO: ${dtIni} | DATA FIM: ${dtFim}</p>
            </div>
            <div style="width: 20%; font-size: 9px; border-left: 2px solid #000; padding: 8px; font-weight: bold;">TAG: ${tag}</div>
        </div>
        
        <table style="margin-bottom: 15px; border: 2px solid #000;">
            <tr>
                <td style="width: 25%;"><strong>Nº MOLDE:</strong> ${num}</td>
                <td style="width: 30%;"><strong>MOTIVO:</strong> ${mot}</td>
                <td style="width: 25%; color: #002b5e;"><strong>EXECUÇÃO:</strong> ${tipoE}</td>
                <td style="width: 20%; background-color: #f0f0f0; text-align: center;"><strong>NOVA META:</strong> ${novaMeta}</td>
            </tr>
        </table>

        <div class="titulo-secao">IDENTIFICAÇÃO DE COMPONENTES</div>
        <table>
            <tr><th>PLACAS</th><th>SAÍDA MÁQ</th><th>SAÍDA OFI</th><th>REDUTORES</th><th>SAÍDA MÁQ</th><th>SAÍDA OFI</th><th>CILINDROS</th><th>SAÍDA MÁQ</th><th>SAÍDA OFI</th></tr>
            <tr><td>FIXA:</td><td style="text-align:center;">${getV('m4-id-pl-fixa-mq')}</td><td style="text-align:center;">${getV('m4-id-pl-fixa-of')}</td><td>SUP DIR</td><td style="text-align:center;">${getV('m4-id-red-sd-mq')}</td><td style="text-align:center;">${getV('m4-id-red-sd-of')}</td><td>SUP DIR</td><td style="text-align:center;">${getV('m4-id-cil-sd-mq')}</td><td style="text-align:center;">${getV('m4-id-cil-sd-of')}</td></tr>
            <tr><td>MÓVEL:</td><td style="text-align:center;">${getV('m4-id-pl-movel-mq')}</td><td style="text-align:center;">${getV('m4-id-pl-movel-of')}</td><td>INF DIR</td><td style="text-align:center;">${getV('m4-id-red-id-mq')}</td><td style="text-align:center;">${getV('m4-id-red-id-of')}</td><td>INF DIR</td><td style="text-align:center;">${getV('m4-id-cil-id-mq')}</td><td style="text-align:center;">${getV('m4-id-cil-id-of')}</td></tr>
            <tr><td>DIREITA:</td><td style="text-align:center;">${getV('m4-id-pl-dir-mq')}</td><td style="text-align:center;">${getV('m4-id-pl-dir-of')}</td><td>SUP ESQ</td><td style="text-align:center;">${getV('m4-id-red-se-mq')}</td><td style="text-align:center;">${getV('m4-id-red-se-of')}</td><td>SUP ESQ</td><td style="text-align:center;">${getV('m4-id-cil-se-mq')}</td><td style="text-align:center;">${getV('m4-id-cil-se-of')}</td></tr>
            <tr><td>ESQUERDA:</td><td style="text-align:center;">${getV('m4-id-pl-esq-mq')}</td><td style="text-align:center;">${getV('m4-id-pl-esq-of')}</td><td>INF ESQ</td><td style="text-align:center;">${getV('m4-id-red-ie-mq')}</td><td style="text-align:center;">${getV('m4-id-red-ie-of')}</td><td>INF ESQ</td><td style="text-align:center;">${getV('m4-id-cil-ie-mq')}</td><td style="text-align:center;">${getV('m4-id-cil-ie-of')}</td></tr>
        </table>
        <div class="assinatura-box">DATA: ____/____/____ NOME:______________________________________ MATRÍCULA:_________</div>

        <div class="titulo-secao">1. INSPEÇÃO DE RECEBIMENTO MECÂNICA</div>
        ${gerarTabelaCheckPDF('m4-rec', checklistsM4.recebimentoMecanica)}
        
        <div class="titulo-secao">2. INSPEÇÃO DE RECEBIMENTO ELÉTRICA</div>
        ${gerarTabelaCheckPDF('m4-ele', checklistsM4.recebimentoEletrica)}

        <div class="quebra-pagina"></div>
        <div class="titulo-secao">3. REVISÃO DOS MOLDES</div>
        ${gerarTabelaCheckPDF('m4-rev', checklistsM4.revisao)}

        <div class="titulo-secao">4. INSPEÇÃO FINAL DOS MOLDES</div>
        ${gerarTabelaCheckPDF('m4-fin', checklistsM4.inspecaoFinal, true)}
        <div class="assinatura-box">DATA: ____/____/____ NOME:______________________________________ MATRÍCULA:_________</div>

        <div class="quebra-pagina"></div>
        <div class="titulo-secao">5. PLANILHA DE AJUSTE E MEDIDAS NOMINAIS DO MOLDE</div>
        <table>
            <tr><th>ITEM</th><th>DESCRIÇÃO</th><th>NOMINAL</th><th>REAL</th></tr>
            <tr><td style="text-align:center;">1</td><td>APERTO DO PARAFUSO EXCÊNTRICO</td><td>-</td><td>Dir: ${getV('m4-aj-exc-dir')} | Esq: ${getV('m4-aj-exc-esq')}</td></tr>
            <tr><td style="text-align:center;">2</td><td>TORQUE DO PARAFUSO DE FIXAÇÃO DO FOOT ROLL</td><td>300 + 5 Nm</td><td style="text-align:center;">${getV('m4-aj-tfr')}</td></tr>
            <tr><td style="text-align:center;">3</td><td>TORQUE DO PARAFUSO DE FIXAÇÃO DA PLACA LATERAL</td><td>200 + 5 Nm</td><td style="text-align:center;">${getV('m4-aj-tpl')}</td></tr>
            <tr><td style="text-align:center;">4</td><td>TIRANTE FIXAÇÃO DAS GUIAS LATERAIS</td><td>100 Nm</td><td style="text-align:center;">${getV('m4-aj-tir')}</td></tr>
            <tr><td style="text-align:center;">5</td><td>FOLGA DE GABARITO DO CLAMP (Ø250)</td><td>1,60 ± 0,15 mm</td><td>Sup: ${getV('m4-aj-clp-sup')} | Inf: ${getV('m4-aj-clp-inf')}</td></tr>
        </table>
        
        <div style="margin-top:40px; display:flex; justify-content:space-around; text-align:center; font-size:10px; font-weight:bold;">
            <div><p>___________________________________</p><p>Assinatura Mecânica / Operador</p></div>
            <div><p>___________________________________</p><p>Inspetor de Qualidade</p></div>
        </div>
    </div>`;

    // 5. JOGA O HTML NO CONTAINER DE IMPRESSÃO
    const printDiv = document.getElementById('print-content');
    if (printDiv) printDiv.innerHTML = htmlPDF;
    
    // 6. FECHA A JANELA E SÓ AGORA CHAMA O PRINT
    fecharFolhaoMolde4();
    if (typeof renderReparos === 'function') renderReparos();
    if (typeof renderReservas === 'function') renderReservas();
    if (typeof renderAtivos === 'function') renderAtivos();
    
    setTimeout(() => window.print(), 500);
}

// GARANTE QUE O NAVEGADOR VAI RECONHECER A NOVA FUNÇÃO
window.salvarEImprimirFolhaoMolde4 = salvarEImprimirFolhaoMolde4;

// ==============================================================
// SALVAR LAUDO INTELIGENTE (BENDER)
// ==============================================================
export function salvarLaudoInteligente() {
    if (!ID_FOLHAO_ATUAL) return;
    let tag = ID_FOLHAO_ATUAL;
    let item = BANCO_ATIVOS.find(a => a.id === tag);
    if (!item) return;

    item.ton = 0; item.dias = 0; item.local = "Oficina / Reserva";
    localStorage.setItem("oms_ativos_v32_local", JSON.stringify(BANCO_ATIVOS));

    let motivo = document.getElementById("mcc4-motivo")?.value || "Manutenção";
    if (window.registrarHistorico) {
        window.registrarHistorico(tag, `Laudo Bender finalizado. Motivo: ${motivo}`);
    }
    fecharFolhaoMCC4();
    if (renderReparos) renderReparos();
    if (renderReservas) renderReservas();
    if (renderAtivos) renderAtivos();
    if (window.calcularKpisGlobais) window.calcularKpisGlobais();
    imprimirPDFBender(tag, motivo, getV);
}

// ==============================================================
// EXPOSIÇÃO GLOBAL
// ==============================================================
window.abrirFolhaoMCC4 = abrirFolhaoMCC4;
window.fecharFolhaoMCC4 = fecharFolhaoMCC4;
window.fecharFolhaoMolde4 = fecharFolhaoMolde4;
window.trocarAbaFolhao = trocarAbaFolhao;
window.trocarAbaMolde4 = trocarAbaMolde4;
window.salvarLaudoInteligente = salvarLaudoInteligente;
window.salvarEImprimirFolhaoMolde4 = salvarEImprimirFolhaoMolde4;
window.adicionarLinhaMaterialBender = window.adicionarLinhaMaterialBender || function() {};
window.getV = getV;

console.log("✅ folhaoMolde4.js carregado – com BENDER e MOLDE MCC4 corrigidos.");