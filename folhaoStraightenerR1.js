// folhaoStraightenerR1.js - VERSÃO COMPLETA PARA STRAIGHTENER R1

let ID_FOLHAO_R1_ATUAL = null;

// ==============================================================
// 1. DADOS DAS TABELAS (transcritos do documento oficial R1)
// ==============================================================

const itensChegadaR1 = [
    { grupo: "LUBRIFICAÇÃO", desc: "Sistema de lubrificação isento de vazamentos." },
    { grupo: "", desc: "Tubulação amassada." },
    { grupo: "", desc: "Distribuidores de graxa funcionando corretamente sem vazamentos." },
    { grupo: "REFRIGERAÇÃO", desc: "Resfriadores completos e alinhados." },
    { grupo: "", desc: "Bicos obstruídos." },
    { grupo: "", desc: "Flexíveis isentos de vazamentos." },
    { grupo: "", desc: "Tubulações isentas de empenos." },
    { grupo: "", desc: "Tubulações furadas." },
    { grupo: "CILINDROS", desc: "Isento de vazamento." },
    { grupo: "", desc: "Conexões completas e apertadas." },
    { grupo: "", desc: "Flexíveis isentos de vazamentos." },
    { grupo: "", desc: "Tubulações isentas de empenos." },
    { grupo: "PORCA HIDRÁULICA", desc: "Isento de vazamento." },
    { grupo: "", desc: "Conexões completas e apertadas." },
    { grupo: "", desc: "Proteções danificadas." },
    { grupo: "", desc: "Tubulações isentas de vazamentos." },
    { grupo: "ESTRUTURA", desc: "Tubulações isentas de amassados." },
    { grupo: "", desc: "Proteções isentas de avarias." },
    { grupo: "", desc: "Estrutura com break-out." },
    { grupo: "", desc: "Rolamentos quebrados." },
    { grupo: "", desc: "Rolos travados" },
    { grupo: "", desc: "Mancais furados." },
    { grupo: "", desc: "Estrias do rolo puxador danificada." },
    { grupo: "", desc: "Conexões apertadas." }
];

const refPassLineInfR1 = ["12,46", "41,22", "56,80", "60,15", "52,68", "36,07", "12,11"];
const refPassLineSupR1 = ["79,75", "52,18", "37,61", "35,00", "42,83", "59,38", "82,89"];

// Mesmos refs de saída (Bow) conforme documento
const refsInfSaiR1 = ["68,66", "91,34", "105,13", "110,00", "105,13", "91,34", "68,66"];
const refsSupSaiR1 = ["124,13", "102,66", "89,61", "85,00", "89,61", "102,66", "124,13"];

const manutencaoR1 = [
    { item: "1", desc: "Lavagem e/ou Limpeza Mecânica" },
    { item: "2.1", desc: "Teste Hidrostático" },
    { item: "2.2", desc: "Teste Hidráulico" },
    { item: "2.3", desc: "Teste de Refrigeração" },
    { item: "2.4", desc: "Aferição de Gap (255mm)" },
    { item: "2.5", desc: "Abrir Segmento" },
    { item: "3.1", desc: "Desmontagem de proteções" },
    { item: "3.2", desc: "Retirar chavetas" },
    { item: "3.3", desc: "Desconectar pinos dos cilindros de elevação" },
    { item: "3.4", desc: "Retirada da Barra Transversal" },
    { item: "3.5", desc: "Desconectar flexíveis principais" },
    { item: "3.6", desc: "Retirar parafusos de fixação das buchas" },
    { item: "3.7", desc: "Transferir base para stand" },
    { item: "3.8", desc: "Aferir pass-line Inf. e Sup." },
    { item: "3.9", desc: "Retirar cangalhas (Inf. e Sup.)" },
    { item: "3.10", desc: "Desconectar flexíveis das juntas rotativas" },
    { item: "3.11", desc: "Retirar proteções de mancal" },
    { item: "3.12", desc: "Desmontagem dos rolos (Destorquear e soltá-los) inferior" },
    { item: "3.13", desc: "Desmontagem dos rolos (Destorquear e soltá-los) superior" },
    { item: "3.14", desc: "Desmontagem da estrutura do rolo acionado" },
    { item: "3.15", desc: "Retirada dos cilindros motriz" },
    { item: "3.16", desc: "Desmontagem de buchas e conjuntos na base" },
    { item: "3.17", desc: "Desmontagem de buchas e conjuntos" },
    { item: "3.18", desc: "Preparar bases e barra para jateamento e pintura" },
    { item: "4.1", desc: "Desmontagem de proteções e preparação dos calços e base Inferior" },
    { item: "4.2", desc: "Troca de oring’s" },
    { item: "4.3", desc: "Montagem de distribuidores" },
    { item: "4.4", desc: "Fixação dos distribuidores na base" },
    { item: "4.5", desc: "Desobstrução das tubulações de graxa e de refrigeração" },
    { item: "4.6", desc: "Preparação dos Rolos" },
    { item: "4.7", desc: "Montagem de flexíveis na base" },
    { item: "4.8", desc: "Preparação de pés e tulipas" },
    { item: "4.9", desc: "Montagem de rolos na base" },
    { item: "4.10", desc: "Torque dos parafusos dos mancais" },
    { item: "4.11", desc: "Regulagem dos distribuidores" },
    { item: "4.12", desc: "Teste de Lubrificação" },
    { item: "4.13", desc: "Fixação dos distribuidores na base" },
    { item: "4.14", desc: "Preparar hastes" },
    { item: "4.15", desc: "Preparar e montar conjuntos de ajustes e buchas" },
    { item: "4.16", desc: "Montagem das buchas e conjuntos na base" },
    { item: "4.17", desc: "Montagem dos flexíveis principais" },
    { item: "4.18", desc: "Conectar flexíveis de juntas nos rolos" },
    { item: "4.19", desc: "Teste hidrostático juntas rotativas" },
    { item: "4.20", desc: "Teste hidrostático Mancal" },
    { item: "4.21", desc: "Aferir Pass-Line e Ajustar" },
    { item: "4.22", desc: "Montagem e alinhamento das cangalhas" },
    { item: "5.1", desc: "Desmontar todos os bicos" },
    { item: "5.2", desc: "Realizar Limpeza das tubulações" },
    { item: "5.3", desc: "Montar os bicos e flexíveis" },
    { item: "5.4", desc: "Realizar teste" },
    { item: "6.1", desc: "Preparação de Lines ou troca" },
    { item: "6.2", desc: "Preparação dos calços e apoios" },
    { item: "6.3", desc: "Troca de oring’s" },
    { item: "6.4", desc: "Desobstrução de tubulações de graxa e de refrigeração" },
    { item: "6.5", desc: "Montagem de proteções das tubulações e de stauff" },
    { item: "6.6", desc: "Verificar roscas dos parafusos M30" },
    { item: "6.7", desc: "Montagem do rolo motriz" },
    { item: "7.1", desc: "Preparação para receber estrutura e cilindros (Lines e mancais)" },
    { item: "7.2", desc: "Montagem de Cilindros Motriz" },
    { item: "7.3", desc: "Desmontagem de proteções e preparação dos calços e base Superior" },
    { item: "7.4", desc: "Troca de oring’s" },
    { item: "7.5", desc: "Desobstruição das tubulações de graxa e de refrigeração" },
    { item: "7.6", desc: "Preparação dos Rolos" },
    { item: "7.7", desc: "Troca de parafusos dos calços de alinhamento pass-line" },
    { item: "7.8", desc: "Montagem de rolos na base" },
    { item: "7.9", desc: "Aperto de parafusos nos mancais" },
    { item: "7.10", desc: "Montagem da estrutura" },
    { item: "7.11", desc: "Montagem de distribuidores" },
    { item: "7.12", desc: "Regulagem dos distribuidores" },
    { item: "7.13", desc: "Teste de Lubrificação" },
    { item: "7.14", desc: "Fixação dos distribuidores na base" },
    { item: "7.15", desc: "Montagem de proteções dos mancais" },
    { item: "7.16", desc: "Realização do teste hidrostático da base" },
    { item: "7.17", desc: "Virar a base" },
    { item: "7.18", desc: "Torque dos parafusos dos mancais" },
    { item: "7.19", desc: "Montagem de flexíveis de junta rotativa" },
    { item: "7.20", desc: "Aferir e ajustar pass-line" },
    { item: "7.21", desc: "Troca das válvulas dos cilindros" },
    { item: "7.22", desc: "Troca dos mangotes hidráulicos dos cilindros" },
    { item: "7.23", desc: "Montagem de proteções sanfonadas" },
    { item: "7.24", desc: "Substituição dos engates rápidos (hidráulicos)" },
    { item: "7.25", desc: "Substituição dos engates rápidos (refrigeração)" },
    { item: "7.26", desc: "Montagem de cangalhas na base" },
    { item: "8.1", desc: "Troca de cilindros de elevação" },
    { item: "8.2", desc: "Troca de cilindros clamp" },
    { item: "8.3", desc: "Montagem de blocos nos cilindros clamp" },
    { item: "8.4", desc: "Troca de oring’s (completo)" },
    { item: "8.5", desc: "Aperto de tubulações (Conferir)" },
    { item: "8.6", desc: "Montagem de mangotes dos cilindros de elevação" },
    { item: "8.7", desc: "Teste hidráulico da barra" },
    { item: "9.1", desc: "Movimentar base sup para inf" },
    { item: "9.2", desc: "Conectar flexíveis principais (graxa e água)" },
    { item: "9.3", desc: "Montar parafusos das buchas" },
    { item: "9.4", desc: "Preparação das hastes para receber a barra" },
    { item: "9.5", desc: "Alinhamento de cangalha superior" },
    { item: "9.6", desc: "Teste geral de juntas" },
    { item: "9.7", desc: "Montagem da barra transversal no segmento" },
    { item: "9.8", desc: "Aperto de parafusos dos cilindros clamp" },
    { item: "9.9", desc: "Montagem de pinos e chavetas" },
    { item: "9.10", desc: "Montagem de proteções" },
    { item: "9.11", desc: "Conexão da hidráulica" },
    { item: "9.12", desc: "Equalização dos cilindros motriz" },
    { item: "9.13", desc: "Aferir e Ajustar Gap (255mm)" },
    { item: "10.1", desc: "Teste e Liberação hidráulica" },
    { item: "10.2", desc: "Teste e Liberação hidrostática" },
    { item: "10.3", desc: "Retirar Segmento do Stand" },
    { item: "10.4", desc: "Montagem de Acoplamentos" },
    { item: "10.5", desc: "Teste de lubrificação geral" }
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
    return el && el.checked ? 'X' : '';
}

function garantirContainer(id) {
    let container = document.getElementById(id);
    if (!container) {
        const body = document.querySelector('.folhao-body');
        if (body) {
            container = document.createElement('div');
            container.id = id;
            body.appendChild(container);
        }
    }
    return container;
}

// ==============================================================
// 3. RENDERIZAR CHECKLIST DE CHEGADA (com categorias)
// ==============================================================
function renderizarInspecaoChegadaR1() {
    const container = garantirContainer('container-check-recebimento-r1');
    if (!container) return;

    let categorias = {};
    let currentGroup = "GERAL";
    itensChegadaR1.forEach(item => {
        if (item.grupo && item.grupo.trim() !== "") currentGroup = item.grupo;
        if (!categorias[currentGroup]) categorias[currentGroup] = [];
        categorias[currentGroup].push(item.desc);
    });

    let html = "";
    let groupIndex = 0;
    for (const [nomeCategoria, perguntas] of Object.entries(categorias)) {
        html += `<h4 style="margin: 20px 0 10px 0; color: var(--text-accent); border-bottom: 1px dashed var(--border-color); padding-bottom: 5px;"><i class="fas fa-tasks"></i> ${nomeCategoria}</h4><div class="checklist-container">`;
        perguntas.forEach((pergunta, index) => {
            const name = `r1-g${groupIndex}-q${index}`;
            html += `<div class="check-item"><p>${index + 1}. ${pergunta}</p><div class="check-options"><label><input type="radio" name="${name}" value="SIM" checked> SIM</label><label><input type="radio" name="${name}" value="NÃO"> NÃO</label></div></div>`;
        });
        html += `</div>`;
        groupIndex++;
    }
    container.innerHTML = html;
}

// ==============================================================
// 4. GAP (7 conjuntos)
// ==============================================================
function renderizarGapR1() {
    const container = garantirContainer('r1-gap');
    if (!container) return;
    let html = `<h3 style="color:var(--text-heading);">AFERIÇÃO DE GAP (255+0,3/-0,3)</h3>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>CONJ. ROLO</th><th>Posição A</th><th>Posição B</th><th>Posição C</th></tr>`;
    for (let i = 1; i <= 7; i++) {
        html += `<tr><td style="text-align:center;font-weight:bold;">${i}</td>
            <td><input id="r1gap-${i}-a"></td>
            <td><input id="r1gap-${i}-b"></td>
            <td><input id="r1gap-${i}-c"></td></tr>`;
    }
    html += `</table>`;
    container.innerHTML = html;
}

// ==============================================================
// 5. CANGALHAS (Superior e Inferior)
// ==============================================================
function renderizarCangalhasR1() {
    const container = garantirContainer('r1-cangalhas');
    if (!container) return;
    const bases = ['Sup', 'Inf'];
    let html = `<h3 style="color:var(--text-heading);">INSPEÇÃO DE CANGALHAS</h3>`;
    bases.forEach(base => {
        const prefix = base === 'Sup' ? 'sup' : 'inf';
        html += `<h4>Base ${base}</h4>
            <table class="premium-table" style="font-size:9px;">
                <tr><th>Posição</th><th colspan="2">Posição Bico A</th><th colspan="2">Posição Bico B</th></tr>
                <tr><th></th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td>${i}ª</td>
                <td style="text-align:center;"><input type="radio" name="r1cang-${prefix}-${i}-a" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="r1cang-${prefix}-${i}-a" value="NOK"></td>
                <td style="text-align:center;"><input type="radio" name="r1cang-${prefix}-${i}-b" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="r1cang-${prefix}-${i}-b" value="NOK"></td></tr>`;
        }
        html += `</table>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 6. PASS LINE (Chegada e Saída)
// ==============================================================
function renderizarPassLinesR1() {
    const renderTable = (id, refs, titulo) => {
        const container = garantirContainer(id);
        if (!container) return;
        let html = `<h3 style="color:var(--text-heading);">${titulo}</h3>
            <table class="premium-table" style="font-size:9px;">
                <tr><th>Conj. Rolo</th><th>Referência</th><th>Posição A</th><th>Posição B</th><th>Posição C</th></tr>`;
        refs.forEach((ref, i) => {
            html += `<tr><td style="text-align:center;font-weight:bold;">${i+1}°</td>
                <td style="text-align:center;font-weight:bold;">${ref}</td>
                <td><input id="${id}-a-${i}"></td>
                <td><input id="${id}-b-${i}"></td>
                <td><input id="${id}-c-${i}"></td></tr>`;
        });
        html += `</table>`;
        container.innerHTML = html;
    };
    renderTable('r1-passline-inf-chegada', refPassLineInfR1, 'PASS LINE - BASE INFERIOR (CHEGADA)');
    renderTable('r1-passline-sup-chegada', refPassLineSupR1, 'PASS LINE - BASE SUPERIOR (CHEGADA)');
    renderTable('r1-passline-inf-saida', refsInfSaiR1, 'PASS LINE - BASE INFERIOR (SAÍDA)');
    renderTable('r1-passline-sup-saida', refsSupSaiR1, 'PASS LINE - BASE SUPERIOR (SAÍDA)');
}

// ==============================================================
// 7. CILINDROS HIDRÁULICOS (Chegada)
// ==============================================================
function renderizarCilindrosChegadaR1() {
    const container = garantirContainer('r1-cilindros-chegada');
    if (!container) return;
    const tipos = [
        { nome: 'Cilindro de Elevação', prefix: 'ce', pos: ['A','B','C','D'] },
        { nome: 'Cilindro Clamp (Porcas Hidráulicas)', prefix: 'cc', pos: ['A','B','C','D'] },
        { nome: 'Cilindros Motriz', prefix: 'cm', pos: ['A','B'] }
    ];
    let html = `<h3 style="color:var(--text-heading);">CILINDROS HIDRÁULICOS (CHEGADA)</h3>`;
    tipos.forEach(t => {
        html += `<h4>${t.nome}</h4>
            <table class="premium-table" style="font-size:9px;">
                <tr><th>Posição</th><th>Número</th><th>Produção</th><th>OK</th><th>NOK</th><th>Observação</th></tr>`;
        t.pos.forEach(p => {
            html += `<tr><td style="text-align:center;font-weight:bold;">${p}</td>
                <td><input id="r1cil-${t.prefix}-num-${p}"></td>
                <td><input id="r1cil-${t.prefix}-prod-${p}"></td>
                <td style="text-align:center;"><input type="radio" name="r1cil-${t.prefix}-${p}" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="r1cil-${t.prefix}-${p}" value="NOK"></td>
                <td><input id="r1cil-${t.prefix}-obs-${p}"></td></tr>`;
        });
        html += `</table>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 8. CILINDROS HIDRÁULICOS (Saída)
// ==============================================================
function renderizarCilindrosSaidaR1() {
    const container = garantirContainer('r1-cilindros-saida');
    if (!container) return;
    const tipos = [
        { nome: 'Cilindro de Elevação', prefix: 'se', pos: ['A','B','C','D'] },
        { nome: 'Cilindro Clamp (Porcas Hidráulicas)', prefix: 'sc', pos: ['A','B','C','D'] },
        { nome: 'Cilindros Motriz', prefix: 'sm', pos: ['A','B'] }
    ];
    let html = `<h3 style="color:var(--text-heading);">CILINDROS HIDRÁULICOS (SAÍDA)</h3>`;
    tipos.forEach(t => {
        html += `<h4>${t.nome}</h4>
            <table class="premium-table" style="font-size:9px;">
                <tr><th>Posição</th><th>Número</th><th>Produção</th><th>Reparado</th><th>Reutilizado</th><th>Novo</th><th>Observação</th></tr>`;
        t.pos.forEach(p => {
            html += `<tr><td style="text-align:center;font-weight:bold;">${p}</td>
                <td><input id="r1cils-${t.prefix}-num-${p}"></td>
                <td><input id="r1cils-${t.prefix}-prod-${p}"></td>
                <td style="text-align:center;"><input type="checkbox" id="r1cils-${t.prefix}-rep-${p}"></td>
                <td style="text-align:center;"><input type="checkbox" id="r1cils-${t.prefix}-reu-${p}"></td>
                <td style="text-align:center;"><input type="checkbox" id="r1cils-${t.prefix}-nov-${p}"></td>
                <td><input id="r1cils-${t.prefix}-obs-${p}"></td></tr>`;
        });
        html += `</table>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 9. INSPEÇÃO DE ROLOS (Chegada e Saída)
// ==============================================================
function renderizarInspecaoRolosR1(tipo) {
    const idContainer = `r1-rolos-${tipo}`;
    const container = garantirContainer(idContainer);
    if (!container) return;
    const titulo = tipo === 'chegada' ? 'CHEGADA' : 'SAÍDA';
    const prefix = tipo === 'chegada' ? 'ch' : 'sa';
    const bases = ['Inferior', 'Superior'];
    let html = `<h3 style="color:var(--text-heading);">INSPEÇÃO DE ROLOS (${titulo})</h3>`;
    bases.forEach(base => {
        const bPrefix = base === 'Inferior' ? 'inf' : 'sup';
        html += `<h4>Base ${base}</h4>
            <h5>Rolamento</h5>
            <table class="premium-table" style="font-size:8px;">
                <tr><th>Posição</th><th colspan="2">1</th><th colspan="2">2</th><th colspan="2">3</th><th colspan="2">4</th></tr>
                <tr><th></th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center;font-weight:bold;">${i}</td>`;
            for (let j = 1; j <= 4; j++) {
                html += `<td style="text-align:center;"><input type="radio" name="r1rol-${prefix}-${bPrefix}-${i}-${j}" value="OK" checked></td>
                         <td style="text-align:center;"><input type="radio" name="r1rol-${prefix}-${bPrefix}-${i}-${j}" value="NOK"></td>`;
            }
            html += `</tr>`;
        }
        html += `</table>
            <h5>Teste Hidrostático</h5>
            <table class="premium-table" style="font-size:8px;">
                <tr><th>Posição</th><th colspan="2">1</th><th colspan="2">2</th><th colspan="2">3</th><th colspan="2">4</th></tr>
                <tr><th></th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center;font-weight:bold;">${i}</td>`;
            for (let j = 1; j <= 4; j++) {
                html += `<td style="text-align:center;"><input type="radio" name="r1hid-${prefix}-${bPrefix}-${i}-${j}" value="OK" checked></td>
                         <td style="text-align:center;"><input type="radio" name="r1hid-${prefix}-${bPrefix}-${i}-${j}" value="NOK"></td>`;
            }
            html += `</tr>`;
        }
        html += `</table>
            <h5>Medidas dos Rolos</h5>
            <table class="premium-table" style="font-size:8px;">
                <tr><th>Posição</th><th colspan="2">1</th><th colspan="2">2</th><th colspan="2">3</th></tr>
                <tr><th></th><th>Num</th><th>Medida</th><th>Num</th><th>Medida</th><th>Num</th><th>Medida</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center;font-weight:bold;">${i}</td>
                <td><input id="r1med-${prefix}-${bPrefix}-${i}-n1"></td>
                <td><input id="r1med-${prefix}-${bPrefix}-${i}-m1"></td>
                <td><input id="r1med-${prefix}-${bPrefix}-${i}-n2"></td>
                <td><input id="r1med-${prefix}-${bPrefix}-${i}-m2"></td>
                <td><input id="r1med-${prefix}-${bPrefix}-${i}-n3"></td>
                <td><input id="r1med-${prefix}-${bPrefix}-${i}-m3"></td></tr>`;
        }
        html += `</table>
            <p style="font-size:8px;color:var(--text-muted);">*Nota: Diâmetros nominais: Bow: 230,00mm louco; Bow 250,00mm acionado; H e R: 300,00mm.</p>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 10. DISTRIBUIÇÃO DE GRAXA
// ==============================================================
function renderizarGraxaR1() {
    const container = garantirContainer('r1-graxa');
    if (!container) return;
    const bases = ['Superior', 'Inferior'];
    let html = `<h3 style="color:var(--text-heading);">INSPEÇÃO DE DISTRIBUIÇÃO DE GRAXA</h3>
        <p style="font-size:9px;color:var(--text-muted);">*Nota: Checklist de vazamento (Tubulações e distribuidores)</p>`;
    bases.forEach(base => {
        const prefix = base === 'Superior' ? 'sup' : 'inf';
        html += `<h4>Base ${base}</h4>
            <table class="premium-table" style="font-size:9px;">
                <tr><th>Esquerda</th><th colspan="4">Status</th><th>Direita</th></tr>
                <tr><th></th><th>OK</th><th>VT</th><th>SA</th><th></th><th></th></tr>`;
        for (let i = 7; i >= 1; i--) {
            html += `<tr><td style="text-align:center;font-weight:bold;">${i}</td>
                <td style="text-align:center;"><input type="radio" name="r1grx-${prefix}-${i}" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="r1grx-${prefix}-${i}" value="VT"></td>
                <td style="text-align:center;"><input type="radio" name="r1grx-${prefix}-${i}" value="SA"></td>
                <td></td>
                <td style="text-align:center;font-weight:bold;">${i}</td></tr>`;
        }
        html += `</table>`;
    });
    html += `<p style="font-size:9px;color:var(--text-muted);">*Nota: VT – Vazamento em tubulação; SA – Sem alimentação;</p>`;
    container.innerHTML = html;
}

// ==============================================================
// 11. CHECKLIST DE MANUTENÇÃO (com P, G, Executante, Matrícula, Data)
// ==============================================================
function renderizarChecklistManutencaoR1() {
    const container = garantirContainer('r1-checklist-manutencao');
    if (!container) return;
    let html = `<h3 style="color:var(--text-heading);">CHECKLIST DE MANUTENÇÃO</h3>
        <table class="premium-table" style="font-size:9px;">
            <tr><th>Item</th><th>Descrição da Atividade</th><th style="width:30px;">P</th><th style="width:30px;">G</th><th>Executante</th><th>Matrícula</th><th>Data</th></tr>`;
    manutencaoR1.forEach((tarefa, index) => {
        html += `<tr><td style="text-align:center;font-weight:bold;">${tarefa.item}</td>
            <td style="font-size:9px;">${tarefa.desc}</td>
            <td style="text-align:center;"><input type="checkbox" id="r1-p-${index}"></td>
            <td style="text-align:center;"><input type="checkbox" id="r1-g-${index}"></td>
            <td><input id="r1-resp-${index}"></td>
            <td><input id="r1-mat-${index}"></td>
            <td><input type="date" id="r1-dat-${index}"></td></tr>`;
    });
    html += `</table>`;
    container.innerHTML = html;
}

// ==============================================================
// 12. MATERIAIS APLICADOS
// ==============================================================
function renderizarMateriaisR1() {
    const container = garantirContainer('r1-materiais');
    if (!container) return;
    let rows = '';
    for (let i = 1; i <= 30; i++) {
        rows += `<tr><td><input id="r1mat-desc-${i}" style="width:100%;"></td><td><input id="r1mat-qtd-${i}" style="width:60px;"></td></tr>`;
    }
    const html = `<h3 style="color:var(--text-heading);">MATERIAIS APLICADOS</h3>
        <table class="premium-table" style="font-size:9px;">
            <tr><th style="width:80%;">MATERIAIS</th><th style="width:20%;">QUANTIDADE</th></tr>
            ${rows}
        </table>`;
    container.innerHTML = html;
}

// ==============================================================
// 13. FUNÇÃO PRINCIPAL DE ABRIR
// ==============================================================
window.abrirFolhaoR1 = function(id) {
    ID_FOLHAO_R1_ATUAL = id;
    const modal = document.getElementById('modal-folhao-r1');
    if (!modal) {
        console.error("Modal #modal-folhao-r1 não encontrado!");
        return;
    }

    // Preenche cabeçalho
    const tagNameEl = document.getElementById('r1-tag-name');
    if (tagNameEl) tagNameEl.innerText = id;
    const dataInicio = document.getElementById('r1-data-inicio');
    const dataFim = document.getElementById('r1-data-fim');
    if (dataInicio) dataInicio.valueAsDate = new Date();
    if (dataFim) dataFim.valueAsDate = new Date();
    const motivoEl = document.getElementById('r1-motivo');
    if (motivoEl) motivoEl.value = '';

    // Renderiza todas as abas
    renderizarInspecaoChegadaR1();
    renderizarGapR1();
    renderizarCangalhasR1();
    renderizarPassLinesR1();
    renderizarCilindrosChegadaR1();
    renderizarCilindrosSaidaR1();
    renderizarInspecaoRolosR1('chegada');
    renderizarInspecaoRolosR1('saida');
    renderizarGraxaR1();
    renderizarChecklistManutencaoR1();
    renderizarMateriaisR1();

    modal.classList.remove('hidden');
    // Ativa a primeira aba
    window.trocarAbaR1({ currentTarget: document.querySelector('#modal-folhao-r1 .folhao-tab') }, 'r1-aba-dados');
};

// ==============================================================
// 14. FECHAR E TROCAR ABA
// ==============================================================
window.fecharFolhaoR1 = function() {
    const modal = document.getElementById('modal-folhao-r1');
    if (modal) modal.classList.add('hidden');
    ID_FOLHAO_R1_ATUAL = null;
};

window.trocarAbaR1 = function(evt, abaId) {
    const modal = document.getElementById('modal-folhao-r1');
    if (!modal) return;
    modal.querySelectorAll('.folhao-content').forEach(c => c.classList.add('hidden'));
    modal.querySelectorAll('.folhao-tab').forEach(b => b.classList.remove('active'));
    const aba = document.getElementById(abaId);
    if (aba) aba.classList.remove('hidden');
    if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');
};

// ==============================================================
// 15. GERAR PDF COMPLETO
// ==============================================================
window.salvarEImprimirFolhaoR1 = function() {
    if (!window.verificarAcesso || !window.verificarAcesso()) { alert("Acesso negado."); return; }
    if (!ID_FOLHAO_R1_ATUAL) { alert("Nenhuma TAG carregada."); return; }

    const tag = ID_FOLHAO_R1_ATUAL;
    const item = BANCO_ATIVOS.find(a => a.id === tag);
    if (item) {
        item.ton = 0;
        item.dias = 0;
        item.local = "Oficina / Reserva";
        localStorage.setItem("oms_ativos_v32_local", JSON.stringify(BANCO_ATIVOS));
    }

    // Coleta dados do cabeçalho
    const dtInicio = getV('r1-data-inicio') || new Date().toLocaleDateString('pt-BR');
    const dtFim = getV('r1-data-fim') || new Date().toLocaleDateString('pt-BR');
    const numSeg = getV('r1-num-segmento') || '______';
    const veio = document.getElementById('r1-veio')?.value || '';
    const motivo = getV('r1-motivo') || '_______________';
    const tipoExec = document.getElementById('r1-tipo-execucao')?.value || 'GERAL';

    // Função auxiliar para checklist de chegada
    function gerarLinhasChegada() {
        let html = '';
        let categorias = {};
        let currentGroup = "GERAL";
        itensChegadaR1.forEach(it => {
            if (it.grupo && it.grupo.trim() !== "") currentGroup = it.grupo;
            if (!categorias[currentGroup]) categorias[currentGroup] = [];
            categorias[currentGroup].push(it.desc);
        });
        let groupIndex = 0;
        for (const [nomeCategoria, perguntas] of Object.entries(categorias)) {
            html += `<tr><th colspan="3" style="background:#002b5e; color:#fff; font-size:10px; text-align:left; padding:4px; border:1px solid #000;">${nomeCategoria}</th></tr>`;
            html += `<tr><th style="border:1px solid #000; padding:3px; width:5%;">Item</th><th style="border:1px solid #000; padding:3px;">Descrição</th><th style="border:1px solid #000; padding:3px; width:12%;">Status</th></tr>`;
            perguntas.forEach((pergunta, index) => {
                const name = `r1-g${groupIndex}-q${index}`;
                const val = getRadioValue(name);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px;">${index+1}</td>
                    <td style="border:1px solid #000; padding:3px;">${pergunta}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${val}</td></tr>`;
            });
            groupIndex++;
        }
        return html;
    }

    // Gera tabela de GAP
    function gerarGapPDF() {
        let html = '';
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1gap-${i}-a`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1gap-${i}-b`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1gap-${i}-c`)}</td></tr>`;
        }
        return html;
    }

    // Gera tabela de Cangalhas
    function gerarCangalhasPDF() {
        let html = '';
        const bases = ['sup', 'inf'];
        const labels = ['Superior', 'Inferior'];
        bases.forEach((b, idx) => {
            html += `<tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">Base ${labels[idx]}</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Posição</th>
                    <th colspan="2" style="border:1px solid #000; padding:3px;">Bico A</th>
                    <th colspan="2" style="border:1px solid #000; padding:3px;">Bico B</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;"></th>
                    <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th>
                    <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th></tr>`;
            for (let i = 1; i <= 7; i++) {
                const a = getRadioValue(`r1cang-${b}-${i}-a`);
                const bVal = getRadioValue(`r1cang-${b}-${i}-b`);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px;">${i}ª</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${a === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${a === 'NOK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${bVal === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${bVal === 'NOK' ? 'X' : ''}</td></tr>`;
            }
        });
        return html;
    }

    // Gera Pass Line
    function gerarPassLinePDF(id, refs) {
        let html = '';
        refs.forEach((ref, i) => {
            html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i+1}°</td>
                <td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${ref}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`${id}-a-${i}`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`${id}-b-${i}`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`${id}-c-${i}`)}</td></tr>`;
        });
        return html;
    }

    // Gera Cilindros Chegada
    function gerarCilindrosChegadaPDF() {
        let html = '';
        const tipos = [
            { nome: 'Cilindro de Elevação', prefix: 'ce', pos: ['A','B','C','D'] },
            { nome: 'Cilindro Clamp (Porcas Hidráulicas)', prefix: 'cc', pos: ['A','B','C','D'] },
            { nome: 'Cilindros Motriz', prefix: 'cm', pos: ['A','B'] }
        ];
        tipos.forEach(t => {
            html += `<tr><th colspan="6" style="background:#ddd; border:1px solid #000; padding:3px;">${t.nome}</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Pos</th><th style="border:1px solid #000; padding:3px;">Número</th>
                    <th style="border:1px solid #000; padding:3px;">Produção</th><th style="border:1px solid #000; padding:3px;">OK</th>
                    <th style="border:1px solid #000; padding:3px;">NOK</th><th style="border:1px solid #000; padding:3px;">Obs</th></tr>`;
            t.pos.forEach(p => {
                const ok = getRadioValue(`r1cil-${t.prefix}-${p}`);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${p}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1cil-${t.prefix}-num-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1cil-${t.prefix}-prod-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${ok === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${ok === 'NOK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1cil-${t.prefix}-obs-${p}`)}</td></tr>`;
            });
        });
        return html;
    }

    // Gera Cilindros Saída
    function gerarCilindrosSaidaPDF() {
        let html = '';
        const tipos = [
            { nome: 'Cilindro de Elevação', prefix: 'se', pos: ['A','B','C','D'] },
            { nome: 'Cilindro Clamp (Porcas Hidráulicas)', prefix: 'sc', pos: ['A','B','C','D'] },
            { nome: 'Cilindros Motriz', prefix: 'sm', pos: ['A','B'] }
        ];
        tipos.forEach(t => {
            html += `<tr><th colspan="7" style="background:#ddd; border:1px solid #000; padding:3px;">${t.nome}</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Pos</th><th style="border:1px solid #000; padding:3px;">Número</th>
                    <th style="border:1px solid #000; padding:3px;">Produção</th><th style="border:1px solid #000; padding:3px;">Rep</th>
                    <th style="border:1px solid #000; padding:3px;">Reu</th><th style="border:1px solid #000; padding:3px;">Novo</th>
                    <th style="border:1px solid #000; padding:3px;">Obs</th></tr>`;
            t.pos.forEach(p => {
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${p}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1cils-${t.prefix}-num-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1cils-${t.prefix}-prod-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getCheckboxValue(`r1cils-${t.prefix}-rep-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getCheckboxValue(`r1cils-${t.prefix}-reu-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getCheckboxValue(`r1cils-${t.prefix}-nov-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1cils-${t.prefix}-obs-${p}`)}</td></tr>`;
            });
        });
        return html;
    }

    // Gera Rolos
    function gerarRolosPDF(tipo, base) {
        const prefix = tipo === 'chegada' ? 'ch' : 'sa';
        const bPrefix = base === 'Inferior' ? 'inf' : 'sup';
        let html = '';
        html += `<tr><th colspan="9" style="background:#ddd; border:1px solid #000; padding:3px;">Rolamento - Base ${base}</th></tr>
            <tr><th style="border:1px solid #000; padding:3px;">Pos</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">1</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">2</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">3</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">4</th></tr>
            <tr><th style="border:1px solid #000; padding:3px;"></th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td>`;
            for (let j = 1; j <= 4; j++) {
                const val = getRadioValue(`r1rol-${prefix}-${bPrefix}-${i}-${j}`);
                html += `<td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'OK' ? 'X' : ''}</td>
                         <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'NOK' ? 'X' : ''}</td>`;
            }
            html += `</tr>`;
        }
        html += `<tr><th colspan="9" style="background:#ddd; border:1px solid #000; padding:3px;">Teste Hidrostático - Base ${base}</th></tr>
            <tr><th style="border:1px solid #000; padding:3px;">Pos</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">1</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">2</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">3</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">4</th></tr>
            <tr><th style="border:1px solid #000; padding:3px;"></th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th>
                <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">NOK</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td>`;
            for (let j = 1; j <= 4; j++) {
                const val = getRadioValue(`r1hid-${prefix}-${bPrefix}-${i}-${j}`);
                html += `<td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'OK' ? 'X' : ''}</td>
                         <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'NOK' ? 'X' : ''}</td>`;
            }
            html += `</tr>`;
        }
        html += `<tr><th colspan="7" style="background:#ddd; border:1px solid #000; padding:3px;">Medidas dos Rolos - Base ${base}</th></tr>
            <tr><th style="border:1px solid #000; padding:3px;">Pos</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">1</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">2</th>
                <th colspan="2" style="border:1px solid #000; padding:3px;">3</th></tr>
            <tr><th style="border:1px solid #000; padding:3px;"></th>
                <th style="border:1px solid #000; padding:3px;">Num</th><th style="border:1px solid #000; padding:3px;">Medida</th>
                <th style="border:1px solid #000; padding:3px;">Num</th><th style="border:1px solid #000; padding:3px;">Medida</th>
                <th style="border:1px solid #000; padding:3px;">Num</th><th style="border:1px solid #000; padding:3px;">Medida</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1med-${prefix}-${bPrefix}-${i}-n1`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1med-${prefix}-${bPrefix}-${i}-m1`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1med-${prefix}-${bPrefix}-${i}-n2`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1med-${prefix}-${bPrefix}-${i}-m2`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1med-${prefix}-${bPrefix}-${i}-n3`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`r1med-${prefix}-${bPrefix}-${i}-m3`)}</td></tr>`;
        }
        return html;
    }

    // Gera Graxa
    function gerarGraxaPDF() {
        let html = '';
        const bases = ['sup', 'inf'];
        const labels = ['Superior', 'Inferior'];
        bases.forEach((b, idx) => {
            html += `<tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">Base ${labels[idx]}</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Esq</th>
                    <th style="border:1px solid #000; padding:3px;">OK</th><th style="border:1px solid #000; padding:3px;">VT</th>
                    <th style="border:1px solid #000; padding:3px;">SA</th><th style="border:1px solid #000; padding:3px;">Dir</th></tr>`;
            for (let i = 7; i >= 1; i--) {
                const val = getRadioValue(`r1grx-${b}-${i}`);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'VT' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'SA' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td></tr>`;
            }
        });
        return html;
    }

    // Gera Checklist de Manutenção
    function gerarManutencaoPDF() {
        let html = '';
        manutencaoR1.forEach((tarefa, index) => {
            const p = document.getElementById(`r1-p-${index}`)?.checked ? 'X' : '';
            const g = document.getElementById(`r1-g-${index}`)?.checked ? 'X' : '';
            const mat = getV(`r1-mat-${index}`);
            const data = getV(`r1-dat-${index}`);
            html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${tarefa.item}</td>
                <td style="border:1px solid #000; padding:3px; font-size:9px;">${tarefa.desc}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${p}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${g}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${mat}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${data}</td></tr>`;
        });
        return html;
    }

    // ==============================================================
    // MONTA HTML DO PDF
    // ==============================================================
    let htmlPDF = `
    <style>
        .pdf-base { font-family: Arial, sans-serif; font-size: 9px; color: #000; }
        .pdf-base table { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
        .pdf-base th, .pdf-base td { border: 1px solid #000; padding: 3px; }
        .pdf-base th { background: #e0e0e0; text-align: center; font-weight: bold; font-size: 9px; }
        .pdf-base .titulo-secao { background: #002b5e; color: #fff; font-weight: bold; padding: 4px; text-align: left; margin: 10px 0 4px 0; border: 1px solid #000; font-size: 10px; text-transform: uppercase; }
        .pdf-base .subtitulo { background: #d0d0d0; font-weight: bold; text-align: center; padding: 3px; font-size: 9px; }
        @media print { .quebra-pagina { break-before: page; page-break-before: always; margin-top: 10px; } }
    </style>
    <div class="pdf-base">
        <!-- Cabeçalho -->
        <div style="display: flex; border: 2px solid #000; border-bottom: 5px solid #002b5e; margin-bottom: 8px; align-items: center; background: #fff;">
            <div style="width: 20%; text-align: center; border-right: 2px solid #000; padding: 8px;"><span style="font-weight: 900; font-size: 28px; color: #002b5e; letter-spacing: -2px;">CSN</span></div>
            <div style="width: 60%; text-align: center; padding: 8px;">
                <h2 style="margin: 0; font-size: 12px; color: #000;">CHECK LIST GERAL SEGMENTOS STRAIGHTENER R-I MCC#4</h2>
                <p style="margin: 4px 0 0 0; font-size: 8px; color: #333; font-weight: bold;">DATA INÍCIO: ${dtInicio} | DATA FIM: ${dtFim}</p>
            </div>
            <div style="width: 20%; font-size: 9px; border-left: 2px solid #000; padding: 8px; line-height: 1.4; font-weight: bold;">
                <div style="color: #002b5e;">TAG: <span style="color:#000;">${tag}</span></div>
            </div>
        </div>

        <!-- Dados adicionais -->
        <table>
            <tr><td><strong>Nº SEGMENTO:</strong> ${numSeg}</td>
                <td><strong>VEIO(SAIDA):</strong> ${veio}</td>
                <td><strong>TIPO EXECUÇÃO:</strong> ${tipoExec}</td></tr>
            <tr><td><strong>MOTIVO:</strong> ${motivo}</td>
                <td colspan="2"><strong>VEIO(ENTRADA):</strong> ${veio}</td></tr>
        </table>

        <!-- INSPEÇÃO DE CHEGADA -->
        <div class="titulo-secao">1. INSPEÇÃO DE CHEGADA</div>
        <table>${gerarLinhasChegada()}</table>

        <div class="quebra-pagina"></div>

        <!-- AFERIÇÃO DE GAP -->
        <div class="titulo-secao">2. AFERIÇÃO DE GAP (255+0,3/-0,3)</div>
        <table>
            <tr><th style="width:15%;">CONJ. ROLO</th><th>Posição A</th><th>Posição B</th><th>Posição C</th></tr>
            ${gerarGapPDF()}
        </table>

        <!-- CANGALHAS -->
        <div class="titulo-secao">3. INSPEÇÃO DE CANGALHAS</div>
        <table>${gerarCangalhasPDF()}</table>

        <div class="quebra-pagina"></div>

        <!-- PASS LINE - CHEGADA -->
        <div class="titulo-secao">4. PASS LINE (CHEGADA)</div>
        <div style="display:flex; gap:8px; width:100%;">
            <div style="width:50%;"><table>
                <tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">BASE INFERIOR (CHEGADA)</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Conj</th><th style="border:1px solid #000; padding:3px;">Ref</th>
                    <th style="border:1px solid #000; padding:3px;">Pos A</th><th style="border:1px solid #000; padding:3px;">Pos B</th>
                    <th style="border:1px solid #000; padding:3px;">Pos C</th></tr>
                ${gerarPassLinePDF('r1-passline-inf-chegada', refPassLineInfR1)}
            </table></div>
            <div style="width:50%;"><table>
                <tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">BASE SUPERIOR (CHEGADA)</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Conj</th><th style="border:1px solid #000; padding:3px;">Ref</th>
                    <th style="border:1px solid #000; padding:3px;">Pos A</th><th style="border:1px solid #000; padding:3px;">Pos B</th>
                    <th style="border:1px solid #000; padding:3px;">Pos C</th></tr>
                ${gerarPassLinePDF('r1-passline-sup-chegada', refPassLineSupR1)}
            </table></div>
        </div>

        <!-- CILINDROS HIDRÁULICOS (CHEGADA) -->
        <div class="titulo-secao">5. CILINDROS HIDRÁULICOS (CHEGADA)</div>
        <table>${gerarCilindrosChegadaPDF()}</table>

        <div class="quebra-pagina"></div>

        <!-- INSPEÇÃO DE ROLOS (CHEGADA) -->
        <div class="titulo-secao">6. INSPEÇÃO DE ROLOS (CHEGADA)</div>
        <table>
            ${gerarRolosPDF('chegada', 'Inferior')}
            ${gerarRolosPDF('chegada', 'Superior')}
        </table>

        <div class="quebra-pagina"></div>

        <!-- GRAXA -->
        <div class="titulo-secao">7. INSPEÇÃO DE DISTRIBUIÇÃO DE GRAXA</div>
        <table>${gerarGraxaPDF()}</table>

        <!-- CHECKLIST DE MANUTENÇÃO -->
        <div class="titulo-secao">8. CHECKLIST DE MANUTENÇÃO</div>
        <table>
            <tr><th style="width:5%;">Item</th><th>Descrição da Atividade</th>
                <th style="width:4%;">P</th><th style="width:4%;">G</th>
                <th style="width:12%;">Matrícula</th><th style="width:12%;">Data</th></tr>
            ${gerarManutencaoPDF()}
        </table>

        <div class="quebra-pagina"></div>

        <!-- PASS LINE - SAÍDA -->
        <div class="titulo-secao">9. PASS LINE (SAÍDA FINAL)</div>
        <div style="display:flex; gap:8px; width:100%;">
            <div style="width:50%;"><table>
                <tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">BASE INFERIOR (SAÍDA)</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Conj</th><th style="border:1px solid #000; padding:3px;">Ref</th>
                    <th style="border:1px solid #000; padding:3px;">Pos A</th><th style="border:1px solid #000; padding:3px;">Pos B</th>
                    <th style="border:1px solid #000; padding:3px;">Pos C</th></tr>
                ${gerarPassLinePDF('r1-passline-inf-saida', refsInfSaiR1)}
            </table></div>
            <div style="width:50%;"><table>
                <tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">BASE SUPERIOR (SAÍDA)</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Conj</th><th style="border:1px solid #000; padding:3px;">Ref</th>
                    <th style="border:1px solid #000; padding:3px;">Pos A</th><th style="border:1px solid #000; padding:3px;">Pos B</th>
                    <th style="border:1px solid #000; padding:3px;">Pos C</th></tr>
                ${gerarPassLinePDF('r1-passline-sup-saida', refsSupSaiR1)}
            </table></div>
        </div>

        <!-- CILINDROS HIDRÁULICOS (SAÍDA) -->
        <div class="titulo-secao">10. CILINDROS HIDRÁULICOS (SAÍDA)</div>
        <table>${gerarCilindrosSaidaPDF()}</table>

        <div class="quebra-pagina"></div>

        <!-- INSPEÇÃO DE ROLOS (SAÍDA) -->
        <div class="titulo-secao">11. INSPEÇÃO DE ROLOS (SAÍDA)</div>
        <table>
            ${gerarRolosPDF('saida', 'Inferior')}
            ${gerarRolosPDF('saida', 'Superior')}
        </table>

        <!-- MATERIAIS -->
        <div class="titulo-secao">12. MATERIAIS APLICADOS</div>
        <table>
            <tr><th style="width:80%;">MATERIAIS</th><th style="width:20%;">QUANTIDADE</th></tr>
            ${[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30].map(i => `
                <tr><td>${getV(`r1mat-desc-${i}`)}</td><td>${getV(`r1mat-qtd-${i}`)}</td></tr>
            `).join('')}
        </table>

        <!-- ASSINATURAS -->
        <div style="margin-top:40px; display:flex; justify-content:space-around; text-align:center; font-size:10px; font-weight:bold;">
            <div><p>___________________________________</p><p>Líder Responsável / Operador</p></div>
            <div><p>___________________________________</p><p>Inspetor de Qualidade</p></div>
        </div>
    </div>`;

    // ===== SALVA NO HISTÓRICO =====
    if (typeof window.salvarLaudoNoHistorico === 'function') {
        window.salvarLaudoNoHistorico(tag, "Straightener R1 MCC 4", htmlPDF);
    }

    // ===== IMPRIME =====
    const printDiv = document.getElementById('print-content');
    if (!printDiv) { alert("Div 'print-content' não encontrada!"); return; }
    printDiv.innerHTML = htmlPDF;
    window.fecharFolhaoR1();
    if (typeof renderReparos === 'function') renderReparos();
    if (typeof renderReservas === 'function') renderReservas();
    if (typeof renderAtivos === 'function') renderAtivos();
    if (typeof renderPainelVeios === 'function') renderPainelVeios();
    if (typeof renderHistorico === 'function') renderHistorico();
    if (typeof window.calcularKpisGlobais === 'function') window.calcularKpisGlobais();
    if (typeof window.atualizarPainelCompleto === 'function') window.atualizarPainelCompleto();
    setTimeout(() => window.print(), 500);
};

console.log("✅ folhaoStraightenerR1.js carregado com todas as seções do documento oficial.");