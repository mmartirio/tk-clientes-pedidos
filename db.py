# db.py
import sqlite3
from decimal import Decimal, ROUND_HALF_UP

def inicializar_banco():
    """Inicializa o banco de dados com tabelas necessárias."""
    conn = sqlite3.connect('clientes_pedidos.db')
    cursor = conn.cursor()
    
    # Tabela clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE,
            telefone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data DATE NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')
    
    # Tabela itens_pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            preco_unit REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    conn.commit()
    conn.close()


def get_connection():
    """Retorna conexão com o banco."""
    return sqlite3.connect('clientes_pedidos.db')


# === FUNÇÕES DE EXECUÇÃO E CONSULTA COM TRATAMENTO DE VALORES ===

def formatar_decimal(valor):
    """Garante que o valor seja Decimal com duas casas."""
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def executar_comando(sql, parametros=()):
    """
    Executa um comando SQL (INSERT, UPDATE, DELETE),
    convertendo automaticamente valores monetários para Decimal com 2 casas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Formata valores do tipo float antes de inserir
        parametros_formatados = tuple(
            float(formatar_decimal(p)) if isinstance(p, float) else p
            for p in parametros
        )

        cursor.execute(sql, parametros_formatados)
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def consultar(sql, parametros=()):
    """
    Executa uma consulta SQL (SELECT) e retorna os valores formatados.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, parametros)
        resultados = cursor.fetchall()
        resultados_formatados = []
        for linha in resultados:
            nova_linha = []
            for valor in linha:
                # Se for float, converte para string formatada
                if isinstance(valor, float):
                    valor = formatar_decimal(valor)
                nova_linha.append(valor)
            resultados_formatados.append(tuple(nova_linha))
        return resultados_formatados
    finally:
        conn.close()


def consultar_um(sql, parametros=()):
    """
    Executa uma consulta SQL e retorna apenas um resultado formatado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, parametros)
        linha = cursor.fetchone()
        if linha:
            linha_formatada = tuple(
                formatar_decimal(v) if isinstance(v, float) else v for v in linha
            )
            return linha_formatada
        return None
    finally:
        conn.close()


def conectar():
    """Função de compatibilidade para views antigas."""
    return get_connection()
