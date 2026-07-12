// folhao_bender.js - Módulo completo para BENDER
// ================================================

// Função auxiliar para obter valor de input
function getV(id) {
  let el = document.getElementById(id);
  return el ? el.value : '';
}

// ==========================================
// CHECKLIST DE MANUTENÇÃO (do PDF)
// ==========================================
export const itensExecucao = [
  { i: "1", d: "Limpeza e lavagem" },
  { i: "2.1", d: "Limpeza de Break Out" },
  { i: "3.1", d: "Soltar as uniões das cangalhas de refrigeração e tampar as uniões" },
  { i: "3.2", d: "Retirar chavetas das cangalhas" },
  { i: "3.3", d: "Remover as cangalhas" },
  { i: "3.4", d: "Isolar as pontas dos bicos spray" },
  { i: "3.5", d: "Retirar as proteções de madeira" },
  { i: "3.6", d: "Posicionar segmento na horizontal" },
  { i: "3.7", d: "Aferir medida do GAP de chegada" },
  { i: "3.8", d: "Soltar as 4 porcas de segurança que ajusta a base superior e base inferior" },
  { i: "3.9", d: "Içar e separar a base superior da base inferior" },
  { i: "3.10", d: "Posicionar base superior cavalete" },
  { i: "3.11", d: "Retirar as proteções dos rolos" },
  { i: "3.12", d: "Desconectar toda tubulação de graxa e parafusos de fixação dos mancais" },
  { i: "3.13", d: "Retirar os conjuntos dos rolos" },
  { i: "3.14", d: "Guardar todos os calços de alinhamento dos conjuntos de rolos desmontados que estiverem em boas condições" },
  { i: "3.15", d: "Preparar a base superior para jateamento e pintura" },
  { i: "3.16", d: "Preparar a base inferior para jateamento e pintura" },
  { i: "4.1", d: "Preparação de refrigeração nas cangalhas" },
  { i: "4.2", d: "Testes de refrigeração nas cangalhas" },
  { i: "5.1", d: "Preparar a base inferior" },
  { i: "5.2", d: "Conferir o aperto dos calços nas bases de apoio dos mancais" },
  { i: "5.3", d: "Remover as válvulas de graxa e fazer teste de passagem interna. Montar as válvulas de graxa na base e efetuar o teste de lubrificação" },
  { i: "5.4", d: "Instalar os conjuntos de rolos na base, apertando os parafusos" },
  { i: "5.5", d: "Colocar os parafusos M16 (com graxa nas roscas) nos rolos" },
  { i: "5.6", d: "Aferir passline com auxílio da régua na base inferior do Bender conforme procedimento" },
  { i: "5.7", d: "Conectar os tubos de lubrificação e testar" },
  { i: "5.8", d: "Montar as proteções dos rolos e apertar" },
  { i: "5.9", d: "Passar graxa para alta temperatura nas hastes para proteção" },
  { i: "5.10", d: "Preparar a base superior" },
  { i: "5.11", d: "Conferir o aperto dos calços nas bases de apoio dos mancais" },
  { i: "5.12", d: "Remover as válvulas de graxa e fazer teste de passagem interna. Montar as válvulas de graxa na base e efetuar o teste de lubrificação" },
  { i: "5.13", d: "Instalar os conjuntos de rolos na base, apertando os parafusos" },
  { i: "5.14", d: "Colocar os parafusos M16 (com graxa nas roscas) nos rolos" },
  { i: "5.15", d: "Aferir passline com auxílio da régua na base inferior do Bender conforme procedimento" },
  { i: "5.16", d: "Conectar os tubos de lubrificação e testar" },
  { i: "5.17", d: "Montar as proteções dos rolos e apertar" },
  { i: "5.18", d: "Virar a base superior" },
  { i: "5.19", d: "Transportar a base superior e montar os calços de ajuste nas hastes da base inferior para fechar o segmento" },
  { i: "5.20", d: "Retirar as proteções das roscas, montar os espaçadores e porca de segurança" },
  { i: "5.21", d: "Conferir o GAP e registrar" },
  { i: "5.22", d: "Virar o segmento Bender e colocar na vertical" },
  { i: "5.23", d: "Montar as cangalhas dos resfriadores" },
  { i: "5.24", d: "Montar as mangueiras de lubrificação que alimentam base inferior com a superior" },
  { i: "5.25", d: "Montar proteções superiores" },
  { i: "6.1", d: "Efetuar teste de todos resfriadores" },
  { i: "6.2", d: "Realizar teste de lubrificação" },
  { i: "6.3", d: "Montar as proteções de lubrificação" },
  { i: "6.4", d: "Realizar inspeção final do equipamento" }
];

// ==========================================
// TABELAS DO BENDER
// ==========================================

// GERAÇÃO DA TABELA DE EXECUÇÃO (CHECKLIST)
export function tExec(p) {
  return itensExecucao.map((obj, i) =>
    `<tr>
      <td style="text-align:center;">${obj.i}</td>
      <td>${obj.d}</td>
      ${p
        ? `<td style="text-align:center;">${document.getElementById(`exe-p-${i}`)?.checked ? 'X' : ''}</td>
           <td style="text-align:center;">${document.getElementById(`exe-g-${i}`)?.checked ? 'X' : ''}</td>
           <td style="text-align:center;">${getV(`exe-resp-${i}`)}</td>
           <td style="text-align:center;">${getV(`exe-mat-${i}`)}</td>
           <td style="text-align:center;">${getV(`exe-dat-${i}`)}</td>`
        : `<td style="text-align:center"><input type="checkbox" id="exe-p-${i}"></td>
           <td style="text-align:center"><input type="checkbox" id="exe-g-${i}"></td>
           <td><input id="exe-resp-${i}" class="w-100"></td>
           <td><input id="exe-mat-${i}" class="w-100"></td>
           <td><input id="exe-dat-${i}" type="date" class="w-100"></td>`
      }
    </tr>`
  ).join('');
}

// PASS LINE - Base Inferior (15 rolos)
export function trPL(pfx, p) {
  const refs = [149.97,149.95,149.92,149.90,149.89,149.86,149.63,148.73,146.53,142.41,135.74,125.92,112.46,95.06,73.66];
  return Array.from({ length: 15 }).map((_, i) =>
    `<tr>
      <td style="text-align:center">${i+1}º</td>
      <td style="text-align:center">${refs[i]}</td>
      ${p
        ? `<td style="text-align:center">${getV(`pl-${pfx}-a-${i}`)}</td>
           <td style="text-align:center">${getV(`pl-${pfx}-b-${i}`)}</td>
           <td style="text-align:center">${getV(`pl-${pfx}-c-${i}`)}</td>`
        : `<td><input id="pl-${pfx}-a-${i}" class="w-100"></td>
           <td><input id="pl-${pfx}-b-${i}" class="w-100"></td>
           <td><input id="pl-${pfx}-c-${i}" class="w-100"></td>`
      }
    </tr>`
  ).join('');
}

// PASS LINE - Base Superior (15 rolos)
export function trPLSup(pfx, p) {
  const refs = [149.97,149.95,149.92,149.91,149.89,149.90,150.06,150.83,152.81,156.63,162.91,172.29,185.28,202.24,223.26];
  return Array.from({ length: 15 }).map((_, i) =>
    `<tr>
      <td style="text-align:center">${i+1}º</td>
      <td style="text-align:center">${refs[i]}</td>
      ${p
        ? `<td style="text-align:center">${getV(`plsup-${pfx}-a-${i}`)}</td>
           <td style="text-align:center">${getV(`plsup-${pfx}-b-${i}`)}</td>
           <td style="text-align:center">${getV(`plsup-${pfx}-c-${i}`)}</td>`
        : `<td><input id="plsup-${pfx}-a-${i}" class="w-100"></td>
           <td><input id="plsup-${pfx}-b-${i}" class="w-100"></td>
           <td><input id="plsup-${pfx}-c-${i}" class="w-100"></td>`
      }
    </tr>`
  ).join('');
}

// LUBRIFICAÇÃO - CHECK
export function trLub(pfx, p) {
  return Array.from({ length: 15 }).map((_, i) =>
    `<tr>
      <td style="text-align:center">${i+1}º</td>
      ${p
        ? `<td style="text-align:center">${getV(`lub-${pfx}-st-${i}`)}</td>
           <td style="text-align:center">${getV(`lub-${pfx}-obs-${i}`)}</td>`
        : `<td><select id="lub-${pfx}-st-${i}"><option></option><option>OK</option><option>NOK</option></select></td>
           <td><input id="lub-${pfx}-obs-${i}" class="w-100"></td>`
      }
    </tr>`
  ).join('');
}

// INSPEÇÃO DE ROLOS (OK/NOK para 4 posições)
export function trRol(pfx, p) {
  return Array.from({ length: 15 }).map((_, i) =>
    `<tr>
      <td style="text-align:center">${i+1}</td>
      ${p
        ? `<td style="text-align:center">${getV(`rol-${pfx}-1-${i}`)}</td>
           <td style="text-align:center">${getV(`rol-${pfx}-2-${i}`)}</td>
           <td style="text-align:center">${getV(`rol-${pfx}-3-${i}`)}</td>
           <td style="text-align:center">${getV(`rol-${pfx}-4-${i}`)}</td>`
        : `<td><select id="rol-${pfx}-1-${i}"><option></option><option>OK</option><option>NOK</option></select></td>
           <td><select id="rol-${pfx}-2-${i}"><option></option><option>OK</option><option>NOK</option></select></td>
           <td><select id="rol-${pfx}-3-${i}"><option></option><option>OK</option><option>NOK</option></select></td>
           <td><select id="rol-${pfx}-4-${i}"><option></option><option>OK</option><option>NOK</option></select></td>`
      }
    </tr>`
  ).join('');
}

// MEDIDAS DOS ROLOS (Num / Medida / Classe)
export function trMed(pfx, p) {
  return Array.from({ length: 15 }).map((_, i) =>
    `<tr>
      <td style="text-align:center">${i+1}</td>
      ${p
        ? `<td style="text-align:center">${getV(`med-${pfx}-n1-${i}`)}</td>
           <td style="text-align:center">${getV(`med-${pfx}-m1-${i}`)}</td>
           <td style="text-align:center">${getV(`med-${pfx}-n2-${i}`)}</td>
           <td style="text-align:center">${getV(`med-${pfx}-m2-${i}`)}</td>
           <td style="text-align:center">${getV(`med-${pfx}-n3-${i}`)}</td>
           <td style="text-align:center">${getV(`med-${pfx}-m3-${i}`)}</td>
           <td style="text-align:center">${getV(`med-${pfx}-cls-${i}`)}</td>`
        : `<td><input id="med-${pfx}-n1-${i}" style="width:30px"></td>
           <td><input id="med-${pfx}-m1-${i}" style="width:30px"></td>
           <td><input id="med-${pfx}-n2-${i}" style="width:30px"></td>
           <td><input id="med-${pfx}-m2-${i}" style="width:30px"></td>
           <td><input id="med-${pfx}-n3-${i}" style="width:30px"></td>
           <td><input id="med-${pfx}-m3-${i}" style="width:30px"></td>
           <td><input id="med-${pfx}-cls-${i}" style="width:40px"></td>`
      }
    </tr>`
  ).join('');
}

// GAP TABELA (Chegada e Saída)
export function gapTabela(pfx, p) {
  return `<table class="premium-table" style="font-size: 11px;">
    <thead><tr><th>Conjunto</th><th>Pos A</th><th>Pos B</th><th>Pos C</th></tr></thead>
    <tbody>
      <tr><td style="text-align:center; font-weight:bold;">1º ao 3º (255,00 ±0,30)</td>
        ${p
          ? `<td style="text-align:center;">${getV(`gap-${pfx}-a-1`)}</td>
             <td style="text-align:center;">${getV(`gap-${pfx}-b-1`)}</td>
             <td style="text-align:center;">${getV(`gap-${pfx}-c-1`)}</td>`
          : `<td><input id="gap-${pfx}-a-1" class="w-100"></td>
             <td><input id="gap-${pfx}-b-1" class="w-100"></td>
             <td><input id="gap-${pfx}-c-1" class="w-100"></td>`
        }
      </tr>
      <tr><td style="text-align:center; font-weight:bold;">4º ao 6º (254,70 ±0,30)</td>
        ${p
          ? `<td style="text-align:center;">${getV(`gap-${pfx}-a-2`)}</td>
             <td style="text-align:center;">${getV(`gap-${pfx}-b-2`)}</td>
             <td style="text-align:center;">${getV(`gap-${pfx}-c-2`)}</td>`
          : `<td><input id="gap-${pfx}-a-2" class="w-100"></td>
             <td><input id="gap-${pfx}-b-2" class="w-100"></td>
             <td><input id="gap-${pfx}-c-2" class="w-100"></td>`
        }
      </tr>
    </tbody>
  </table>`;
}

// DIÂMETRO DOS APOIOS (Ø205 ±0,30)
export function diametrosApoios(pfx, p) {
  return `<table class="premium-table">
    <thead><tr><th>Posição</th><th>A</th><th>B</th><th>C</th><th>D</th></tr></thead>
    <tbody>
      <tr>
        <td style="font-weight:bold;">${pfx === 'inf' ? 'Base Inferior' : 'Base Superior'}</td>
        ${p
          ? `<td style="text-align:center;">${getV(`diam-${pfx}-a`)}</td>
             <td style="text-align:center;">${getV(`diam-${pfx}-b`)}</td>
             <td style="text-align:center;">${getV(`diam-${pfx}-c`)}</td>
             <td style="text-align:center;">${getV(`diam-${pfx}-d`)}</td>`
          : `<td><input id="diam-${pfx}-a" class="w-100"></td>
             <td><input id="diam-${pfx}-b" class="w-100"></td>
             <td><input id="diam-${pfx}-c" class="w-100"></td>
             <td><input id="diam-${pfx}-d" class="w-100"></td>`
        }
      </tr>
    </tbody>
  </table>`;
}

// ==========================================
// GERAÇÃO DO HTML DAS ABAS (TODAS AS INFORMAÇÕES DO PDF)
// ==========================================
export function gerarTelasBenderHTML() {
  return `
    <!-- ABA CHEGADA -->
    <div id="bender-chegada" class="folhao-content content-dinamico hidden">
      <h3 style="margin-bottom: 10px;">Aferição de Gap (Chegada)</h3>
      ${gapTabela('cheg', false)}
      
      <h3 style="margin: 20px 0 10px;">Pass Line - Base Inferior</h3>
      <table class="premium-table" style="font-size:10px;"><tr><th>Conj. Rolo</th><th>Referência</th><th>Pos A</th><th>Pos B</th><th>Pos C</th></tr>${trPL('inf-cheg', false)}</table>
      
      <h3 style="margin: 20px 0 10px;">Pass Line - Base Superior</h3>
      <table class="premium-table" style="font-size:10px;"><tr><th>Conj. Rolo</th><th>Referência</th><th>Pos A</th><th>Pos B</th><th>Pos C</th></tr>${trPLSup('sup-cheg', false)}</table>
      
      <h3 style="margin: 20px 0 10px;">Diâmetro dos Apoios (Ø205 ±0,30)</h3>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div>${diametrosApoios('inf', false)}</div>
        <div>${diametrosApoios('sup', false)}</div>
      </div>
      
      <h3 style="margin: 20px 0 10px;">Check de Lubrificação (Chegada)</h3>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div><h4 class="text-center">Base Inferior</h4><table class="premium-table" style="font-size:10px;"><tr><th>Rolo</th><th>Status</th><th>Obs</th></tr>${trLub('inf', false)}</table></div>
        <div><h4 class="text-center">Base Superior</h4><table class="premium-table" style="font-size:10px;"><tr><th>Rolo</th><th>Status</th><th>Obs</th></tr>${trLub('sup', false)}</table></div>
      </div>
      
      <h3 style="margin: 20px 0 10px;">Inspeção de Rolos (Chegada)</h3>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div><h4 class="text-center">Base Inferior</h4><table class="premium-table" style="font-size:10px;"><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('inf-cheg', false)}</table></div>
        <div><h4 class="text-center">Base Superior</h4><table class="premium-table" style="font-size:10px;"><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('sup-cheg', false)}</table></div>
      </div>
      
      <h3 style="margin: 20px 0 10px;">Medidas dos Rolos (Chegada)</h3>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div><h4 class="text-center">Base Inferior</h4><table class="premium-table" style="font-size:8px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Classe</th></tr>${trMed('inf-cheg', false)}</table></div>
        <div><h4 class="text-center">Base Superior</h4><table class="premium-table" style="font-size:8px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Classe</th></tr>${trMed('sup-cheg', false)}</table></div>
      </div>
    </div>

    <!-- ABA EXECUÇÃO -->
    <div id="bender-execucao" class="folhao-content content-dinamico hidden">
      <h3 style="margin-bottom: 10px;">Checklist de Manutenção</h3>
      <table class="premium-table" style="font-size: 10px;">
        <tr><th>Item</th><th>Descrição da Atividade</th><th>P</th><th>G</th><th>Executante</th><th>Matrícula</th><th>Data</th></tr>
        ${tExec(false)}
      </table>
      <div style="margin-top: 20px;">
        <h4>Observações</h4>
        <textarea id="bender-observacoes" class="premium-textarea" rows="4" placeholder="Observações gerais..."></textarea>
      </div>
    </div>

    <!-- ABA SAÍDA -->
    <div id="bender-saida" class="folhao-content content-dinamico hidden">
      <h3 style="margin-bottom: 10px;">Aferição de Gap (Saída)</h3>
      ${gapTabela('sai', false)}
      
      <h3 style="margin: 20px 0 10px;">Pass Line - Base Inferior (Saída)</h3>
      <table class="premium-table" style="font-size:10px;"><tr><th>Conj. Rolo</th><th>Referência</th><th>Pos A</th><th>Pos B</th><th>Pos C</th></tr>${trPL('inf-sai', false)}</table>
      
      <h3 style="margin: 20px 0 10px;">Pass Line - Base Superior (Saída)</h3>
      <table class="premium-table" style="font-size:10px;"><tr><th>Conj. Rolo</th><th>Referência</th><th>Pos A</th><th>Pos B</th><th>Pos C</th></tr>${trPLSup('sup-sai', false)}</table>
      
      <h3 style="margin: 20px 0 10px;">Inspeção de Rolos (Saída)</h3>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div><h4 class="text-center">Base Inferior</h4><table class="premium-table" style="font-size:10px;"><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('inf-sai', false)}</table></div>
        <div><h4 class="text-center">Base Superior</h4><table class="premium-table" style="font-size:10px;"><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('sup-sai', false)}</table></div>
      </div>
      
      <h3 style="margin: 20px 0 10px;">Medidas dos Rolos (Saída)</h3>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div><h4 class="text-center">Base Inferior</h4><table class="premium-table" style="font-size:8px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Classe</th></tr>${trMed('inf-sai', false)}</table></div>
        <div><h4 class="text-center">Base Superior</h4><table class="premium-table" style="font-size:8px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Classe</th></tr>${trMed('sup-sai', false)}</table></div>
      </div>
    </div>

    <!-- ABA MATERIAIS -->
    <div id="aba-materiais-geral" class="folhao-content content-dinamico hidden">
      <h3 style="margin-bottom: 15px;">Materiais Aplicados no Reparo</h3>
      <table class="premium-table">
        <thead><tr><th>Material</th><th>Quantidade</th></tr></thead>
        <tbody id="materiais-bender-body">
          ${Array.from({length: 20}).map((_, i) => `
            <tr>
              <td><input id="mat-bender-desc-${i}" class="w-100" placeholder="Descrição do material"></td>
              <td><input id="mat-bender-qtd-${i}" class="w-100" placeholder="Qtd" style="width:80px;"></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      <button class="btn-xs-primary" onclick="window.adicionarLinhaMaterialBender()" style="margin-top:10px;">+ Adicionar linha</button>
    </div>
  `;
}

// ==========================================
// IMPRESSÃO PDF DO BENDER (com todas as informações)
// ==========================================
export function imprimirPDFBender(tag, motivo, getVFunc) {
  const getV = getVFunc || ((id) => document.getElementById(id)?.value || '');
  const printDiv = document.getElementById("print-content");

  const cssBase = `
    <style>
      .pdf-base { font-family: Arial, sans-serif; font-size: 9px; color: #000; }
      .pdf-base table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
      .pdf-base th, .pdf-base td { border: 1px solid #000; padding: 3px; }
      .pdf-base th { background: #e0e0e0; text-align: center; font-weight: bold; font-size: 8px; }
      .pdf-base .titulo-secao { background: #002b5e; color: #fff; font-weight: bold; padding: 5px; text-align: left; margin: 8px 0; border: 1px solid #000; font-size: 10px; }
      @media print { .quebra-pagina { break-before: page; page-break-before: always; margin-top: 10px; } }
      .pdf-base .small-text { font-size: 7px; }
    </style>`;

  const cabecalho = `
    <div style="display: flex; border: 2px solid #000; border-bottom: 5px solid #002b5e; margin-bottom: 10px; align-items: center; background: #fff;">
      <div style="width: 15%; text-align: center; border-right: 2px solid #000; padding: 8px;">
        <span style="font-weight: 900; font-size: 28px; color: #002b5e;">CSN</span>
      </div>
      <div style="width: 60%; text-align: center; padding: 8px;">
        <h2 style="margin: 0; font-size: 14px; color: #000; text-decoration: underline;">CHECK LIST GERAL SEGMENTOS BENDER MCC#4</h2>
        <p style="margin: 3px 0 0 0; font-size: 9px; color: #333; font-weight: bold;">Laudo Oficial de Manutenção e Peritagem</p>
      </div>
      <div style="width: 25%; font-size: 8px; border-left: 2px solid #000; padding: 8px; line-height: 1.4;">
        <div><strong>TAG:</strong> ${tag}</div>
        <div><strong>INÍCIO:</strong> ${getV('mcc4-data-inicio')}</div>
        <div><strong>FIM:</strong> ${getV('mcc4-data-fim')}</div>
        <div><strong>MOTIVO:</strong> ${motivo}</div>
        <div><strong>VEIO SAÍDA:</strong> ${document.querySelector('input[name="mcc4-veio-saida"]:checked')?.value || ''}</div>
        <div><strong>VEIO ENTRADA:</strong> ${document.querySelector('input[name="mcc4-veio-entrada"]:checked')?.value || ''}</div>
        <div><strong>TIPO:</strong> ${document.querySelector('input[name="mcc4-tipo-exec"]:checked')?.value || ''}</div>
      </div>
    </div>`;

  // Função para gerar checklist do PDF (a partir dos radios)
  function gerarChecklistPDF() {
    let html = '';
    const categorias = {
      'LUBRIFICAÇÃO': [
        'Sistema de lubrificação isento de vazamentos.',
        'Tubulação amassada.',
        'Distribuidores de graxa funcionando corretamente sem vazamentos.',
        'Flexíveis estão perfeitos, sem avarias',
        'Tubulações Inox ou Cobre danificadas'
      ],
      'REFRIGERAÇÃO': [
        'Resfriadores completos e alinhados.',
        'Bicos completos e obstruídos.',
        'Flexíveis isentos de vazamentos.',
        'Tubulações isentas de empenos.',
        'Tubulações furadas.'
      ],
      'ESTRUTURA': [
        'Rolos Lubrificados, girando normalmente',
        'Proteções isentas de avarias.',
        'Estrutura com break-out.',
        'Rolamentos quebrados.',
        'Rolos travados',
        'Parafusos de fixação dos mancais todos apertados',
        'Conexões apertadas.'
      ]
    };
    let groupIndex = 0;
    for (const [cat, perguntas] of Object.entries(categorias)) {
      html += `<tr><th colspan="3" style="background:#002b5e; color:#fff; font-size:9px; text-align:left; padding:4px;">${cat}</th></tr>`;
      html += `<tr><th style="width:5%;">Item</th><th>Descrição</th><th style="width:12%;">Status</th></tr>`;
      perguntas.forEach((pergunta, idx) => {
        let name = `geral-g${groupIndex}-q${idx}`;
        let radios = document.getElementsByName(name);
        let valor = 'N/A';
        for (let r of radios) if (r.checked) { valor = r.value; break; }
        html += `<tr><td style="text-align:center;">${idx+1}</td><td>${pergunta}</td><td style="text-align:center;font-weight:bold;">${valor}</td></tr>`;
      });
      groupIndex++;
    }
    return html;
  }

  // Gera as tabelas para o PDF (versão impressão)
  function tExecPDF() {
    return itensExecucao.map((obj, i) =>
      `<tr>
        <td style="text-align:center;">${obj.i}</td>
        <td>${obj.d}</td>
        <td style="text-align:center;">${document.getElementById(`exe-p-${i}`)?.checked ? 'X' : ''}</td>
        <td style="text-align:center;">${document.getElementById(`exe-g-${i}`)?.checked ? 'X' : ''}</td>
        <td style="text-align:center;">${getV(`exe-resp-${i}`)}</td>
        <td style="text-align:center;">${getV(`exe-mat-${i}`)}</td>
        <td style="text-align:center;">${getV(`exe-dat-${i}`)}</td>
      </tr>`
    ).join('');
  }

  let html = `${cssBase}<div class="pdf-base">
    ${cabecalho}
    
    <div class="titulo-secao">1. INSPEÇÃO DE CHEGADA</div>
    <table style="font-size:8px;">${gerarChecklistPDF()}</table>
    <div style="margin:5px 0;"><strong>Observações:</strong> ${getV('bender-observacoes')}</div>
    
    <div class="quebra-pagina"></div>
    <div class="titulo-secao">2. AFERIÇÃO DE GAP (CHEGADA)</div>
    ${gapTabela('cheg', true)}
    
    <div class="titulo-secao">3. PASS LINE (CHEGADA)</div>
    <div style="display:flex; gap:10px; width:100%;">
      <div style="width:50%;"><table><tr><th colspan="5">BASE INFERIOR</th></tr><tr><th>Rolo</th><th>Ref</th><th>A</th><th>B</th><th>C</th></tr>${trPL('inf-cheg', true)}</table></div>
      <div style="width:50%;"><table><tr><th colspan="5">BASE SUPERIOR</th></tr><tr><th>Rolo</th><th>Ref</th><th>A</th><th>B</th><th>C</th></tr>${trPLSup('sup-cheg', true)}</table></div>
    </div>
    
    <div class="titulo-secao">4. DIÂMETRO DOS APOIOS (Ø205 ±0,30)</div>
    <div style="display:flex; gap:10px;">
      <div style="width:50%;">${diametrosApoios('inf', true)}</div>
      <div style="width:50%;">${diametrosApoios('sup', true)}</div>
    </div>
    
    <div class="quebra-pagina"></div>
    <div class="titulo-secao">5. CHECK DE LUBRIFICAÇÃO (CHEGADA)</div>
    <div style="display:flex; gap:10px;">
      <div style="width:50%;"><table><tr><th>Rolo</th><th>Status</th><th>Obs</th></tr>${trLub('inf', true)}</table></div>
      <div style="width:50%;"><table><tr><th>Rolo</th><th>Status</th><th>Obs</th></tr>${trLub('sup', true)}</table></div>
    </div>
    
    <div class="titulo-secao">6. INSPEÇÃO DE ROLOS (CHEGADA)</div>
    <div style="display:flex; gap:10px;">
      <div style="width:50%;"><table><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('inf-cheg', true)}</table></div>
      <div style="width:50%;"><table><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('sup-cheg', true)}</table></div>
    </div>
    
    <div class="titulo-secao">7. MEDIDAS DOS ROLOS (CHEGADA)</div>
    <div style="display:flex; gap:10px;">
      <div style="width:50%;"><table style="font-size:7px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Cls</th></tr>${trMed('inf-cheg', true)}</table></div>
      <div style="width:50%;"><table style="font-size:7px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Cls</th></tr>${trMed('sup-cheg', true)}</table></div>
    </div>
    
    <div class="quebra-pagina"></div>
    <div class="titulo-secao">8. CHECKLIST DE MANUTENÇÃO (EXECUÇÃO)</div>
    <table style="font-size:7px;"><tr><th>Item</th><th>Descrição</th><th>P</th><th>G</th><th>Executante</th><th>Matrícula</th><th>Data</th></tr>${tExecPDF()}</table>
    
    <div class="quebra-pagina"></div>
    <div class="titulo-secao">9. AFERIÇÃO DE GAP (SAÍDA)</div>
    ${gapTabela('sai', true)}
    
    <div class="titulo-secao">10. PASS LINE (SAÍDA)</div>
    <div style="display:flex; gap:10px;">
      <div style="width:50%;"><table><tr><th colspan="5">BASE INFERIOR</th></tr><tr><th>Rolo</th><th>Ref</th><th>A</th><th>B</th><th>C</th></tr>${trPL('inf-sai', true)}</table></div>
      <div style="width:50%;"><table><tr><th colspan="5">BASE SUPERIOR</th></tr><tr><th>Rolo</th><th>Ref</th><th>A</th><th>B</th><th>C</th></tr>${trPLSup('sup-sai', true)}</table></div>
    </div>
    
    <div class="titulo-secao">11. INSPEÇÃO DE ROLOS (SAÍDA)</div>
    <div style="display:flex; gap:10px;">
      <div style="width:50%;"><table><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('inf-sai', true)}</table></div>
      <div style="width:50%;"><table><tr><th>Rolo</th><th>1</th><th>2</th><th>3</th><th>4</th></tr>${trRol('sup-sai', true)}</table></div>
    </div>
    
    <div class="titulo-secao">12. MEDIDAS DOS ROLOS (SAÍDA)</div>
    <div style="display:flex; gap:10px;">
      <div style="width:50%;"><table style="font-size:7px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Cls</th></tr>${trMed('inf-sai', true)}</table></div>
      <div style="width:50%;"><table style="font-size:7px;"><tr><th>R</th><th>N1</th><th>M1</th><th>N2</th><th>M2</th><th>N3</th><th>M3</th><th>Cls</th></tr>${trMed('sup-sai', true)}</table></div>
    </div>
    
    <div class="titulo-secao">13. MATERIAIS APLICADOS</div>
    <table>
      <tr><th>Material</th><th>Quantidade</th></tr>
      ${Array.from({length: 20}).map((_, i) => {
        let desc = getV(`mat-bender-desc-${i}`);
        let qtd = getV(`mat-bender-qtd-${i}`);
        if (desc || qtd) {
          return `<tr><td>${desc}</td><td style="text-align:center;">${qtd}</td></tr>`;
        }
        return '';
      }).filter(row => row).join('')}
    </table>
    
    <div style="margin-top: 20px; display: flex; justify-content: space-around; text-align: center; font-size: 10px; font-weight: bold; padding-bottom:20px;">
      <div><p>___________________________________</p><p>Líder Responsável / Operador</p></div>
      <div><p>___________________________________</p><p>Inspetor de Qualidade</p></div>
    </div>
  </div>`;

  printDiv.innerHTML = html;
  setTimeout(() => { window.print(); }, 500);
}

// Função para adicionar linha de material (global)
window.adicionarLinhaMaterialBender = function() {
  const tbody = document.getElementById('materiais-bender-body');
  if (tbody) {
    const idx = tbody.querySelectorAll('tr').length;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input id="mat-bender-desc-${idx}" class="w-100" placeholder="Descrição do material"></td>
      <td><input id="mat-bender-qtd-${idx}" class="w-100" placeholder="Qtd" style="width:80px;"></td>
    `;
    tbody.appendChild(tr);
  }
};
// Função para abrir o modal do Bender
window.abrirFolhaoBender = function(id) {
  console.log("Abrindo Bender:", id);
  // Pega o item do banco
  let item = window.BANCO_ATIVOS.find(a => a.id === id);
  if (!item) return alert('Bender não encontrado!');

  // Preenche informações gerais
  document.getElementById("mcc4-tag-name").innerText = id;
  document.getElementById("mcc4-data-inicio").valueAsDate = new Date();
  document.getElementById("mcc4-data-fim").valueAsDate = new Date();

  // Injeta as abas do Bender no modal MCC4
  const tabsContainer = document.querySelector('#modal-folhao-mcc4 .folhao-tabs');
  const bodyContainer = document.querySelector('#modal-folhao-mcc4 .folhao-body');
  // Remove abas e conteúdos antigos que não sejam do Bender (opcional)
  // Aqui você pode limpar ou adicionar
  // Como o modal pode ser reutilizado, é melhor limpar antes
  document.querySelectorAll('#modal-folhao-mcc4 .tab-dinamica, #modal-folhao-mcc4 .content-dinamico').forEach(el => el.remove());

  // Adiciona as abas
  tabsContainer.innerHTML += `
    <button class="folhao-tab tab-dinamica" onclick="trocarAbaFolhao(event, 'bender-chegada')">3. Chegada</button>
    <button class="folhao-tab tab-dinamica" onclick="trocarAbaFolhao(event, 'bender-execucao')">4. Execução</button>
    <button class="folhao-tab tab-dinamica" onclick="trocarAbaFolhao(event, 'bender-saida')">5. Saída</button>
    <button class="folhao-tab tab-dinamica" onclick="trocarAbaFolhao(event, 'aba-materiais-geral')">6. Materiais</button>
  `;
  // Adiciona o conteúdo
  bodyContainer.innerHTML += gerarTelasBenderHTML();

  // Abre o modal
  document.getElementById("modal-folhao-mcc4").classList.remove("hidden");
  // Ativa a primeira aba
  document.querySelector('#modal-folhao-mcc4 .folhao-tab').click();
};