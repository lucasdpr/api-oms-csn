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

# Nome real do arquivo pode variar um pouco dependendo de como foi salvo.
NOMES_POSSIVEIS = [
    "ATUALIZADO.xlsx",
    "Atualizado.xlsx",
    "atualizado.xlsx",
]


def encontrar_arquivo():
    for nome in NOMES_POSSIVEIS:
        if os.path.isfile(nome):
            return nome
    for arquivo in os.listdir("."):
        if arquivo.lower().endswith(".xlsx") and "atualizado" in arquivo.lower():
            return arquivo
    raise FileNotFoundError(
        "Não encontrei a planilha de materiais nesta pasta. Tentei: "
        + ", ".join(NOMES_POSSIVEIS)
        + ". Confirme que o arquivo .xlsx está salvo na mesma pasta deste script."
    )


def importar():
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("Verificando/criando tabela 'materiais'...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiais (
            codigo TEXT PRIMARY KEY,
            descricao TEXT NOT NULL,
            qtd REAL NOT NULL DEFAULT 0
        )
    ''')
    cursor.execute("ALTER TABLE materiais ADD COLUMN IF NOT EXISTS local TEXT")
    cursor.execute("ALTER TABLE materiais ADD COLUMN IF NOT EXISTS valor_unit REAL")
    cursor.execute("ALTER TABLE materiais ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE")
    conn.commit()

    excel_file = encontrar_arquivo()
    print(f"Lendo planilha '{excel_file}'...")
    # Cabeçalho de verdade está na 2ª linha da planilha (a 1ª vem vazia),
    # e os dados começam na coluna F (as 5 primeiras vêm vazias também).
    df = pd.read_excel(excel_file, header=1, engine='openpyxl')
    df = df.dropna(axis=1, how='all')  # remove as colunas vazias A-E

    linhas = []
    erros = []

    for _, row in df.iterrows():
        try:
            codigo_raw = row.get('Código')
            descricao_raw = row.get('Texto')

            if pd.isna(codigo_raw) or pd.isna(descricao_raw):
                continue

            codigo = str(int(codigo_raw)) if isinstance(codigo_raw, float) else str(codigo_raw).strip()
            codigo = codigo.strip().upper()
            descricao = str(descricao_raw).strip().upper()

            # "Total em Estoque" é o saldo real e atual (considera entradas
            # e saídas já registradas) — mais confiável que "Quantidade
            # Inicial", que é só o ponto de partida.
            qtd_raw = row.get('Total em Estoque')
            qtd = float(qtd_raw) if pd.notna(qtd_raw) else 0.0

            local_raw = row.get('Local 1')
            local = str(local_raw).strip() if pd.notna(local_raw) else None

            valor_raw = row.get('Valor Unit.')
            valor_unit = float(valor_raw) if pd.notna(valor_raw) else None

            linhas.append((codigo, descricao, qtd, local, valor_unit))
        except Exception as e:
            erros.append((row.get('Código'), str(e)))

    print(f"\n{len(linhas)} material(is) processado(s) da planilha.")

    if erros:
        print(f"\n⚠️  {len(erros)} linha(s) com problema (não foram importadas):")
        for cod, msg in erros:
            print(f"   Código='{cod}': {msg}")

    print("\nInserindo/atualizando materiais (upsert por código)...")
    cursor.executemany('''
        INSERT INTO materiais (codigo, descricao, qtd, local, valor_unit, ativo)
        VALUES (%s, %s, %s, %s, %s, TRUE)
        ON CONFLICT (codigo) DO UPDATE SET
            descricao = EXCLUDED.descricao,
            qtd = EXCLUDED.qtd,
            local = EXCLUDED.local,
            valor_unit = EXCLUDED.valor_unit,
            ativo = TRUE
    ''', linhas)

    conn.commit()
    print(f"\n✅ {len(linhas)} material(is) importado(s)/atualizado(s) com sucesso no Neon!")
    print("   (materiais que já existiam e não estão nesta planilha foram mantidos como estavam)")
    conn.close()


if __name__ == "__main__":
    importar()
