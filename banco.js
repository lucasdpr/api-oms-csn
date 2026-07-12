// banco.js - O Coração de Dados do Sistema

export let BANCO_ATIVOS = JSON.parse(localStorage.getItem("oms_ativos_v32_local"));
export let HISTORICO_ACOES = JSON.parse(localStorage.getItem("oms_historico_v32_local")) || [];
export let BANCO_ROLOS = JSON.parse(localStorage.getItem("oms_rolos_v32_local"));
export let BANCO_MATERIAIS = JSON.parse(localStorage.getItem("oms_materiais_v32_local"));
export let EM_EMERGENCIA = JSON.parse(localStorage.getItem("oms_emergencia_v32_local")) || null;
export let OPERADOR_LOGADO = JSON.parse(localStorage.getItem("oms_operador_v32_local")) || null;
export let VEIO_SELECIONADO_PAINEL = "C";

export const CADASTRO_MATRICULAS = {
    "1011": "Desenvoldedor"
};


const API_PLANILHA_URL = "https://script.google.com/macros/s/AKfycby_XSR5hrrvOgDEqlWhbKC2l7iPjthe6ht5YrabNliXsFlkNhzYGFU2BR8JUhzv8yY2/exec";
// FUNÇÃO AUXILIAR EXPORTADA PARA ORDEM PADRÃO
// ==========================================================================
export function getOrdemPadrao(tipo) {
    if (tipo === "Molde") return 10;
    if (tipo === "Mesa Osciladora") return 20;
    if (tipo === "Segmento Zero") return 30;
    if (tipo === "Bender") return 40;
    if (tipo === "Cadeira Superior") return 100;
    if (tipo === "Cadeira Inferior") return 200;
    if (tipo === "Bow") return 300;
    if (tipo === "Straightener") return 400;
    if (tipo === "Horizontal") return 500;
    return 999;
}

// ==========================================================================
// INICIALIZAÇÃO AUTOMÁTICA DOS BANCOS DE DADOS
// ==========================================================================
if (!BANCO_ATIVOS || BANCO_ATIVOS.length === 0) {   
    BANCO_ATIVOS = [];
    const veiosMcc23 = [{ mcc: 2, veio: "C" }, { mcc: 2, veio: "D" }, { mcc: 3, veio: "E" }, { mcc: 3, veio: "F" }];
    
    veiosMcc23.forEach(m => {
        const vNome = `MCC ${m.mcc} - Veio ${m.veio}`;
        BANCO_ATIVOS.push({ id: `MLD-2${m.veio}`, tipo: "Molde", local: vNome, pos: `Molde Veio ${m.veio}`, dias: 14, ton: 1000000, meta: 1200000, ordem: 10, mcc_compat: "2/3" });
        BANCO_ATIVOS.push({ id: `OSC-2${m.veio}`, tipo: "Mesa Osciladora", local: vNome, pos: `Osciladora ${m.veio}`, dias: 65, ton: 610000, meta: 1800000, ordem: 20, mcc_compat: "2/3" });
        BANCO_ATIVOS.push({ id: `SEG-0-2${m.veio}`, tipo: "Segmento Zero", local: vNome, pos: "Segmento Zero", dias: 38, ton: 142100, meta: 450000, ordem: 30, mcc_compat: "2/3" });

        for (let c = 43; c <= 79; c++) {
            let isTracionada = [45, 48, 52, 56, 60, 64, 68, 72, 76, 79].includes(c);
            BANCO_ATIVOS.push({ id: `CAD-SUP-${c}-2${m.veio}`, tipo: "Cadeira Superior", local: vNome, pos: `Cad Sup ${c}`, dias: 45, ton: c === 43 ? 1438977 : 943444, meta: 2000000, ordem: 100 + c, mcc_compat: "2/3" });
            BANCO_ATIVOS.push({ id: `CAD-INF-${c}-2${m.veio}`, tipo: "Cadeira Inferior", local: vNome, pos: `Cad Inf ${c} ${isTracionada ? '(⚡)' : ''}`, dias: 50, ton: c === 43 ? 1348264 : 1414185, meta: 2500000, ordem: 200 + c, mcc_compat: "2/3" });
        }
    });

    const veiosMcc4 = ["H", "G"];
    veiosMcc4.forEach(veio => {
        const vNome = `MCC 4 - Veio ${veio}`;
        BANCO_ATIVOS.push({ id: `MLD-4${veio}`, tipo: "Molde", local: vNome, pos: "Molde Alta Perf.", dias: 12, ton: 180000, meta: 1000000, ordem: 10, mcc_compat: "4" });
        BANCO_ATIVOS.push({ id: `BND-4${veio}`, tipo: "Bender", local: vNome, pos: "Dobrador (Bender)", dias: 45, ton: 520000, meta: 1500000, ordem: 40, mcc_compat: "4" });
        
        // Bow (Mantido padrão de 1 a 5)
        for (let b = 1; b <= 5; b++) BANCO_ATIVOS.push({ id: `BOW-${b}-4${veio}`, tipo: "Bow", local: vNome, pos: `Curvo Bow #0${b}`, dias: 60, ton: 650000, meta: 1600000, ordem: 300 + b, mcc_compat: "4" });
        
        // ⚡ CORREÇÃO: Straightener configurado com ID real de 6 e 7 (R1 e R2)
        for (let s = 6; s <= 7; s++) BANCO_ATIVOS.push({ id: `STR-${s}-4${veio}`, tipo: "Straightener", local: vNome, pos: `Endireitador #0${s === 6 ? '1' : '2'}`, dias: 88, ton: 910000, meta: 1800000, ordem: 400 + s, mcc_compat: "4" });
        
        // ⚡ CORREÇÃO: Horizontal configurado com ID real de 8 a 17 para sincronizar com a planilha
        for (let h = 8; h <= 17; h++) BANCO_ATIVOS.push({ id: `HOR-${h}-4${veio}`, tipo: "Horizontal", local: vNome, pos: `Horizontal #${h < 10 ? '0'+h : h}`, dias: 102, ton: 430000, meta: 2000000, ordem: 500 + h, mcc_compat: "4" });
    });

    // Pushes de Equipamentos Reservas e de Oficina
    BANCO_ATIVOS.push({ id: `MLD-RES-01`, tipo: "Molde", local: "Oficina / Reserva", pos: "Estoque Central", dias: 0, ton: 0, meta: 1200000, ordem: 10, mcc_compat: "2/3" });
    BANCO_ATIVOS.push({ id: `MLD-MCC4-REP`, tipo: "Molde", local: "Oficina / Reparo", pos: "Bancada", dias: 25, ton: 800000, meta: 1000000, ordem: 10, mcc_compat: "4" });

    localStorage.setItem("oms_ativos_v32_local", JSON.stringify(BANCO_ATIVOS));
}

if (!BANCO_ROLOS) {
    BANCO_ROLOS = [
        { id: "R-S5", nome: "Rolo de Cadeira 450", conjunto: "Cadeira", mcc_compat: "2/3", qtd: 14 },
        { id: "R-S5P", nome: "Rolo de Cadeira 450 Puxador", conjunto: "Cadeira", mcc_compat: "2/3", qtd: 8 },
        { id: "R-S4", nome: "Rolo de Cadeira 400", conjunto: "Cadeira", mcc_compat: "2/3", qtd: 12 },
        { id: "R-S4P", nome: "Rolo de Cadeira 400 Puxador", conjunto: "Cadeira", mcc_compat: "2/3", qtd: 6 },
        { id: "R-H300A", nome: "Rolo Horizontal de 300 Acionado", conjunto: "Segmento", mcc_compat: "4", qtd: 6 },
        { id: "R-200", nome: "Rolo 200", conjunto: "Segmento Zero", mcc_compat: "2/3/4", qtd: 8 },
        { id: "R-FR23", nome: "Foot Roll", conjunto: "Molde", mcc_compat: "2/3", qtd: 4 }
    ];
    localStorage.setItem("oms_rolos_v32_local", JSON.stringify(BANCO_ROLOS));
}

if (!BANCO_MATERIAIS) {
    BANCO_MATERIAIS = [
        { codigo: "1660669", descricao: "ABRACADEIRA BIPARTIDA PP 12,MM", qtd: 50 },
        { codigo: "1641056", descricao: "ABRACADEIRA BIPARTIDA PP 16,0MM", qtd: 25 },
        { codigo: "8008878", descricao: "ACOPLAMENTO DESENHO CSN DM-028275", qtd: 5 },
        { codigo: "1205526", descricao: "ARRUELA DE PRESSÃO M10", qtd: 2097 },
        { codigo: "8497231", descricao: "PARAF .CAB. SEXT. M12 X 30MM CL 8.8", qtd: 150 },
        { codigo: "1195469", descricao: "ARAME SOLDA ACO ER70S-6 1,20MM", qtd: 24 },
        { codigo: "8004825", descricao: "CADEADO DE LATAO 35MM PAPAIZ", qtd: 10 }
    ];
    localStorage.setItem("oms_materiais_v32_local", JSON.stringify(BANCO_MATERIAIS));
}

const NOVOS_NOMES_ROLOS = {
    "R-S5": "Rolo de Cadeira 450",
    "R-S5P": "Rolo de Cadeira 450 Puxador",
    "R-H300A": "Rolo Horizontal de 300 Acionado"
};

if (BANCO_ROLOS) {
    let atualizouNomes = false;
    BANCO_ROLOS.forEach(rolo => {
        if (NOVOS_NOMES_ROLOS[rolo.id] && rolo.nome !== NOVOS_NOMES_ROLOS[rolo.id]) {
            rolo.nome = NOVOS_NOMES_ROLOS[rolo.id];
            atualizouNomes = true;
        }
    });
    if (atualizouNomes) {
        localStorage.setItem("oms_rolos_v32_local", JSON.stringify(BANCO_ROLOS));
    }
}

// Funções de acesso para alterar variáveis blindadas
export function setOperador(novoOperador) { OPERADOR_LOGADO = novoOperador; }
export function setEmergencia(status) { EM_EMERGENCIA = status; }
export function setVeioSelecionado(veio) { VEIO_SELECIONADO_PAINEL = veio; }


export async function sincronizarAtivosReaisMCC4() {
    try {
        const resposta = await fetch("http://localhost:8000/api/pecas");

        if (!resposta.ok) {
            throw new Error(`API respondeu com status ${resposta.status}`);
        }

        const dadosLimposPython = await resposta.json();

        if (!Array.isArray(dadosLimposPython) || dadosLimposPython.length === 0) {
            console.warn("⚠️ Python retornou vazio.");
            return false;
        }

        let pecasAtualizadas = 0;

        // O código agora é direto e reto, porque o banco de dados é limpo!
        dadosLimposPython.forEach(pecaBanco => {
            
            // 1. Procura a peça no sistema pelo ID exato da planilha nova
            let itemLocal = BANCO_ATIVOS.find(a => a.id === pecaBanco.ID);
            
            // 2. Se não achar pelo ID, usa a função de inteligência do sistema para buscar por Veio/Posição
            if (!itemLocal) {
                const ativoBusca = {
                    veio: pecaBanco.VEIO,
                    posicao: pecaBanco.POSICAO,
                    tipo: pecaBanco.TIPO
                };
                itemLocal = encontrarAtivoCorrespondente(ativoBusca);
            }

            // 3. Atualiza os dados de forma limpa!
            if (itemLocal) {
                itemLocal.ton = parseFloat(pecaBanco.TONELAGEM) || 0;
                itemLocal.meta = parseFloat(pecaBanco.META) || itemLocal.meta;
                itemLocal.dias = parseInt(pecaBanco.DIAS) || itemLocal.dias || 0;
                pecasAtualizadas++;
            }
        });

        console.log(`✅ MARCO ZERO ESTABELECIDO: ${pecasAtualizadas} ativos atualizados com dados 100% limpos.`);

        // Salva a versão atualizada
        localStorage.setItem("oms_ativos_v32_local", JSON.stringify(BANCO_ATIVOS));
        return true;

    } catch (erro) {
        console.error("❌ Falha ao buscar dados do Python. O servidor (uvicorn) está ligado?", erro);
        return false;
    }
}

/**
 * Casa o ativo da planilha com o ID do banco local de forma exata.
 * Suporta o formato MCC4 (HOR-8-4G) e MCC2/3 (CAD-SUP-43-2C).
 */
function encontrarAtivoCorrespondente(ativoReal) {
    // 1. Identifica a letra do veio (C, D, E, F, G ou H)
    const matchVeio = String(ativoReal.veio).match(/[CDEFGH]/i);
    const letraVeio = matchVeio ? matchVeio[0].toUpperCase() : null;

    if (!letraVeio) return null;

    // 2. Filtra pelo tipo e pela letra do veio correspondente
    const candidatos = BANCO_ATIVOS.filter(item =>
        item.tipo === ativoReal.tipo &&
        item.local && item.local.includes(`Veio ${letraVeio}`)
    );

    if (candidatos.length === 0) return null;
    if (candidatos.length === 1) return candidatos[0];

    // 3. Se houver mais de um candidato, busca pelo número da posição (ex: 43 ou 8)
    const textoBusca = ativoReal.posicao ? String(ativoReal.posicao) : String(ativoReal.veio);
    const matchPosicao = textoBusca.match(/(\d+)/);
    
    if (matchPosicao) {
        const posicaoDesejada = matchPosicao[1];
        // Quebra o ID local por hífens e verifica se o número da posição está contido ali
        const porPosicaoExata = candidatos.find(item => {
            const partes = item.id.split('-');
            return partes.includes(posicaoDesejada);
        });
        if (porPosicaoExata) return porPosicaoExata;
    }

    return candidatos[0]; // Retorna o primeiro caso não ache a posição exata
}
// ==========================================================================
// MÃO DUPLA: Enviando atualizações para o Python (SQLite)
// ==========================================================================
export async function salvarPecaNoPython(peca) {
    try {
        const resposta = await fetch("http://localhost:8000/api/atualizar_peca", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: peca.id || peca.ID, 
                tonelagem: peca.ton || 0,
                dias: peca.dias || 0,
                local: peca.local || "",
                status: peca.status || ""
            })
        });

        const resultado = await resposta.json();
        
        if (resultado.status === "sucesso") {
            console.log(`✅ [Banco de Dados] Peça ${peca.id} atualizada com sucesso!`);
        } else {
            console.error("❌ Erro no Python:", resultado.mensagem);
        }

    } catch (erro) {
        console.error("❌ Erro de comunicação com o servidor:", erro);
    }
}

// ==========================================================================
// EXPORTAÇÃO PADRÃO
// ==========================================================================
export default {
    BANCO_ATIVOS,
    HISTORICO_ACOES,
    BANCO_ROLOS,
    BANCO_MATERIAIS,
    EM_EMERGENCIA,
    OPERADOR_LOGADO,
    VEIO_SELECIONADO_PAINEL,
    CADASTRO_MATRICULAS,
    getOrdemPadrao,
    setOperador,
    setEmergencia,
    setVeioSelecionado,
    sincronizarAtivosReaisMCC4,
    salvarPecaNoPython
};