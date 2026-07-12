// ==========================================
// FOLHÃO DESEMPENADEIRA (CADEIRA SUPERIOR/INFERIOR)
// ==========================================

let ID_DESEMP_ATUAL = null;

// 1. INSPEÇÃO DE SAÍDA (15 itens)
const itensInspecaoDesemp = [
    { grupo: "LUBRIFICAÇÃO", desc: "Sistema de lubrificação isento de vazamentos." },
    { grupo: "", desc: "Mancal lubrificado." },
    { grupo: "REFRIGERAÇÃO", desc: "Flexíveis isentos de vazamentos." },
    { grupo: "", desc: "Tubulações isentas de empenos." },
    { grupo: "", desc: "Tubulações furadas." },
    { grupo: "CILINDROS", desc: "Isento de vazamento." },
    { grupo: "", desc: "Conexões completas e apertadas." },
    { grupo: "", desc: "Flexíveis isentos de vazamentos." },
    { grupo: "", desc: "Tubulações isentas de empenos." },
    { grupo: "ESTRUTURA", desc: "Tubulações isentas de amassados." },
    { grupo: "", desc: "Proteções isentas de avarias." },
    { grupo: "", desc: "Estrutura com break-out." },
    { grupo: "", desc: "Estrutura limpa e pintada." },
    { grupo: "", desc: "Mancal isento de avarias." },
    { grupo: "", desc: "Conexões apertadas." }
];

// 2. MOTIVOS DE SAÍDA
const motivosSaidaDesemp = [
    "VIDA - PLANO DE TROCA",
    "DESGASTE",
    "TRINCAS",
    "ROLAMENTO QUEBRADO",
    "ROLO QUEBRADO",
    "VAZAMENTO NO CILINDRO HIDRÁULICO",
    "EMPENO",
    "ACIDENTE"
];

// 3. MATERIAIS (dois conjuntos: Inferior e Superior)
const MATERIAIS_INFERIOR = [
    { codigo: "8008878", descricao: "ACOPLAMENTO DESENHO CSN DM-028275" },
    { codigo: "1210851", descricao: "ANEL O'RING 139,40 X 3,10MM - MANGA" },
    { codigo: "1646007", descricao: "ANEL O'RING 199,30MM X 5,70MM -ESPAÇADOR" },
    { codigo: "1205526", descricao: "ARRUELA DE PRESSÃO M10" },
    { codigo: "1606249", descricao: "ARRUELA DE PRESSÃO M12 INOX" },
    { codigo: "1205317", descricao: "ARRUELA DE PRESSÃO M20" },
    { codigo: "8061614", descricao: "ARRUELA DE SEGURANÇA NTN MB-30 - ARANHA" },
    { codigo: "1640576", descricao: "BUCHA HITACHI 0296769 MC.7-TAMPA INTERNA" },
    { codigo: "8005265", descricao: "CHAVETA DESENHO HITACHI 0294751 MC.3" },
    { codigo: "1640573", descricao: "ESPAÇADOR HITACHI 0296769 MC.3 - MANGA" },
    { codigo: "1640569", descricao: "ESPAÇADOR HITACHI 0296770 MC.4 - G.INF" },
    { codigo: "1640570", descricao: "ESPAÇADOR HITACHI 0296770 MC.5 - P.INF" },
    { codigo: "1640555", descricao: "GUIA HITACHI 0294770 MC.1 - LISO-10" },
    { codigo: "1640559", descricao: "GUIA HITACHI 0294770 MC.2 - LISO-20" },
    { codigo: "1640560", descricao: "GUIA HITACHI 0294770 MC.3 - LISO - 30" },
    { codigo: "1640556", descricao: "GUIA HITACHI 0294770 MC.4 - PEQ.-10" },
    { codigo: "1640561", descricao: "GUIA HITACHI 0294770 MC.5 - PEQ.-20" },
    { codigo: "1640562", descricao: "GUIA HITACHI 0294770 MC.6 - PEQ.-30" },
    { codigo: "1640553", descricao: "GUIA HITACHI 0294771 MC.4 - 2-SAL-10" },
    { codigo: "1640567", descricao: "GUIA HITACHI 0294771 MC.5 - 2-SAL-20" },
    { codigo: "1640568", descricao: "GUIA HITACHI 0294771 MC.6 - 2-SAL-30" },
    { codigo: "1640566", descricao: "GUIA HITACHI 0294771 MC.8 - 1-SAL-20" },
    { codigo: "1640565", descricao: "GUIA HITACHI 0294771 MC.9 - 1-SAL-30" },
    { codigo: "9227139", descricao: "JUNTA DEUBLIN 2425000003 1,2 - (DUO -ROLO ACIONADO)" },
    { codigo: "9155306", descricao: "JUNTA DEUBLIN 2425000004 1, 2 (MONO - ROLO NÃO ACIONADO)" },
    { codigo: "1640582", descricao: "MANCAL HITACHI 0294049 MC.1- INF 400MM" },
    { codigo: "1640583", descricao: "MANCAL HITACHI 0294050 MC.1- INF.420MM" },
    { codigo: "1204944", descricao: "PARAFUSO CABEÇA SEXTAVADA M10 X 45MM" },
    { codigo: "1221385", descricao: "PARAFUSO SEXT AISI316 M12X 30MM (Junta Rotativa)" },
    { codigo: "1620774", descricao: "PARAFUSO SEXT CL8.8 M12X 25MM (Junta Rotativa)" },
    { codigo: "1042518", descricao: "PINO GRAXEIRO 1/8\" TIPO RETO - BOZZA 627" },
    { codigo: "1740070", descricao: "PORCA DESENHO HITACHI 0296769 MC.2" },
    { codigo: "1210487", descricao: "RETENTOR DI 160 X DE 190 X 16MM - VITON" },
    { codigo: "1640578", descricao: "RETENTOR DI 190 X DE 220 X 15MM - VITON" },
    { codigo: "1639748", descricao: "ROLAMENTO 24032 MB-W33-C4S1" },
    { codigo: "1640571", descricao: "TAMPA HITACHI 0296769 MC.1 - EXTERNA" },
    { codigo: "1639420", descricao: "PARAFUSO CABEÇA CIL.SEXT.INT.M20 X 45MM" },
    { codigo: "8023476", descricao: "PARAFUSO CABEÇA CIL.SEXT.INT.M20 X 50MM" },
    { codigo: "8011321", descricao: "PAPELAO HIDR ARAMIDA 1,6X 1500X 1600MM" }
];

const MATERIAIS_SUPERIOR = [
    { codigo: "1219088", descricao: "ANEL ELASTICO TIPO \"E\" 55MM" },
    { codigo: "8003064", descricao: "ANEL O'RING 11 X 3,00MM - VITON" },
    { codigo: "1210851", descricao: "ANEL O'RING 139,40 X 3,10MM - MANGA" },
    { codigo: "1646007", descricao: "ANEL O'RING 199,30MM X 5,70MM -ESPAÇADOR" },
    { codigo: "1205526", descricao: "ARRUELA DE PRESSÃO M10" },
    { codigo: "1606249", descricao: "ARRUELA DE PRESSÃO M12 INOX" },
    { codigo: "1205317", descricao: "ARRUELA DE PRESSÃO M20" },
    { codigo: "8061614", descricao: "ARRUELA DE SEGURANÇA NTN MB-30 - ARANHA" },
    { codigo: "1640576", descricao: "BUCHA HITACHI 0296769 MC.7-TAMPA INTERNA" },
    { codigo: "1216378", descricao: "BUCHA REDUÇÃO 1/2\" X 3/8\" - BSP" },
    { codigo: "8023215", descricao: "BUJAO Ø 1/4\" SEXTAVADO INTERNO - INOX" },
    { codigo: "1059049", descricao: "CONTRA PINO 3/8\" X 5\" COMPRIMENTO" },
    { codigo: "1083053", descricao: "COTOVELO MACHO/FEMEA 1\" - TIPO CACHIMBO" },
    { codigo: "1640573", descricao: "ESPAÇADOR HITACHI 0296769 MC.3 - MANGA" },
    { codigo: "1640574", descricao: "ESPAÇADOR HITACHI 0296769 MC.4 - P.SUP." },
    { codigo: "1640575", descricao: "ESPAÇADOR HITACHI 0296769 MC.5 - G.SUP" },
    { codigo: "1195185", descricao: "GRAMPO TIPO \"U\" DE 1\" - INOX" },
    { codigo: "1640555", descricao: "GUIA HITACHI 0294770 MC.1 - LISO-10" },
    { codigo: "1640558", descricao: "GUIA HITACHI 0294770 MC.12-PINO MANCAL30" },
    { codigo: "1640563", descricao: "GUIA HITACHI 0294770 MC.13 - PINO MANCAL" },
    { codigo: "1640564", descricao: "GUIA HITACHI 0294770 MC.14-PINO MANCAL50" },
    { codigo: "1640559", descricao: "GUIA HITACHI 0294770 MC.2 - LISO-20" },
    { codigo: "1640560", descricao: "GUIA HITACHI 0294770 MC.3 - LISO - 30" },
    { codigo: "1640556", descricao: "GUIA HITACHI 0294770 MC.4 - PEQ.-10" },
    { codigo: "1640561", descricao: "GUIA HITACHI 0294770 MC.5 - PEQ.-20" },
    { codigo: "1640562", descricao: "GUIA HITACHI 0294770 MC.6 - PEQ.-30" },
    { codigo: "1640553", descricao: "GUIA HITACHI 0294771 MC.4 - 2-SAL-10" },
    { codigo: "1640567", descricao: "GUIA HITACHI 0294771 MC.5 - 2-SAL-20" },
    { codigo: "1640568", descricao: "GUIA HITACHI 0294771 MC.6 - 2-SAL-30" },
    { codigo: "1640554", descricao: "GUIA HITACHI 0294771 MC.7 - 1-SAL-10" },
    { codigo: "1640566", descricao: "GUIA HITACHI 0294771 MC.8 - 1-SAL-20" },
    { codigo: "1640565", descricao: "GUIA HITACHI 0294771 MC.9 - 1-SAL-30" },
    { codigo: "9155306", descricao: "JUNTA DEUBLIN 2425000004 1, 2 (MONO)" },
    { codigo: "8038832", descricao: "LUVA CONFORME DESENHO CSN-DH048001 MC1" },
    { codigo: "8038831", descricao: "LUVA CONFORME DESENHO CSN-DH048001 MC2" },
    { codigo: "1639859", descricao: "MANCAL HITACHI 0294045 MC.1-SUP.FIXO 400" },
    { codigo: "1640579", descricao: "MANCAL HITACHI 0294046 MC.1- SUP.MOV.400" },
    { codigo: "1640580", descricao: "MANCAL HITACHI 0294047 MC.1-SUP.FIXO 420" },
    { codigo: "1640581", descricao: "MANCAL HITACHI 0294048 MC.1-SUP.MOV 420" },
    { codigo: "1268042", descricao: "MANGUEIRA SBR 9,5 X 650MM" },
    { codigo: "9265349", descricao: "MANGUEIRA SBR 12,7 X 600MM (COD.ANTIGO 1268039)" }
];

// ==============================================================
// FUNÇÕES DE RENDERIZAÇÃO
// ==============================================================

// 1. Renderizar Inspeção de Saída
function renderizarInspecaoDesemp() {
    const tbody = document.querySelector('#tabela-desemp-inspecao tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    itensInspecaoDesemp.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center; font-weight:bold;">${String(index + 1).padStart(2, '0')}</td>
            <td>${item.grupo ? `<strong style="color: #f59e0b; font-size:11px;">${item.grupo}</strong><br>` : ''}${item.desc}</td>
            <td style="text-align:center;"><input type="radio" name="desemp_inspecao_${index}" value="SIM" checked></td>
            <td style="text-align:center;"><input type="radio" name="desemp_inspecao_${index}" value="NÃO"></td>
        `;
        tbody.appendChild(tr);
    });
}

// 2. Renderizar Motivo de Saída
function renderizarMotivoDesemp() {
    const tbody = document.querySelector('#tabela-desemp-motivo tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    motivosSaidaDesemp.forEach((motivo, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-weight:bold;">${motivo}</td>
            <td style="text-align:center;"><input type="radio" name="desemp_motivo_${index}" value="SIM"></td>
            <td style="text-align:center;"><input type="radio" name="desemp_motivo_${index}" value="NÃO" checked></td>
        `;
        tbody.appendChild(tr);
    });
}

// 3. Carregar Materiais (Inferior ou Superior)
window.carregarMateriaisDesemp = function(tipo) {
    const tbody = document.querySelector('#tabela-desemp-materiais tbody');
    if (!tbody) return;
    const materiais = tipo === 'INFERIOR' ? MATERIAIS_INFERIOR : MATERIAIS_SUPERIOR;
    tbody.innerHTML = '';
    materiais.forEach((mat, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-family:monospace; font-size:12px;">${mat.codigo}</td>
            <td>${mat.descricao}</td>
            <td><input type="number" id="desemp_mat_qtd_${index}" style="width:70px;" placeholder="Qtd"></td>
        `;
        tbody.appendChild(tr);
    });
    alert(`Materiais de Cadeira ${tipo} carregados!`);
};

// 4. Adicionar linha de material
window.adicionarLinhaMaterialDesemp = function() {
    const tbody = document.querySelector('#tabela-desemp-materiais tbody');
    if (!tbody) return;
    const i = tbody.children.length;
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input id="desemp_mat_cod_${i}" style="width:100%;" placeholder="Código"></td>
        <td><input id="desemp_mat_desc_${i}" style="width:100%;" placeholder="Descrição"></td>
        <td><input id="desemp_mat_qtd_${i}" style="width:70px;" placeholder="Qtd"></td>
    `;
    tbody.appendChild(tr);
};

// 5. Trocar Aba
window.trocarAbaDesemp = function(evt, abaId) {
    document.querySelectorAll('#modal-folhao-desempenadeira .folhao-content').forEach(aba => {
        aba.classList.add('hidden');
        aba.classList.remove('active');
    });
    document.querySelectorAll('#modal-folhao-desempenadeira .folhao-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    const target = document.getElementById(abaId);
    if (target) {
        target.classList.remove('hidden');
        target.classList.add('active');
    }
    if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');
};

// 6. Abrir Folhão
window.abrirFolhaoDesempenadeira = function(id) {
    ID_DESEMP_ATUAL = id;
    const item = window.BANCO_ATIVOS.find(a => a.id === id);
    if (!item) {
        alert('Equipamento não encontrado!');
        return;
    }

    const modal = document.getElementById('modal-folhao-desempenadeira');
    if (!modal) {
        alert('Modal da Desempenadeira não encontrado!');
        return;
    }

    // Preenche a TAG e campos iniciais
    document.getElementById('desemp-tag-ativo').value = id;

    // Define o tipo de cadeira (Superior ou Inferior) automaticamente
    const tipoSelect = document.getElementById('desemp-tipo-cadeira');
    const tipoSelectDados = document.getElementById('desemp-tipo-cadeira-dados');
    if (item.tipo === 'Cadeira Superior') {
        tipoSelect.value = 'SUPERIOR';
        tipoSelectDados.value = 'SUPERIOR';
    } else if (item.tipo === 'Cadeira Inferior') {
        tipoSelect.value = 'INFERIOR';
        tipoSelectDados.value = 'INFERIOR';
    }

    // Carrega os materiais correspondentes automaticamente
    const tipoAtual = tipoSelect.value;
    window.carregarMateriaisDesemp(tipoAtual);

    // Renderiza as tabelas
    renderizarInspecaoDesemp();
    renderizarMotivoDesemp();

    // Abre o modal
    modal.classList.remove('hidden');

    // Abre a primeira aba
    const firstTab = document.querySelector('#modal-folhao-desempenadeira .folhao-tab');
    if (firstTab) {
        window.trocarAbaDesemp({ currentTarget: firstTab }, 'desemp-aba-dados');
    }

    // Preenche datas
    const hoje = new Date().toISOString().split('T')[0];
    document.getElementById('desemp-data-montagem').value = hoje;
    document.getElementById('desemp-data-troca').value = hoje;
};

// 7. Fechar Folhão
window.fecharFolhaoDesempenadeira = function() {
    document.getElementById('modal-folhao-desempenadeira').classList.add('hidden');
    ID_DESEMP_ATUAL = null;
};

// 8. Salvar e Imprimir PDF
window.salvarEImprimirFolhaoDesemp = function() {
    if (!ID_DESEMP_ATUAL) {
        alert('Nenhuma TAG carregada.');
        return;
    }

    const tag = ID_DESEMP_ATUAL;
    const item = window.BANCO_ATIVOS.find(a => a.id === tag);
    if (!item) {
        alert('Equipamento não encontrado!');
        return;
    }

    // Coleta dados do formulário
    const dataMontagem = document.getElementById('desemp-data-montagem')?.value || '';
    const dataTroca = document.getElementById('desemp-data-troca')?.value || '';
    const motivo = document.getElementById('desemp-motivo')?.value || 'Manutenção';
    const numCadeira = document.getElementById('desemp-num-cadeira')?.value || '';
    const veio = document.getElementById('desemp-veio')?.value || '';
    const tipoCadeira = document.getElementById('desemp-tipo-cadeira')?.value || 'INFERIOR';
    const numRolo = document.getElementById('desemp-num-rolo')?.value || '';
    const tipoExec = document.getElementById('desemp-tipo-exec')?.value || 'GERAL';

    // Coleta dos motivos de saída
    let motivosSelecionados = [];
    motivosSaidaDesemp.forEach((motivoLabel, index) => {
        const radios = document.getElementsByName(`desemp_motivo_${index}`);
        let selecionado = 'NÃO';
        for (let r of radios) {
            if (r.checked && r.value === 'SIM') selecionado = 'SIM';
        }
        if (selecionado === 'SIM') {
            motivosSelecionados.push(motivoLabel);
        }
    });
    const outrosMotivo = document.getElementById('desemp-motivo-outros')?.value || '';
    if (outrosMotivo) motivosSelecionados.push(`OUTROS: ${outrosMotivo}`);

    // Coleta das medidas dos mancais
    const mancalA = document.getElementById('desemp-mancal-a')?.value || '';
    const mancalB = document.getElementById('desemp-mancal-b')?.value || '';
    const mancalAp = document.getElementById('desemp-mancal-ap')?.value || '';
    const mancalBp = document.getElementById('desemp-mancal-bp')?.value || '';
    const mancalFixo = document.getElementById('desemp-mancal-fixo')?.value || '';
    const mancalMovel = document.getElementById('desemp-mancal-movel')?.value || '';

    // Coleta dos cilindros
    const cilFixo = document.getElementById('desemp-cil-fixo')?.value || '';
    const cilMovel = document.getElementById('desemp-cil-movel')?.value || '';
    const cilFixoRep = document.getElementById('desemp-cil-fixo-rep')?.checked ? 'X' : '';
    const cilFixoReut = document.getElementById('desemp-cil-fixo-reut')?.checked ? 'X' : '';
    const cilMovelRep = document.getElementById('desemp-cil-movel-rep')?.checked ? 'X' : '';
    const cilMovelReut = document.getElementById('desemp-cil-movel-reut')?.checked ? 'X' : '';

    // Coleta dos sobressalentes
    const sobFixoNovo = document.getElementById('desemp-sob-fixo-novo')?.checked ? 'X' : '';
    const sobFixoReut = document.getElementById('desemp-sob-fixo-reut')?.checked ? 'X' : '';
    const sobMovelNovo = document.getElementById('desemp-sob-movel-novo')?.checked ? 'X' : '';
    const sobMovelReut = document.getElementById('desemp-sob-movel-reut')?.checked ? 'X' : '';
    const sobAranhaNovo = document.getElementById('desemp-sob-aranha-novo')?.checked ? 'X' : '';
    const sobAranhaReut = document.getElementById('desemp-sob-aranha-reut')?.checked ? 'X' : '';
    const sobNuNovo = document.getElementById('desemp-sob-rol-nu-novo')?.checked ? 'X' : '';
    const sobNuReut = document.getElementById('desemp-sob-rol-nu-reut')?.checked ? 'X' : '';
    const sob24032Novo = document.getElementById('desemp-sob-rol-24032-novo')?.checked ? 'X' : '';
    const sob24032Reut = document.getElementById('desemp-sob-rol-24032-reut')?.checked ? 'X' : '';
    const sobJuntaNovo = document.getElementById('desemp-sob-junta-novo')?.checked ? 'X' : '';
    const sobJuntaReut = document.getElementById('desemp-sob-junta-reut')?.checked ? 'X' : '';

    // Geração do PDF
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
                <h2 style="margin: 0; font-size: 16px; color: #000; text-decoration: underline;">CHECK LIST GERAL DESEMPENADEIRA - CADEIRA ${tipoCadeira}</h2>
                <p style="margin: 5px 0 0 0; font-size: 10px; color: #333; text-transform: uppercase; font-weight: bold;">Laudo Oficial de Manutenção e Peritagem</p>
            </div>
            <div style="width: 20%; font-size: 10px; border-left: 2px solid #000; padding: 10px; line-height: 1.5; font-weight: bold;">
                <div style="color: #002b5e;">TAG: <span style="color:#000;">${tag}</span></div>
                <div>MONTAGEM: <span style="color:#000; font-weight:normal;">${dataMontagem}</span></div>
                <div>TROCA: <span style="color:#000; font-weight:normal;">${dataTroca}</span></div>
            </div>
        </div>

        <table style="margin-top:5px; background: #f9f9f9;">
            <tr><td><strong>Nº CADEIRA:</strong> ${numCadeira}</td><td><strong>VEIO:</strong> ${veio}</td><td><strong>TIPO:</strong> ${tipoCadeira}</td></tr>
            <tr><td><strong>Nº ROLO:</strong> ${numRolo}</td><td><strong>MOTIVO:</strong> ${motivo}</td><td><strong>TIPO EXECUÇÃO:</strong> ${tipoExec}</td></tr>
        </table>
    `;

    // 1. INSPEÇÃO DE SAÍDA
    html += `<div class="titulo-secao">1. INSPEÇÃO DE SAÍDA</div>
        <table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:15%;">SIM</th><th style="width:15%;">NÃO</th></tr>`;
    itensInspecaoDesemp.forEach((item, index) => {
        const radios = document.getElementsByName(`desemp_inspecao_${index}`);
        let sim = ' ', nao = ' ';
        for (let r of radios) {
            if (r.checked && r.value === 'SIM') sim = 'X';
            if (r.checked && r.value === 'NÃO') nao = 'X';
        }
        html += `<tr><td style="text-align:center; font-weight:bold;">${String(index+1).padStart(2,'0')}</td>
            <td>${item.grupo ? `<b>${item.grupo}</b><br>` : ''}${item.desc}</td>
            <td style="text-align:center;">${sim}</td>
            <td style="text-align:center;">${nao}</td></tr>`;
    });
    html += `</table><div class="quebra-pagina"></div>`;

    // 2. MOTIVO DE SAÍDA
    html += `<div class="titulo-secao">2. MOTIVO DE SAÍDA DA MCC</div>
        <table><tr><th>MOTIVO</th><th style="width:15%;">SIM</th><th style="width:15%;">NÃO</th></tr>`;
    motivosSaidaDesemp.forEach((motivoLabel, index) => {
        const radios = document.getElementsByName(`desemp_motivo_${index}`);
        let sim = ' ', nao = ' ';
        for (let r of radios) {
            if (r.checked && r.value === 'SIM') sim = 'X';
            if (r.checked && r.value === 'NÃO') nao = 'X';
        }
        html += `<tr><td style="font-weight:bold;">${motivoLabel}</td>
            <td style="text-align:center;">${sim}</td>
            <td style="text-align:center;">${nao}</td></tr>`;
    });
    if (outrosMotivo) {
        html += `<tr><td style="font-weight:bold;">OUTROS: ${outrosMotivo}</td><td style="text-align:center;">X</td><td style="text-align:center;"></td></tr>`;
    }
    html += `</table><div class="quebra-pagina"></div>`;

    // 3. MANCAIS
    html += `<div class="titulo-secao">3. INSPEÇÃO DOS MANCAIS</div>
        <table>
            <tr><th>Referência</th><th>Valor (mm)</th></tr>
            <tr><td><strong>A</strong></td><td>${mancalA}</td></tr>
            <tr><td><strong>B</strong></td><td>${mancalB}</td></tr>
            <tr><td><strong>A'</strong></td><td>${mancalAp}</td></tr>
            <tr><td><strong>B'</strong></td><td>${mancalBp}</td></tr>
            <tr><td><strong>Fixo</strong></td><td>${mancalFixo}</td></tr>
            <tr><td><strong>Móvel</strong></td><td>${mancalMovel}</td></tr>
        </table>
        <div style="margin-top:5px;"><strong>Máximo:</strong> 240,15 mm | <strong>Mínima:</strong> 240,05 mm</div>
        <div class="quebra-pagina"></div>`;

    // 4. SOBRESSALENTES
    html += `<div class="titulo-secao">4. SOBRESSALENTES DE MONTAGEM</div>
        <table><tr><th>Componente</th><th>Novo</th><th>Reutilizado</th></tr>
        <tr><td>Mancal fixo</td><td style="text-align:center;">${sobFixoNovo}</td><td style="text-align:center;">${sobFixoReut}</td></tr>
        <tr><td>Mancal móvel</td><td style="text-align:center;">${sobMovelNovo}</td><td style="text-align:center;">${sobMovelReut}</td></tr>
        <tr><td>Aranha</td><td style="text-align:center;">${sobAranhaNovo}</td><td style="text-align:center;">${sobAranhaReut}</td></tr>
        <tr><td>Rolamento Nu 1032</td><td style="text-align:center;">${sobNuNovo}</td><td style="text-align:center;">${sobNuReut}</td></tr>
        <tr><td>Rolamento 24032</td><td style="text-align:center;">${sob24032Novo}</td><td style="text-align:center;">${sob24032Reut}</td></tr>
        <tr><td>Junta rotativa</td><td style="text-align:center;">${sobJuntaNovo}</td><td style="text-align:center;">${sobJuntaReut}</td></tr>
    </table><div class="quebra-pagina"></div>`;

    // 5. CILINDROS
    html += `<div class="titulo-secao">5. CILINDROS</div>
        <table><tr><th>Posição</th><th>Faixa Amarela (mm)</th><th>Reparado</th><th>Reutilizado</th></tr>
        <tr><td><strong>Fixo</strong></td><td>${cilFixo}</td><td style="text-align:center;">${cilFixoRep}</td><td style="text-align:center;">${cilFixoReut}</td></tr>
        <tr><td><strong>Móvel</strong></td><td>${cilMovel}</td><td style="text-align:center;">${cilMovelRep}</td><td style="text-align:center;">${cilMovelReut}</td></tr>
    </table><div class="quebra-pagina"></div>`;

    // 6. MATERIAIS
    html += `<div class="titulo-secao">6. MATERIAIS APLICADOS (CADEIRA ${tipoCadeira})</div>
        <table><tr><th>Código</th><th>Descrição</th><th>Quantidade</th></tr>`;
    const tbodyMateriais = document.querySelector('#tabela-desemp-materiais tbody');
    if (tbodyMateriais) {
        const linhas = tbodyMateriais.querySelectorAll('tr');
        linhas.forEach((row, idx) => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 3) {
                const codigo = cells[0].textContent.trim() || cells[0].querySelector('input')?.value || '';
                const descricao = cells[1].textContent.trim() || cells[1].querySelector('input')?.value || '';
                const qtd = cells[2].querySelector('input')?.value || '';
                html += `<tr><td>${codigo}</td><td>${descricao}</td><td style="text-align:center;">${qtd}</td></tr>`;
            }
        });
    }
    html += `</table><div class="quebra-pagina"></div>`;

    // OBSERVAÇÕES
    html += `<div class="titulo-secao">7. OBSERVAÇÕES</div>
        <div style="border:1px solid #000; padding:10px; min-height:50px;">${document.getElementById('desemp-observacoes')?.value || ''}</div>`;

    // ASSINATURAS
    html += `
        <div style="margin-top: 50px; display: flex; justify-content: space-around; text-align: center; font-size: 12px; font-weight: bold; padding-bottom:30px;">
            <div><p>___________________________________</p><p>Líder Responsável / Operador</p></div>
            <div><p>___________________________________</p><p>Inspetor de Qualidade</p></div>
        </div>
    </div>`;

    const printContent = document.getElementById('print-content');
    if (!printContent) {
        alert('Elemento print-content não encontrado.');
        return;
    }
    printContent.innerHTML = html;

    // Atualiza o banco
    item.ton = 0;
    item.dias = 0;
    item.local = "Oficina / Reserva";
    localStorage.setItem("oms_ativos_v32_local", JSON.stringify(window.BANCO_ATIVOS));

    if (window.registrarHistorico) {
        window.registrarHistorico(tag, `Laudo Desempenadeira (${tipoCadeira}) concluído.`);
    }

    window.fecharFolhaoDesempenadeira?.();
    setTimeout(() => window.print(), 500);
};