from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar app_core aqui já dispara, como efeito colateral (igual sempre
# foi), a checagem/criação das tabelas e o seed inicial — init_db() é
# chamado no fim do próprio app_core.py, na mesma ordem relativa que
# tinha no main.py original antes desta divisão em módulos.
import app_core  # noqa: F401  (import só pelo efeito colateral do init_db)

from routers import (
    pecas,
    producao,
    sistema,
    auditoria,
    colaboradores,
    materiais,
    rolos,
    hidraulica,
    folhoes,
    notificacoes_push,
    registros_ocorrencia,
    oficina,
    checklist_execucao,
    ordens_servico,
    qualidade,
    laudos,
    avisos,
)

tags_metadata = [
    {"name": "Sistema", "description": "Verificações de saúde do servidor e do banco de dados."},
    {"name": "Peças", "description": "Cadastro, edição, exclusão e histórico de fotos das peças/equipamentos."},
    {"name": "Produção", "description": "Apontamento de produção geral e de moldes, com histórico e opção de desfazer."},
    {"name": "Auditoria", "description": "Registro de eventos e consulta do histórico completo de ações do sistema."},
    {"name": "Colaboradores", "description": "Login, cadastro, cargo e controle de acesso dos colaboradores."},
    {"name": "Materiais (Estoque Geral)", "description": "Estoque geral de materiais (cadastro, ajuste de quantidade, remoção)."},
    {"name": "Rolos", "description": "Estoque de rolos."},
    {"name": "Hidráulica", "description": "Estoque hidráulico."},
    {"name": "Folhões", "description": "Rascunho de progresso dos folhões de manutenção (salvar, carregar, finalizar)."},
    {"name": "Notificações Push", "description": "Inscrição e envio de notificações push (Web Push / VAPID)."},
    {"name": "Registros e Ocorrências", "description": "Intervenções, melhorias, comentários e ocorrências registradas com foto."},
    {"name": "Oficina", "description": "Atividades, materiais por área, equipe, notas e procedimentos de cada área da Oficina."},
    {"name": "Ordens de Serviço (OS)", "description": "Registro digital de OS em papel (foto por página) com status Em Andamento / Concluído / Não Executada."},
    {"name": "Laudos", "description": "Laudos (PDFs) gerados ao finalizar um folhão."},
    # 🔧 "Checklist de Execução" e "Qualidade" já existiam como tag em
    # várias rotas antes desta divisão em módulos, mas nunca tiveram uma
    # entrada aqui em tags_metadata (só afeta a descrição mostrada no
    # /docs — não achou nem perdeu nenhuma rota). Preenchido agora que
    # ficou fácil de notar a lacuna, olhando os módulos lado a lado.
    {"name": "Checklist de Execução", "description": "Checklist de execução por tipo de equipamento — etapas, execuções em andamento e atividades extra."},
    {"name": "Qualidade", "description": "Registros de entrada/saída de Qualidade, com achados e fotos por etapa."},
    {"name": "Avisos", "description": "Comunicados do ADM que o colaborador precisa ler e confirmar ao entrar no sistema."},
]

app = FastAPI(
    title="API - Oficina de Moldes CSN",
    description="Backend do sistema OMS (Oficina de Moldes e Segmentos) da CSN — gerencia peças, produção, "
                 "oficina, colaboradores e ordens de serviço, com persistência no PostgreSQL (Neon).",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🗂️ main.py agora só monta o app e liga cada grupo de rotas (mesma
# divisão por assunto que já aparecia no /docs, via `tags=[...]`) — a
# lógica de cada rota mora em routers/<assunto>.py, e tudo que é
# compartilhado (conexão com o banco, helpers de push/notificação,
# modelos Pydantic, constantes) mora em app_core.py. Nenhuma rota, nem
# uma linha de lógica, mudou nesta divisão — só o arquivo onde cada
# pedaço vive.
for modulo in (
    pecas, producao, sistema, auditoria, colaboradores, materiais, rolos,
    hidraulica, folhoes, notificacoes_push, registros_ocorrencia, oficina,
    checklist_execucao, ordens_servico, qualidade, laudos, avisos,
):
    app.include_router(modulo.router)
