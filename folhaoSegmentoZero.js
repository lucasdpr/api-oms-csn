import { BANCO_ATIVOS } from './banco.js';
import { renderAtivos, renderReparos, renderReservas } from './ui.js';

let ID_FOLHAO_SEGZERO_ATUAL = null;

export function getV(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
}

export function getRadioValue(name) {
    const radios = document.getElementsByName(name);
    for (let r of radios) if (r.checked) return r.value;
    return '';
}

// ==============================================================
// 1. DADOS DAS TABELAS (Transcritos do Documento Oficial)
// ==============================================================
const itensChegadaSegZero = [
    { grupo: "LUBRIFICAÇÃO", desc: "Distribuidores de graxa com vazamentos" },
    { grupo: "", desc: "Distribuidores de graxa com agarramentos" },
    { grupo: "", desc: "Tubulações de graxa amassadas ou danificadas" },
    { grupo: "", desc: "Flexíveis com vazamentos e/ou avarias" },
    { grupo: "", desc: "Tubulações de graxa (inox), com avarias" },
    { grupo: "REFRIGERAÇÃO", desc: "Resfriadores com vazamento" },
    { grupo: "", desc: "Resfriadores com empeno" },
    { grupo: "", desc: "Bicos de spray obstruídos" },
    { grupo: "", desc: "Tubulação com avarias" },
    { grupo: "", desc: "Uniões com avarias" },
    { grupo: "ESTRUTURA", desc: "Proteções dos parafusos em perfeito estado, sem avarias" },
    { grupo: "", desc: "Rolamentos quebrados" },
    { grupo: "", desc: "Mancais soltos e avariados" },
    { grupo: "", desc: "Rolos girando normalmente sem restrições" },
    { grupo: "", desc: "Estrutura com break-out" }
];

const itensSaidaSegZero = [
    { grupo: "LUBRIFICAÇÃO", desc: "Distribuidores de graxa sem vazamentos, isentos de agarramento" },
    { grupo: "", desc: "Mancais lubrificados" },
    { grupo: "", desc: "Flexíveis apertados e distorcidos" },
    { grupo: "", desc: "Pressão de teste entre 90 a 110 kgf/cm2 (pressão de referência)." },
    { grupo: "", desc: "Tubulações em inox, sem avarias" },
    { grupo: "REFRIGERAÇÃO", desc: "Flexíveis isentos de vazamentos" },
    { grupo: "", desc: "Resfriadores isentos de empenos" },
    { grupo: "", desc: "Bicos de spray alinhados e isentos de obstruções" },
    { grupo: "", desc: "Tubulação apertada sem avaria" },
    { grupo: "", desc: "Teste de pressão lateral com 5kg/cm² (Pressão referência)" },
    { grupo: "", desc: "Uniões apertadas isentas de vazamento e avarias" },
    { grupo: "", desc: "Uniões montadas na tubulação 2'' da cangalha inferior" },
    { grupo: "ESTRUTURA", desc: "Proteções dos parafusos fixadas" },
    { grupo: "", desc: "Estrutura jateada e pintada" },
    { grupo: "", desc: "Gap em conformidade com o desenho" },
    { grupo: "", desc: "Rolos girando normalmente sem restrições" },
    { grupo: "", desc: "Chapa de proteção soldada." }
];

const materiaisSegZero = [
    { cod: "1205772", desc: "ARRUELA DE PRESSÃO M16" },
    { cod: "1203902", desc: "ARRUELA DE PRESSAO M24 DIN 127" },
    { cod: "1205307", desc: "ARRUELA DE PRESSÃO M36" },
    { cod: "1203775", desc: "ARRUELA LISA M64 X 66MM X 115MM" },
    { cod: "1777550", desc: "BASE DESENHO HITACHI 0294000 MC.1 - PÉ" },
    { cod: "1660305", desc: "CARCAÇA DESENHO HITACHI 0144798 MC1 INFERIOR" },
    { cod: "1660305", desc: "CARCAÇA DESENHO HITACHI 0294079 MC1" },
    { cod: "1660303", desc: "CARCAÇA HITACHI 2245098 SUPERIOR" },
    { cod: "1672147", desc: "CARCAÇA LATERAL HITACHI 2253621 MC.1" },
    { cod: "1672146", desc: "CARCAÇA LATERAL HITACHI 2253621 MC.2" },
    { cod: "8288919", desc: "CONEXÃO 1/4\" COMPRESSÃO 188D-E-1" },
    { cod: "9140946", desc: "CORPO CSN DM613216 1" },
    { cod: "1691878", desc: "COTOVELO 1.1/4\" X 90º ROSCA BSP" },
    { cod: "1064442", desc: "COTOVELO 1/4\" X 90º" },
    { cod: "8097039", desc: "DISTRIBUIDOR GRAXA 3/8 X1/4\" NPTF 2 SAID" },
    { cod: "1211859", desc: "ENGATE RAPIDO 1.1/4\"" },
    { cod: "1211500", desc: "ENGATE RAPIDO 2\"" },
    { cod: "1268070", desc: "ENGATE RÁPIDO 3/8\" - GRAXA" },
    { cod: "1195298", desc: "FITA DE ARAMIDA 1\" X 1,7MM X 30 METROS" },
    { cod: "1624645", desc: "MANGUEIRA 3/8\" X 1400MM (GRAXA)" },
    { cod: "1204966", desc: "PARAF CB SEXT M16X140MM" },
    { cod: "1204620", desc: "PARAFUSO CABEÇA SEXT.M12 X 45MM - INOX" },
    { cod: "8003560", desc: "PARAFUSO CABEÇA SEXT.M16 X 70MM-INOX" },
    { cod: "1628930", desc: "PARAFUSO CABEÇA SEXT.M16 X 90MM-INOX" },
    { cod: "1204624", desc: "PARAFUSO CABEÇA SEXTAVADA M12 X 30MM" },
    { cod: "8010789", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 115MM" },
    { cod: "1221020", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 150MM" },
    { cod: "1615479", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 160MM" },
    { cod: "1615369", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 175MM" },
    { cod: "1204967", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 180MM" },
    { cod: "1205571", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 190MM" },
    { cod: "1205334", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 200MM" },
    { cod: "1205193", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 210MM" },
    { cod: "1219654", desc: "PARAFUSO CABEÇA SEXTAVADA M16 X 90MM" },
    { cod: "1203880", desc: "PARAFUSO CABEÇA SEXTAVADA M36 X 150MM" },
    { cod: "1620873", desc: "PARAFUSO CABEÇA SEXTAVADA M36 X 440MM" },
    { cod: "1205431", desc: "PARAFUSO CABEÇA SEXTAVADA M64 X 170MM" },
    { cod: "1204965", desc: "PARAFUSO CABEÇA SEXTAVADO M16 X 120MM" },
    { cod: "1205144", desc: "PARAFUSO CIL CL10.9 M16X 150MM" },
    { cod: "1752138", desc: "PINO HITACHI 0294015 2" },
    { cod: "8500175", desc: "PLACA HITACHI 0293493 1" },
    { cod: "8500174", desc: "PLACA HITACHI 0293493 2" },
    { cod: "9272310", desc: "PONTA UNIJET TP1285L - 12,3 L/MIN" },
    { cod: "9140945", desc: "PORCA FIX. INOX PONTA UNIJET" },
    { cod: "1205361", desc: "PORCA SEXTAVADA M12" },
    { cod: "1204312", desc: "PORCA SEXTAVADA M16" },
    { cod: "1228240", desc: "PORCA SEXTAVADA M24" },
    { cod: "1206197", desc: "PORCA SEXTAVADA M64" },
    { cod: "1642482", desc: "RESFRIADOR DESENHO HITACHI 0295300 MC.1" },
    { cod: "1642484", desc: "RESFRIADOR DESENHO HITACHI 0295300 MC.31" },
    { cod: "1642483", desc: "RESFRIADOR DESENHO HITACHI 0295301MC.12" },
    { cod: "1642481", desc: "RESFRIADOR DESENHO HITACHI 0295302 MC.25" },
    { cod: "8287526", desc: "TUBO DE COBRE 6,35MM X 0,79MM X 30M" },
    { cod: "9182710", desc: "TUBO FLEX SANF AISI304 1.1/4 \" 2600MM" },
    { cod: "1220355", desc: "TUBO Ø 1.1/4 X 42,16 X 6M - AÇO INOX" },
    { cod: "1726447", desc: "UNIÃO 3/8\" INOX PARA SOLDA" },
    { cod: "1220503", desc: "UNIÃO DE 1.1/4\" - INOX - ROSCA NPT" },
    { cod: "1064438", desc: "UNIÃO PARA TUBO 1/4\"" },
    { cod: "1779160", desc: "VALVULA BM-7 (Distributor)" }
];

// ==============================================================
// 2. FUNÇÕES DE CRIAÇÃO DA INTERFACE DO MODAL
// ==============================================================
function renderizarModalSegZeroUI() {
    const modal = document.getElementById('modal-folhao-segmento-zero');
    if (!modal) return;
    
    // Configurando HTML das abas dinâmicas
    let htmlAbas = `
        <button class="folhao-tab active" onclick="window.trocarAbaSegZero(event, 'sz-aba-ident')">1. Identificação</button>
        <button class="folhao-tab" onclick="window.trocarAbaSegZero(event, 'sz-aba-chegada')">2. Chegada & Gap</button>
        <button class="folhao-tab" onclick="window.trocarAbaSegZero(event, 'sz-aba-dimensional')">3. Dimensional</button>
        <button class="folhao-tab" onclick="window.trocarAbaSegZero(event, 'sz-aba-mancais')">4. Mancais</button>
        <button class="folhao-tab" onclick="window.trocarAbaSegZero(event, 'sz-aba-rolos')">5. Rolos Saída & Pass Line</button>
        <button class="folhao-tab" onclick="window.trocarAbaSegZero(event, 'sz-aba-saida')">6. Saída Final & Materiais</button>
    `;

    // Função auxiliar de checklist Sim/Não
    const funcTabelaSimNao = (arr, prefix) => {
        let h = `<table class="premium-table" style="font-size:10px;"><thead><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO</th><th style="width:10%;">SIM</th><th style="width:10%;">NÃO</th></tr></thead><tbody>`;
        arr.forEach((it, i) => {
            h += `<tr><td style="text-align:center;font-weight:bold;">${String(i+1).padStart(2, '0')}</td>
                  <td>${it.grupo ? `<strong style="color:var(--primary);">${it.grupo}</strong><br>` : ''}${it.desc}</td>
                  <td style="text-align:center;"><input type="radio" name="${prefix}-${i}" value="SIM" checked></td>
                  <td style="text-align:center;"><input type="radio" name="${prefix}-${i}" value="NÃO"></td></tr>`;
        });
        return h + `</tbody></table>`;
    };

    // Função auxiliar para GRID 1 a 10 (Rolos/Mancais) (1 a 4 tem 3 colunas, 5 a 10 tem 2 colunas)
    const funcGrid10 = (prefix) => {
        let h = `<table class="premium-table" style="font-size:10px; text-align:center;">
                 <thead><tr><th>Pos</th><th colspan="2">1</th><th colspan="2">2</th><th colspan="2">3</th></tr>
                 <tr><th></th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th></tr></thead><tbody>`;
        for(let i=1; i<=10; i++) {
            let cols = (i <= 4) ? 3 : 2;
            h += `<tr><td style="font-weight:bold;">${i}</td>`;
            for(let j=1; j<=3; j++) {
                if(j <= cols) {
                    h += `<td><input type="radio" name="${prefix}-${i}-${j}" value="OK" checked></td>
                          <td><input type="radio" name="${prefix}-${i}-${j}" value="NOK"></td>`;
                } else {
                    h += `<td style="background:rgba(255,255,255,0.05);">-</td><td style="background:rgba(255,255,255,0.05);">-</td>`;
                }
            }
            h += `</tr>`;
        }
        return h + `</tbody></table>`;
    };

    // Montando o Body
    let htmlBody = `
        <!-- ABA 1: IDENTIFICAÇÃO -->
        <div id="sz-aba-ident" class="folhao-content">
            <div style="display:flex;gap:15px;flex-wrap:wrap; background:var(--bg-th); padding:12px; border-radius:8px;">
                <div class="input-group"><label>TAG</label><input type="text" id="sz-tag" readonly class="premium-input"></div>
                <div class="input-group"><label>Nº SEGMENTO</label><input type="text" id="sz-num-seg" class="premium-input"></div>
                <div class="input-group"><label>VEIO(SAÍDA)</label><select id="sz-veio" class="premium-select"><option value="C">C</option><option value="D">D</option><option value="E">E</option><option value="F">F</option></select></div>
                <div class="input-group"><label>DESEMPENHO</label><input type="text" id="sz-desemp" class="premium-input"></div>
                <div class="input-group"><label>DATA INÍCIO</label><input type="date" id="sz-dt-ini" class="premium-input"></div>
                <div class="input-group"><label>DATA FIM</label><input type="date" id="sz-dt-fim" class="premium-input"></div>
                <div class="input-group"><label>MOTIVO</label><input type="text" id="sz-motivo" class="premium-input"></div>
                <div class="input-group"><label>TIPO EXECUÇÃO</label><select id="sz-tipo-exec" class="premium-select"><option>GERAL</option><option>PARCIAL</option></select></div>
            </div>
            <div style="margin-top:15px;">
                <label style="font-size:11px; color:var(--text-muted); font-weight:bold;">OBSERVAÇÕES DA INSPEÇÃO (Identificação)</label>
                <textarea id="sz-obs-ident" class="premium-textarea" rows="2"></textarea>
            </div>
        </div>

        <!-- ABA 2: CHEGADA & GAP -->
        <div id="sz-aba-chegada" class="folhao-content hidden">
            <h3 style="color:var(--text-heading);">INSPEÇÃO DE CHEGADA</h3>
            ${funcTabelaSimNao(itensChegadaSegZero, 'sz-chg')}
            
            <h3 style="color:var(--text-heading); margin-top:20px;">AFERIÇÃO DE GAP (CHEGADA E SAÍDA)</h3>
            <p style="font-size:10px; color:var(--text-muted); font-weight:bold;">Espessura A/B = 261,5 (-0,1) mm | Máximo: 261,50 | Mínimo: 261,40</p>
            <table class="premium-table" style="font-size:10px; text-align:center;">
                <thead><tr><th>CONJ ROLO</th><th colspan="3">CHEGADA (Pos 1 / 2 / 3)</th><th colspan="3">SAÍDA (Pos 1 / 2 / 3)</th></tr></thead>
                <tbody>
                    ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="font-weight:bold;">${i}º</td>
                        <td><input id="sz-gap-ca-${i}" class="premium-input" style="width:50px;"></td><td><input id="sz-gap-cb-${i}" class="premium-input" style="width:50px;"></td><td>${i<=4?`<input id="sz-gap-cc-${i}" class="premium-input" style="width:50px;">`:'-'}</td>
                        <td><input id="sz-gap-sa-${i}" class="premium-input" style="width:50px;"></td><td><input id="sz-gap-sb-${i}" class="premium-input" style="width:50px;"></td><td>${i<=4?`<input id="sz-gap-sc-${i}" class="premium-input" style="width:50px;">`:'-'}</td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>

        <!-- ABA 3: DIMENSIONAL -->
        <div id="sz-aba-dimensional" class="folhao-content hidden">
            <h3 style="color:var(--text-heading);">INSPEÇÃO DIMENSIONAL DOS ROLOS (DIÂMETRO)</h3>
            <div style="display:flex; gap:15px; flex-wrap:wrap;">
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Inferior</h4>
                    <table class="premium-table" style="font-size:10px; text-align:center;">
                        <tr><th>POSIÇÃO</th><th>Diâmetro</th></tr>
                        ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="font-weight:bold;">${i}º</td><td><input id="sz-dim-inf-${i}" class="premium-input w-100"></td></tr>`).join('')}
                    </table>
                </div>
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Superior</h4>
                    <table class="premium-table" style="font-size:10px; text-align:center;">
                        <tr><th>POSIÇÃO</th><th>Diâmetro</th></tr>
                        ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="font-weight:bold;">${i}º</td><td><input id="sz-dim-sup-${i}" class="premium-input w-100"></td></tr>`).join('')}
                    </table>
                </div>
            </div>
            <h3 style="color:var(--text-heading); margin-top:20px;">INSPEÇÃO DE EMPENO (MÁX 0,5mm)</h3>
            <div style="display:flex; gap:15px; flex-wrap:wrap;">
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Inferior</h4>
                    <table class="premium-table" style="font-size:10px; text-align:center;">
                        <tr><th>POSIÇÃO</th><th>Empeno</th></tr>
                        ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="font-weight:bold;">${i}º</td><td><input id="sz-emp-inf-${i}" class="premium-input w-100"></td></tr>`).join('')}
                    </table>
                </div>
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Superior</h4>
                    <table class="premium-table" style="font-size:10px; text-align:center;">
                        <tr><th>POSIÇÃO</th><th>Empeno</th></tr>
                        ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="font-weight:bold;">${i}º</td><td><input id="sz-emp-sup-${i}" class="premium-input w-100"></td></tr>`).join('')}
                    </table>
                </div>
            </div>
        </div>

        <!-- ABA 4: MANCAIS -->
        <div id="sz-aba-mancais" class="folhao-content hidden">
            <h3 style="color:var(--text-heading);">INSPEÇÃO DE MANCAIS (CHEGADA)</h3>
            <div style="display:flex; gap:15px; flex-wrap:wrap;">
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Inferior</h4>
                    ${funcGrid10('sz-manc-inf')}
                </div>
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Superior</h4>
                    ${funcGrid10('sz-manc-sup')}
                </div>
            </div>
        </div>

        <!-- ABA 5: ROLOS SAÍDA E PASS LINE -->
        <div id="sz-aba-rolos" class="folhao-content hidden">
            <h3 style="color:var(--text-heading);">INSPEÇÃO DE ROLOS (SAÍDA)</h3>
            <div style="display:flex; gap:15px; flex-wrap:wrap;">
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Inferior</h4>
                    ${funcGrid10('sz-rol-inf')}
                </div>
                <div style="flex:1; min-width:300px;">
                    <h4 style="color:var(--text-accent);">Base Superior</h4>
                    ${funcGrid10('sz-rol-sup')}
                </div>
            </div>

            <h3 style="color:var(--text-heading); margin-top:20px;">MEDIDAS DOS ROLOS</h3>
            <table class="premium-table" style="font-size:10px; text-align:center;">
                <thead><tr><th>Posição</th><th>Nº 1</th><th>Medida 1</th><th>Nº 2</th><th>Medida 2</th><th>Classe</th></tr></thead>
                <tbody>
                    ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="font-weight:bold;">${i}º</td>
                        <td><input id="sz-mr-n1-${i}" class="premium-input w-100"></td><td><input id="sz-mr-m1-${i}" class="premium-input w-100"></td>
                        <td><input id="sz-mr-n2-${i}" class="premium-input w-100"></td><td><input id="sz-mr-m2-${i}" class="premium-input w-100"></td>
                        <td><input id="sz-mr-cls-${i}" class="premium-input w-100"></td>
                    </tr>`).join('')}
                </tbody>
            </table>

            <h3 style="color:var(--text-heading); margin-top:20px;">PASS LINE - BASE INFERIOR (1 ± 0,05mm)</h3>
            <table class="premium-table" style="font-size:10px; text-align:center;">
                <thead><tr><th>Conj. Rolo</th><th>Posição 1</th><th>Posição 2</th><th>Posição 3</th></tr></thead>
                <tbody>
                    ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="font-weight:bold;">${i}º</td>
                        <td><input id="sz-pl-1-${i}" class="premium-input w-100"></td><td><input id="sz-pl-2-${i}" class="premium-input w-100"></td>
                        <td>${i<=4?`<input id="sz-pl-3-${i}" class="premium-input w-100">`:'-'}</td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>

        <!-- ABA 6: SAÍDA FINAL & MATERIAIS -->
        <div id="sz-aba-saida" class="folhao-content hidden">
            <h3 style="color:var(--text-heading);">INSPEÇÃO DE SAÍDA</h3>
            ${funcTabelaSimNao(itensSaidaSegZero, 'sz-sai')}
            
            <h3 style="color:var(--text-heading); margin-top:20px;">MATERIAIS APLICADOS</h3>
            <table class="premium-table" style="font-size:10px;">
                <thead><tr><th style="width:70%;">MATERIAL / CÓDIGO SKU</th><th>QUANTIDADE</th></tr></thead>
                <tbody>
                    ${materiaisSegZero.map((m, i) => `<tr><td style="font-size:9px;"><strong>${m.desc}</strong> <span style="color:var(--text-muted);">(${m.cod})</span><input type="hidden" id="sz-mat-desc-${i}" value="${m.desc} (${m.cod})"></td><td><input id="sz-mat-qtd-${i}" class="premium-input w-100"></td></tr>`).join('')}
                </tbody>
            </table>
            
            <div style="margin-top:15px;">
                <label style="font-size:11px; font-weight:bold; color:var(--text-muted);">OBSERVAÇÕES GERAIS (FIM DA MONTAGEM)</label>
                <textarea id="sz-observacoes-finais" class="premium-textarea" rows="3"></textarea>
            </div>

            <div style="display:flex; gap:15px; margin-top:15px;">
                <div class="input-group" style="flex:1;"><label>Operador / Nome</label><input id="sz-assin-op-nome" class="premium-input"></div>
                <div class="input-group" style="flex:1;"><label>Matrícula (Op)</label><input id="sz-assin-op-mat" class="premium-input"></div>
                <div class="input-group" style="flex:1;"><label>Inspetor / Nome</label><input id="sz-assin-insp-nome" class="premium-input"></div>
                <div class="input-group" style="flex:1;"><label>Matrícula (Insp)</label><input id="sz-assin-insp-mat" class="premium-input"></div>
            </div>
        </div>
    `;

    // Atualiza a estrutura do modal injetando as abas e o body
    modal.querySelector('.modal-content').innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;padding: 16px 24px; border-bottom: 2px solid #002b5e; background: rgba(0,0,0,0.3);">
            <h2 style="margin: 0; font-size: 20px; color: var(--text-title);"><i class="fas fa-clipboard-check"></i> Laudo de Liberação - Segmento Zero</h2>
            <button class="btn-close-modal" onclick="window.fecharFolhaoSegmentoZero()">&times;</button>
        </div>
        <div class="folhao-tabs" style="padding: 0 20px;">${htmlAbas}</div>
        <div class="folhao-body" style="padding: 20px; flex: 1; overflow-y: auto;">${htmlBody}</div>
        <div class="modal-footer" style="padding: 12px 24px;">
            <button class="btn-success" onclick="window.salvarFolhaoSegmentoZero()"><i class="fas fa-save"></i> Salvar e Imprimir</button>
            <button class="btn-secondary" onclick="window.fecharFolhaoSegmentoZero()">Fechar</button>
        </div>
    `;
}

// ==============================================================
// 3. FUNÇÕES PRINCIPAIS (ABRIR, FECHAR, TROCAR ABA)
// ==============================================================
window.abrirFolhaoSegmentoZero = function(idAtivo) {
    ID_FOLHAO_SEGZERO_ATUAL = idAtivo;
    const modal = document.getElementById('modal-folhao-segmento-zero');
    if (!modal) return alert("Modal do Segmento Zero não encontrado!");

    // Recria o modal limpo para garantir integridade dos dados na abertura
    renderizarModalSegZeroUI();

    document.getElementById("sz-tag").value = idAtivo;
    document.getElementById("sz-dt-ini").valueAsDate = new Date();
    document.getElementById("sz-dt-fim").valueAsDate = new Date();

    modal.classList.remove('hidden');
};

window.fecharFolhaoSegmentoZero = function() {
    const modal = document.getElementById('modal-folhao-segmento-zero');
    if (modal) modal.classList.add('hidden');
    ID_FOLHAO_SEGZERO_ATUAL = null;
};

window.trocarAbaSegZero = function(evt, abaId) {
    const modal = document.getElementById('modal-folhao-segmento-zero');
    if (!modal) return;
    modal.querySelectorAll('.folhao-content').forEach(c => c.classList.add('hidden'));
    modal.querySelectorAll('.folhao-tab').forEach(b => b.classList.remove('active'));
    const aba = document.getElementById(abaId);
    if (aba) aba.classList.remove('hidden');
    if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');
};

// ==============================================================
// 4. SALVAR E IMPRIMIR PDF (NUVEM + PDF NATIVO)
// ==============================================================
window.salvarFolhaoSegmentoZero = async function() {
    if (!ID_FOLHAO_SEGZERO_ATUAL) return alert("Nenhuma TAG carregada.");
    const tag = ID_FOLHAO_SEGZERO_ATUAL;

    const dtIni = getV('sz-dt-ini') || new Date().toLocaleDateString('pt-BR');
    const dtFim = getV('sz-dt-fim') || new Date().toLocaleDateString('pt-BR');
    const seg = getV('sz-num-seg') || '____';
    const veio = getV('segzero-veio') || ''; 
    const desemp = getV('sz-desemp') || '';
    const mot = getV('segzero-motivo') || '';
    const tipo = getV('segzero-tipo-execucao') || '';
    const novaMeta = getV('segzero-nova-meta') || 'Manter Atual'; // 🔥 CAPTURA A NOVA META

    // PREPARA OS DADOS PARA A NUVEM
    const dadosFolhao = {
        id_peca: tag,
        tipo_equipamento: "Segmento Zero",
        tecnico: window.OPERADOR_LOGADO ? window.OPERADOR_LOGADO.nome : "Técnico",
        nova_meta: parseFloat(novaMeta) || 0,
        tipo_manutencao: tipo,
        dados_chegada: "{}", 
        dados_saida: "{}",
        status_reparo: "Concluido",
        pdf_base64: "" 
    };

    // 🔥 COMUNICAÇÃO COM O PYTHON 🔥
    try {
        const resposta = await fetch(window.API_BASE + "/api/salvar_folhao", {
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

    // Helpers de Geração do PDF
    const genCheck = (arr, prefix) => {
        let h = `<table><tr><th style="width:5%;">ITEM</th><th>DESCRIÇÃO DOS ITENS</th><th style="width:10%;">SIM</th><th style="width:10%;">NÃO</th></tr>`;
        arr.forEach((it, i) => {
            let val = getRadioValue(`${prefix}-${i}`);
            h += `<tr><td style="text-align:center;font-weight:bold;">${String(i+1).padStart(2, '0')}</td>
                  <td>${it.grupo ? `<b>${it.grupo}</b><br>` : ''}${it.desc}</td>
                  <td style="text-align:center;font-weight:bold;">${val==='SIM'?'X':''}</td>
                  <td style="text-align:center;font-weight:bold;">${val==='NÃO'?'X':''}</td></tr>`;
        });
        return h + `</table>`;
    };

    const genGrid = (titulo, prefix) => {
        let h = `<table><tr><th colspan="7" style="background:#ddd;">${titulo}</th></tr>
                 <tr><th>POS</th><th colspan="2">1</th><th colspan="2">2</th><th colspan="2">3</th></tr>
                 <tr><th></th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th><th>OK</th><th>NOK</th></tr>`;
        for(let i=1; i<=10; i++) {
            let cols = (i <= 4) ? 3 : 2;
            h += `<tr><td style="text-align:center;font-weight:bold;">${i}</td>`;
            for(let j=1; j<=3; j++) {
                if(j <= cols) {
                    let v = getRadioValue(`${prefix}-${i}-${j}`);
                    h += `<td style="text-align:center;">${v==='OK'?'X':''}</td><td style="text-align:center;">${v==='NOK'?'X':''}</td>`;
                } else {
                    h += `<td style="background:#eee;">-</td><td style="background:#eee;">-</td>`;
                }
            }
            h += `</tr>`;
        }
        return h + `</table>`;
    };

    let htmlPDF = `
    <style>
        .pdf-base { font-family: Arial, sans-serif; font-size: 9px; color: #000; }
        .pdf-base table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
        .pdf-base th, .pdf-base td { border: 1px solid #000; padding: 3px; }
        .pdf-base th { background: #e0e0e0; text-align: center; font-weight: bold; font-size: 9px; }
        .pdf-base .titulo-secao { background: #002b5e; color: #fff; font-weight: bold; padding: 4px; text-align: left; margin: 10px 0 4px; border: 1px solid #000; font-size: 10px; text-transform: uppercase; }
        .pdf-base .assinatura-box { margin-top:2px; font-size:8px; font-weight:bold; }
        @media print { .quebra-pagina { break-before: page; page-break-before: always; margin-top: 10px; } }
    </style>
    <div class="pdf-base">
        <!-- HEADER -->
        <div style="display: flex; border: 2px solid #000; border-bottom: 5px solid #002b5e; margin-bottom: 10px; align-items: center;">
            <div style="width: 20%; text-align: center; border-right: 2px solid #000; padding: 8px;"><span style="font-weight: 900; font-size: 28px; color: #002b5e;">CSN</span></div>
            <div style="width: 60%; text-align: center; padding: 8px;">
                <h2 style="margin: 0; font-size: 13px; color: #000;">LAUDO DE LIBERAÇÃO - SEGMENTO ZERO</h2>
                <p style="margin: 4px 0 0 0; font-size: 8px; font-weight: bold;">DATA INÍCIO: ${dtIni} | DATA FIM: ${dtFim}</p>
            </div>
            <div style="width: 20%; font-size: 10px; border-left: 2px solid #000; padding: 8px; font-weight: bold;">TAG: ${tag}</div>
        </div>
        
        <!-- 🔥 TABELA ATUALIZADA COM NOVA META 🔥 -->
        <table style="margin-bottom: 15px; border: 2px solid #000;">
            <tr>
                <td style="width: 25%;"><strong>Nº SEGMENTO:</strong> ${seg}</td>
                <td style="width: 30%;"><strong>MOTIVO:</strong> ${mot}</td>
                <td style="width: 25%; color: #002b5e;"><strong>EXECUÇÃO:</strong> ${tipo}</td>
                <td style="width: 20%; background-color: #f0f0f0; text-align: center;"><strong>NOVA META:</strong> ${novaMeta}</td>
            </tr>
            <tr>
                <td colspan="2"><strong>VEIO:</strong> ${veio}</td>
                <td colspan="2"><strong>DESEMPENHO:</strong> ${desemp}</td>
            </tr>
        </table>
        <div style="margin-bottom:10px;"><strong>OBSERVAÇÕES INICIAIS:</strong> ${getV('sz-obs-ident')}</div>

        <div class="titulo-secao">1. INSPEÇÃO DE CHEGADA</div>
        ${genCheck(itensChegadaSegZero, 'sz-chg')}

        <div class="quebra-pagina"></div>
        <div class="titulo-secao">2. AFERIÇÃO DE GAP (261,5 -0,1 mm)</div>
        <table>
            <tr><th>CONJ ROLO</th><th colspan="3">CHEGADA (Pos 1 / 2 / 3)</th><th colspan="3">SAÍDA (Pos 1 / 2 / 3)</th></tr>
            ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr>
                <td style="text-align:center;font-weight:bold;">${i}º</td>
                <td style="text-align:center;">${getV(`sz-gap-ca-${i}`)}</td><td style="text-align:center;">${getV(`sz-gap-cb-${i}`)}</td><td style="text-align:center;background:${i>4?'#eee':''}">${i<=4?getV(`sz-gap-cc-${i}`):'-'}</td>
                <td style="text-align:center;">${getV(`sz-gap-sa-${i}`)}</td><td style="text-align:center;">${getV(`sz-gap-sb-${i}`)}</td><td style="text-align:center;background:${i>4?'#eee':''}">${i<=4?getV(`sz-gap-sc-${i}`):'-'}</td>
            </tr>`).join('')}
        </table>

        <div class="titulo-secao">3. INSPEÇÃO DIMENSIONAL DOS ROLOS E EMPENO</div>
        <div style="display:flex; gap:10px;">
            <div style="width:50%;">
                <table><tr><th colspan="3" style="background:#ddd;">BASE INFERIOR</th></tr><tr><th>POS</th><th>DIÂMETRO</th><th>EMPENO</th></tr>
                ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="text-align:center;font-weight:bold;">${i}º</td><td style="text-align:center;">${getV(`sz-dim-inf-${i}`)}</td><td style="text-align:center;">${getV(`sz-emp-inf-${i}`)}</td></tr>`).join('')}</table>
            </div>
            <div style="width:50%;">
                <table><tr><th colspan="3" style="background:#ddd;">BASE SUPERIOR</th></tr><tr><th>POS</th><th>DIÂMETRO</th><th>EMPENO</th></tr>
                ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr><td style="text-align:center;font-weight:bold;">${i}º</td><td style="text-align:center;">${getV(`sz-dim-sup-${i}`)}</td><td style="text-align:center;">${getV(`sz-emp-sup-${i}`)}</td></tr>`).join('')}</table>
            </div>
        </div>

        <div class="quebra-pagina"></div>
        <div class="titulo-secao">4. INSPEÇÃO DE MANCAIS (CHEGADA)</div>
        <div style="display:flex; gap:10px;">
            <div style="width:50%;">${genGrid('BASE INFERIOR', 'sz-manc-inf')}</div>
            <div style="width:50%;">${genGrid('BASE SUPERIOR', 'sz-manc-sup')}</div>
        </div>

        <div class="titulo-secao">5. INSPEÇÃO DE ROLOS (SAÍDA)</div>
        <div style="display:flex; gap:10px;">
            <div style="width:50%;">${genGrid('BASE INFERIOR', 'sz-rol-inf')}</div>
            <div style="width:50%;">${genGrid('BASE SUPERIOR', 'sz-rol-sup')}</div>
        </div>

        <div class="quebra-pagina"></div>
        <div class="titulo-secao">6. MEDIDAS DOS ROLOS & PASS LINE</div>
        <table>
            <tr><th>POS</th><th>Nº 1</th><th>MEDIDA 1</th><th>Nº 2</th><th>MEDIDA 2</th><th>CLASSE</th><th style="border-left:3px solid #000;">PASS LINE (P1)</th><th>PASS LINE (P2)</th><th>PASS LINE (P3)</th></tr>
            ${[1,2,3,4,5,6,7,8,9,10].map(i => `<tr>
                <td style="text-align:center;font-weight:bold;">${i}º</td>
                <td style="text-align:center;">${getV(`sz-mr-n1-${i}`)}</td><td style="text-align:center;">${getV(`sz-mr-m1-${i}`)}</td>
                <td style="text-align:center;">${getV(`sz-mr-n2-${i}`)}</td><td style="text-align:center;">${getV(`sz-mr-m2-${i}`)}</td>
                <td style="text-align:center;">${getV(`sz-mr-cls-${i}`)}</td>
                <td style="text-align:center;border-left:3px solid #000;">${getV(`sz-pl-1-${i}`)}</td><td style="text-align:center;">${getV(`sz-pl-2-${i}`)}</td><td style="text-align:center;background:${i>4?'#eee':''}">${i<=4?getV(`sz-pl-3-${i}`):'-'}</td>
            </tr>`).join('')}
        </table>

        <div class="titulo-secao">7. INSPEÇÃO DE SAÍDA</div>
        ${genCheck(itensSaidaSegZero, 'sz-sai')}

        <div class="quebra-pagina"></div>
        <div class="titulo-secao">8. MATERIAIS APLICADOS</div>
        <table><tr><th>MATERIAL / CÓDIGO SKU</th><th>QUANTIDADE</th></tr>
            ${materiaisSegZero.map((m, i) => { let q = getV(`sz-mat-qtd-${i}`); if(q) return `<tr><td>${m.desc} (${m.cod})</td><td style="text-align:center;">${q}</td></tr>`; return ''; }).join('')}
        </table>
        <div style="margin-bottom:10px;"><strong>OBSERVAÇÕES FINAIS:</strong> ${getV('sz-observacoes-finais')}</div>

        <div style="margin-top:40px; display:flex; justify-content:space-around; text-align:center; font-weight:bold; font-size:10px;">
            <div><p>___________________________________</p><p>Nome: ${getV('sz-assin-op-nome')} | Mat: ${getV('sz-assin-op-mat')}</p><p>Operador / Mecânico</p></div>
            <div><p>___________________________________</p><p>Nome: ${getV('sz-assin-insp-nome')} | Mat: ${getV('sz-assin-insp-mat')}</p><p>Inspetor de Qualidade</p></div>
        </div>
    </div>`;

    if (window.registrarHistorico) window.registrarHistorico(tag, `Laudo Oficial Segmento Zero finalizado.`);
    
    const printDiv = document.getElementById('print-content');
    if (printDiv) printDiv.innerHTML = htmlPDF;
    
    window.fecharFolhaoSegmentoZero();
    if (typeof renderReparos === 'function') renderReparos();
    if (typeof renderReservas === 'function') renderReservas();
    if (typeof renderAtivos === 'function') renderAtivos();
    if (typeof window.calcularKpisGlobais === 'function') window.calcularKpisGlobais();
    if (typeof window.atualizarPainelCompleto === 'function') window.atualizarPainelCompleto();
    setTimeout(() => window.print(), 500);
};