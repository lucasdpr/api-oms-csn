// gas-api.js - Integração do Front-End com a API do Google Apps Script

// Cole aqui a URL de implantação /exec do seu Google Apps Script
const URL_API_GAS = "https://script.google.com/macros/s/AKfycbyrZv6UDupcXxHNQoYFDtmmthQMnFUEB6Jv9mMLapWTVnT1kG4Imjnhb7Sg1rW3_Ygp/exec";

/**
 * Busca todos os dados de manutenção e atividades da aba 'OFICINA'
 * @returns {Promise<Array>} Array de objetos com as linhas da planilha
 */
async function buscarDadosOficina() {
    try {
        const resposta = await fetch(`${URL_API_GAS}?acao=getOficina`);
        
        if (!resposta.ok) {
            throw new Error(`Erro na requisição: ${resposta.status}`);
        }
        
        const dados = await resposta.json();
        
        if (dados.erro) {
            console.error("⚠️ Erro retornado pela API do GAS:", dados.erro);
            return [];
        }
        
        console.log("✅ Dados da Oficina carregados com sucesso:", dados);
        return dados;
    } catch (erro) {
        console.error("❌ Falha de rede ou CORS ao buscar dados da Oficina:", erro);
        return [];
    }
}

/**
 * Atualiza o percentual de conclusão de uma atividade na aba 'OFICINA' usando o ID
 * @param {string|number} id - O ID da linha/atividade na planilha
 * @param {number} novoPercentual - Valor decimal ou inteiro (ex: 0.75 ou 75 dependendo de como digita na planilha)
 * @returns {Promise<boolean>} Retorna true se atualizou com sucesso
 */
async function atualizarPercentualOficina(id, novoPercentual) {
    try {
        const payload = {
            acao: "updateOficina",
            id: id,
            percentual: novoPercentual
        };

        const resposta = await fetch(URL_API_GAS, {
            method: "POST",
            mode: "cors",
            headers: {
                "Content-Type": "text/plain;charset=utf-8" // Usar text/plain evita problemas de pré-voo (CORS preflight) no GAS
            },
            body: JSON.stringify(payload)
        });

        if (!resposta.ok) {
            throw new Error(`Erro ao enviar dados: ${resposta.status}`);
        }

        const resultado = await resposta.json();
        
        if (resultado.sucesso) {
            console.log(`✅ ID ${id} atualizado para ${novoPercentual}% na planilha.`);
            return true;
        } else {
            console.error("⚠️ Falha na atualização:", resultado.erro);
            return false;
        }
    } catch (erro) {
        console.error("❌ Erro ao tentar atualizar dados da Oficina via POST:", erro);
        return false;
    }
}

// Torna as funções disponíveis globalmente caso use módulos em outros scripts
window.buscarDadosOficina = buscarDadosOficina;
window.atualizarPercentualOficina = atualizarPercentualOficina;