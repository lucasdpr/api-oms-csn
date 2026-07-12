// folhao_straightener_r2.js - Módulo específico do STRAIGHTENER R-II (padrão BENDER)

let ID_FOLHAO_R2_ATUAL = null;

// ==============================================================
// 1. CONSTANTES - CHECKLIST DE CHEGADA (do PDF R2)
// ==============================================================
const itensChegadaR2 = [
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
    { grupo: "", desc: "Rolos travados." },
    { grupo: "", desc: "Mancais furados." },
    { grupo: "", desc: "Estrias do rolo puxador danificada." },
    { grupo: "", desc: "Conexões apertadas." }
];

// ==============================================================
// 2. CONSTANTES - PASS LINE (REFERÊNCIAS - 7 ROLOS)
// ==============================================================
const refPassLineInfChegR2 = ["55,19", "58,48", "59,70", "60,15", "60,01", "60,01", "60,01"];
const refPassLineSupChegR2 = ["39,46", "36,39", "35,26", "35,00", "34,99", "34,99", "34,99"];
const refPassLineInfSaiR2  = ["55,19", "58,48", "59,70", "60,15", "60,01", "60,01", "60,01"];
const refPassLineSupSaiR2  = ["39,46", "36,39", "35,26", "35,00", "34,99", "34,99", "34,99"];

// ==============================================================
// 3. CONSTANTES - CHECKLIST DE MANUTENÇÃO (R2)
// ==============================================================
const manutencaoR2 = [
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
    { item: "3.12", desc: "Desmontagem dos rolos inferior" },
    { item: "3.13", desc: "Desmontagem dos rolos superior" },
    { item: "3.14", desc: "Desmontagem da estrutura do rolo acionado" },
    { item: "3.15", desc: "Retirada dos cilindros motriz" },
    { item: "3.16", desc: "Desmontagem de buchas e conjuntos na base" },
    { item: "3.17", desc: "Desmontagem de buchas e conjuntos" },
    { item: "3.18", desc: "Preparar bases e barra para jateamento e pintura" },
    { item: "4.1", desc: "Desmontagem de proteções e preparação dos calços e base Inferior" },
    { item: "4.2", desc: "Troca de oring's" },
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
    { item: "6.3", desc: "Troca de oring's" },
    { item: "6.4", desc: "Desobstrução de tubulações de graxa e de refrigeração" },
    { item: "6.5", desc: "Montagem de proteções das tubulações e de stauff" },
    { item: "6.6", desc: "Verificar roscas dos parafusos M30" },
    { item: "6.7", desc: "Montagem do rolo motriz" },
    { item: "7.1", desc: "Preparação para receber estrutura e cilindros (Lines e mancais)" },
    { item: "7.2", desc: "Montagem de Cilindros Motriz" },
    { item: "7.3", desc: "Desmontagem de proteções e preparação dos calços e base Superior" },
    { item: "7.4", desc: "Troca de oring's" },
    { item: "7.5", desc: "Desobstrução das tubulações de graxa e de refrigeração" },
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
    { item: "8.4", desc: "Troca de oring's (completo)" },
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
// 4. FUNÇÕES DE RENDERIZAÇÃO (com 7 ROLOS)
// ==============================================================

// 4.1 Inspeção de Chegada
function renderizarInspecaoChegadaR2() {
    const tbody = document.getElementById('tabela-r2-chegada');
    if (!tbody) return;
    tbody.innerHTML = '';
    itensChegadaR2.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="font-code text-muted" style="text-align:center; font-weight:bold;">${String(index + 1).padStart(2, '0')}</td>
            <td>${item.grupo ? `<strong style="color: #f59e0b; font-size:11px;">${item.grupo}</strong><br>` : ''}${item.desc}</td>
            <td style="text-align:center;"><input type="radio" name="insp_r2_chg_${index}" value="SIM" checked></td>
            <td style="text-align:center;"><input type="radio" name="insp_r2_chg_${index}" value="NÃO"></td>
        `;
        tbody.appendChild(tr);
    });
}

// 4.2 GAP (Chegada e Saída) - 7 ROLOS
function renderizarGapR2(pfx) {
    const tbody = document.getElementById(`gap-r2-${pfx}-tbody`);
    if (!tbody) return;
    tbody.innerHTML = '';
    for (let i = 1; i <= 7; i++) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; font-weight:bold;">${i}</td>
            <td><input type="number" id="gap-r2-${pfx}-a-${i}" class="w-100" step="0.01" style="width:70px;"></td>
            <td><input type="number" id="gap-r2-${pfx}-b-${i}" class="w-100" step="0.01" style="width:70px;"></td>
            <td><input type="number" id="gap-r2-${pfx}-c-${i}" class="w-100" step="0.01" style="width:70px;"></td>
        `;
        tbody.appendChild(tr);
    }
}

// 4.3 Pass Line (7 rolos, 3 posições)
function renderizarPassLineR2(pfx, refs) {
    const tbody = document.getElementById(`pl-r2-${pfx}-tbody`);
    if (!tbody) return;
    tbody.innerHTML = '';
    refs.forEach((ref, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; font-weight:bold;">${index + 1}º</td>
            <td style="text-align:center; font-weight:bold;">${ref}</td>
            <td><input type="number" id="pl-r2-${pfx}-a-${index}" class="w-100" step="0.01" style="width:60px;"></td>
            <td><input type="number" id="pl-r2-${pfx}-b-${index}" class="w-100" step="0.01" style="width:60px;"></td>
            <td><input type="number" id="pl-r2-${pfx}-c-${index}" class="w-100" step="0.01" style="width:60px;"></td>
        `;
        tbody.appendChild(tr);
    });
}

// 4.4 Cangalhas (Base Superior e Inferior - 7 posições, Bicos A e B)
function renderizarCangalhasR2() {
    ['sup', 'inf'].forEach(base => {
        const tbody = document.getElementById(`cangalha-r2-${base}-tbody`);
        if (!tbody) return;
        tbody.innerHTML = '';
        for (let i = 1; i <= 7; i++) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="text-align:center; font-weight:bold;">${i}ª</td>
                <td style="text-align:center;"><select id="cang-r2-${base}-a-${i}" style="width:55px;"><option></option><option>OK</option><option>Ñ/OK</option></select></td>
                <td style="text-align:center;"><select id="cang-r2-${base}-b-${i}" style="width:55px;"><option></option><option>OK</option><option>Ñ/OK</option></select></td>
            `;
            tbody.appendChild(tr);
        }
    });
}

// 4.5 Cilindros Hidráulicos (Elevação, Clamp, Motriz)
function renderizarCilindrosR2() {
    const tipos = ['elevacao', 'clamp', 'motriz'];
    tipos.forEach(tipo => {
        const tbody = document.getElementById(`cil-r2-${tipo}-tbody`);
        if (!tbody) return;
        tbody.innerHTML = '';
        const posicoes = tipo === 'motriz' ? ['A', 'B'] : ['A', 'B', 'C', 'D'];
        posicoes.forEach(pos => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="text-align:center; font-weight:bold;">${pos}</td>
                <td><input id="cil-r2-${tipo}-num-${pos}" style="width:70px;" placeholder="Nº"></td>
                <td><input id="cil-r2-${tipo}-prod-${pos}" style="width:70px;" placeholder="Produção"></td>
                <td style="text-align:center;"><input type="checkbox" id="cil-r2-${tipo}-ok-${pos}"></td>
                <td style="text-align:center;"><input type="checkbox" id="cil-r2-${tipo}-nok-${pos}"></td>
                <td><input id="cil-r2-${tipo}-obs-${pos}" style="width:100%;" placeholder="Obs"></td>
            `;
            tbody.appendChild(tr);
        });
    });
}

// 4.6 Check de Lubrificação (7 rolos)
function renderizarLubrificacaoR2(pfx) {
    const tbody = document.getElementById(`lub-r2-${pfx}-tbody`);
    if (!tbody) return;
    tbody.innerHTML = '';
    for (let i = 0; i < 7; i++) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; font-weight:bold;">${i + 1}º</td>
            <td><select id="lub-r2-${pfx}-st-${i}" style="width:70px;"><option></option><option>OK</option><option>NOK</option></select></td>
            <td><input id="lub-r2-${pfx}-obs-${i}" style="width:100%;"></td>
        `;
        tbody.appendChild(tr);
    }
}

// 4.7 Inspeção de Rolos (7 rolos, 4 posições)
function renderizarInspecaoRolosR2(pfx) {
    const tbody = document.getElementById(`rol-r2-${pfx}-tbody`);
    if (!tbody) return;
    tbody.innerHTML = '';
    for (let i = 0; i < 7; i++) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; font-weight:bold;">${i + 1}</td>
            <td><select id="rol-r2-${pfx}-1-${i}" style="width:55px;"><option></option><option>OK</option><option>NOK</option></select></td>
            <td><select id="rol-r2-${pfx}-2-${i}" style="width:55px;"><option></option><option>OK</option><option>NOK</option></select></td>
            <td><select id="rol-r2-${pfx}-3-${i}" style="width:55px;"><option></option><option>OK</option><option>NOK</option></select></td>
            <td><select id="rol-r2-${pfx}-4-${i}" style="width:55px;"><option></option><option>OK</option><option>NOK</option></select></td>
        `;
        tbody.appendChild(tr);
    }
}

// 4.8 Medidas dos Rolos (7 rolos, 3 medições + classe)
function renderizarMedidasRolosR2(pfx) {
    const tbody = document.getElementById(`med-r2-${pfx}-tbody`);
    if (!tbody) return;
    tbody.innerHTML = '';
    for (let i = 0; i < 7; i++) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; font-weight:bold;">${i + 1}</td>
            <td><input id="med-r2-${pfx}-n1-${i}" style="width:35px;"></td>
            <td><input id="med-r2-${pfx}-m1-${i}" style="width:45px;"></td>
            <td><input id="med-r2-${pfx}-n2-${i}" style="width:35px;"></td>
            <td><input id="med-r2-${pfx}-m2-${i}" style="width:45px;"></td>
            <td><input id="med-r2-${pfx}-n3-${i}" style="width:35px;"></td>
            <td><input id="med-r2-${pfx}-m3-${i}" style="width:45px;"></td>
            <td><input id="med-r2-${pfx}-cls-${i}" style="width:55px;" placeholder="Classe"></td>
        `;
        tbody.appendChild(tr);
    }
}

// 4.9 Checklist de Manutenção
function renderizarChecklistManutencaoR2() {
    const tbody = document.getElementById('tabela-r2-manutencao');
    if (!tbody) return;
    tbody.innerHTML = '';
    manutencaoR2.forEach((tarefa, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; font-weight:bold; color:#f59e0b;">${tarefa.item}</td>
            <td style="font-size:11px;">${tarefa.desc}</td>
            <td style="text-align:center;"><input type="checkbox" id="chk-r2-p-${index}"></td>
            <td style="text-align:center;"><input type="checkbox" id="chk-r2-g-${index}"></td>
            <td><input type="text" id="resp-r2-${index}" style="width:80px;" placeholder="Resp."></td>
            <td><input type="text" id="mat-r2-${index}" style="width:80px;" placeholder="Matrícula"></td>
            <td><input type="date" id="dat-r2-${index}" style="width:100px;"></td>
        `;
        tbody.appendChild(tr);
    });
}

// 4.10 Materiais (6 linhas)
function renderizarMateriaisR2() {
    const tbody = document.getElementById('tabela-r2-materiais');
    if (!tbody) return;
    tbody.innerHTML = '';
    for (let i = 0; i < 6; i++) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input id="mat-r2-${i}" style="width:100%;" placeholder="Material"></td>
            <td><input id="qtd-r2-${i}" style="width:80px;" placeholder="Qtd"></td>
        `;
        tbody.appendChild(tr);
    }
}

// ==============================================================
// 5. TROCAR ABA (R2)
// ==============================================================
window.trocarAbaR2 = function(evt, abaId) {
    document.querySelectorAll('#modal-folhao-r2 .folhao-content').forEach(aba => {
        aba.classList.add('hidden');
        aba.classList.remove('active');
    });
    document.querySelectorAll('#modal-folhao-r2 .folhao-tab').forEach(btn => {
        btn.classList.remove('active');
    });

    let abaDestino = document.getElementById(abaId);
    if (abaDestino) {
        abaDestino.classList.remove('hidden');
        abaDestino.classList.add('active');
    }

    if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');
};

// ==============================================================
// 6. ABRIR FOLHÃO R2
// ==============================================================
window.abrirFolhaoR2 = function(id) {
    ID_FOLHAO_R2_ATUAL = id;
    let tagNameEl = document.getElementById('r2-tag-name');
    if (tagNameEl) tagNameEl.value = id;

    document.getElementById('modal-folhao-r2').classList.remove('hidden');

    // Renderiza todas as seções
    renderizarInspecaoChegadaR2();
    renderizarGapR2('cheg');
    renderizarGapR2('sai');
    renderizarPassLineR2('inf-cheg', refPassLineInfChegR2);
    renderizarPassLineR2('sup-cheg', refPassLineSupChegR2);
    renderizarPassLineR2('inf-sai', refPassLineInfSaiR2);
    renderizarPassLineR2('sup-sai', refPassLineSupSaiR2);
    renderizarCangalhasR2();
    renderizarCilindrosR2();
    renderizarLubrificacaoR2('inf');
    renderizarLubrificacaoR2('sup');
    renderizarInspecaoRolosR2('inf-cheg');
    renderizarInspecaoRolosR2('sup-cheg');
    renderizarInspecaoRolosR2('inf-sai');
    renderizarInspecaoRolosR2('sup-sai');
    renderizarMedidasRolosR2('inf-cheg');
    renderizarMedidasRolosR2('sup-cheg');
    renderizarMedidasRolosR2('inf-sai');
    renderizarMedidasRolosR2('sup-sai');
    renderizarChecklistManutencaoR2();
    renderizarMateriaisR2();

    let firstTab = document.querySelector('#modal-folhao-r2 .folhao-tab');
    if (firstTab) {
        window.trocarAbaR2({ currentTarget: firstTab }, 'r2-chegada');
    }

    let hoje = new Date().toISOString().split('T')[0];
    let dataInicio = document.getElementById('r2-data-inicio');
    let dataFim = document.getElementById('r2-data-fim');
    if (dataInicio) dataInicio.value = hoje;
    if (dataFim) dataFim.value = hoje;
};

// ==============================================================
// 7. SALVAR E IMPRIMIR PDF (R2) - CORRIGIDO
// ==============================================================
window.salvarEImprimirFolhaoR2 = function() {
    console.log("Iniciando geração de PDF para STRAIGHTENER R-II...");

    if (!ID_FOLHAO_R2_ATUAL) {
        alert("Erro: Nenhuma TAG R2 carregada no momento.");
        return;
    }

    let tag = ID_FOLHAO_R2_ATUAL;
    let item = window.BANCO_ATIVOS.find(a => a.id === tag);

    if (!item) {
        alert(`Erro: A TAG ${tag} não foi encontrada no BANCO_ATIVOS.`);
        return;
    }

    item.ton = 0;
    item.dias = 0;
    item.local = "Oficina / Reserva";
    localStorage.setItem("oms_ativos_v32_local", JSON.stringify(window.BANCO_ATIVOS));

    let btnPDF = `<button onclick="window.abrirFolhaoR2('${tag}')" class="btn-outline-danger" style="padding: 2px 8px; font-size: 10px; margin-left: 10px; cursor: pointer;"><i class="fas fa-file-pdf"></i> Visualizar Folhão</button>`;

    if (window.registrarHistorico) {
        window.registrarHistorico(tag, `Laudo Oficial (STRAIGHTENER R-II) concluído. <br><div style="margin-top: 5px;">${btnPDF}</div>`);
    }

    if (typeof renderReparos === 'function') renderReparos();
    if (typeof renderReservas === 'function') renderReservas();
    if (typeof renderAtivos === 'function') renderAtivos();
    if (window.calcularKpisGlobais) window.calcularKpisGlobais();

    // ========== CONSTRUÇÃO DO PDF ==========
    const hoje = new Date().toLocaleDateString('pt-BR');
    const dataInicio = document.getElementById('r2-data-inicio')?.value || hoje;
    const dataFim = document.getElementById('r2-data-fim')?.value || hoje;
    const motivo = document.getElementById('r2-motivo')?.value || 'Manutenção';
    const numSegmento = document.getElementById('r2-num-segmento')?.value || '';

    let html = `
    <style>
        .pdf-base { font-family: Arial, sans-serif; font-size: 10px; color: #000; }
        .pdf-base table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        .pdf-base th, .pdf-base td { border: 1px solid #000; padding: 4px; }
        .pdf-base th { background: #f0f0f0; text-align: center; font-weight: bold; }
        .pdf-base .titulo-secao { background: #002b5e; color: #fff; font-weight: bold; padding: 6px; text-align: left; margin: 10px 0; border: 1px solid #000; font-size: 11px;}
        @media print { .quebra-pagina { break-before: page; page-break-before: always; margin-top: 15px;} }
    </style>
    <div class="pdf-base">
        <div style="display: flex; border: 2px solid #000; border-bottom: 5px solid #002b5e; margin-bottom: 15px; align-items: center; background: #fff;">
            <div style="width: 20%; text-align: center; border-right: 2px solid #000; padding: 10px;">
                <span style="font-family: Arial, sans-serif; font-weight: 900; font-size: 34px; color: #002b5e; letter-spacing: -2px;">CSN</span>
            </div>
            <div style="width: 60%; text-align: center; padding: 10px;">
                <h2 style="margin: 0; font-size: 16px; color: #000; text-decoration: underline;">CHECK LIST GERAL SEGMENTOS STRAIGHTENER R-II</h2>
                <p style="margin: 5px 0 0 0; font-size: 10px; color: #333; text-transform: uppercase; font-weight: bold;">Laudo Oficial de Manutenção e Peritagem</p>
            </div>
            <div style="width: 20%; font-size: 10px; border-left: 2px solid #000; padding: 10px; line-height: 1.5; font-weight: bold;">
                <div style="color: #002b5e;">TAG: <span style="color:#000;">${tag}</span></div>
                <div>INÍCIO: <span style="color:#000; font-weight:normal;">${dataInicio}</span></div>
                <div>FIM: <span style="color:#000; font-weight:normal;">${dataFim}</span></div>
            </div>
        </div>

        <table style="margin-top:5px; background: #f9f9f9;">
            <tr><td><strong>Nº SEGMENTO:</strong> ${numSegmento}</td><td><strong>MOTIVO:</strong> ${motivo}</td><td><strong>TIPO EXECUÇÃO:</strong> ${document.querySelector('select#r2-tipo-exec')?.value || 'GERAL'}</td></tr>
        </table>

        <div class="titulo-secao">1. INSPEÇÃO DE CHEGADA</div>
        <table>
            <tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO DOS ITENS</th><th style="width:15%;">SIM</th><th style="width:15%;">NÃO</th></tr>
    `;

    itensChegadaR2.forEach((item, index) => {
        let radios = document.getElementsByName(`insp_r2_chg_${index}`);
        let sim = ' ', nao = ' ';
        for (let r of radios) {
            if (r.checked && r.value === 'SIM') sim = 'X';
            if (r.checked && r.value === 'NÃO') nao = 'X';
        }
        html += `<tr>
            <td style="text-align:center; font-weight:bold;">${String(index + 1).padStart(2, '0')}</td>
            <td>${item.grupo ? `<b>${item.grupo}</b><br>` : ''}${item.desc}</td>
            <td style="text-align:center;">${sim}</td>
            <td style="text-align:center;">${nao}</td>
        </tr>`;
    });

    html += `</table>
        <div class="quebra-pagina"></div>
    `;

    // GAP Chegada
    html += `<div class="titulo-secao">2. AFERIÇÃO DE GAP (CHEGADA) - 255+0,3/-0,3</div>
        <table><tr><th>CONJ. ROLO</th><th>Posição A</th><th>Posição B</th><th>Posição C</th></tr>`;
    for (let i = 1; i <= 7; i++) {
        html += `<tr>
            <td style="text-align:center; font-weight:bold;">${i}</td>
            <td style="text-align:center;">${document.getElementById(`gap-r2-cheg-a-${i}`)?.value || ''}</td>
            <td style="text-align:center;">${document.getElementById(`gap-r2-cheg-b-${i}`)?.value || ''}</td>
            <td style="text-align:center;">${document.getElementById(`gap-r2-cheg-c-${i}`)?.value || ''}</td>
        </tr>`;
    }
    html += `</table><div class="quebra-pagina"></div>`;

    // GAP Saída
    html += `<div class="titulo-secao">3. AFERIÇÃO DE GAP (SAÍDA) - 255+0,3/-0,3</div>
        <table><tr><th>CONJ. ROLO</th><th>Posição A</th><th>Posição B</th><th>Posição C</th></tr>`;
    for (let i = 1; i <= 7; i++) {
        html += `<tr>
            <td style="text-align:center; font-weight:bold;">${i}</td>
            <td style="text-align:center;">${document.getElementById(`gap-r2-sai-a-${i}`)?.value || ''}</td>
            <td style="text-align:center;">${document.getElementById(`gap-r2-sai-b-${i}`)?.value || ''}</td>
            <td style="text-align:center;">${document.getElementById(`gap-r2-sai-c-${i}`)?.value || ''}</td>
        </tr>`;
    }
    html += `</table><div class="quebra-pagina"></div>`;

    // Pass Line Chegada
    function gerarPassLineR2PDF(pfx, refs) {
        let html = `<table><tr><th>Conj. Rolo</th><th>Referência</th><th>Pos A</th><th>Pos B</th><th>Pos C</th></tr>`;
        refs.forEach((ref, index) => {
            html += `<tr>
                <td style="text-align:center; font-weight:bold;">${index + 1}º</td>
                <td style="text-align:center; font-weight:bold;">${ref}</td>
                <td style="text-align:center;">${document.getElementById(`pl-r2-${pfx}-a-${index}`)?.value || ''}</td>
                <td style="text-align:center;">${document.getElementById(`pl-r2-${pfx}-b-${index}`)?.value || ''}</td>
                <td style="text-align:center;">${document.getElementById(`pl-r2-${pfx}-c-${index}`)?.value || ''}</td>
            </tr>`;
        });
        html += `</table>`;
        return html;
    }

    html += `<div class="titulo-secao">4. PASS LINE (CHEGADA)</div>`;
    html += `<h4 style="font-size:11px;">Base Inferior</h4>${gerarPassLineR2PDF('inf-cheg', refPassLineInfChegR2)}`;
    html += `<h4 style="font-size:11px;">Base Superior</h4>${gerarPassLineR2PDF('sup-cheg', refPassLineSupChegR2)}`;
    html += `<div class="quebra-pagina"></div>`;

    // Pass Line Saída
    html += `<div class="titulo-secao">5. PASS LINE (SAÍDA)</div>`;
    html += `<h4 style="font-size:11px;">Base Inferior</h4>${gerarPassLineR2PDF('inf-sai', refPassLineInfSaiR2)}`;
    html += `<h4 style="font-size:11px;">Base Superior</h4>${gerarPassLineR2PDF('sup-sai', refPassLineSupSaiR2)}`;
    html += `<div class="quebra-pagina"></div>`;

    // Cangalhas
    html += `<div class="titulo-secao">6. INSPEÇÃO DE CANGALHAS</div>`;
    ['sup', 'inf'].forEach(base => {
        html += `<h4 style="font-size:11px;">Base ${base === 'sup' ? 'Superior' : 'Inferior'}</h4><table><tr><th>Posição</th><th>Bico A</th><th>Bico B</th></tr>`;
        for (let i = 1; i <= 7; i++) {
            let a = document.getElementById(`cang-r2-${base}-a-${i}`)?.value || '';
            let b = document.getElementById(`cang-r2-${base}-b-${i}`)?.value || '';
            html += `<tr><td style="text-align:center; font-weight:bold;">${i}ª</td><td style="text-align:center;">${a}</td><td style="text-align:center;">${b}</td></tr>`;
        }
        html += `</table>`;
    });
    html += `<div class="quebra-pagina"></div>`;

    // Cilindros Hidráulicos
    html += `<div class="titulo-secao">7. CILINDROS HIDRÁULICOS</div>`;
    const cilTipos = [
        { id: 'elevacao', label: 'Elevação' },
        { id: 'clamp', label: 'Clamp (Porcas Hidráulicas)' },
        { id: 'motriz', label: 'Motriz' }
    ];
    cilTipos.forEach(tipo => {
        html += `<h4 style="font-size:11px;">Cilindro ${tipo.label}</h4><table><tr><th>Pos</th><th>Número</th><th>Produção</th><th>OK</th><th>Ñ/OK</th><th>Observação</th></tr>`;
        const posicoes = tipo.id === 'motriz' ? ['A', 'B'] : ['A', 'B', 'C', 'D'];
        posicoes.forEach(pos => {
            let num = document.getElementById(`cil-r2-${tipo.id}-num-${pos}`)?.value || '';
            let prod = document.getElementById(`cil-r2-${tipo.id}-prod-${pos}`)?.value || '';
            let ok = document.getElementById(`cil-r2-${tipo.id}-ok-${pos}`)?.checked ? 'X' : '';
            let nok = document.getElementById(`cil-r2-${tipo.id}-nok-${pos}`)?.checked ? 'X' : '';
            let obs = document.getElementById(`cil-r2-${tipo.id}-obs-${pos}`)?.value || '';
            html += `<tr><td style="text-align:center; font-weight:bold;">${pos}</td><td style="text-align:center;">${num}</td><td style="text-align:center;">${prod}</td><td style="text-align:center;">${ok}</td><td style="text-align:center;">${nok}</td><td>${obs}</td></tr>`;
        });
        html += `</table>`;
    });
    html += `<div class="quebra-pagina"></div>`;

    // Check Lubrificação
    function gerarLubR2PDF(pfx) {
        let html = `<table><tr><th>Rolo</th><th>Status</th><th>Observação</th></tr>`;
        for (let i = 0; i < 7; i++) {
            let st = document.getElementById(`lub-r2-${pfx}-st-${i}`)?.value || '';
            let obs = document.getElementById(`lub-r2-${pfx}-obs-${i}`)?.value || '';
            html += `<tr><td style="text-align:center;">${i + 1}º</td><td style="text-align:center;">${st}</td><td>${obs}</td></tr>`;
        }
        html += `</table>`;
        return html;
    }
    html += `<div class="titulo-secao">8. CHECK DE LUBRIFICAÇÃO</div>`;
    html += `<h4 style="font-size:11px;">Base Inferior</h4>${gerarLubR2PDF('inf')}`;
    html += `<h4 style="font-size:11px;">Base Superior</h4>${gerarLubR2PDF('sup')}`;
    html += `<div class="quebra-pagina"></div>`;

    // Inspeção de Rolos
    function gerarRolR2PDF(pfx) {
        let html = `<table><tr><th>Pos</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>`;
        for (let i = 0; i < 7; i++) {
            let p1 = document.getElementById(`rol-r2-${pfx}-1-${i}`)?.value || '';
            let p2 = document.getElementById(`rol-r2-${pfx}-2-${i}`)?.value || '';
            let p3 = document.getElementById(`rol-r2-${pfx}-3-${i}`)?.value || '';
            let p4 = document.getElementById(`rol-r2-${pfx}-4-${i}`)?.value || '';
            html += `<tr><td style="text-align:center; font-weight:bold;">${i + 1}</td>
                <td style="text-align:center;">${p1}</td><td style="text-align:center;">${p2}</td>
                <td style="text-align:center;">${p3}</td><td style="text-align:center;">${p4}</td></tr>`;
        }
        html += `</table>`;
        return html;
    }
    html += `<div class="titulo-secao">9. INSPEÇÃO DE ROLOS (CHEGADA)</div>`;
    html += `<h4 style="font-size:11px;">Base Inferior</h4>${gerarRolR2PDF('inf-cheg')}`;
    html += `<h4 style="font-size:11px;">Base Superior</h4>${gerarRolR2PDF('sup-cheg')}`;
    html += `<div class="quebra-pagina"></div>`;

    html += `<div class="titulo-secao">10. INSPEÇÃO DE ROLOS (SAÍDA)</div>`;
    html += `<h4 style="font-size:11px;">Base Inferior</h4>${gerarRolR2PDF('inf-sai')}`;
    html += `<h4 style="font-size:11px;">Base Superior</h4>${gerarRolR2PDF('sup-sai')}`;
    html += `<div class="quebra-pagina"></div>`;

    // Medidas dos Rolos
    function gerarMedR2PDF(pfx) {
        let html = `<table><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Classe</th></tr>`;
        for (let i = 0; i < 7; i++) {
            let n1 = document.getElementById(`med-r2-${pfx}-n1-${i}`)?.value || '';
            let m1 = document.getElementById(`med-r2-${pfx}-m1-${i}`)?.value || '';
            let n2 = document.getElementById(`med-r2-${pfx}-n2-${i}`)?.value || '';
            let m2 = document.getElementById(`med-r2-${pfx}-m2-${i}`)?.value || '';
            let n3 = document.getElementById(`med-r2-${pfx}-n3-${i}`)?.value || '';
            let m3 = document.getElementById(`med-r2-${pfx}-m3-${i}`)?.value || '';
            let cls = document.getElementById(`med-r2-${pfx}-cls-${i}`)?.value || '';
            html += `<tr><td style="text-align:center; font-weight:bold;">${i + 1}</td>
                <td style="text-align:center;">${n1}</td><td style="text-align:center;">${m1}</td>
                <td style="text-align:center;">${n2}</td><td style="text-align:center;">${m2}</td>
                <td style="text-align:center;">${n3}</td><td style="text-align:center;">${m3}</td>
                <td style="text-align:center;">${cls}</td></tr>`;
        }
        html += `</table>`;
        return html;
    }
    html += `<div class="titulo-secao">11. MEDIDAS DOS ROLOS (CHEGADA)</div>`;
    html += `<h4 style="font-size:11px;">Base Inferior</h4>${gerarMedR2PDF('inf-cheg')}`;
    html += `<h4 style="font-size:11px;">Base Superior</h4>${gerarMedR2PDF('sup-cheg')}`;
    html += `<div class="quebra-pagina"></div>`;

    html += `<div class="titulo-secao">12. MEDIDAS DOS ROLOS (SAÍDA)</div>`;
    html += `<h4 style="font-size:11px;">Base Inferior</h4>${gerarMedR2PDF('inf-sai')}`;
    html += `<h4 style="font-size:11px;">Base Superior</h4>${gerarMedR2PDF('sup-sai')}`;
    html += `<div class="quebra-pagina"></div>`;

    // Checklist de Manutenção
    html += `<div class="titulo-secao">13. CHECKLIST DE MANUTENÇÃO</div>
        <table>
            <tr><th>Item</th><th>Descrição da Atividade</th><th>P</th><th>G</th><th>Executante</th><th>Matrícula</th><th>Data</th></tr>
    `;
    manutencaoR2.forEach((tarefa, index) => {
        let p = document.getElementById(`chk-r2-p-${index}`)?.checked ? 'X' : '';
        let g = document.getElementById(`chk-r2-g-${index}`)?.checked ? 'X' : '';
        let resp = document.getElementById(`resp-r2-${index}`)?.value || '';
        let mat = document.getElementById(`mat-r2-${index}`)?.value || '';
        let dat = document.getElementById(`dat-r2-${index}`)?.value || '';
        html += `<tr>
            <td style="text-align:center; font-weight:bold;">${tarefa.item}</td>
            <td style="font-size:10px;">${tarefa.desc}</td>
            <td style="text-align:center;">${p}</td>
            <td style="text-align:center;">${g}</td>
            <td style="text-align:center;">${resp}</td>
            <td style="text-align:center;">${mat}</td>
            <td style="text-align:center;">${dat}</td>
        </tr>`;
    });
    html += `</table><div class="quebra-pagina"></div>`;

    // Materiais
    html += `<div class="titulo-secao">14. MATERIAIS APLICADOS</div>
        <table><tr><th>Material</th><th>Quantidade</th></tr>`;
    for (let i = 0; i < 6; i++) {
        let mat = document.getElementById(`mat-r2-${i}`)?.value || '';
        let qtd = document.getElementById(`qtd-r2-${i}`)?.value || '';
        html += `<tr><td>${mat}</td><td style="text-align:center;">${qtd}</td></tr>`;
    }
    html += `</table><div class="quebra-pagina"></div>`;

    // Observações
    html += `<div class="titulo-secao">15. OBSERVAÇÕES</div>
        <div style="border:1px solid #000; padding:10px; min-height:50px;">${document.getElementById('r2-observacoes')?.value || ''}</div>
    `;

    // Assinaturas
    html += `
        <div style="margin-top: 50px; display: flex; justify-content: space-around; text-align: center; font-size: 12px; font-weight: bold; padding-bottom:30px;">
            <div><p>___________________________________</p><p>Líder Responsável / Operador</p></div>
            <div><p>___________________________________</p><p>Inspetor de Qualidade</p></div>
        </div>
    </div>`;

    let printContent = document.getElementById('print-content');
    if (!printContent) {
        alert("Erro: A div com id 'print-content' não foi encontrada no HTML.");
        return;
    }
    printContent.innerHTML = html;
    window.fecharFolhaoR2?.();
    setTimeout(() => window.print(), 500);
};

// ==============================================================
// 8. FECHAR FOLHÃO R2
// ==============================================================
window.fecharFolhaoR2 = function() {
    document.getElementById('modal-folhao-r2').classList.add('hidden');
    ID_FOLHAO_R2_ATUAL = null;
};

// ==============================================================
// 9. ADICIONAR LINHA MATERIAL
// ==============================================================
window.adicionarLinhaMaterialR2 = function() {
    const tbody = document.querySelector('#tabela-r2-materiais tbody');
    if (!tbody) return;
    const i = tbody.children.length;
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input id="mat-r2-${i}" style="width:100%;" placeholder="Material"></td>
        <td><input id="qtd-r2-${i}" style="width:80px;" placeholder="Qtd"></td>
    `;
    tbody.appendChild(tr);
};