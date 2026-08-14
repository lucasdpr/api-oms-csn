# ==============================================================
# ADICIONAR AO main.py — Listagem de Ocorrências (com foto)
# ==============================================================
# Esta rota é NOVA, além da /api/registro_com_foto e /api/fotos/{peca_id}
# que você já colou antes (do pacote foto_intervencao). Cole esta rota
# junto das outras, depois de get_fotos_da_peca.
# ==============================================================

@app.get("/api/registros_ocorrencia")
def get_registros_ocorrencia(categoria: Optional[str] = None, limite: int = 100):
    """
    Lista os registros de ocorrência (Melhoria, Intervenção, Comentário,
    Atividade Pendente), já com a foto (se tiver) anexada em cada linha.
    Usado pela aba "Registro de Ocorrência" pra montar a lista visível
    de tudo que já foi lançado, com filtro opcional por categoria.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        if categoria:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria,
                       f.foto_base64
                FROM log_eventos e
                LEFT JOIN fotos_registro f ON f.evento_id = e.id
                WHERE e.categoria = %s
                ORDER BY e.id DESC
                LIMIT %s
            """, (categoria, limite))
        else:
            cursor.execute("""
                SELECT e.id, e.data_hora, e.operador, e.peca_id, e.acao, e.categoria,
                       f.foto_base64
                FROM log_eventos e
                LEFT JOIN fotos_registro f ON f.evento_id = e.id
                WHERE e.categoria IS NOT NULL
                ORDER BY e.id DESC
                LIMIT %s
            """, (limite,))
        return cursor.fetchall()
