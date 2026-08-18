import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Carrega variáveis de um .env local (na nuvem/Render isso é ignorado,
# as variáveis já vêm configuradas no ambiente).
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Variável de ambiente DATABASE_URL não configurada. "
        "Defina ela com a connection string do Neon (veja .env.example)."
    )

# ==============================================================
# Cada planilha de material vira linhas na tabela materiais_area,
# associadas à "chave" de área correspondente (mesma chave usada em
# AREAS_OFICINA no dados.js). Quando mais de uma planilha aponta pra
# mesma área (ex: Grupo 1/2/3 -> segmento-grupo), os itens de todas
# são somados na mesma área, sem duplicar (upsert por código).
#
# Se o nome real do arquivo na sua pasta for um pouco diferente
# (espaço x underline, singular x plural), ajuste aqui.
# ==============================================================
PLANILHAS = [
    ("LISTA_DE_MATERIAL_DO_BENDER_.xlsx", "bender"),
    ("LISTA_DE_MATERIAL_MOLDE_DE_MCC_4.xlsx", "molde-mcc4"),
    ("LISTA_DE_MATERAL_DE_CADEIRA_SUPERIOR_.xlsx", "cadeira"),
    ("LISTA_DE_MATERIAL_DA_CADEIRA_INFERIOR.xlsx", "cadeira"),
    ("LISTA_DE_MATERIAL_DO_GRUPO_1.xlsx", "segmento-grupo"),
    ("LISTA_DE_MATERIAL_DO_GRUPO_2.xlsx", "segmento-grupo"),
    ("LISTA_DE_MATERIAL_DO_GRUPO_3.xlsx", "segmento-grupo"),
    ("LISTA_DE_MATERIAL_DO_ZERO.xlsx", "zero"),
    ("LISTA_DE_MATERIAL_DO_MOLDE_2_3.xlsx", "molde-mcc23"),
    ("LISTA_DE_MATERIAL_DO_HORIZONTAL.xlsx", "mcc4"),
    ("LISTA_DE_MATERIAL_DO_STRAINGHTENER.xlsx", "mcc4"),
    ("LISTA_DE_MATERIAL_DO_BOW.xlsx", "mcc4"),
    ("LISTA_DE_MATERIAL_DA_CALDEIRARIA.xlsx", "caldeiraria"),
]

SHEET_NAME = "Planilha1"

# Possíveis nomes de coluna encontrados nas planilhas (elas não seguem
# um padrão único). O script detecta automaticamente qual coluna é o
# código e qual é a descrição, testando essas variações.
COLUNAS_CODIGO = ["CODIGO", "CÓDIGO", "Código", "codigo"]
COLUNAS_DESCRICAO = ["TEXTO BREVE", "Descrição Material", "Descricao Material", "DESCRICAO"]


def encontrar_coluna(df, opcoes):
    for opc in opcoes:
        if opc in df.columns:
            return opc
    # tentativa "por aproximação": ignora maiúsculas/acentos
    import unicodedata

    def normalizar(s):
        s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode("ASCII")
        return s.strip().lower()

    alvo = [normalizar(o) for o in opcoes]
    for col in df.columns:
        if normalizar(col) in alvo:
            return col
    return None


def encontrar_arquivo(nome_esperado):
    """Se o arquivo exato não existir, tenta achar por aproximação na
    pasta atual (mesma lógica dos outros importadores)."""
    if os.path.isfile(nome_esperado):
        return nome_esperado

    # tenta achar algo parecido: mesmas primeiras palavras-chave
    candidatos = [f for f in os.listdir(".") if f.lower().endswith(".xlsx")]
    chave = nome_esperado.lower().replace(".xlsx", "").replace("_", " ").split()
    chave_relevante = [p for p in chave if p not in ("lista", "de", "do", "da")]

    for arq in candidatos:
        arq_norm = arq.lower().replace("_", " ")
        if all(p in arq_norm for p in chave_relevante):
            return arq

    return None


def importar():
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("Verificando/criando tabela 'materiais_area'...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiais_area (
            id SERIAL PRIMARY KEY,
            area TEXT NOT NULL,
            codigo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            criado_por TEXT,
            criado_em TEXT,
            UNIQUE(area, codigo)
        )
    ''')
    conn.commit()

    from datetime import datetime
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_geral = 0
    resumo_por_area = {}

    for nome_esperado, area in PLANILHAS:
        arquivo = encontrar_arquivo(nome_esperado)
        if not arquivo:
            print(f"\n⚠️  Não encontrei o arquivo '{nome_esperado}' nesta pasta. Pulei essa planilha.")
            continue

        print(f"\nLendo '{arquivo}' -> área '{area}'...")
        df = pd.read_excel(arquivo, sheet_name=SHEET_NAME, engine="openpyxl")

        col_codigo = encontrar_coluna(df, COLUNAS_CODIGO)
        col_descricao = encontrar_coluna(df, COLUNAS_DESCRICAO)

        if not col_codigo or not col_descricao:
            print(f"   ⚠️  Não consegui identificar as colunas de código/descrição em '{arquivo}'. "
                  f"Colunas encontradas: {list(df.columns)}. Pulei essa planilha.")
            continue

        linhas = []
        vazias = 0
        for _, row in df.iterrows():
            codigo_raw = row.get(col_codigo)
            descricao_raw = row.get(col_descricao)

            if pd.isna(codigo_raw) or pd.isna(descricao_raw):
                vazias += 1
                continue

            codigo = str(int(codigo_raw)) if isinstance(codigo_raw, float) and codigo_raw.is_integer() else str(codigo_raw).strip()
            codigo = codigo.strip().upper()
            descricao = str(descricao_raw).strip().upper()

            if not codigo or not descricao:
                continue

            linhas.append((area, codigo, descricao, "Sistema (importado planilha)", agora))

        if not linhas:
            print(f"   ⚠️  Nenhuma linha válida encontrada em '{arquivo}'.")
            continue

        cursor.executemany('''
            INSERT INTO materiais_area (area, codigo, descricao, criado_por, criado_em)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (area, codigo) DO UPDATE SET
                descricao = EXCLUDED.descricao
        ''', linhas)
        conn.commit()

        print(f"   ✅ {len(linhas)} item(ns) importado(s)/atualizado(s) ({vazias} linha(s) vazia(s) ignorada(s)).")
        total_geral += len(linhas)
        resumo_por_area[area] = resumo_por_area.get(area, 0) + len(linhas)

    print("\n" + "=" * 60)
    print(f"✅ Total geral: {total_geral} item(ns) processado(s) no Neon!")
    print("\n📋 Resumo por área:")
    for area, qtd in sorted(resumo_por_area.items()):
        cursor.execute("SELECT COUNT(*) as qtd FROM materiais_area WHERE area = %s", (area,))
        total_no_banco = cursor.fetchone()[0]
        print(f"   {area}: +{qtd} nesta importação (total atual no banco: {total_no_banco})")

    conn.close()


if __name__ == "__main__":
    importar()
