import sqlite3

conn = sqlite3.connect('clientes_pedidos.db')
c = conn.cursor()

# Verificar clientes
c.execute('SELECT COUNT(*), MIN(id), MAX(id) FROM clientes')
cli = c.fetchone()
print(f"Clientes: {cli[0]} registros, IDs de {cli[1]} a {cli[2]}")

# Verificar pedidos
c.execute('SELECT COUNT(*), MIN(cliente_id), MAX(cliente_id) FROM pedidos')
ped = c.fetchone()
print(f"Pedidos: {ped[0]} registros, cliente_id de {ped[1]} a {ped[2]}")

# Verificar pedidos orfaos
c.execute('SELECT COUNT(*) FROM pedidos WHERE cliente_id NOT IN (SELECT id FROM clientes)')
orf = c.fetchone()[0]
print(f"Pedidos orfaos (sem cliente): {orf}")

# Verificar alguns pedidos
c.execute('SELECT id, cliente_id FROM pedidos LIMIT 5')
print("\nPrimeiros 5 pedidos:")
for p in c.fetchall():
    print(f"  Pedido #{p[0]} -> cliente_id: {p[1]}")

# Verificar alguns clientes
c.execute('SELECT id, nome FROM clientes LIMIT 5')
print("\nPrimeiros 5 clientes:")
for cl in c.fetchall():
    print(f"  Cliente #{cl[0]} - {cl[1]}")

# Testar o JOIN
c.execute('''
    SELECT COUNT(*) 
    FROM pedidos p 
    INNER JOIN clientes c ON p.cliente_id = c.id
''')
print(f"\nResultado do JOIN: {c.fetchone()[0]} pedidos")

conn.close()
