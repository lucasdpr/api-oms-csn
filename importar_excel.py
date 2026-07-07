import sqlite3
import pandas as pd
import math

def importar_fabrica_inteira():
    print("🚀 Iniciando Limpeza e Injeção (Com Correção de Gavetas)...")
    conexao = sqlite3.connect('oficina.db')
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM equipamentos")

    try:
        excel_file = pd.ExcelFile('dados_reais.xlsx')
        contador_instalados = 0
        contador_historico = 0
        slots_ocupados = {}

        for nome_aba in excel_file.sheet_names:
            aba_upper = nome_aba.upper()
            if "HIST" in aba_upper or "FAROL" in aba_upper or "2026" in aba_upper or "PRODUÇÃO" in aba_upper:
                continue

            df = excel_file.parse(nome_aba, header=None)
            linha_cabecalho = -1
            colunas_map = {}

            for i, row in df.iterrows():
                row_str = " ".join([str(val).upper() for val in row if pd.notna(val)])
                if ("Nº DO ROLO" in row_str or "NUM" in row_str or "POSIÇÃO" in row_str or "POSICAO" in row_str):
                    linha_cabecalho = i
                    for col_idx, val in enumerate(row):
                        if pd.notna(val): colunas_map[str(val).strip().upper()] = col_idx
                    break

            if linha_cabecalho == -1 or len(colunas_map) == 0: continue

            for i in range(linha_cabecalho + 1, len(df)):
                linha = df.iloc[i]
                
                tag = ""
                for nome_col in ["Nº DO ROLO", "NUM", "ID"]:
                    if nome_col in colunas_map and pd.notna(linha.iloc[colunas_map[nome_col]]):
                        tag = str(linha.iloc[colunas_map[nome_col]]).strip()
                        break
                if not tag or tag.lower() == 'nan' or len(tag) < 2: continue

                veio = ""
                for nome_col in ["VEIO", "VEIO E POSIÇÃO"]:
                    if nome_col in colunas_map and pd.notna(linha.iloc[colunas_map[nome_col]]):
                        veio = str(linha.iloc[colunas_map[nome_col]]).strip()

                posicao = ""
                for nome_col in ["POSIÇÃO", "POSICAO"]:
                    if nome_col in colunas_map and pd.notna(linha.iloc[colunas_map[nome_col]]):
                        posicao = str(linha.iloc[colunas_map[nome_col]]).strip()

                if "-" in veio and not posicao:
                    partes = veio.split("-")
                    posicao = partes[0]
                    veio = partes[1]
                elif "/" in veio:
                    partes = veio.split("/")
                    posicao = partes[0]
                    veio = partes[1]

                tonelagem = 0.0
                for nome_col in ["PRODUÇÃO EM TON.", "TONELAGEM", "TONELAGEM "]:
                    if nome_col in colunas_map and pd.notna(linha.iloc[colunas_map[nome_col]]):
                        try: tonelagem = float(linha.iloc[colunas_map[nome_col]])
                        except: pass

                motivo_saida = ""
                for nome_col in ["MOTIVO DA SAÍDA", "MOTIVO SAÍDA", "DATA DE SAÍDA", "DATA SAÍDA"]:
                    if nome_col in colunas_map and pd.notna(linha.iloc[colunas_map[nome_col]]):
                        motivo_saida = str(linha.iloc[colunas_map[nome_col]]).strip()

                mcc = "4"
                if veio.upper() in ['C', 'D']: mcc = "2"
                elif veio.upper() in ['E', 'F']: mcc = "3"

                tipo = "Equipamento"
                if "CADEIRA" in aba_upper and "SUP" in aba_upper: tipo = "Cadeira Superior"
                elif "CADEIRA" in aba_upper and "INF" in aba_upper: tipo = "Cadeira Inferior"
                elif "ZERO" in aba_upper: tipo = "Segmento Zero"
                elif "GRUPO #1" in aba_upper: tipo = "Segmento Grupo 1"
                elif "GRUPO #2" in aba_upper: tipo = "Segmento Grupo 2"
                elif "GRUPO #3" in aba_upper: tipo = "Segmento Grupo 3"
                elif "BENDER" in aba_upper: tipo = "Bender"
                elif "BOW" in aba_upper: tipo = "Bow"
                elif "STRAIGHTENER" in aba_upper:
                    if "RII" in tag.upper() or "R2" in tag.upper(): tipo = "Straightener R2"
                    else: tipo = "Straightener R1"
                elif "HORIZONTAL" in aba_upper: tipo = "Horizontal"
                
                if tipo == "Equipamento":
                    try:
                        pos_num = int(float(posicao))
                        if pos_num >= 43: tipo = "Cadeira Superior"
                        elif pos_num <= 17: tipo = "Segmento"
                    except: pass

                # 🔥 O SEGREDO ESTÁ AQUI: FORMATANDO A GAVETA EXATA 🔥
                slot_chassi = ""
                t_upper = tipo.upper()
                if "MOLDE" in t_upper: slot_chassi = "MOLDE"
                elif "OSCILADORA" in t_upper: slot_chassi = "OSCILADORA"
                elif "ZERO" in t_upper: slot_chassi = "SEG-ZERO"
                elif "BENDER" in t_upper: slot_chassi = "BENDER"
                elif "BOW" in t_upper: slot_chassi = f"BOW-{posicao}"
                elif "HORIZONTAL" in t_upper: slot_chassi = f"HOR-{posicao}"
                elif "STR-1" in t_upper or "R1" in t_upper: slot_chassi = "STR-1"
                elif "STR-2" in t_upper or "R2" in t_upper: slot_chassi = "STR-2"
                elif "CADEIRA SUPERIOR" in t_upper: slot_chassi = f"CAD-SUP-{posicao}"
                elif "CADEIRA INFERIOR" in t_upper: slot_chassi = f"CAD-INF-{posicao}"
                elif "SEGMENTO" in t_upper: slot_chassi = f"SEG-{posicao}"
                else: slot_chassi = str(posicao)

                chave_slot = f"MCC{mcc}-{veio}-{slot_chassi}"

                if motivo_saida or chave_slot in slots_ocupados or not veio or str(veio).lower() == 'nan':
                    local = "Oficina / Reserva"
                    status = "Oficina / Reserva"
                    contador_historico += 1
                    slot_chassi = "" # Tira a gaveta de quem está no estoque
                else:
                    local = f"MCC {mcc} - Veio {veio}"
                    status = "Instalado"
                    slots_ocupados[chave_slot] = True
                    contador_instalados += 1
                
                meta = 2000000 
                if tipo == "Molde": meta = 1100

                cursor.execute('''
                    INSERT OR REPLACE INTO equipamentos 
                    (ID, TIPO, LOCAL, STATUS, TONELAGEM, DIAS, META, POSICAO)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (tag, tipo, local, status, tonelagem, 0, meta, slot_chassi))

        conexao.commit()
        print(f"\n🔥 GAVETAS ALINHADAS E INJEÇÃO CONCLUÍDA!")
        print(f"✔️ {contador_instalados} Equipamentos perfeitamente encaixados nas Máquinas.")

    except Exception as e: print(f"\n❌ ERRO: {e}")
    finally: conexao.close()

if __name__ == "__main__":
    importar_fabrica_inteira()