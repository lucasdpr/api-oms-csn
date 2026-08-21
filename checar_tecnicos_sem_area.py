import os
import psycopg2
from dotenv import load_dotenv

# ==============================================================
# checar_tecnicos_sem_area.py
# ==============================================================
# Compara quem pode LOGAR no sistema (tabela colaboradores, vem da
# planilha RELAÇÃO TECNICOS.xlsx) com quem tem uma ÁREA cadastrada
# (tabela equipe_oficina, vem da planilha efetivo_oms.xlsx).
#
# Mostra quem está numa lista mas não na outra, pra você saber quem
# precisa ser corrigido/adicionado em alguma das duas planilhas antes
# de a restrição por área entrar em produção.
# ==============================================================

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Variável de ambiente DATABASE_URL não configurada. "
        "Defina ela com a connection string do Neon (veja .env.example)."
    )


def checar():
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT matricula, nome, cargo FROM colaboradores WHERE ativo = TRUE ORDER BY nome"
    )
    colaboradores = {m: (nome, cargo) for m, nome, cargo in cursor.fetchall()}

    cursor.execute(
        "SELECT matricula, nome, area FROM equipe_oficina WHERE ativo = TRUE"
    )
    equipe = {m: (nome, area) for m, nome, area in cursor.fetchall()}

    sem_area = []
    for matricula, (nome, cargo) in colaboradores.items():
        if matricula not in equipe:
            sem_area.append((matricula, nome, cargo))

    so_na_equipe = []
    for matricula, (nome, area) in equipe.items():
        if matricula not in colaboradores:
            so_na_equipe.append((matricula, nome, area))

    print(f"\n👥 Total de colaboradores com login ativo: {len(colaboradores)}")
    print(f"🏭 Total de pessoas com área cadastrada: {len(equipe)}")

    print(f"\n⚠️  {len(sem_area)} colaborador(es) COM LOGIN mas SEM ÁREA cadastrada:")
    print("   (esses vão cair na regra de 'sem área' até serem corrigidos)")
    for matricula, nome, cargo in sem_area:
        print(f"   {matricula} — {nome} ({cargo})")

    if so_na_equipe:
        print(f"\nℹ️  {len(so_na_equipe)} pessoa(s) com ÁREA cadastrada mas SEM LOGIN no sistema:")
        print("   (normal se forem pessoas que não usam o app, só aparecem na 'Equipe da Área')")
        for matricula, nome, area in so_na_equipe:
            print(f"   {matricula} — {nome} ({area})")

    conn.close()


if __name__ == "__main__":
    checar()
