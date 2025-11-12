# popular_dados.py
from db import executar_comando, consultar
from datetime import datetime, timedelta
import random

def popular_dados_exemplo():
    """Popula o banco com dados de exemplo: 120 clientes, 86 pedidos (jan/2025-hoje), 20 produtos de TI."""
    
    # 120 Clientes de exemplo (nomes e emails variados)
    nomes = [
        "João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa", "Carlos Lima",
        "Fernanda Souza", "Ricardo Alves", "Juliana Rocha", "Marcos Ferreira", "Patricia Gomes",
        "Lucas Martins", "Camila Dias", "Rafael Pinto", "Beatriz Cardoso", "Thiago Barbosa",
        "Aline Correia", "Bruno Mendes", "Carla Moreira", "Diego Castro", "Elaine Ribeiro",
        "Felipe Azevedo", "Gabriela Nunes", "Henrique Teixeira", "Isabela Monteiro", "José Campos",
        "Karina Freitas", "Leonardo Sousa", "Mariana Lima", "Nicolas Pereira", "Olivia Fernandes",
        "Paulo Rodrigues", "Queila Santos", "Rodrigo Cavalcanti", "Sara Vieira", "Tiago Nascimento",
        "Ursula Reis", "Vinicius Araujo", "Wanda Baptista", "Xavier Costa", "Yara Lopes",
        "Zélia Ramos", "André Carvalho", "Bruna Farias", "Caio Duarte", "Daniela Melo",
        "Eduardo Barros", "Fabiana Torres", "Gustavo Pires", "Helena Cruz", "Igor Moura",
        "Jéssica Campos", "Kevin Nogueira", "Larissa Almeida", "Matheus Cunha", "Natália Borges",
        "Otávio Guedes", "Priscila Sampaio", "Quintino Macedo", "Renata Fonseca", "Samuel Braga",
        "Tatiana Xavier", "Ulisses Viana", "Valéria Porto", "Wagner Matos", "Ximena Silva",
        "Yuri Andrade", "Zara Dantas", "Adriano Siqueira", "Bianca Coelho", "Cleber Ramos",
        "Débora Motta", "Evandro Pacheco", "Flávia Santana", "Giovanna Amaral", "Hugo Lacerda",
        "Ingrid Mesquita", "Jaime Gouveia", "Kátia Barreto", "Leandro Serra", "Mônica Chaves",
        "Nilton Brito", "Olga Marques", "Pablo Rezende", "Quitéria Paiva", "Renan Figueiredo",
        "Silvia Tavares", "Túlio Leal", "Úrsula Medeiros", "Valdir Miranda", "Wilma Sá",
        "Yago Menezes", "Zenaide Furtado", "Alberto Dias", "Bárbara Queiroz", "Ciro Toledo",
        "Denise Guerreiro", "Enzo Salles", "Fabíola Mattos", "Gilberto Aragão", "Heloisa Bezerra",
        "Ivo Ferraz", "Josefa Abreu", "Klaus Becker", "Lívia Rangel", "Moacir Peixoto",
        "Nina Caldas", "Orlando Bastos", "Pietra Vasconcelos", "Quirino Neto", "Roberta Salgado",
        "Sandro Prado", "Teresa Lago", "Ubirajara Fonseca", "Vitória Leite", "Wesley Costa",
        "Xuxa Rocha", "Yasmin Neves", "Zilma Farias", "Antônio Alves", "Célia Rios"
    ]
    
    dominios = ["email.com", "mail.com", "empresa.com.br", "tech.com", "corp.com.br"]
    
    clientes = []
    for i, nome in enumerate(nomes[:120], 1):
        email = nome.lower().replace(" ", ".") + f"{i}@{random.choice(dominios)}"
        telefone = f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        clientes.append((nome, email, telefone))
    
    # 20 Produtos de TI
    produtos = [
        ("Notebook Dell Inspiron 15", 3499.00, 15),
        ("Mouse Logitech MX Master 3", 449.90, 30),
        ("Teclado Mecânico Keychron K2", 599.00, 25),
        ("Monitor LG UltraWide 29''", 1299.00, 12),
        ("Headset HyperX Cloud II", 399.00, 20),
        ("Webcam Logitech C920 HD", 449.00, 18),
        ("SSD Samsung 1TB NVMe", 599.00, 40),
        ("Memória RAM Corsair 16GB DDR4", 349.00, 35),
        ("HD Externo Seagate 2TB", 449.00, 28),
        ("Roteador TP-Link AC1750", 299.00, 22),
        ("Switch Gigabit 8 Portas", 199.00, 15),
        ("Cabo HDMI 2.0 Premium 2m", 49.90, 50),
        ("Hub USB-C 7 em 1", 159.00, 30),
        ("Mousepad Gamer RGB Grande", 89.90, 40),
        ("Cadeira Gamer ThunderX3", 899.00, 10),
        ("Suporte Monitor Articulado", 179.00, 25),
        ("Webcam Ring Light USB", 129.00, 20),
        ("Filtro de Linha 8 Tomadas", 79.90, 35),
        ("Pen Drive 128GB USB 3.0", 69.90, 60),
        ("Adaptador WiFi USB Dual Band", 89.00, 45)
    ]
    
    print("🎯 Populando banco com dados de exemplo...")
    print("📊 Configuração:")
    print(f"   • 120 clientes")
    print(f"   • 20 produtos de TI")
    print(f"   • 86 pedidos (Janeiro/2025 - Novembro/2025)")
    print()
    
    # Limpar dados existentes
    print("🧹 Limpando dados existentes...")
    executar_comando("DELETE FROM itens_pedido")
    executar_comando("DELETE FROM pedidos")
    executar_comando("DELETE FROM produtos")
    executar_comando("DELETE FROM clientes")
    
    # Inserir clientes
    print("👥 Inserindo clientes...")
    for nome, email, telefone in clientes:
        executar_comando(
            "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
            (nome, email, telefone)
        )
    
    # Inserir produtos
    print("📦 Inserindo produtos...")
    for nome, preco, estoque in produtos:
        executar_comando(
            "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
            (nome, float(preco), estoque)
        )
    
    # Criar 86 pedidos distribuídos de Janeiro/2025 até hoje (12/Nov/2025)
    print("🛒 Criando pedidos...")
    data_inicio = datetime(2025, 1, 1)  # 1º de janeiro de 2025
    data_fim = datetime(2025, 11, 12)    # 12 de novembro de 2025
    dias_total = (data_fim - data_inicio).days
    
    status_opcoes = ['Concluído', 'Pendente', 'Cancelado']
    pesos_status = [0.75, 0.20, 0.05]  # 75% concluído, 20% pendente, 5% cancelado
    
    for i in range(86):
        cliente_id = random.randint(1, len(clientes))
        # Distribuir pedidos ao longo do período
        dias_aleatorio = random.randint(0, dias_total)
        data_pedido = data_inicio + timedelta(days=dias_aleatorio)
        
        status = random.choices(status_opcoes, weights=pesos_status)[0]
        
        # Gerar pedidos com valores variados
        num_itens = random.randint(1, 4)
        total_pedido = 0
        itens_pedido = []
        
        for _ in range(num_itens):
            produto_idx = random.randint(0, len(produtos) - 1)
            produto_id = produto_idx + 1
            quantidade = random.randint(1, 3)
            preco_unit = float(produtos[produto_idx][1])
            total_pedido += preco_unit * quantidade
            itens_pedido.append((produto_id, quantidade, preco_unit))
        
        # Inserir pedido
        pedido_id = executar_comando(
            "INSERT INTO pedidos (cliente_id, data, total, status) VALUES (?, ?, ?, ?)",
            (cliente_id, data_pedido.strftime('%Y-%m-%d'), float(total_pedido), status)
        )
        
        # Adicionar itens ao pedido
        for produto_id, quantidade, preco_unit in itens_pedido:
            executar_comando(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unit) VALUES (?, ?, ?, ?)",
                (pedido_id, produto_id, quantidade, float(preco_unit))
            )
    
    print()
    print("✅ Dados de exemplo inseridos com sucesso!")
    print("📊 Resumo:")
    print(f"   • {len(clientes)} clientes cadastrados")
    print(f"   • {len(produtos)} produtos de TI cadastrados") 
    print(f"   • 86 pedidos criados")
    print(f"   • Período: Janeiro/2025 - Novembro/2025")
    print(f"   • Status: ~75% Concluído, ~20% Pendente, ~5% Cancelado")

if __name__ == "__main__":
    popular_dados_exemplo()

if __name__ == "__main__":
    popular_dados_exemplo()