import customtkinter as ctk
import tkinter as tk
from tkinter import Toplevel, Label, Entry, Button, messagebox, ttk
from models import Cliente


class ClienteForm(ctk.CTkToplevel):
    def __init__(self, master=None, cliente=None, on_save=None):
        super().__init__(master)
        self.cliente = cliente
        self.on_save = on_save
        self.title("Formulário de Cliente")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Centralizar na tela
        self.transient(master)
        self.grab_set()

        # Frame do formulário
        frame_form = ctk.CTkFrame(self)
        frame_form.pack(padx=20, pady=15, fill='both', expand=True)

        ctk.CTkLabel(frame_form, text="Nome:*", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w')
        self.entry_nome = ctk.CTkEntry(frame_form, width=300, font=ctk.CTkFont(size=12))
        self.entry_nome.pack(fill='x', pady=(0, 10))

        ctk.CTkLabel(frame_form, text="Email:", font=ctk.CTkFont(size=12)).pack(anchor='w')
        self.entry_email = ctk.CTkEntry(frame_form, width=300, font=ctk.CTkFont(size=12))
        self.entry_email.pack(fill='x', pady=(0, 10))

        ctk.CTkLabel(frame_form, text="Telefone:*", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w')
        self.entry_telefone = ctk.CTkEntry(frame_form, width=300, font=ctk.CTkFont(size=12))
        self.entry_telefone.pack(fill='x', pady=(0, 20))

        # Inserir dados se for edição
        if self.cliente:
            self.entry_nome.insert(0, self.cliente[1] if len(self.cliente) > 1 else "")
            self.entry_email.insert(0, self.cliente[2] if len(self.cliente) > 2 else "")
            self.entry_telefone.insert(0, self.cliente[3] if len(self.cliente) > 3 else "")
            self.title(f"Editando Cliente: {self.cliente[1]}")
        else:
            self.title("Novo Cliente")

        # Frame dos botões
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(pady=10)

        btn_salvar = ctk.CTkButton(
            frame_botoes, 
            text="Salvar", 
            command=self.salvar,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=100,
            height=35
        )
        btn_salvar.pack(side='left', padx=5)

        btn_cancelar = ctk.CTkButton(
            frame_botoes, 
            text="Cancelar", 
            command=self.destroy,
            fg_color="#f44336",
            hover_color="#da190b",
            font=ctk.CTkFont(size=12),
            width=100,
            height=35
        )
        btn_cancelar.pack(side='left', padx=5)

        # Focar no primeiro campo
        self.entry_nome.focus()

    def validar(self):
        """Valida os dados do formulário"""
        nome = self.entry_nome.get().strip()
        email = self.entry_email.get().strip()
        telefone = self.entry_telefone.get().strip()

        if not nome:
            messagebox.showerror("Erro", "O campo Nome é obrigatório.")
            self.entry_nome.focus()
            return None
        
        if not telefone:
            messagebox.showerror("Erro", "O campo Telefone é obrigatório.")
            self.entry_telefone.focus()
            return None
        
        # Validação básica de email
        if email and "@" not in email:
            messagebox.showerror("Erro", "Por favor, insira um email válido.")
            self.entry_email.focus()
            return None

        return {
            'nome': nome,
            'email': email,
            'telefone': telefone
        }

    def salvar(self):
        """Salva ou atualiza o cliente"""
        dados = self.validar()
        if not dados:
            return

        try:
            if self.cliente:
                # Atualizar cliente existente
                cliente_id = self.cliente[0]
                sucesso = Cliente.atualizar(
                    cliente_id, 
                    dados['nome'], 
                    dados['email'], 
                    dados['telefone']
                )
                acao = "atualizado"
            else:
                # Criar novo cliente
                sucesso = Cliente.criar(
                    dados['nome'], 
                    dados['email'], 
                    dados['telefone']
                )
                acao = "criado"

            if sucesso:
                messagebox.showinfo("Sucesso", f"Cliente {acao} com sucesso!")
                if self.on_save:
                    self.on_save()
                self.destroy()
            else:
                messagebox.showerror("Erro", f"Falha ao salvar o cliente. Verifique os dados e tente novamente.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar cliente: {str(e)}")


class ClientesView(ctk.CTkFrame):
    """Listagem de clientes com interface moderna"""
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='both', expand=True, padx=10, pady=10)
        self.create_widgets()
        self.carregar_clientes()

    def create_widgets(self):
        """Cria os widgets da interface"""
        # Frame de cabeçalho
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.pack(fill='x', pady=10)

        lbl_titulo = ctk.CTkLabel(
            frame_header, 
            text="Gerenciamento de Clientes", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_titulo.pack(anchor='w', padx=10)  # MARGIN LEFT ADICIONADO

        # Frame de busca
        frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        frame_busca.pack(fill='x', pady=10)

        lbl_busca = ctk.CTkLabel(frame_busca, text="Buscar:", font=ctk.CTkFont(size=12))
        lbl_busca.pack(side='left', padx=(10, 5))  # MARGIN LEFT ADICIONADO

        self.entry_busca = ctk.CTkEntry(frame_busca, width=200, font=ctk.CTkFont(size=12))
        self.entry_busca.pack(side='left', padx=5)
        self.entry_busca.bind('<KeyRelease>', self._on_busca_change)

        btn_pesquisar = ctk.CTkButton(
            frame_busca, 
            text="Pesquisar", 
            command=self.carregar_clientes,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=12),
            width=80
        )
        btn_pesquisar.pack(side='left', padx=5)

        btn_limpar = ctk.CTkButton(
            frame_busca, 
            text="Limpar", 
            command=self._limpar_busca,
            fg_color="#FF9800",
            hover_color="#F57C00",
            font=ctk.CTkFont(size=12),
            width=80
        )
        btn_limpar.pack(side='left', padx=5)

        # Frame de botões de ação
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill='x', pady=10)

        btn_novo = ctk.CTkButton(
            frame_botoes, 
            text="➕ Novo Cliente", 
            command=self.novo_cliente,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=120,
            height=35
        )
        btn_novo.pack(side='left', padx=(10, 5))  # MARGIN LEFT ADICIONADO

        btn_editar = ctk.CTkButton(
            frame_botoes, 
            text="✏️ Editar", 
            command=self.editar_cliente,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=12),
            width=100,
            height=35
        )
        btn_editar.pack(side='left', padx=5)

        btn_excluir = ctk.CTkButton(
            frame_botoes, 
            text="🗑️ Excluir", 
            command=self.deletar_cliente,
            fg_color="#f44336",
            hover_color="#da190b",
            font=ctk.CTkFont(size=12),
            width=100,
            height=35
        )
        btn_excluir.pack(side='left', padx=5)

        btn_atualizar = ctk.CTkButton(
            frame_botoes, 
            text="🔄 Atualizar", 
            command=self.carregar_clientes,
            fg_color="#9C27B0",
            hover_color="#7B1FA2",
            font=ctk.CTkFont(size=12),
            width=100,
            height=35
        )
        btn_atualizar.pack(side='left', padx=5)

        # Treeview de clientes
        frame_tree = ctk.CTkFrame(self)
        frame_tree.pack(fill='both', expand=True, pady=10, padx=10)  # MARGIN LEFT ADICIONADO

        # Configurar a treeview com scrollbar
        self.tree = ttk.Treeview(
            frame_tree, 
            columns=("id", "Nome", "Email", "Telefone"), 
            show="headings", 
            height=15
        )

        # Scrollbar vertical
        v_scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        # Scrollbar horizontal
        h_scrollbar = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # Empacotar treeview e scrollbars
        self.tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')

        # Configurar colunas
        colunas = [
            ("id", "ID", 50),
            ("Nome", "Nome", 200),
            ("Email", "Email", 200),
            ("Telefone", "Telefone", 150)
        ]

        for col_id, heading, width in colunas:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, minwidth=50)

        # Bind duplo clique para editar
        self.tree.bind('<Double-1>', lambda e: self.editar_cliente())

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self, 
            text="Pronto", 
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_bar.pack(fill='x', side='bottom', pady=5, padx=10)  # MARGIN LEFT ADICIONADO

    def _on_busca_change(self, event=None):
        """Atualiza a busca automaticamente enquanto digita"""
        self.carregar_clientes()

    def _limpar_busca(self):
        """Limpa o campo de busca"""
        self.entry_busca.delete(0, tk.END)
        self.carregar_clientes()

    def _get_clientes(self, filtro=None):
        """
        Método seguro para obter clientes, lidando com diferentes assinaturas do método listar
        """
        try:
            # Verifica se o método listar existe
            if not hasattr(Cliente, 'listar'):
                self.status_bar.configure(text="❌ Método 'listar' não encontrado na classe Cliente")
                return []
            
            # Tenta chamar o método listar com filtro
            if filtro:
                try:
                    return Cliente.listar(filtro)
                except TypeError:
                    # Se falhar, tenta sem filtro e filtra localmente
                    todos_clientes = Cliente.listar()
                    return [c for c in todos_clientes if filtro.lower() in str(c).lower()]
            else:
                return Cliente.listar()
                
        except Exception as e:
            self.status_bar.configure(text=f"❌ Erro ao buscar clientes: {str(e)}")
            return []

    def carregar_clientes(self):
        """Carrega os clientes na Treeview"""
        try:
            filtro = self.entry_busca.get().strip()
            
            # Atualizar status
            self.status_bar.configure(text="Carregando clientes...")
            self.update_idletasks()

            # Buscar clientes usando método seguro
            clientes = self._get_clientes(filtro)

            # Limpar treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Adicionar clientes
            for cliente in clientes:
                self.tree.insert("", "end", values=cliente)

            # Atualizar status
            total = len(clientes)
            if filtro:
                self.status_bar.configure(text=f"✅ {total} cliente(s) encontrado(s) para '{filtro}'")
            else:
                self.status_bar.configure(text=f"✅ {total} cliente(s) no total")

        except Exception as e:
            self.status_bar.configure(text=f"❌ Erro ao carregar clientes: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao carregar clientes: {str(e)}")

    def novo_cliente(self):
        """Abre o formulário para criar um novo cliente"""
        ClienteForm(self.master, on_save=self.carregar_clientes)
    
    def editar_cliente(self):
        """Abre o formulário para editar o cliente selecionado"""
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Editar Cliente", "Selecione um cliente para editar.")
            return
        
        try:
            dados = self.tree.item(selecionado[0])['values']
            if not dados:
                messagebox.showerror("Erro", "Nenhum dado do cliente encontrado.")
                return
            
            ClienteForm(self.master, cliente=dados, on_save=self.carregar_clientes)
        
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir editor: {str(e)}")

    def deletar_cliente(self):
        """Deleta o cliente selecionado"""
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Deletar Cliente", "Selecione um cliente para deletar.")
            return
        
        try:
            dados = self.tree.item(selecionado[0])['values']
            if not dados or len(dados) < 2:
                messagebox.showerror("Erro", "Dados do cliente inválidos.")
                return

            cliente_id = dados[0]
            cliente_nome = dados[1]

            confirmar = messagebox.askyesno(
                "Confirmar Exclusão", 
                f"Tem certeza que deseja excluir o cliente:\n\n\"{cliente_nome}\"?\n\nEsta ação não pode ser desfeita."
            )
            
            if confirmar:
                # Verifica se o método deletar existe
                if hasattr(Cliente, 'deletar'):
                    sucesso = Cliente.deletar(cliente_id)
                else:
                    sucesso = False
                
                if sucesso:
                    messagebox.showinfo("Sucesso", "Cliente excluído com sucesso!")
                    self.carregar_clientes()
                else:
                    messagebox.showerror("Erro", "Falha ao excluir o cliente. Verifique se não há pedidos vinculados.")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao excluir cliente: {str(e)}")