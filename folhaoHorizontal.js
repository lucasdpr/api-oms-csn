// folhaoHorizontal.js - VERSÃO COMPLETA COM TODAS AS SEÇÕES DO DOCUMENTO OFICIAL


let ID_FOLHAO_HORIZ_ATUAL = null;

// ==============================================================
// 1. DADOS DAS TABELAS (transcritos do documento)
// ==============================================================

const itensChegadaHorizontal = [
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
    { grupo: "", desc: "Conexões apertadas." }
];

const refPassLineInfHoriz = ["60,00", "60,00", "60,00", "60,00", "60,00", "60,00", "60,00"];
const refPassLineSupHoriz = ["35,00", "35,00", "35,00", "35,00", "35,00", "35,00", "35,00"];

const manutencaoHorizontal = [
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
function renderizarInspecaoChegadaHorizontal() {
    const container = garantirContainer('container-check-recebimento-horizontal');
    if (!container) return;

    let categorias = {};
    let currentGroup = "GERAL";
    itensChegadaHorizontal.forEach(item => {
        if (item.grupo && item.grupo.trim() !== "") currentGroup = item.grupo;
        if (!categorias[currentGroup]) categorias[currentGroup] = [];
        categorias[currentGroup].push(item.desc);
    });

    let html = "";
    let groupIndex = 0;
    for (const [nomeCategoria, perguntas] of Object.entries(categorias)) {
        html += `<h4 style="margin: 20px 0 10px 0; color: var(--text-accent); border-bottom: 1px dashed var(--border-color); padding-bottom: 5px;"><i class="fas fa-tasks"></i> ${nomeCategoria}</h4><div class="checklist-container">`;
        perguntas.forEach((pergunta, index) => {
            const name = `hz-g${groupIndex}-q${index}`;
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
function renderizarGapHorizontal() {
    const container = garantirContainer('horiz-gap');
    if (!container) return;
    let html = `<h3 style="color:var(--text-heading);">AFERIÇÃO DE GAP (255+0,3/-0,3)</h3>
        <table class="premium-table" style="font-size:10px;">
            <tr><th>CONJ. ROLO</th><th>Posição A</th><th>Posição B</th><th>Posição C</th></tr>`;
    for (let i = 1; i <= 7; i++) {
        html += `<tr><td style="text-align:center;font-weight:bold;">${i}</td>
            <td><input id="hgap-${i}-a"></td>
            <td><input id="hgap-${i}-b"></td>
            <td><input id="hgap-${i}-c"></td></tr>`;
    }
    html += `</table>`;
    container.innerHTML = html;
}

// ==============================================================
// 5. CANGALHAS (Superior e Inferior)
// ==============================================================
function renderizarCangalhasHorizontal() {
    const container = garantirContainer('horiz-cangalhas');
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
                <td style="text-align:center;"><input type="radio" name="hcang-${prefix}-${i}-a" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="hcang-${prefix}-${i}-a" value="NOK"></td>
                <td style="text-align:center;"><input type="radio" name="hcang-${prefix}-${i}-b" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="hcang-${prefix}-${i}-b" value="NOK"></td></tr>`;
        }
        html += `</table>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 6. PASS LINE (Chegada e Saída)
// ==============================================================
function renderizarPassLinesHorizontal() {
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
    renderTable('horiz-passline-inf-chegada', refPassLineInfHoriz, 'PASS LINE - BASE INFERIOR (CHEGADA)');
    renderTable('horiz-passline-sup-chegada', refPassLineSupHoriz, 'PASS LINE - BASE SUPERIOR (CHEGADA)');
    renderTable('horiz-passline-inf-saida', refPassLineInfHoriz, 'PASS LINE - BASE INFERIOR (SAÍDA)');
    renderTable('horiz-passline-sup-saida', refPassLineSupHoriz, 'PASS LINE - BASE SUPERIOR (SAÍDA)');
}

// ==============================================================
// 7. CILINDROS HIDRÁULICOS (Chegada)
// ==============================================================
function renderizarCilindrosChegadaHorizontal() {
    const container = garantirContainer('horiz-cilindros-chegada');
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
                <td><input id="hcil-${t.prefix}-num-${p}"></td>
                <td><input id="hcil-${t.prefix}-prod-${p}"></td>
                <td style="text-align:center;"><input type="radio" name="hcil-${t.prefix}-${p}" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="hcil-${t.prefix}-${p}" value="NOK"></td>
                <td><input id="hcil-${t.prefix}-obs-${p}"></td></tr>`;
        });
        html += `</table>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 8. CILINDROS HIDRÁULICOS (Saída)
// ==============================================================
function renderizarCilindrosSaidaHorizontal() {
    const container = garantirContainer('horiz-cilindros-saida');
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
                <td><input id="hcils-${t.prefix}-num-${p}"></td>
                <td><input id="hcils-${t.prefix}-prod-${p}"></td>
                <td style="text-align:center;"><input type="checkbox" id="hcils-${t.prefix}-rep-${p}"></td>
                <td style="text-align:center;"><input type="checkbox" id="hcils-${t.prefix}-reu-${p}"></td>
                <td style="text-align:center;"><input type="checkbox" id="hcils-${t.prefix}-nov-${p}"></td>
                <td><input id="hcils-${t.prefix}-obs-${p}"></td></tr>`;
        });
        html += `</table>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 9. INSPEÇÃO DE ROLOS (Chegada e Saída)
// ==============================================================
function renderizarInspecaoRolosHorizontal(tipo) {
    const idContainer = `horiz-rolos-${tipo}`;
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
                html += `<td style="text-align:center;"><input type="radio" name="hrol-${prefix}-${bPrefix}-${i}-${j}" value="OK" checked></td>
                         <td style="text-align:center;"><input type="radio" name="hrol-${prefix}-${bPrefix}-${i}-${j}" value="NOK"></td>`;
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
                html += `<td style="text-align:center;"><input type="radio" name="hhid-${prefix}-${bPrefix}-${i}-${j}" value="OK" checked></td>
                         <td style="text-align:center;"><input type="radio" name="hhid-${prefix}-${bPrefix}-${i}-${j}" value="NOK"></td>`;
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
                <td><input id="hmed-${prefix}-${bPrefix}-${i}-n1"></td>
                <td><input id="hmed-${prefix}-${bPrefix}-${i}-m1"></td>
                <td><input id="hmed-${prefix}-${bPrefix}-${i}-n2"></td>
                <td><input id="hmed-${prefix}-${bPrefix}-${i}-m2"></td>
                <td><input id="hmed-${prefix}-${bPrefix}-${i}-n3"></td>
                <td><input id="hmed-${prefix}-${bPrefix}-${i}-m3"></td></tr>`;
        }
        html += `</table>
            <p style="font-size:8px;color:var(--text-muted);">*Nota: Diâmetros nominais: Bow: 230,00mm louco; Bow 250,00mm acionado; H e R: 300,00mm.</p>`;
    });
    container.innerHTML = html;
}

// ==============================================================
// 10. DISTRIBUIÇÃO DE GRAXA
// ==============================================================
function renderizarGraxaHorizontal() {
    const container = garantirContainer('horiz-graxa');
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
                <td style="text-align:center;"><input type="radio" name="hgrx-${prefix}-${i}" value="OK" checked></td>
                <td style="text-align:center;"><input type="radio" name="hgrx-${prefix}-${i}" value="VT"></td>
                <td style="text-align:center;"><input type="radio" name="hgrx-${prefix}-${i}" value="SA"></td>
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
function renderizarChecklistManutencaoHorizontal() {
    const container = garantirContainer('horiz-checklist-manutencao');
    if (!container) return;
    let html = `<h3 style="color:var(--text-heading);">CHECKLIST DE MANUTENÇÃO</h3>
        <table class="premium-table" style="font-size:9px;">
            <tr><th>Item</th><th>Descrição da Atividade</th><th style="width:30px;">P</th><th style="width:30px;">G</th><th>Executante</th><th>Matrícula</th><th>Data</th></tr>`;
    manutencaoHorizontal.forEach((tarefa, index) => {
        html += `<tr><td style="text-align:center;font-weight:bold;">${tarefa.item}</td>
            <td style="font-size:9px;">${tarefa.desc}</td>
            <td style="text-align:center;"><input type="checkbox" id="hz-p-${index}"></td>
            <td style="text-align:center;"><input type="checkbox" id="hz-g-${index}"></td>
            <td><input id="hz-resp-${index}"></td>
            <td><input id="hz-mat-${index}"></td>
            <td><input type="date" id="hz-dat-${index}"></td></tr>`;
    });
    html += `</table>`;
    container.innerHTML = html;
}

// ==============================================================
// 12. MATERIAIS APLICADOS
// ==============================================================
function renderizarMateriaisHorizontal() {
    const container = garantirContainer('horiz-materiais');
    if (!container) return;
    let rows = '';
    for (let i = 1; i <= 30; i++) {
        rows += `<tr><td><input id="hmat-desc-${i}" style="width:100%;"></td><td><input id="hmat-qtd-${i}" style="width:60px;"></td></tr>`;
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
window.abrirFolhaoHorizontal = function(id) {
    ID_FOLHAO_HORIZ_ATUAL = id;
    const modal = document.getElementById('modal-folhao-horizontal');
    if (!modal) {
        console.error("Modal #modal-folhao-horizontal não encontrado!");
        return;
    }

    // Preenche cabeçalho
    const tagNameEl = document.getElementById('horizontal-tag-name');
    if (tagNameEl) tagNameEl.innerText = id;
    const dataInicio = document.getElementById('horiz-data-inicio');
    const dataFim = document.getElementById('horiz-data-fim');
    if (dataInicio) dataInicio.valueAsDate = new Date();
    if (dataFim) dataFim.valueAsDate = new Date();
    const motivoEl = document.getElementById('horiz-motivo');
    if (motivoEl) motivoEl.value = '';

    // Renderiza todas as abas
    renderizarInspecaoChegadaHorizontal();
    renderizarGapHorizontal();
    renderizarCangalhasHorizontal();
    renderizarPassLinesHorizontal();
    renderizarCilindrosChegadaHorizontal();
    renderizarCilindrosSaidaHorizontal();
    renderizarInspecaoRolosHorizontal('chegada');
    renderizarInspecaoRolosHorizontal('saida');
    renderizarGraxaHorizontal();
    renderizarChecklistManutencaoHorizontal();
    renderizarMateriaisHorizontal();

    modal.classList.remove('hidden');
    // Ativa a primeira aba
    window.trocarAbaHorizontal({ currentTarget: document.querySelector('#modal-folhao-horizontal .folhao-tab') }, 'horiz-aba-dados');
};

// ==============================================================
// 14. FECHAR E TROCAR ABA
// ==============================================================
window.fecharFolhaoHorizontal = function() {
    const modal = document.getElementById('modal-folhao-horizontal');
    if (modal) modal.classList.add('hidden');
    ID_FOLHAO_HORIZ_ATUAL = null;
};

window.trocarAbaHorizontal = function(evt, abaId) {
    const modal = document.getElementById('modal-folhao-horizontal');
    if (!modal) return;
    modal.querySelectorAll('.folhao-content').forEach(c => c.classList.add('hidden'));
    modal.querySelectorAll('.folhao-tab').forEach(b => b.classList.remove('active'));
    const aba = document.getElementById(abaId);
    if (aba) aba.classList.remove('hidden');
    if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');
};

// ==============================================================
// 15. GERAR PDF COMPLETO E SALVAR NO BANCO (NUVEM + PDF NATIVO)
// ==============================================================
window.salvarEImprimirFolhaoHorizontal = async function() {
    if (!window.verificarAcesso || !window.verificarAcesso()) { alert("Acesso negado."); return; }
    if (!ID_FOLHAO_HORIZ_ATUAL) { alert("Nenhuma TAG carregada."); return; }

    const tag = ID_FOLHAO_HORIZ_ATUAL;

    // 1. CAPTURA DOS DADOS DO CABEÇALHO
    const dtInicio = getV('horiz-data-inicio') || new Date().toLocaleDateString('pt-BR');
    const dtFim = getV('horiz-data-fim') || new Date().toLocaleDateString('pt-BR');
    const numSeg = getV('horiz-num-segmento') || '______';
    const veio = document.getElementById('horiz-veio')?.value || '';
    const motivo = getV('horiz-motivo') || '_______________';
    const tipoExec = document.getElementById('horiz-tipo-execucao')?.value || 'GERAL';
    const novaMeta = getV('horiz-nova-meta') || 'Manter Atual'; // 🔥 CAPTURA A NOVA META

    // 2. PREPARA OS DADOS PARA A NUVEM
    const dadosFolhao = {
        id_peca: tag,
        tipo_equipamento: "Horizontal",
        tecnico: window.OPERADOR_LOGADO ? window.OPERADOR_LOGADO.nome : "Técnico",
        nova_meta: parseFloat(novaMeta) || 0,
        tipo_manutencao: tipoExec,
        dados_chegada: "{}", 
        dados_saida: "{}",
        status_reparo: "Concluido",
        pdf_base64: "" 
    };

    // 3. 🔥 COMUNICAÇÃO COM O PYTHON (ESPERA O BANCO SALVAR) 🔥
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

    // ==========================================================
    // FUNÇÕES AUXILIARES DO PDF (Mantidas do original)
    // ==========================================================
    function gerarLinhasChegada() {
        let html = '';
        let categorias = {};
        let currentGroup = "GERAL";
        itensChegadaHorizontal.forEach(it => {
            if (it.grupo && it.grupo.trim() !== "") currentGroup = it.grupo;
            if (!categorias[currentGroup]) categorias[currentGroup] = [];
            categorias[currentGroup].push(it.desc);
        });
        let groupIndex = 0;
        for (const [nomeCategoria, perguntas] of Object.entries(categorias)) {
            html += `<tr><th colspan="3" style="background:#002b5e; color:#fff; font-size:10px; text-align:left; padding:4px; border:1px solid #000;">${nomeCategoria}</th></tr>`;
            html += `<tr><th style="border:1px solid #000; padding:3px; width:5%;">Item</th><th style="border:1px solid #000; padding:3px;">Descrição</th><th style="border:1px solid #000; padding:3px; width:12%;">Status</th></tr>`;
            perguntas.forEach((pergunta, index) => {
                const name = `hz-g${groupIndex}-q${index}`;
                const val = getRadioValue(name);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px;">${index+1}</td>
                    <td style="border:1px solid #000; padding:3px;">${pergunta}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${val}</td></tr>`;
            });
            groupIndex++;
        }
        return html;
    }

    function gerarGapPDF() {
        let html = '';
        for (let i = 1; i <= 7; i++) {
            html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hgap-${i}-a`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hgap-${i}-b`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hgap-${i}-c`)}</td></tr>`;
        }
        return html;
    }

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
                const a = getRadioValue(`hcang-${b}-${i}-a`);
                const bVal = getRadioValue(`hcang-${b}-${i}-b`);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px;">${i}ª</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${a === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${a === 'NOK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${bVal === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${bVal === 'NOK' ? 'X' : ''}</td></tr>`;
            }
        });
        return html;
    }

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
                const ok = getRadioValue(`hcil-${t.prefix}-${p}`);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${p}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hcil-${t.prefix}-num-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hcil-${t.prefix}-prod-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${ok === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${ok === 'NOK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hcil-${t.prefix}-obs-${p}`)}</td></tr>`;
            });
        });
        return html;
    }

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
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hcils-${t.prefix}-num-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hcils-${t.prefix}-prod-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getCheckboxValue(`hcils-${t.prefix}-rep-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getCheckboxValue(`hcils-${t.prefix}-reu-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getCheckboxValue(`hcils-${t.prefix}-nov-${p}`)}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hcils-${t.prefix}-obs-${p}`)}</td></tr>`;
            });
        });
        return html;
    }

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
                const val = getRadioValue(`hrol-${prefix}-${bPrefix}-${i}-${j}`);
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
                const val = getRadioValue(`hhid-${prefix}-${bPrefix}-${i}-${j}`);
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
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hmed-${prefix}-${bPrefix}-${i}-n1`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hmed-${prefix}-${bPrefix}-${i}-m1`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hmed-${prefix}-${bPrefix}-${i}-n2`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hmed-${prefix}-${bPrefix}-${i}-m2`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hmed-${prefix}-${bPrefix}-${i}-n3`)}</td>
                <td style="text-align:center; border:1px solid #000; padding:3px;">${getV(`hmed-${prefix}-${bPrefix}-${i}-m3`)}</td></tr>`;
        }
        return html;
    }

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
                const val = getRadioValue(`hgrx-${b}-${i}`);
                html += `<tr><td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'OK' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'VT' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px;">${val === 'SA' ? 'X' : ''}</td>
                    <td style="text-align:center; border:1px solid #000; padding:3px; font-weight:bold;">${i}</td></tr>`;
            }
        });
        return html;
    }

    function gerarManutencaoPDF() {
        let html = '';
        manutencaoHorizontal.forEach((tarefa, index) => {
            const p = document.getElementById(`hz-p-${index}`)?.checked ? 'X' : '';
            const g = document.getElementById(`hz-g-${index}`)?.checked ? 'X' : '';
            const mat = getV(`hz-mat-${index}`);
            const data = getV(`hz-dat-${index}`);
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
    // 4. MONTA O HTML DO PDF
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
                <h2 style="margin: 0; font-size: 12px; color: #000;">CHECK LIST GERAL SEGMENTOS HORIZONTAL MCC#4</h2>
                <p style="margin: 4px 0 0 0; font-size: 8px; color: #333; font-weight: bold;">DATA INÍCIO: ${dtInicio} | DATA FIM: ${dtFim}</p>
            </div>
            <div style="width: 20%; font-size: 9px; border-left: 2px solid #000; padding: 8px; line-height: 1.4; font-weight: bold;">
                <div style="color: #002b5e;">TAG: <span style="color:#000;">${tag}</span></div>
            </div>
        </div>

        <!-- 🔥 TABELA CORRIGIDA COM A NOVA META E EXECUÇÃO 🔥 -->
        <table style="margin-bottom: 15px; border: 2px solid #000;">
            <tr>
                <td style="width: 25%;"><strong>Nº SEGMENTO:</strong> ${numSeg}</td>
                <td style="width: 30%;"><strong>MOTIVO:</strong> ${motivo}</td>
                <td style="width: 25%; color: #002b5e;"><strong>EXECUÇÃO:</strong> ${tipoExec}</td>
                <td style="width: 20%; background-color: #f0f0f0; text-align: center;"><strong>NOVA META:</strong> ${novaMeta}</td>
            </tr>
            <tr>
                <td colspan="2"><strong>VEIO (ENTRADA):</strong> ${veio}</td>
                <td colspan="2"><strong>VEIO (SAÍDA):</strong> ${veio}</td>
            </tr>
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
                ${gerarPassLinePDF('horiz-passline-inf-chegada', refPassLineInfHoriz)}
            </table></div>
            <div style="width:50%;"><table>
                <tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">BASE SUPERIOR (CHEGADA)</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Conj</th><th style="border:1px solid #000; padding:3px;">Ref</th>
                    <th style="border:1px solid #000; padding:3px;">Pos A</th><th style="border:1px solid #000; padding:3px;">Pos B</th>
                    <th style="border:1px solid #000; padding:3px;">Pos C</th></tr>
                ${gerarPassLinePDF('horiz-passline-sup-chegada', refPassLineSupHoriz)}
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
                ${gerarPassLinePDF('horiz-passline-inf-saida', refPassLineInfHoriz)}
            </table></div>
            <div style="width:50%;"><table>
                <tr><th colspan="5" style="background:#ddd; border:1px solid #000; padding:3px;">BASE SUPERIOR (SAÍDA)</th></tr>
                <tr><th style="border:1px solid #000; padding:3px;">Conj</th><th style="border:1px solid #000; padding:3px;">Ref</th>
                    <th style="border:1px solid #000; padding:3px;">Pos A</th><th style="border:1px solid #000; padding:3px;">Pos B</th>
                    <th style="border:1px solid #000; padding:3px;">Pos C</th></tr>
                ${gerarPassLinePDF('horiz-passline-sup-saida', refPassLineSupHoriz)}
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
                <tr><td>${getV(`hmat-desc-${i}`)}</td><td>${getV(`hmat-qtd-${i}`)}</td></tr>
            `).join('')}
        </table>

        <!-- ASSINATURAS -->
        <div style="margin-top:40px; display:flex; justify-content:space-around; text-align:center; font-size:10px; font-weight:bold;">
            <div><p>___________________________________</p><p>Líder Responsável / Operador</p></div>
            <div><p>___________________________________</p><p>Inspetor de Qualidade</p></div>
        </div>
    </div>`;

    // 5. ATUALIZA A INTERFACE E IMPRIME SÓ DEPOIS DE TUDO CERTO
    const printDiv = document.getElementById('print-content');
    if (!printDiv) { alert("Div 'print-content' não encontrada!"); return; }
    printDiv.innerHTML = htmlPDF;
    
    window.fecharFolhaoHorizontal();
    if (typeof renderReparos === 'function') renderReparos();
    if (typeof renderReservas === 'function') renderReservas();
    if (typeof renderAtivos === 'function') renderAtivos();
    if (typeof renderPainelVeios === 'function') renderPainelVeios();
    if (typeof renderHistorico === 'function') renderHistorico();
    if (typeof window.calcularKpisGlobais === 'function') window.calcularKpisGlobais();
    if (typeof window.atualizarPainelCompleto === 'function') window.atualizarPainelCompleto();
    
    setTimeout(() => window.print(), 500);
};