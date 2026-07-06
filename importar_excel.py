import pandas as pd
import sqlite3

print("🔄 Lendo a planilha limpa...")

# 1. Lê a sua nova planilha simplificada
df = pd.read_excel('OM_Producao_Dados.xlsx')

# 2. Abre (ou cria) o cofre do banco de dados
conexao = sqlite3.connect('oficina.db')

# 3. Joga os dados perfeitos lá para dentro, criando a tabela "equipamentos"
df.to_sql('equipamentos', conexao, if_exists='replace', index=False)

conexao.close()
print("✅ SUCESSO! Banco de dados 'oficina.db' recriado e pronto para a guerra!")