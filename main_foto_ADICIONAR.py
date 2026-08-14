# ==============================================================
# ADICIONAR AO main.py — Registro com Categoria + Foto
# ==============================================================
# Onde colar cada bloco está indicado nos comentários. A ideia:
# reaproveita a tabela log_eventos que já existe (pra continuar
# aparecendo certinho na Auditoria e no Prontuário), e adiciona uma
# tabela nova só pra guardar a foto em si, vinculada ao mesmo evento.
# ==============================================================


# --------------------------------------------------------------
# 1) TABELA NOVA (colar dentro de init_db(), junto das outras)
# --------------------------------------------------------------
"""
        # Fotos anexadas a registros/intervenções em equipamentos. Cada
        # foto fica vinculada a um evento em log_eventos através de
        # evento_id (não duplicamos data/operador/ação — já existe lá).
        # foto_base64 guarda a imagem já comprimida (JPEG, enviada pelo
        # front-end como data URL). Isso mantém tudo num único banco,
        # sem precisar de um serviço externo de storage por enquanto.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fotos_registro (
                id SERIAL PRIMARY KEY,
                evento_id INTEGER REFERENCES log_eventos(id) ON DELETE CASCADE,
                peca_id TEXT NOT NULL,
                foto_base64 TEXT NOT NULL,
                criado_em TEXT
            )
        ''')

        # Categoria do registro (Melhoria, Intervenção, Comentário,
        # Atividade Pendente). Guardada direto em log_eventos pra não
        # precisar de join só pra filtrar por tipo.
        cursor.execute('''
            ALTER TABLE log_eventos ADD COLUMN IF NOT EXISTS categoria TEXT
        ''')
"""


# --------------------------------------------------------------
# 2) MODELO NOVO (colar junto dos outros modelos Pydantic)
# --------------------------------------------------------------
class RegistroComFoto(BaseModel):
    peca_id: str
    acao: str
    operador: str
    categoria: str  # "Melhoria" | "Intervenção" | "Comentário" | "Atividade Pendente"
    foto_base64: Optional[str] = None  # data URL (ex: "data:image/jpeg;base64,...")


# --------------------------------------------------------------
# 3) ROTA NOVA (colar junto das outras rotas — pode ir logo depois
#    de registrar_evento)
# --------------------------------------------------------------
@app.post("/api/registro_com_foto")
def registrar_com_foto(dados: RegistroComFoto):
    """
    Versão do registrar_evento que aceita categoria + foto opcional.
    Continua gravando em log_eventos (então aparece normal na
    Auditoria e no /api/historico_eventos), e se veio foto, salva
    também em fotos_registro vinculada ao mesmo evento.
    """
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_eventos (data_hora, operador, peca_id, acao, categoria) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (agora, dados.operador, dados.peca_id, dados.acao, dados.categoria)
        )
        evento_id = cursor.fetchone()["id"]

        if dados.foto_base64:
            cursor.execute(
                "INSERT INTO fotos_registro (evento_id, peca_id, foto_base64, criado_em) "
                "VALUES (%s, %s, %s, %s)",
                (evento_id, dados.peca_id, dados.foto_base64, agora)
            )

        conn.commit()

    # 📲 Mesma lógica de criticidade do registrar_evento normal.
    PALAVRAS_CRITICAS = ["b.o", "blackout", "quebra", "fim de vida", "alarme"]
    is_critico = any(p in dados.acao.lower() for p in PALAVRAS_CRITICAS)

    enviar_push_para_area(
        titulo="🚨 Evento crítico" if is_critico else f"📋 {dados.categoria}",
        corpo=f"{dados.operador} — {dados.peca_id}: {dados.acao}",
        area="Mecânico" if is_critico else "Ambos"
    )

    return {"sucesso": True, "evento_id": evento_id}


@app.get("/api/fotos/{peca_id}")
def get_fotos_da_peca(peca_id: str):
    """
    Retorna todas as fotos de um equipamento, já com data/ação/operador
    juntados (join simples com log_eventos), pra montar a timeline do
    Prontuário sem precisar de duas chamadas separadas.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, f.foto_base64, f.criado_em, e.data_hora, e.operador, e.acao, e.categoria
            FROM fotos_registro f
            JOIN log_eventos e ON e.id = f.evento_id
            WHERE f.peca_id = %s
            ORDER BY f.id DESC
        """, (peca_id,))
        return cursor.fetchall()
