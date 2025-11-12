import sqlite3
import os

# Caminho do banco
DB_PATH = 'clientes_pedidos.db'

print("Resetando banco de dados...")

# Deletar o banco existente
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Banco '{DB_PATH}' removido.")

# Recriar o banco
from db import inicializar_banco
inicializar_banco()
print("Banco recriado com tabelas vazias.")

# Popular com dados
from popular_dados_exemplo import popular_dados_exemplo
popular_dados_exemplo()

print("\nBanco resetado e populado com sucesso!")
