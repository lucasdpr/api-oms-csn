import os
import re
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Carrega variáveis de um .env local (na nuvem/Render isso é ignorado,
# as variáveis já vêm configuradas no ambiente).
load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError(
        "Variáveis de ambiente do banco não configuradas. "
        "Defina DB_HOST, DB_NAME, DB_USER e DB_PASSWORD (veja .env.example)."
    )

# Nome real do arquivo, do jeito que está na pasta do projeto.
EXCEL_FILE = "MCC4 OMS PRONTO FINALIZADO.xlsx"
SHEET_NAME = "MMCs"


def limpar_veio(mcc, veio_bruto):
    """
    Corrige o typo conhecido na planilha: algumas linhas da MCC 3 têm a
    coluna VEIO escrita como 'MCC 2 - Veio F' por engano (deveria ser
    'MCC 3 - Veio F'). A coluna MCC da própria linha está sempre correta,
    então usamos ela como fonte da verdade e só extraímos a letra do veio
    do texto original.
    Retorna (veio_corrigido, letra_do_veio).
    """
    veio_bruto = str(veio_bruto).strip()
    m = re.search(r'Veio\s+([CDEFGH])', veio_bruto, re.IGNORECASE)
    letra = m.group(1).upper() if m else None
    mcc_num = str(mcc).strip().replace("MCC", "").strip()
    if letra:
        return f"MCC {mcc_num} - Veio {letra}", letra
    return veio_bruto, None


def gerar_id_sistema(veio_letra, tipo, rank_no_veio_tipo):
    """
    Gera um ID de sistema único e estável, no MESMO formato que o
    banco.js do front-end já usa (MLD-4H, CAD-SUP-43-2C, BOW-1-4H...).

    Isso é necessário porque o código de patrimônio real (coluna ID da
    planilha) NÃO é único — o mesmo código aparece em mais de uma peça
    física em veios ou tipos diferentes (13 casos confirmados na
    planilha atual). O código real de patrimônio é preservado à parte,
    na coluna tag_patrimonio.
    """
    t = tipo.upper()
    is_mcc4 = veio_letra in ("G", "H")
    sufixo = f"4{veio_letra}" if is_mcc4 else f"2{veio_letra}"

    if t == "MOLDE":
        return f"MLD-{sufixo}"
    if t == "BENDER":
        return f"BND-{sufixo}"
    if t == "BOW":
        return f"BOW-{rank_no_veio_tipo}-{sufixo}"
    if t == "R1":
        return f"STR-1-{sufixo}"
    if t == "R2":
        return f"STR-2-{sufixo}"
    if t.startswith("HORIZONTAL"):
        # "HORIZONTAL 3" -> HOR-10-4G (mapeia 1..10 para 8..17,
        # igual à numeração que o banco.js já usa)
        m = re.search(r'(\d+)', t)
        n = int(m.group(1)) if m else rank_no_veio_tipo
        return f"HOR-{7 + n}-{sufixo}"
    if t == "CADEIRA SUP":
        # Numeração física real das cadeiras: 43 a 79
        return f"CAD-SUP-{42 + rank_no_veio_tipo}-{sufixo}"
    if t == "CADEIRA INF":
        return f"CAD-INF-{42 + rank_no_veio_tipo}-{sufixo}"
    if t == "ZERO":
        return f"SEG-0-{sufixo}"
    if t == "GRUPO 1":
        return f"GRP1-{sufixo}"
    if t == "GRUPO 2":
        return f"GRP2-{rank_no_veio_tipo}-{sufixo}"
    if t == "GRUPO 3":
        return f"GRP3-{rank_no_veio_tipo}-{sufixo}"
    # fallback de segurança para qualquer tipo não previsto acima
    return f"{t.replace(' ', '')}-{rank_no_veio_tipo}-{sufixo}"


def montar_posicao(id_sistema):
    """Rótulo de posição legível, derivado do próprio ID de sistema."""
    return id_sistema


def importar():
    print("Conectando ao PostgreSQL do Render...")
    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER,
        password=DB_PASSWORD, port=DB_PORT
    )
    cursor = conn.cursor()

    print("Verificando/atualizando estrutura da tabela...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipamentos (
            id TEXT PRIMARY KEY,
            tipo TEXT,
            local TEXT,
            status TEXT,
            tonelagem REAL,
            dias INTEGER,
            meta REAL,
            posicao TEXT
        )
    ''')
    # Coluna nova: guarda o código de patrimônio real da peça física,
    # separado do id de sistema (que representa a VAGA, não a peça).
    cursor.execute('''
        ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS tag_patrimonio TEXT
    ''')
    cursor.execute('''
        ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS data_entrada TEXT
    ''')
    conn.commit()

    print(f"Lendo planilha '{EXCEL_FILE}'...")
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, engine='openpyxl')

    contadores = {}
    linhas = []
    tags_vistas = {}
    tags_duplicadas = []
    erros = []

    for _, row in df.iterrows():
        try:
            if pd.isna(row.get('ID')) or pd.isna(row.get('MCC')):
                continue

            tag_patrimonio = str(row['ID']).strip()
            tipo = str(row['TIPO']).strip()
            veio, letra = limpar_veio(row['MCC'], row['VEIO'])

            if not letra:
                erros.append((tag_patrimonio, f"Não consegui identificar o veio em '{row['VEIO']}'"))
                continue

            tonelagem = float(row['TONELAGEM']) if pd.notna(row['TONELAGEM']) else 0.0
            meta = float(row['META']) if pd.notna(row['META']) else 0.0
            dias = int(row['DIAS']) if pd.notna(row['DIAS']) else 0
            status = str(row['STATUS']).strip() if pd.notna(row['STATUS']) else "Instalado"

            # Data de entrada/instalação: vem da coluna ENTRADA da planilha
            # (já existia lá, só não estava sendo aproveitada até agora)
            entrada_raw = row.get('ENTRADA')
            if pd.notna(entrada_raw):
                data_entrada = entrada_raw.strftime('%d/%m/%Y') if hasattr(entrada_raw, 'strftime') else str(entrada_raw).strip()
            else:
                data_entrada = None

            chave = (veio, tipo)
            contadores[chave] = contadores.get(chave, 0) + 1
            id_sistema = gerar_id_sistema(letra, tipo, contadores[chave])
            posicao = montar_posicao(id_sistema)

            if tag_patrimonio in tags_vistas and tags_vistas[tag_patrimonio] != id_sistema:
                tags_duplicadas.append(tag_patrimonio)
            tags_vistas[tag_patrimonio] = id_sistema

            linhas.append((id_sistema, tipo, veio, status, tonelagem, dias, meta, posicao, tag_patrimonio, data_entrada))
        except Exception as e:
            erros.append((row.get('ID'), str(e)))

    print(f"\n{len(linhas)} equipamentos processados da planilha.")

    if tags_duplicadas:
        print(f"\n⚠️  {len(set(tags_duplicadas))} código(s) de patrimônio aparecem em mais de uma peça física")
        print("   (isso é esperado — o id de sistema abaixo resolve isso). Códigos:")
        print("  ", sorted(set(tags_duplicadas)))

    if erros:
        print(f"\n⚠️  {len(erros)} linha(s) com problema (não foram importadas):")
        for tag, msg in erros:
            print(f"   ID='{tag}': {msg}")

    print("\nApagando dados antigos da tabela...")
    cursor.execute("DELETE FROM equipamentos")

    print("Inserindo os equipamentos...")
    cursor.executemany('''
        INSERT INTO equipamentos (id, tipo, local, status, tonelagem, dias, meta, posicao, tag_patrimonio, data_entrada)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', linhas)

    conn.commit()
    print(f"\n✅ {len(linhas)} equipamentos importados com sucesso para o PostgreSQL no Render!")
    conn.close()


if __name__ == "__main__":
    importar()