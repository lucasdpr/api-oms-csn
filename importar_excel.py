import pandas as pd
import sqlite3

arquivo_excel = 'OMS_Controle_MCC.xlsx'
nome_banco = 'oficina.db'

print(f"Iniciando a leitura do arquivo: {arquivo_excel}...\n")

try:
    xls = pd.ExcelFile(arquivo_excel)
    todas_as_pecas = []

    for nome_da_aba in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=nome_da_aba)
        df['Origem_Aba'] = nome_da_aba
        todas_as_pecas.append(df)

    tabela_final = pd.concat(todas_as_pecas, ignore_index=True)
    
    # --- A FAXINA DOS DADOS (O SEGREDO PARA O BANCO DE DADOS NÃO TRAVAR) ---
    # 1. Garante que todos os nomes de colunas sejam texto e tira espaços extras
    tabela_final.columns = [str(c).strip().replace(' ', '_') for c in tabela_final.columns]
    
    # 2. Remove colunas com nomes duplicados (comum quando o Excel tem células mescladas)
    tabela_final = tabela_final.loc[:, ~tabela_final.columns.duplicated()]
    
    # 3. Converte todos os dados para texto puro na primeira injeção para evitar quebras
    tabela_final = tabela_final.astype(str)
    # ----------------------------------------------------------------------
    
    print(f"Leitura e faxina concluídas. Total de peças unificadas: {len(tabela_final)}")
    print("Iniciando injeção no Banco de Dados SQLite...\n")
    
    conexao = sqlite3.connect(nome_banco)
    tabela_final.to_sql('equipamentos', conexao, if_exists='replace', index=False)
    conexao.close()
    
    print("="*40)
    print("SUCESSO ABSOLUTO!")
    print(f"As {len(tabela_final)} linhas foram salvas permanentemente no banco '{nome_banco}'.")
    print("="*40 + "\n")

except Exception as e:
    # Se der erro, agora ele vai mostrar o motivo exato em detalhes
    print(f"Ocorreu um erro detalhado: {repr(e)}")