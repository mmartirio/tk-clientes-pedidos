from db import executar_comando, consultar, consultar_um

class Cliente:
    @staticmethod
    def listar():
        return consultar("SELECT id, nome, email, telefone FROM clientes ORDER BY id DESC")

    @staticmethod
    def obter_por_id(cliente_id):
        return consultar("SELECT id, nome, email, telefone FROM clientes WHERE id = ?", (cliente_id,))

    @staticmethod
    def criar(nome, email=None, telefone=None):
        sql = "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)"
        novo_id = executar_comando(sql, (nome, email if email else None, telefone))
        return bool(novo_id)

    @staticmethod
    def atualizar(cliente_id, nome, email=None, telefone=None):
        sql = "UPDATE clientes SET nome = ?, email = ?, telefone = ? WHERE id = ?"
        linhas = executar_comando(sql, (nome, email if email else None, telefone, cliente_id))
        return linhas > 0

    @staticmethod
    def deletar(cliente_id):
        # Impede apagar se houver pedidos vinculados
        qtd = consultar_um("SELECT COUNT(1) FROM pedidos WHERE cliente_id = ?", (cliente_id,))
        if qtd and qtd[0] and int(qtd[0]) > 0:
            return False
        sql = "DELETE FROM clientes WHERE id = ?"
        linhas = executar_comando(sql, (cliente_id,))
        return linhas > 0

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
