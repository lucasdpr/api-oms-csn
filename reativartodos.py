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

# Matrículas que NÃO devem virar "Técnico" (o dev, por exemplo — se você
# quiser que ele continue como "Desenvolvedor" no banco). Deixe vazio
# se quiser que TODOS, sem exceção, virem "Técnico".
EXCECOES_CARGO = ()


def reativar_e_ajustar_cargo():
    """
    1) Reativa TODOS os colaboradores (desfaz o efeito do
       restringir_acesso.py, se ele tiver sido rodado).
    2) Ajusta o cargo de todos pra "Técnico" (em vez do valor padrão
       "Colaborador"), exceto quem estiver em EXCECOES_CARGO.

    Importante: isso NÃO mexe em quem pode ver o painel de 'Teste de
    Folhões' — essa restrição (só CBK3574 e CSP1869) é controlada à
    parte no front-end (MATRICULAS_TESTE_FOLHOES, em script.js) e
    continua funcionando normalmente depois de rodar este script.
    """
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("Reativando todos os colaboradores...")
    cursor.execute("UPDATE colaboradores SET ativo = TRUE WHERE ativo = FALSE")
    reativados = cursor.rowcount

    print("Ajustando cargo de todos para 'Técnico'...")
    if EXCECOES_CARGO:
        cursor.execute(
            "UPDATE colaboradores SET cargo = 'Técnico' WHERE matricula NOT IN %s",
            (EXCECOES_CARGO,)
        )
    else:
        cursor.execute("UPDATE colaboradores SET cargo = 'Técnico'")
    ajustados = cursor.rowcount

    conn.commit()

    cursor.execute("SELECT matricula, nome, cargo FROM colaboradores WHERE ativo = TRUE ORDER BY nome")
    ativos = cursor.fetchall()

    print(f"\n✅ {reativados} colaborador(es) reativado(s).")
    print(f"✅ {ajustados} colaborador(es) com cargo ajustado para 'Técnico'.")
    print(f"\n📋 Total de colaboradores com acesso agora ({len(ativos)}):")
    for matricula, nome, cargo in ativos:
        print(f"   {matricula} — {nome} ({cargo})")

    conn.close()


if __name__ == "__main__":
    reativar_e_ajustar_cargo()