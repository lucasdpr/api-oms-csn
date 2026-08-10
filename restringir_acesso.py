import os
import psycopg2
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

# Únicas matrículas autorizadas a logar no sistema (além do acesso local
# de desenvolvedor, que nem passa pelo banco — fica direto no script.js).
MATRICULAS_AUTORIZADAS = ("CBK3574", "CSP1869")


def restringir():
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print(f"Desativando todos os colaboradores, exceto: {', '.join(MATRICULAS_AUTORIZADAS)}...")
    cursor.execute(
        "UPDATE colaboradores SET ativo = FALSE WHERE matricula NOT IN %s AND ativo = TRUE",
        (MATRICULAS_AUTORIZADAS,)
    )
    desativados = cursor.rowcount

    print("Garantindo que as matrículas autorizadas estão ativas...")
    cursor.execute(
        "UPDATE colaboradores SET ativo = TRUE WHERE matricula IN %s",
        (MATRICULAS_AUTORIZADAS,)
    )

    conn.commit()

    cursor.execute("SELECT matricula, nome, cargo FROM colaboradores WHERE ativo = TRUE ORDER BY nome")
    ativos = cursor.fetchall()

    print(f"\n🔒 {desativados} colaborador(es) desativado(s).")
    print(f"\n✅ Colaboradores com acesso agora ({len(ativos)}):")
    for matricula, nome, cargo in ativos:
        print(f"   {matricula} — {nome} ({cargo})")

    conn.close()


if __name__ == "__main__":
    restringir()
