import os
import unicodedata
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

# Importa a EQUIPE da oficina (mecânicos, eletricistas, operadores etc.
# — quem NÃO é liderança). É uma planilha diferente da RELAÇÃO_TECNICOS
# usada em importar_colaboradores.py: aquela cadastra quem faz LOGIN no
# sistema; esta aqui só popula o roster que aparece na seção "Equipe da
# Área" de cada área da Oficina — sem senha, sem login.
NOMES_POSSIVEIS = [
    "efetivo_oms.xlsx",
    "EFETIVO_OMS.xlsx",
    "Efetivo_OMS.xlsx",
    "efetivo oms.xlsx",
]
SHEET_NAME = "Planilha1"


def encontrar_arquivo():
    for nome in NOMES_POSSIVEIS:
        if os.path.isfile(nome):
            return nome
    for arquivo in os.listdir("."):
        if arquivo.lower().endswith(".xlsx") and "efetivo" in arquivo.lower():
            return arquivo
    raise FileNotFoundError(
        "Não encontrei a planilha do efetivo nesta pasta. Tentei: "
        + ", ".join(NOMES_POSSIVEIS)
        + ". Confirme que o arquivo .xlsx está salvo na mesma pasta deste script "
          "(rode 'dir *.xlsx' pra conferir os nomes exatos)."
    )


def normalizar(texto):
    """Remove acentos e deixa minúsculo, pra comparar o texto da coluna
    'Equipe' sem depender de maiúscula/acento exatos vindos da planilha."""
    texto = str(texto).strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.lower()


# Mapa "Equipe" (como vem na coluna da planilha) -> "chave" da área (a
# mesma usada em AREAS_OFICINA no dados.js e nas tabelas
# oficina_atividades / equipe_oficina).
#
# 🔧 Dois pontos de atenção, confirmados olhando a planilha real:
#   1) "Desempenadeira" vira "cadeira" — é o mesmo equipamento, só que o
#      folhão dele se chama "Desempenadeira" (ver folhaoDesempenadeira.js)
#      enquanto o TIPO cadastrado no banco é "Cadeira Superior/Inferior".
#   2) "Segmento de Grupo" NÃO é dividido em Grupo 2 / Grupo 3 aqui — no
#      efetivo real é um time só cuidando dos dois, por isso a área
#      "segmento-grupo" no dados.js também é uma coisa só.
#
# Se aparecer uma "Equipe" nova na planilha que não bate com nada aqui,
# o script avisa no final (não trava, não inventa mapeamento).
MAPA_AREA = {
    normalizar("Hidráulica"): "hidraulica",
    normalizar("Usinagem"): "usinagem",
    normalizar("Caldeiraria"): "caldeiraria",
    normalizar("Jato"): "jato",
    normalizar("Elétrica"): "eletrica",
    normalizar("ADM"): "adm",
    normalizar("Logística"): "logistica",
    normalizar("Ponte Rolante"): "ponte-rolante",
    normalizar("Almoxarifado"): "almoxarifado",
    normalizar("Zero"): "zero",
    normalizar("Segmento de Grupo"): "segmento-grupo",
    normalizar("MCC#4"): "mcc4",
    normalizar("Bender"): "bender",
    normalizar("Molde MCC#4"): "molde-mcc4",
    normalizar("Molde MCC#2 e 3"): "molde-mcc23",
    normalizar("Desempenadeira"): "cadeira",
}


def importar():
    print("Conectando ao PostgreSQL do Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("Verificando/criando tabela 'equipe_oficina'...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipe_oficina (
            matricula TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            cargo TEXT,
            area TEXT NOT NULL,
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
            cargo_raw = row.get('Cargo')
            equipe_raw = row.get('Equipe')

            if pd.isna(matricula_raw) or pd.isna(nome_raw):
                continue

            matricula = str(matricula_raw).strip().upper()
            nome = str(nome_raw).strip()
            cargo = str(cargo_raw).strip() if pd.notna(cargo_raw) else None

            if pd.isna(equipe_raw):
                erros.append((matricula, nome, "Coluna 'Equipe' vazia na planilha — não dá pra saber a área dessa pessoa."))
                continue

            chave_area = MAPA_AREA.get(normalizar(equipe_raw))
            if not chave_area:
                erros.append((matricula, nome, f"Equipe '{equipe_raw}' não reconhecida — confira o nome exato na planilha ou adicione no MAPA_AREA deste script."))
                continue

            linhas.append((matricula, nome, cargo, chave_area))
        except Exception as e:
            erros.append((row.get('Matríc.'), row.get('Nome'), str(e)))

    print(f"\n{len(linhas)} pessoa(s) processada(s) da planilha.")

    if erros:
        print(f"\n⚠️  {len(erros)} linha(s) com problema (NÃO foram importadas):")
        for matricula, nome, msg in erros:
            print(f"   {matricula} — {nome}: {msg}")

    if not linhas:
        print("\n❌ Nenhuma pessoa válida encontrada na planilha. Nada foi importado.")
        conn.close()
        return

    print("\nInserindo/atualizando equipe da oficina (upsert por matrícula)...")
    cursor.executemany('''
        INSERT INTO equipe_oficina (matricula, nome, cargo, area, ativo)
        VALUES (%s, %s, %s, %s, TRUE)
        ON CONFLICT (matricula) DO UPDATE SET
            nome = EXCLUDED.nome,
            cargo = EXCLUDED.cargo,
            area = EXCLUDED.area,
            ativo = TRUE
    ''', linhas)

    # Desativa quem já estava cadastrado mas não está mais nesta
    # planilha (ex: alguém que saiu da oficina) — sem apagar o
    # histórico de atividades que essa pessoa possa ter como
    # "responsável" (esse campo é texto livre, não FK).
    matriculas_atuais = tuple(m for m, _, _, _ in linhas)
    if matriculas_atuais:
        cursor.execute(
            "UPDATE equipe_oficina SET ativo = FALSE WHERE matricula NOT IN %s AND ativo = TRUE",
            (matriculas_atuais,)
        )
        print(f"🔒 {cursor.rowcount} pessoa(s) desativada(s) (não está(ão) mais na planilha).")

    conn.commit()

    cursor.execute("SELECT area, COUNT(*) as qtd FROM equipe_oficina WHERE ativo = TRUE GROUP BY area ORDER BY area")
    print("\n📋 Equipe ativa por área agora:")
    for area, qtd in cursor.fetchall():
        print(f"   {area}: {qtd} pessoa(s)")

    print(f"\n✅ {len(linhas)} pessoa(s) importada(s)/atualizada(s) com sucesso no Neon!")
    conn.close()


if __name__ == "__main__":
    importar()
