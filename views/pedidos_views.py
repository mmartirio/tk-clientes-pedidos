# views/pedidos_views.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from decimal import Decimal
from db import get_connection  # usa seu db.py

class PedidosView(ctk.CTkFrame):
    """Tela de gerenciamento de pedidos."""

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.itens_pedido = []
        self.clientes = []
        self.produtos = []
        self.conn = None
        self.cursor = None
        self._sincronizar_tema()
        self._conectar_banco()
        self._criar_widgets()
        self._carregar_clientes()
        self._carregar_produtos()

    # === CONFIGURAÇÃO DE TEMA ===
    def _sincronizar_tema(self):
        """Mantém o mesmo tema (claro/escuro) que o app principal estiver usando."""
        modo_atual = ctk.get_appearance_mode()
        ctk.set_appearance_mode(modo_atual)
        ctk.set_default_color_theme("blue")

    # === CONEXÃO AO BANCO ===
    def _conectar_banco(self):
        """Conecta usando o módulo db."""
        try:
            self.conn = get_connection()
            self.cursor = self.conn.cursor()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao conectar ao banco: {e}")

    # === INTERFACE ===
    def _criar_widgets(self):
        """Cria e organiza os widgets."""
        self.pack(fill="both", expand=True, padx=10, pady=10)

        frame_principal = ctk.CTkFrame(self)
        frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

        lbl_titulo = ctk.CTkLabel(frame_principal, text="Gerenciamento de Pedidos", font=("Arial", 18, "bold"))
        lbl_titulo.pack(pady=10)

        # --- ABAS ---
        self.tabview = ctk.CTkTabview(frame_principal)
        self.tabview.pack(fill="both", expand=True, pady=10)

        # Aba Cadastro
        tab_cadastro = self.tabview.add("Cadastro")
        self._criar_aba_cadastro(tab_cadastro)

        # Aba Listar
        tab_listar = self.tabview.add("Listar Pedidos")
        self._criar_aba_listar(tab_listar)

    def _criar_aba_cadastro(self, parent):
        """Cria a aba de cadastro de pedidos."""

    def _criar_aba_cadastro(self, parent):
        """Cria a aba de cadastro de pedidos."""
        # --- FORMULÁRIO ---
        form_frame = ctk.CTkFrame(parent)
        form_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(form_frame, text="Cliente:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.combo_cliente = ttk.Combobox(form_frame, width=40, state="readonly")
        self.combo_cliente.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Produto:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.combo_produto = ttk.Combobox(form_frame, width=40, state="readonly")
        self.combo_produto.grid(row=1, column=1, padx=5, pady=5)
        self.combo_produto.bind("<<ComboboxSelected>>", self._on_produto_selecionado)

        ctk.CTkLabel(form_frame, text="Quantidade:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_quantidade = ctk.CTkEntry(form_frame, width=100)
        self.entry_quantidade.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Valor Unitário:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.entry_valor = ctk.CTkEntry(form_frame, width=100)
        self.entry_valor.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        btn_adicionar = ctk.CTkButton(form_frame, text="Adicionar Item", command=self._adicionar_item_pedido)
        btn_adicionar.grid(row=4, column=1, sticky="w", padx=5, pady=10)

        # --- LISTA DE ITENS ---
        self.tree_itens = ttk.Treeview(parent, columns=("produto", "quantidade", "valor", "subtotal"), show="headings", height=8)
        self.tree_itens.heading("produto", text="Produto")
        self.tree_itens.heading("quantidade", text="Qtd")
        self.tree_itens.heading("valor", text="Valor Unitário")
        self.tree_itens.heading("subtotal", text="Subtotal")
        self.tree_itens.pack(fill="both", expand=True, pady=10)

        # --- TOTAL ---
        self.lbl_total = ctk.CTkLabel(parent, text="Total: R$ 0,00", font=("Arial", 14, "bold"))
        self.lbl_total.pack(pady=10)

        # --- BOTÕES ---
        botoes_frame = ctk.CTkFrame(parent)
        botoes_frame.pack(pady=10)

        btn_salvar = ctk.CTkButton(botoes_frame, text="Salvar Pedido", fg_color="green", hover_color="#0b7d0b", command=self._salvar_pedido)
        btn_salvar.grid(row=0, column=0, padx=5)

        btn_limpar = ctk.CTkButton(botoes_frame, text="Limpar", fg_color="gray", hover_color="#555", command=self._limpar_campos)
        btn_limpar.grid(row=0, column=1, padx=5)

    def _criar_aba_listar(self, parent):
        """Cria a aba de listagem de pedidos."""
        # --- FILTROS ---
        filtro_frame = ctk.CTkFrame(parent)
        filtro_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(filtro_frame, text="Filtrar por Cliente:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.combo_filtro_cliente = ttk.Combobox(filtro_frame, width=30, state="readonly")
        self.combo_filtro_cliente.grid(row=0, column=1, padx=5, pady=5)
        self.combo_filtro_cliente["values"] = ["Todos"]
        self.combo_filtro_cliente.set("Todos")

        ctk.CTkLabel(filtro_frame, text="Status:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.combo_filtro_status = ttk.Combobox(filtro_frame, width=15, state="readonly")
        self.combo_filtro_status.grid(row=0, column=3, padx=5, pady=5)
        self.combo_filtro_status["values"] = ["Todos", "Concluído", "Pendente", "Cancelado"]
        self.combo_filtro_status.set("Todos")

        btn_filtrar = ctk.CTkButton(filtro_frame, text="Filtrar", command=self._filtrar_pedidos)
        btn_filtrar.grid(row=0, column=4, padx=5, pady=5)

        btn_limpar_filtro = ctk.CTkButton(filtro_frame, text="Limpar Filtros", fg_color="gray", hover_color="#555", command=self._limpar_filtros)
        btn_limpar_filtro.grid(row=0, column=5, padx=5, pady=5)

        # --- LISTA DE PEDIDOS ---
        colunas = ("id", "cliente", "data", "total", "status")
        self.tree_pedidos = ttk.Treeview(parent, columns=colunas, show="headings", height=15)
        self.tree_pedidos.heading("id", text="ID")
        self.tree_pedidos.heading("cliente", text="Cliente")
        self.tree_pedidos.heading("data", text="Data")
        self.tree_pedidos.heading("total", text="Total")
        self.tree_pedidos.heading("status", text="Status")

        self.tree_pedidos.column("id", width=50, anchor="center")
        self.tree_pedidos.column("cliente", width=250)
        self.tree_pedidos.column("data", width=100, anchor="center")
        self.tree_pedidos.column("total", width=120, anchor="e")
        self.tree_pedidos.column("status", width=100, anchor="center")

        self.tree_pedidos.pack(fill="both", expand=True, pady=10, padx=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree_pedidos.yview)
        self.tree_pedidos.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Bind duplo clique para ver detalhes
        self.tree_pedidos.bind("<Double-1>", self._ver_detalhes_pedido)

        # --- BOTÕES ---
        botoes_frame = ctk.CTkFrame(parent)
        botoes_frame.pack(pady=10)

        btn_atualizar = ctk.CTkButton(botoes_frame, text="🔄 Atualizar Lista", command=self._carregar_pedidos)
        btn_atualizar.grid(row=0, column=0, padx=5)

        btn_ver_detalhes = ctk.CTkButton(botoes_frame, text="👁️ Ver Detalhes", command=lambda: self._ver_detalhes_pedido(None))
        btn_ver_detalhes.grid(row=0, column=1, padx=5)

        # Carregar pedidos ao iniciar (com delay para garantir que tudo foi criado)
        self.after(100, self._carregar_pedidos)

    # === CARREGAMENTO DE DADOS ===
    def _carregar_clientes(self):
        """Carrega os clientes do banco."""
        try:
            self.cursor.execute("SELECT id, nome FROM clientes")
            self.clientes = self.cursor.fetchall()
            if not self.clientes:
                messagebox.showinfo("Aviso", "Nenhum cliente encontrado no banco.")
            self.combo_cliente["values"] = [f"{cid} - {nome}" for cid, nome in self.clientes]
            
            # Atualizar também o combo de filtro se existir
            if hasattr(self, 'combo_filtro_cliente'):
                nomes_clientes = [nome for _, nome in self.clientes]
                self.combo_filtro_cliente["values"] = ["Todos"] + sorted(nomes_clientes)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar clientes: {e}")

    def _carregar_produtos(self):
        """Carrega os produtos do banco."""
        try:
            self.cursor.execute("SELECT id, nome, preco FROM produtos")
            self.produtos = self.cursor.fetchall()
            if not self.produtos:
                messagebox.showinfo("Aviso", "Nenhum produto cadastrado.")
            self.combo_produto["values"] = [f"{pid} - {nome}" for pid, nome, _ in self.produtos]
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar produtos: {e}")

    # === INTERAÇÕES ===
    def _on_produto_selecionado(self, event=None):
        """Preenche preço ao selecionar produto."""
        try:
            selecionado = self.combo_produto.get()
            if not selecionado:
                return

            produto_id = int(selecionado.split(" - ")[0])
            produto = next((p for p in self.produtos if p[0] == produto_id), None)
            if not produto:
                messagebox.showwarning("Aviso", "Produto não encontrado.")
                return

            preco = produto[2]
            if isinstance(preco, Decimal):
                preco = float(preco)
            else:
                preco = float(str(preco).replace(",", "."))

            self.entry_valor.delete(0, ctk.END)
            self.entry_valor.insert(0, f"{preco:.2f}")
            self.entry_quantidade.delete(0, ctk.END)
            self.entry_quantidade.insert(0, "1")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao preencher preço: {e}")

    def _adicionar_item_pedido(self):
        """Adiciona item à lista do pedido."""
        try:
            produto_texto = self.combo_produto.get().strip()
            if not produto_texto:
                messagebox.showwarning("Aviso", "Selecione um produto.")
                return

            produto_id = int(produto_texto.split(" - ")[0])
            produto_nome = produto_texto.split(" - ")[1].split(" (")[0]

            quantidade_str = self.entry_quantidade.get().strip()
            preco_str = self.entry_valor.get().strip()

            if not quantidade_str or not preco_str:
                messagebox.showwarning("Aviso", "Informe quantidade e valor.")
                return

            quantidade = int(quantidade_str)
            preco_unitario = float(preco_str.replace(",", "."))
            subtotal = quantidade * preco_unitario

            item = {
                "produto_id": produto_id,
                "produto_nome": produto_nome,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "subtotal": subtotal,
            }

            self.itens_pedido.append(item)
            self.tree_itens.insert("", "end", values=(produto_nome, quantidade, f"R$ {preco_unitario:.2f}", f"R$ {subtotal:.2f}"))
            self._atualizar_total()

        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos para quantidade ou preço.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar item: {e}")

    def _atualizar_total(self):
        """Atualiza o total do pedido."""
        total = sum(item["subtotal"] for item in self.itens_pedido)
        self.lbl_total.configure(text=f"Total: R$ {total:.2f}")

    def _salvar_pedido(self):
        """Salva o pedido e itens no banco."""
        try:
            cliente_texto = self.combo_cliente.get().strip()
            if not cliente_texto:
                messagebox.showwarning("Aviso", "Selecione um cliente.")
                return

            if not self.itens_pedido:
                messagebox.showwarning("Aviso", "Adicione pelo menos um item ao pedido.")
                return

            cliente_id = int(cliente_texto.split(" - ")[0])
            total = sum(item["subtotal"] for item in self.itens_pedido)

            self.cursor.execute(
                "INSERT INTO pedidos (cliente_id, data, total, status) VALUES (?, DATE('now'), ?, ?)", 
                (cliente_id, total, 'Pendente')
            )
            pedido_id = self.cursor.lastrowid

            for item in self.itens_pedido:
                self.cursor.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unit) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"])
                )

            self.conn.commit()
            messagebox.showinfo("Sucesso", f"Pedido #{pedido_id} salvo com sucesso!")
            self._limpar_campos()
            
            # Atualizar lista de pedidos se estiver na aba de listagem
            if hasattr(self, 'tree_pedidos'):
                self._carregar_pedidos()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar pedido: {e}")

    def _limpar_campos(self):
        """Limpa todos os campos."""
        self.combo_cliente.set("")
        self.combo_produto.set("")
        self.entry_quantidade.delete(0, ctk.END)
        self.entry_valor.delete(0, ctk.END)
        for i in self.tree_itens.get_children():
            self.tree_itens.delete(i)
        self.itens_pedido.clear()
        self.lbl_total.configure(text="Total: R$ 0,00")

    # === LISTAGEM DE PEDIDOS ===
    def _carregar_pedidos(self):
        """Carrega todos os pedidos do banco."""
        try:
            # Verificar se o widget existe
            if not hasattr(self, 'tree_pedidos'):
                print("[ERRO] tree_pedidos ainda não foi criado")
                return
            
            # Reconectar ao banco se necessário
            if self.conn is None or self.cursor is None:
                print("[DEBUG] Reconectando ao banco...")
                self._conectar_banco()
            
            print("[DEBUG] Iniciando carregamento de pedidos...")
            print(f"[DEBUG] Conexão: {self.conn}")
            print(f"[DEBUG] Cursor: {self.cursor}")
            
            # Testar conexão
            self.cursor.execute("SELECT COUNT(*) FROM pedidos")
            total_pedidos = self.cursor.fetchone()[0]
            print(f"[DEBUG] Total no banco: {total_pedidos}")
            
            # Limpar árvore
            for item in self.tree_pedidos.get_children():
                self.tree_pedidos.delete(item)

            # Buscar pedidos com nome do cliente
            query = """
                SELECT p.id, c.nome, p.data, p.total, COALESCE(p.status, 'Concluído') as status
                FROM pedidos p
                INNER JOIN clientes c ON p.cliente_id = c.id
                ORDER BY p.data DESC, p.id DESC
            """
            self.cursor.execute(query)
            pedidos = self.cursor.fetchall()

            print(f"[DEBUG] Pedidos encontrados no JOIN: {len(pedidos)}")

            # Atualizar combo de filtro de clientes
            if pedidos:
                clientes_unicos = sorted(set(p[1] for p in pedidos))
                self.combo_filtro_cliente["values"] = ["Todos"] + clientes_unicos

            # Preencher árvore
            for pedido in pedidos:
                pedido_id, cliente, data, total, status = pedido
                total_formatado = f"R$ {float(total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                self.tree_pedidos.insert("", "end", values=(pedido_id, cliente, data, total_formatado, status))
                if pedido_id <= 5:  # Mostrar apenas os 5 primeiros no log
                    print(f"[DEBUG] Pedido inserido: #{pedido_id} - {cliente}")

            print(f"[DEBUG] OK - Total de {len(pedidos)} pedido(s) carregado(s) com sucesso!")

        except Exception as e:
            print(f"[ERRO] Erro ao carregar pedidos: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao carregar pedidos: {e}")

    def _filtrar_pedidos(self):
        """Filtra pedidos por cliente e status."""
        try:
            # Reconectar ao banco se necessário
            if self.conn is None or self.cursor is None:
                self._conectar_banco()
            
            # Limpar árvore
            for item in self.tree_pedidos.get_children():
                self.tree_pedidos.delete(item)

            # Montar query com filtros
            query = """
                SELECT p.id, c.nome, p.data, p.total, COALESCE(p.status, 'Concluído') as status
                FROM pedidos p
                INNER JOIN clientes c ON p.cliente_id = c.id
                WHERE 1=1
            """
            params = []

            # Filtro cliente
            cliente_filtro = self.combo_filtro_cliente.get()
            if cliente_filtro and cliente_filtro != "Todos":
                query += " AND c.nome = ?"
                params.append(cliente_filtro)

            # Filtro status
            status_filtro = self.combo_filtro_status.get()
            if status_filtro and status_filtro != "Todos":
                query += " AND COALESCE(p.status, 'Concluído') = ?"
                params.append(status_filtro)

            query += " ORDER BY p.data DESC, p.id DESC"

            self.cursor.execute(query, params)
            pedidos = self.cursor.fetchall()

            # Preencher árvore
            for pedido in pedidos:
                pedido_id, cliente, data, total, status = pedido
                total_formatado = f"R$ {float(total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                self.tree_pedidos.insert("", "end", values=(pedido_id, cliente, data, total_formatado, status))

            print(f"[DEBUG] Filtro aplicado: {len(pedidos)} pedido(s) encontrado(s)")

        except Exception as e:
            print(f"[ERRO] Erro ao filtrar pedidos: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao filtrar pedidos: {e}")

    def _limpar_filtros(self):
        """Limpa os filtros e recarrega todos os pedidos."""
        self.combo_filtro_cliente.set("Todos")
        self.combo_filtro_status.set("Todos")
        self._carregar_pedidos()

    def _ver_detalhes_pedido(self, event=None):
        """Exibe os detalhes de um pedido selecionado."""
        try:
            selecionado = self.tree_pedidos.selection()
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um pedido para ver os detalhes.")
                return

            # Pegar ID do pedido
            item = self.tree_pedidos.item(selecionado[0])
            pedido_id = item["values"][0]

            # Buscar detalhes do pedido
            self.cursor.execute("""
                SELECT p.id, c.nome, c.email, c.telefone, p.data, p.total, COALESCE(p.status, 'Concluído') as status
                FROM pedidos p
                INNER JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = ?
            """, (pedido_id,))
            pedido = self.cursor.fetchone()

            if not pedido:
                messagebox.showerror("Erro", "Pedido não encontrado.")
                return

            # Buscar itens do pedido
            self.cursor.execute("""
                SELECT pr.nome, i.quantidade, i.preco_unit, (i.quantidade * i.preco_unit) as subtotal
                FROM itens_pedido i
                INNER JOIN produtos pr ON i.produto_id = pr.id
                WHERE i.pedido_id = ?
            """, (pedido_id,))
            itens = self.cursor.fetchall()

            # Montar mensagem com detalhes
            pid, cliente, email, telefone, data, total, status = pedido
            total_formatado = f"R$ {float(total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            detalhes = f"""
═══════════════════════════════════════
DETALHES DO PEDIDO #{pid}
═══════════════════════════════════════

📅 Data: {data}
💼 Status: {status}
💰 Total: {total_formatado}

👤 CLIENTE
   Nome: {cliente}
   Email: {email}
   Telefone: {telefone}

📦 ITENS DO PEDIDO
"""
            for i, (produto, qtd, preco_unit, subtotal) in enumerate(itens, 1):
                preco_formatado = f"R$ {float(preco_unit):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                subtotal_formatado = f"R$ {float(subtotal):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                detalhes += f"\n   {i}. {produto}"
                detalhes += f"\n      Quantidade: {qtd}"
                detalhes += f"\n      Valor Unit.: {preco_formatado}"
                detalhes += f"\n      Subtotal: {subtotal_formatado}\n"

            detalhes += "\n═══════════════════════════════════════"

            # Criar janela de detalhes
            janela_detalhes = ctk.CTkToplevel(self)
            janela_detalhes.title(f"Pedido #{pid}")
            janela_detalhes.geometry("500x600")

            # Tornar modal
            janela_detalhes.transient(self)
            janela_detalhes.grab_set()

            # Frame com scrollbar
            frame = ctk.CTkFrame(janela_detalhes)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Texto com detalhes
            texto = ctk.CTkTextbox(frame, width=460, height=520, font=("Courier New", 11))
            texto.pack(fill="both", expand=True)
            texto.insert("1.0", detalhes)
            texto.configure(state="disabled")

            # Botão fechar
            btn_fechar = ctk.CTkButton(janela_detalhes, text="Fechar", command=janela_detalhes.destroy)
            btn_fechar.pack(pady=10)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir detalhes: {e}")

