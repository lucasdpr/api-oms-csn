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

# Nome real do arquivo pode variar (espaço x underline, com/sem acento,
# dependendo de como foi salvo/baixado). O script tenta cada variação
# nesta pasta e usa a primeira que encontrar.
NOMES_POSSIVEIS = [
    "RELAÇÃO TECNICOS.xlsx",
    "RELAÇÃO_TECNICOS.xlsx",
    "RELACAO TECNICOS.xlsx",
    "RELACAO_TECNICOS.xlsx",
]
SHEET_NAME = "Planilha1"


def encontrar_arquivo():
    for nome in NOMES_POSSIVEIS:
        if os.path.isfile(nome):
            return nome
    # Última tentativa: procura qualquer .xlsx na pasta atual que contenha
    # "TECNICO" no nome (ignorando maiúsculas/acentos aproximadamente).
    for arquivo in os.listdir("."):
        if arquivo.lower().endswith(".xlsx") and "tecnic" in arquivo.lower():
            return arquivo
    raise FileNotFoundError(
        "Não encontrei a planilha de técnicos nesta pasta. Tentei: "
        + ", ".join(NOMES_POSSIVEIS)
        + ". Confirme que o arquivo .xlsx está salvo na mesma pasta deste script "
          "(rode 'dir *.xlsx' pra conferir os nomes exatos)."
    )

# Colaboradores extras que não vêm da planilha (ex: acesso de dev).
# matricula: (nome, cargo)
EXTRAS = {
    "061012": ("Lucas", "Desenvolvedor"),
}


def importar():
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("Verificando/criando tabela 'colaboradores'...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            matricula TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            cargo TEXT DEFAULT 'Colaborador',
            ativo BOOLEAN DEFAULT TRUE
        )
    ''')
    conn.commit()

    excel_file = encontrar_arquivo()
    print(f"Lendo planilha '{excel_file}'...")
    df = pd.read_excel(excel_file, sheet_name=SHEET_NAME, engine='openpyxl')

    linhas = []
    erros = []

    for _, row in df.iterrows():
        try:
            matricula_raw = row.get('Matríc.')
            nome_raw = row.get('Nome')

            if pd.isna(matricula_raw) or pd.isna(nome_raw):
                continue

            matricula = str(matricula_raw).strip().upper()
            nome = str(nome_raw).strip()

            if not matricula or not nome:
                continue

            linhas.append((matricula, nome, "Técnico"))
        except Exception as e:
            erros.append((row.get('Matríc.'), str(e)))

    for matricula, (nome, cargo) in EXTRAS.items():
        linhas.append((matricula, nome, cargo))

    print(f"\n{len(linhas)} colaborador(es) processado(s) da planilha (+ extras).")

    if erros:
        print(f"\n⚠️  {len(erros)} linha(s) com problema (não foram importadas):")
        for tag, msg in erros:
            print(f"   Matrícula='{tag}': {msg}")

    print("\nInserindo/atualizando colaboradores (upsert por matrícula)...")
    print("(nome/cargo são atualizados; senha e status de primeiro acesso NÃO são mexidos em quem já existe)")
    cursor.executemany('''
        INSERT INTO colaboradores (matricula, nome, cargo, ativo)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (matricula) DO UPDATE SET
            nome = EXCLUDED.nome,
            cargo = EXCLUDED.cargo,
            ativo = TRUE
    ''', linhas)

    # Desativa qualquer colaborador que já esteja no banco mas NÃO está
    # nesta lista (ex: importações antigas com gente que não deve mais
    # ter acesso de edição). Eles deixam de conseguir logar, mas o
    # histórico de ações deles no sistema continua intacto.
    matriculas_atuais = tuple(m for m, _, _ in linhas)
    if matriculas_atuais:
        cursor.execute(
            "UPDATE colaboradores SET ativo = FALSE WHERE matricula NOT IN %s AND ativo = TRUE",
            (matriculas_atuais,)
        )
        print(f"🔒 {cursor.rowcount} colaborador(es) antigo(s) desativado(s) (não estão mais na lista).")

    conn.commit()
    print(f"\n✅ {len(linhas)} colaborador(es) importado(s)/atualizado(s) com sucesso no Neon!")
    conn.close()


if __name__ == "__main__":
    importar()