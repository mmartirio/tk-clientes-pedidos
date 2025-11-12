from db import executar_comando, consultar

class Cliente:
    @staticmethod
    def listar():
        return consultar("SELECT id, nome, email, telefone FROM clientes")

    @staticmethod
    def obter_por_id(cliente_id):
        return consultar("SELECT id, nome, email, telefone FROM clientes WHERE id = ?", (cliente_id,))

class Produto:
    @staticmethod
    def listar():
        """Retorna todos os produtos cadastrados."""
        return consultar("SELECT id, nome, preco FROM produtos")

    @staticmethod
    def adicionar(nome, preco):
        """Adiciona um novo produto."""
        sql = "INSERT INTO produtos (nome, preco) VALUES (?, ?)"
        return executar_comando(sql, (nome, preco))

class Pedido:
    @staticmethod
    def listar():
        """Lista todos os pedidos com o nome do cliente."""
        sql = """
        SELECT p.id, c.nome AS cliente, p.data, p.total, p.status
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.id
        ORDER BY p.data DESC
        """
        return consultar(sql)

    @staticmethod
    def adicionar(cliente_id, data, total, status='Pendente'):
        sql = "INSERT INTO pedidos (cliente_id, data, total, status) VALUES (?, ?, ?, ?)"
        return executar_comando(sql, (cliente_id, data, total, status))

    @staticmethod
    def obter_por_id(pedido_id):
        sql = "SELECT * FROM pedidos WHERE id = ?"
        return consultar(sql, (pedido_id,))

class ItemPedido:
    @staticmethod
    def adicionar(pedido_id, produto, quantidade, preco_unit):
        sql = """
        INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit)
        VALUES (?, ?, ?, ?)
        """
        return executar_comando(sql, (pedido_id, produto, quantidade, preco_unit))

    @staticmethod
    def listar_por_pedido(pedido_id):
        sql = "SELECT produto, quantidade, preco_unit FROM itens_pedido WHERE pedido_id = ?"
        return consultar(sql, (pedido_id,))
