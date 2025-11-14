import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from db import consultar, executar_comando, inicializar_banco
from logs import log_operacao


class ProdutoForm(ctk.CTkToplevel):
    """Formulário para adicionar/editar produtos"""
    
    def __init__(self, master=None, produto=None, on_save=None):
        super().__init__(master)
        self.produto = produto
        self.on_save = on_save
        self.title("Formulário de Produto")
        self.geometry("550x450")
        self.resizable(False, False)
        
        # Centralizar na tela
        self.transient(master)
        self.grab_set()
        
        self._criar_widgets()
        
    def _criar_widgets(self):
        """Cria os widgets do formulário"""
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        titulo = "Editando Produto" if self.produto else "Novo Produto"
        lbl_titulo = ctk.CTkLabel(
            main_frame, 
            text=titulo, 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_titulo.pack(anchor='w', pady=(0, 20))
        
        # Formulário
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill='x', pady=10)
        
        # Nome
        ctk.CTkLabel(form_frame, text="Nome do Produto:*", 
                    font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky='w', pady=12, padx=5
        )
        self.entry_nome = ctk.CTkEntry(form_frame, font=ctk.CTkFont(size=12))
        self.entry_nome.grid(row=0, column=1, sticky='ew', padx=10, pady=12)
        
        # Preço
        ctk.CTkLabel(form_frame, text="Preço (R$):*", 
                    font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky='w', pady=12, padx=5
        )
        self.entry_preco = ctk.CTkEntry(form_frame, font=ctk.CTkFont(size=12))
        self.entry_preco.grid(row=1, column=1, sticky='w', padx=10, pady=12)
        
        # Estoque
        ctk.CTkLabel(form_frame, text="Estoque:*", 
                    font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, sticky='w', pady=12, padx=5
        )
        self.entry_estoque = ctk.CTkEntry(form_frame, font=ctk.CTkFont(size=12))
        self.entry_estoque.grid(row=2, column=1, sticky='w', padx=10, pady=12)
        
        # Dicas
        dicas_frame = ctk.CTkFrame(main_frame, border_width=1)
        dicas_frame.pack(fill='x', pady=15)

        dicas_texto = "💡 Dicas:\n• Você pode digitar com vírgula (ex: 29,90)\n• Estoque inicial pode ser zero"
        lbl_dicas = ctk.CTkLabel(
            dicas_frame, 
            text=dicas_texto,
            font=ctk.CTkFont(size=11),
            justify='left'
        )
        lbl_dicas.pack(padx=15, pady=10)
        
        # Botões
        botoes_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        botoes_frame.pack(pady=10)
        
        btn_salvar = ctk.CTkButton(
            botoes_frame,
            text="💾 Salvar Produto",
            command=self._salvar,
            fg_color="#27ae60",
            hover_color="#219a52",
            font=ctk.CTkFont(weight="bold"),
            width=140,
            height=35
        )
        btn_salvar.pack(side='left', padx=8)
        
        btn_cancelar = ctk.CTkButton(
            botoes_frame,
            text="❌ Cancelar",
            command=self.destroy,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=ctk.CTkFont(size=12),
            width=120,
            height=35
        )
        btn_cancelar.pack(side='left', padx=8)
        
        # Preencher dados se for edição
        if self.produto:
            from utils import formatar_numero_brl, parse_moeda
            self.entry_nome.insert(0, self.produto[1] if len(self.produto) > 1 else "")
            # Preenche preço: pode ter vindo como "R$ 1.234,56" da tabela
            preco_bruto = self.produto[2] if len(self.produto) > 2 else 0
            try:
                if isinstance(preco_bruto, (int, float)):
                    preco_val = float(preco_bruto)
                else:
                    preco_val = parse_moeda(preco_bruto)
            except Exception:
                preco_val = 0.0
            self.entry_preco.insert(0, formatar_numero_brl(preco_val))
            # Preenche estoque: pode ter vindo como "⚠️ 3" da tabela
            estoque_bruto = str(self.produto[3]) if len(self.produto) > 3 else "0"
            try:
                estoque_limpo = ''.join(ch for ch in str(estoque_bruto) if ch.isdigit())
                estoque_val = estoque_limpo if estoque_limpo != '' else '0'
            except Exception:
                estoque_val = '0'
            self.entry_estoque.insert(0, estoque_val)
        
        # Configurar grid
        form_frame.columnconfigure(1, weight=1)
        self.entry_nome.focus()
    
    def _validar(self):
        """Valida os dados do formulário"""
        nome = self.entry_nome.get().strip()
        preco_str = self.entry_preco.get().strip()
        estoque_str = self.entry_estoque.get().strip()
        
        # Validar nome
        if not nome:
            messagebox.showerror("Erro", "O nome do produto é obrigatório.")
            self.entry_nome.focus()
            return None
        
        if len(nome) < 2:
            messagebox.showerror("Erro", "O nome do produto deve ter pelo menos 2 caracteres.")
            self.entry_nome.focus()
            return None
        
        # Validar preço
        if not preco_str:
            messagebox.showerror("Erro", "O preço do produto é obrigatório.")
            self.entry_preco.focus()
            return None
        
        try:
            # Aceitar vírgula e símbolos via utils
            from utils import parse_moeda
            preco = parse_moeda(preco_str)
            if preco <= 0:
                messagebox.showerror("Erro", "O preço deve ser maior que zero.")
                self.entry_preco.focus()
                return None
        except ValueError:
            messagebox.showerror("Erro", "Preço inválido. Use números com vírgula para decimais.\nEx: 29,90")
            self.entry_preco.focus()
            return None
        
        # Validar estoque
        if not estoque_str:
            estoque = 0
        else:
            try:
                estoque = int(estoque_str)
                if estoque < 0:
                    messagebox.showerror("Erro", "O estoque não pode ser negativo.")
                    self.entry_estoque.focus()
                    return None
            except ValueError:
                messagebox.showerror("Erro", "Estoque inválido. Use números inteiros.")
                self.entry_estoque.focus()
                return None
        
        return {
            'nome': nome,
            'preco': preco,
            'estoque': estoque
        }
    
    def _salvar(self):
        """Salva o produto no banco de dados"""
        dados = self._validar()
        if not dados:
            return
        
        try:
            if self.produto:
                # Atualizar produto existente
                produto_id = self.produto[0]
                sucesso = self._atualizar_produto(produto_id, dados)
                acao = "atualizado"
                log_msg = f"Produto '{dados['nome']}' (ID: {produto_id}) atualizado"
            else:
                # Criar novo produto
                sucesso = self._criar_produto(dados)
                acao = "cadastrado"
                log_msg = f"Produto '{dados['nome']}' cadastrado com sucesso"
            
            if sucesso:
                messagebox.showinfo("Sucesso", f"Produto {acao} com sucesso!")
                log_operacao("PRODUTOS", log_msg)
                if self.on_save:
                    self.on_save()
                self.destroy()
            else:
                messagebox.showerror("Erro", "Erro ao salvar produto no banco de dados.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
    
    def _criar_produto(self, dados):
        """Cria um novo produto no banco"""
        try:
            executar_comando(
                "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
                (dados['nome'], dados['preco'], dados['estoque'])
            )
            return True
        except Exception as e:
            print(f"Erro ao criar produto: {e}")
            return False
    
    def _atualizar_produto(self, produto_id, dados):
        """Atualiza um produto existente"""
        try:
            executar_comando(
                "UPDATE produtos SET nome = ?, preco = ?, estoque = ? WHERE id = ?",
                (dados['nome'], dados['preco'], dados['estoque'], produto_id)
            )
            return True
        except Exception as e:
            print(f"Erro ao atualizar produto: {e}")
            return False


class ProdutosView(ctk.CTkFrame):
    """Tela de cadastro e listagem de produtos com interface moderna."""

    def __init__(self, master):
        super().__init__(master)
        # Inicializar banco de dados
        inicializar_banco()
        
        self.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        self._criar_widgets()
        self._carregar_produtos()

    def _criar_widgets(self):
        """Cria os componentes visuais da tela de produtos."""
        # Frame de cabeçalho
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill=ctk.X, pady=15)
        
        titulo = ctk.CTkLabel(
            header_frame, 
            text="📦 Gerenciamento de Produtos", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        titulo.pack(anchor='w', padx=20)

        # Frame de busca e filtros
        busca_frame = ctk.CTkFrame(self, fg_color="transparent")
        busca_frame.pack(fill=ctk.X, pady=15)
        
        ctk.CTkLabel(busca_frame, text="🔍 Buscar:", 
                    font=ctk.CTkFont(size=12)).pack(side=ctk.LEFT, padx=(20, 5))
        
        self.busca_entry = ctk.CTkEntry(busca_frame, font=ctk.CTkFont(size=12), width=300)
        self.busca_entry.pack(side=ctk.LEFT, padx=5)
        self.busca_entry.bind('<KeyRelease>', self._on_busca_change)
        
        ctk.CTkButton(
            busca_frame,
            text="Limpar",
            command=self._limpar_busca,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            font=ctk.CTkFont(size=11),
            width=80
        ).pack(side=ctk.LEFT, padx=5)
        
        # Frame de botões de ação PRINCIPAIS
        botoes_principais_frame = ctk.CTkFrame(self, border_width=1)
        botoes_principais_frame.pack(fill=ctk.X, padx=20, pady=8)
        
        # Título do grupo de botões principais
        lbl_titulo_botoes = ctk.CTkLabel(
            botoes_principais_frame,
            text="Ações Principais:",
            font=ctk.CTkFont(weight="bold")
        )
        lbl_titulo_botoes.pack(anchor='w', padx=15, pady=(10, 8))
        
        # Container para os botões principais
        botoes_container = ctk.CTkFrame(botoes_principais_frame, fg_color="transparent")
        botoes_container.pack(fill=ctk.X, padx=10, pady=5)
        
        # Botões principais com design aprimorado
        botoes_principais = [
            ("➕ Adicionar Produto", "#27ae60", self._novo_produto, "Adicionar novo produto ao sistema"),
            ("💾 Salvar Pedido", "#2980b9", self._salvar_pedido, "Salvar pedido atual"),
            ("🗑️ Limpar", "#e67e22", self._limpar_selecao, "Limpar seleções e campos")
        ]
        
        for texto, cor, comando, tooltip in botoes_principais:
            btn = ctk.CTkButton(
                botoes_container,
                text=texto,
                command=comando,
                fg_color=cor,
                hover_color=self._escurecer_cor(cor),
                font=ctk.CTkFont(weight="bold"),
                width=140,
                height=35
            )
            btn.pack(side=ctk.LEFT, padx=8)
            
            # Tooltip simples
            self._criar_tooltip(btn, tooltip)
        
        # Frame para botões secundários
        botoes_secundarios_frame = ctk.CTkFrame(self, fg_color="transparent")
        botoes_secundarios_frame.pack(fill=ctk.X, padx=20, pady=8)
        
        acoes_secundarias = [
            ("✏️ Editar", "#3498db", self._editar_produto),
            ("🗑️ Excluir", "#e74c3c", self._excluir_produto),
            ("🔄 Atualizar", "#9b59b6", self._carregar_produtos),
            ("📊 Estoque", "#f39c12", self._verificar_estoque)
        ]
        
        for texto, cor, comando in acoes_secundarias:
            btn = ctk.CTkButton(
                botoes_secundarios_frame,
                text=texto,
                command=comando,
                fg_color=cor,
                hover_color=self._escurecer_cor(cor),
                font=ctk.CTkFont(size=11),
                width=100,
                height=30
            )
            btn.pack(side=ctk.LEFT, padx=3)

        # Frame da tabela (com scrollbar interna)
        tabela_frame = ctk.CTkFrame(self)
        tabela_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        tabela_container = ctk.CTkFrame(tabela_frame, fg_color="transparent")
        tabela_container.pack(fill=ctk.BOTH, expand=True)

        colunas = ("id", "nome", "preco", "estoque")
        self.tabela = ttk.Treeview(
            tabela_container, 
            columns=colunas, 
            show="headings",
            height=15,
            selectmode='browse'
        )

        # Configurar colunas
        config_colunas = [
            ("id", "ID", 60),
            ("nome", "Nome do Produto", 300),
            ("preco", "Preço (R$)", 150),
            ("estoque", "Estoque", 100)
        ]

        for col, heading, width in config_colunas:
            # Adiciona comando de ordenação por coluna
            self.tabela.heading(col, text=heading, command=lambda c=col: self._ordenar_por_coluna(c))
            self.tabela.column(col, width=width, anchor="center")

        # Scrollbars dentro do contêiner
        v_scrollbar = ttk.Scrollbar(tabela_container, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=v_scrollbar.set)
        h_scrollbar = ttk.Scrollbar(tabela_container, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(xscrollcommand=h_scrollbar.set)

        # Layout com grid para manter a barra dentro
        tabela_container.grid_columnconfigure(0, weight=1)
        tabela_container.grid_rowconfigure(0, weight=1)
        self.tabela.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, rowspan=2, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Bind duplo clique: só edita se for em célula (não no cabeçalho)
        self.tabela.bind('<Double-1>', self._on_tabela_double_click)

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self, 
            text="Pronto para usar", 
            font=ctk.CTkFont(size=10)
        )
        self.status_bar.pack(fill=ctk.X, side=ctk.BOTTOM, pady=5)

        # Estado de ordenação por coluna
        self._sort_state = {}

    def _on_tabela_double_click(self, event):
        """Abre editor apenas se duplo clique ocorrer em célula de linha."""
        try:
            region = self.tabela.identify('region', event.x, event.y)
            if region != 'cell':
                return
            row_id = self.tabela.identify_row(event.y)
            if row_id:
                self.tabela.selection_set(row_id)
                self._editar_produto()
        except Exception:
            pass

    def _ordenar_por_coluna(self, col_id):
        """Ordena a tabela pela coluna clicada, alternando ASC/DESC."""
        try:
            dados = []
            for iid in self.tabela.get_children(''):
                val = self.tabela.set(iid, col_id)
                chave = val
                if col_id == 'id':
                    try:
                        chave = int(str(val))
                    except Exception:
                        chave = str(val)
                elif col_id == 'estoque':
                    # Pode vir com alerta "⚠️ X"
                    try:
                        numeros = ''.join(ch for ch in str(val) if ch.isdigit())
                        chave = int(numeros) if numeros else 0
                    except Exception:
                        chave = 0
                elif col_id == 'preco':
                    # Converter "R$ 1.234,56" -> 1234.56
                    try:
                        s = str(val).replace('R$','').strip()
                        s = s.replace('.', '').replace(',', '.')
                        chave = float(s)
                    except Exception:
                        chave = 0.0
                else:
                    chave = str(val).lower() if val is not None else ''
                dados.append((chave, iid))

            descending = not self._sort_state.get(col_id, False)
            dados.sort(reverse=descending)

            for index, (_, iid) in enumerate(dados):
                self.tabela.move(iid, '', index)

            self._sort_state[col_id] = descending
            ordem = 'DESC' if descending else 'ASC'
            self.status_bar.configure(text=f"Lista ordenada por '{col_id}' ({ordem})")
        except Exception as e:
            self.status_bar.configure(text=f"❌ Erro ao ordenar: {str(e)}")

    def _formatar_preco_brl(self, valor):
        """Formata o preço para o formato BRL usando utils.formatar_moeda."""
        try:
            from utils import formatar_moeda
            return formatar_moeda(valor)
        except Exception:
            return "R$ 0,00"

    def _escurecer_cor(self, cor):
        """Retorna uma versão mais escura da cor para hover effect"""
        if cor.startswith('#'):
            rgb = tuple(int(cor[i:i+2], 16) for i in (1, 3, 5))
            darker = tuple(max(0, c - 20) for c in rgb)
            return f'#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}'
        return cor

    def _criar_tooltip(self, widget, text):
        """Cria um tooltip simples para o widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _salvar_pedido(self):
        """Salva o pedido atual (função placeholder)"""
        selecionado = self.tabela.selection()
        if selecionado:
            dados = self.tabela.item(selecionado[0])['values']
            messagebox.showinfo("Salvar Pedido", 
                              f"Pedido salvo para o produto:\n{dados[1]}\nPreço: {dados[2]}")
        else:
            messagebox.showwarning("Aviso", "Selecione um produto para salvar o pedido.")

    def _limpar_selecao(self):
        """Limpa seleções e campos"""
        self.tabela.selection_remove(self.tabela.selection())
        self.busca_entry.delete(0, tk.END)
        self._carregar_produtos()
        self.status_bar.configure(text="Seleções e campos limpos")

    def _on_busca_change(self, event=None):
        """Filtra produtos enquanto digita"""
        self._carregar_produtos()

    def _limpar_busca(self):
        """Limpa o campo de busca"""
        self.busca_entry.delete(0, tk.END)
        self._carregar_produtos()

    def _novo_produto(self):
        """Abre formulário para novo produto"""
        form = ProdutoForm(self.master, on_save=self._carregar_produtos)
        form.wait_window()

    def _editar_produto(self):
        """Abre formulário para editar produto selecionado"""
        selecionado = self.tabela.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um produto para editar.")
            return
        
        try:
            dados = self.tabela.item(selecionado[0])['values']
            if not dados:
                messagebox.showerror("Erro", "Nenhum dado do produto encontrado.")
                return
            
            form = ProdutoForm(self.master, produto=dados, on_save=self._carregar_produtos)
            form.wait_window()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir editor: {str(e)}")

    def _excluir_produto(self):
        """Remove produto selecionado."""
        selecionado = self.tabela.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um produto para excluir.")
            return

        try:
            dados = self.tabela.item(selecionado[0])['values']
            if not dados:
                messagebox.showerror("Erro", "Nenhum dado do produto encontrado.")
                return

            produto_id = dados[0]
            produto_nome = dados[1]

            confirmar = messagebox.askyesno(
                "Confirmar Exclusão", 
                f"Tem certeza que deseja excluir o produto?\n\n"
                f"📦 {produto_nome}\n"
                f"💰 {dados[2]}\n"
                f"📊 Estoque: {dados[3]}\n\n"
                f"Esta ação não pode ser desfeita!"
            )
            
            if confirmar:
                executar_comando("DELETE FROM produtos WHERE id = ?", (produto_id,))
                log_operacao("PRODUTOS", f"Produto '{produto_nome}' (ID: {produto_id}) excluído.")
                messagebox.showinfo("Sucesso", "Produto excluído com sucesso!")
                self._carregar_produtos()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao excluir produto: {str(e)}")

    def _verificar_estoque(self):
        """Mostra alertas de estoque baixo"""
        try:
            produtos_estoque_baixo = consultar(
                "SELECT nome, estoque FROM produtos WHERE estoque <= 5 ORDER BY estoque ASC"
            )
            
            if produtos_estoque_baixo:
                mensagem = "📊 Produtos com estoque baixo:\n\n"
                for produto in produtos_estoque_baixo:
                    mensagem += f"• {produto[0]}: {produto[1]} unidades\n"
                mensagem += f"\nTotal: {len(produtos_estoque_baixo)} produto(s) necessitando de reposição"
                messagebox.showwarning("Alerta de Estoque", mensagem)
            else:
                messagebox.showinfo("Estoque", "✅ Todos os produtos possuem estoque adequado!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao verificar estoque: {str(e)}")

    def _carregar_produtos(self):
        """Carrega os produtos do banco e exibe na tabela."""
        try:
            # Atualizar status
            self.status_bar.configure(text="Carregando produtos...")
            self.update_idletasks()

            # Obter filtro de busca
            filtro = self.busca_entry.get().strip()
            
            if filtro:
                query = """
                    SELECT id, nome, preco, estoque 
                    FROM produtos 
                    WHERE nome LIKE ? OR id = ?
                    ORDER BY nome ASC
                """
                like_filtro = f'%{filtro}%'
                produtos = consultar(query, (like_filtro, filtro))
            else:
                produtos = consultar("SELECT id, nome, preco, estoque FROM produtos ORDER BY nome ASC")

            # Limpar tabela
            for item in self.tabela.get_children():
                self.tabela.delete(item)

            # Adicionar produtos formatados
            for prod in produtos:
                # Formatar preço para BRL (R$ com vírgula)
                preco_formatado = self._formatar_preco_brl(prod[2])
                estoque = prod[3] if prod[3] is not None else 0
                
                item_id = self.tabela.insert("", "end", values=(
                    prod[0],      # ID
                    prod[1],      # Nome
                    preco_formatado,  # Preço formatado BRL
                    estoque       # Estoque
                ))
                
                # Destacar estoque baixo
                if estoque <= 5:
                    self.tabela.set(item_id, "estoque", f"⚠️ {estoque}")

            # Atualizar status
            total = len(produtos)
            if filtro:
                self.status_bar.configure(text=f"✅ {total} produto(s) encontrado(s) para '{filtro}'")
            else:
                self.status_bar.configure(text=f"✅ {total} produto(s) carregado(s)")

        except Exception as e:
            self.status_bar.configure(text=f"❌ Erro ao carregar produtos: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao carregar produtos: {str(e)}")


# Código para testar a interface
if __name__ == "__main__":
    app = ctk.CTk()
    app.title("Sistema de Produtos")
    app.geometry("900x600")
    
    # Criar a view de produtos
    produtos_view = ProdutosView(app)
    
    app.mainloop()