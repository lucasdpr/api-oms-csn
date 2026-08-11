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

# Nome real do arquivo pode variar (espaço x underline, com/sem acento).
# O script tenta cada variação nesta pasta e usa a primeira que encontrar.
NOMES_POSSIVEIS = [
    "RELAÇÃO_TECNICOS.xlsx",
    "RELAÇÃO TECNICOS.xlsx",
    "RELACAO_TECNICOS.xlsx",
    "RELACAO TECNICOS.xlsx",
]
SHEET_NAME = "Planilha1"


def encontrar_arquivo():
    for nome in NOMES_POSSIVEIS:
        if os.path.isfile(nome):
            return nome
    for arquivo in os.listdir("."):
        if arquivo.lower().endswith(".xlsx") and "tecnic" in arquivo.lower():
            return arquivo
    raise FileNotFoundError(
        "Não encontrei a planilha de técnicos nesta pasta. Tentei: "
        + ", ".join(NOMES_POSSIVEIS)
        + ". Confirme que o arquivo .xlsx está salvo na mesma pasta deste script."
    )


def resetar():
    """
    ⚠️ AÇÃO DESTRUTIVA: apaga TODOS os colaboradores que estão hoje no
    banco (ex: os 80 que vieram de uma lista mais ampla da fábrica) e
    recadastra do zero SÓ os técnicos que estão na planilha atual —
    todos já com cargo = 'Técnico' e liberados pra logar (ativo=TRUE).

    Como a tabela é apagada e recriada, todo mundo volta a ser
    "primeiro acesso": a senha temporária de cada um passa a ser a
    própria matrícula, e o sistema vai pedir pra cadastrar uma senha
    nova no primeiro login — igual a um cadastro novo.

    O acesso de desenvolvedor (matrícula "061012") não é afetado por
    esse script, porque ele é validado direto no script.js (front-end),
    sem nunca consultar essa tabela.
    """
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

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

    print(f"\n{len(linhas)} técnico(s) encontrado(s) na planilha.")

    if erros:
        print(f"\n⚠️  {len(erros)} linha(s) com problema (não foram importadas):")
        for tag, msg in erros:
            print(f"   Matrícula='{tag}': {msg}")

    if not linhas:
        print("\n❌ Nenhum técnico válido encontrado na planilha. Nada foi apagado, por segurança.")
        conn.close()
        return

    confirmacao = input(
        f"\n⚠️  Isso vai APAGAR TODOS os colaboradores atuais do banco e "
        f"recadastrar só os {len(linhas)} técnicos da planilha. "
        f"Digite CONFIRMAR pra continuar: "
    )
    if confirmacao.strip().upper() != "CONFIRMAR":
        print("Cancelado. Nada foi alterado.")
        conn.close()
        return

    print("\nApagando todos os colaboradores atuais...")
    cursor.execute("DELETE FROM colaboradores")
    apagados = cursor.rowcount

    print(f"Recadastrando os {len(linhas)} técnicos da planilha...")
    cursor.executemany('''
        INSERT INTO colaboradores (matricula, nome, cargo, ativo)
        VALUES (%s, %s, %s, TRUE)
    ''', linhas)

    conn.commit()

    cursor.execute("SELECT matricula, nome, cargo FROM colaboradores WHERE ativo = TRUE ORDER BY nome")
    ativos = cursor.fetchall()

    print(f"\n🗑️  {apagados} colaborador(es) antigo(s) removido(s).")
    print(f"\n✅ {len(ativos)} técnico(s) cadastrado(s) e ativo(s) agora:")
    for matricula, nome, cargo in ativos:
        print(f"   {matricula} — {nome} ({cargo})")

    conn.close()


if __name__ == "__main__":
    resetar()
