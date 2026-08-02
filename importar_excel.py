import psycopg2
import pandas as pd

# 🔥 CREDENCIAIS DO RENDER
DB_HOST = "dpg-d9nsgpvqj5pc73fi170g-a.ohio-postgres.render.com"
DB_NAME = "oficina_zvft"
DB_USER = "oficina_user"
DB_PASSWORD = "xwHUrq4qtkm8E8bFdMxwUcBdkJ8FHUXA"
DB_PORT = "5432"

SLOT_MAP = {
    1: "MOLDE", 2: "BENDER",
    3: "BOW-1", 4: "BOW-2", 5: "BOW-3", 6: "BOW-4", 7: "BOW-5",
    8: "STR-1", 9: "STR-2",
    10: "HOR-8", 11: "HOR-9", 12: "HOR-10", 13: "HOR-11", 14: "HOR-12",
    15: "HOR-13", 16: "HOR-14", 17: "HOR-15"
}

def importar_fabrica_int():
    print("🚀 Conectando ao PostgreSQL do Render...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
        )
        cursor = conn.cursor()
        
        # 🔥 CRIA A TABELA SE ELA NÃO EXISTIR (Pra evitar o erro que você levou)
        print("📦 Verificando/Criando tabelas no banco...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipamentos (
                ID TEXT PRIMARY KEY,
                TIPO TEXT,
                LOCAL TEXT,
                STATUS TEXT,
                TONELAGEM REAL,
                DIAS INTEGER,
                META REAL,
                POSICAO TEXT
            )
        ''')
        conn.commit()
        
        # Agora sim, apaga os dados antigos
        cursor.execute("DELETE FROM equipamentos")

        df = pd.read_excel('MCC4 OMS.xlsx', sheet_name='MMCs', engine='openpyxl')

        contador = 0
        for _, row in df.iterrows():
            try:
                tag_id = str(row['ID']).strip()
                tipo = str(row['TIPO']).strip()
                local = str(row['VEIO']).strip()
                pos_num = int(row['POS_NUM'])
                if pos_num > 17: continue
                posicao_slot = SLOT_MAP[pos_num]
                tonelagem = float(row['TONELAGEM']) if pd.notna(row['TONELAGEM']) else 0.0
                meta = float(row['META']) if pd.notna(row['META']) else 0
                dias = int(row['DIAS']) if pd.notna(row['DIAS']) else 0
                status = str(row['STATUS']).strip()

                cursor.execute('''
                    INSERT INTO equipamentos (ID, TIPO, LOCAL, STATUS, TONELAGEM, DIAS, META, POSICAO)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (tag_id, tipo, local, status, tonelagem, dias, meta, posicao_slot))
                contador += 1
            except Exception as e:
                print(f"⚠️ Erro linha: {e}")

        conn.commit()
        print(f"\n✅ {contador} equipamentos enviados para o banco PostgreSQL no Render!")
    except Exception as e:
        print(f"\n❌ Erro de conexão com o PostgreSQL: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    importar_fabrica_int()