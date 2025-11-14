# views/dashboard_view.py
import customtkinter as ctk
from tkinter import ttk
from dashboard import Dashboard
from logs import log_operacao, log_erro

class DashboardView:
    def __init__(self, master):
        self.master = master
        self.dashboard = Dashboard()
        
        self._criar_widgets()
        self._atualizar_dashboard()
        
        log_operacao("DASHBOARD", "Interface inicializada")
    
    def _criar_widgets(self):
        """Cria os widgets do dashboard com layout responsivo."""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.master)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        self.titulo = ctk.CTkLabel(
            self.main_frame,
            text="📊 Dashboard - Visão Geral do Sistema",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.titulo.pack(pady=(10, 25))
        
        # Seção de métricas
        self._criar_secao_metricas()
        
        # Seção de dados e gráficos
        self._criar_secao_dados()
        
        # Seção de ações
        self._criar_secao_acoes()
        
        # Configurar redimensionamento responsivo
        self._configurar_responsividade()
        
        log_operacao("DASHBOARD", "Interface responsiva inicializada")

    def _configurar_responsividade(self):
        """Configura o comportamento responsivo dos elementos."""
        self.main_frame.bind("<Configure>", self._ajustar_layout)

    def _ajustar_layout(self, event=None):
        """Ajusta o layout dinamicamente baseado no tamanho da tela."""
        largura = self.main_frame.winfo_width()
        
        # Ajusta o número de cards por linha baseado na largura
        if largura < 800:
            self._reorganizar_cards_1_linha()
        else:
            self._reorganizar_cards_2_linhas()

    def _reorganizar_cards_2_linhas(self):
        """Organiza os cards em 2 linhas (layout normal)."""
        if hasattr(self, 'cards_reorganizados') and not self.cards_reorganizados:
            return
            
        # Limpa os frames temporários se existirem
        if hasattr(self, 'frame_cards_temp'):
            self.frame_cards_temp.destroy()
        
        # Restaura o layout original de 2 linhas
        for widget in self.frame_cards_linha1.winfo_children():
            widget.destroy()
        for widget in self.frame_cards_linha2.winfo_children():
            widget.destroy()
            
        # Recria os cards nas linhas originais
        if hasattr(self, 'ultimas_metricas'):
            self._criar_cards_metricas(self.ultimas_metricas, self.ultimas_metricas_logs)
        
        self.cards_reorganizados = False

    def _reorganizar_cards_1_linha(self):
        """Organiza todos os cards em 1 linha para telas menores."""
        if hasattr(self, 'cards_reorganizados') and self.cards_reorganizados:
            return
            
        # Cria um frame temporário para todos os cards
        self.frame_cards_temp = ctk.CTkFrame(self.frame_cards_center, fg_color="transparent")
        self.frame_cards_temp.pack()
        
        # Move todos os cards para o frame temporário
        cards = []
        for linha in [self.frame_cards_linha1, self.frame_cards_linha2]:
            for card in linha.winfo_children():
                cards.append(card)
        
        for card in cards:
            card.pack_forget()
            card.pack(in_=self.frame_cards_temp, side="left", padx=5, pady=5)
            
        self.cards_reorganizados = True

    def _criar_secao_metricas(self):
        """Cria a seção de métricas principais com cards centralizados."""
        # Container da seção
        frame_secao = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_secao.pack(fill="x", pady=(0, 25))

        # Título da seção
        lbl_titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="📈 Métricas Principais",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_titulo_secao.pack(anchor="center", pady=(0, 20))

        # Container principal dos cards (CENTRALIZADO)
        self.frame_cards_principal = ctk.CTkFrame(frame_secao, fg_color="transparent")
        self.frame_cards_principal.pack(fill="x")

        # Container para centralizar as linha de cards
        self.frame_cards_center = ctk.CTkFrame(self.frame_cards_principal, fg_color="transparent")
        self.frame_cards_center.pack(anchor="center")

        # Linhas de cards (CENTRALIZADAS)
        self.frame_cards_linha1 = ctk.CTkFrame(self.frame_cards_center, fg_color="transparent")
        self.frame_cards_linha1.pack(pady=(0, 15))

        self.frame_cards_linha2 = ctk.CTkFrame(self.frame_cards_center, fg_color="transparent")
        self.frame_cards_linha2.pack()

    def _criar_secao_dados(self):
        """Cria a seção de dados e gráficos com layout responsivo."""
        # Container da seção
        frame_secao = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_secao.pack(fill="both", expand=True, pady=(0, 20))

        # Título da seção
        lbl_titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="📋 Dados Detalhados",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_titulo_secao.pack(anchor="center", pady=(0, 20))

        # Container principal dos dados
        frame_dados_container = ctk.CTkFrame(frame_secao, fg_color="transparent")
        frame_dados_container.pack(fill="both", expand=True)

        # Coluna da esquerda - Evolução (60% da largura) COM MARGIN LEFT
        self.frame_evolucao = ctk.CTkFrame(frame_dados_container, corner_radius=10)
        self.frame_evolucao.pack(side="left", fill="both", expand=True, padx=(20, 10))  # Margin left de 20px

        # Coluna da direita - Dados diversos (40% da largura) COM MARGIN RIGHT
        self.frame_dados_direita = ctk.CTkFrame(frame_dados_container, fg_color="transparent")
        self.frame_dados_direita.pack(side="right", fill="both", expand=True, padx=(10, 20))  # Margin right de 20px

        # Status do sistema - COM MARGIN RIGHT
        self.frame_status = ctk.CTkFrame(self.frame_dados_direita, corner_radius=10)
        self.frame_status.pack(fill="both", expand=True, pady=(0, 8))

        # Top clientes - COM MARGIN RIGHT
        self.frame_top_clientes = ctk.CTkFrame(self.frame_dados_direita, corner_radius=10)
        self.frame_top_clientes.pack(fill="both", expand=True)

        # REMOVIDO: Container de logs

    def _criar_secao_acoes(self):
        """Cria a seção de botões de ação."""
        frame_secao = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_secao.pack(fill="x", pady=15)

        # Container dos botões (CENTRALIZADO)
        frame_botoes = ctk.CTkFrame(frame_secao, fg_color="transparent")
        frame_botoes.pack(anchor="center")

        # Botões com cores temáticas e textos maiores
        btn_atualizar = ctk.CTkButton(
            frame_botoes,
            text="🔄 Atualizar Dashboard",
            command=self._atualizar_dashboard,
            fg_color=("#3B82F6", "#1E40AF"),
            hover_color=("#2563EB", "#1E3A8A"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=180
        )
        btn_atualizar.pack(side="left", padx=8)

        btn_logs = ctk.CTkButton(
            frame_botoes,
            text="📊 Ver Logs Detalhados",
            command=self._ver_logs_detalhados,
            fg_color=("#10B981", "#047857"),
            hover_color=("#059669", "#065F46"),
            font=ctk.CTkFont(size=14),
            height=40,
            width=180
        )
        btn_logs.pack(side="left", padx=8)

    def _criar_card_moderno(self, config, parent):
        """Cria um card moderno individual com tamanho aumentado."""
        card = ctk.CTkFrame(
            parent,
            width=220,
            height=140,
            corner_radius=12,
            border_width=1,
            border_color=("gray85", "gray35")
        )
        card.pack(side="left", padx=8, pady=6)
        card.pack_propagate(False)

        # Container interno do card
        frame_conteudo = ctk.CTkFrame(card, fg_color="transparent")
        frame_conteudo.pack(fill="both", expand=True, padx=15, pady=12)

        # Linha superior (ícone e valor)
        frame_superior = ctk.CTkFrame(frame_conteudo, fg_color="transparent")
        frame_superior.pack(fill="x", pady=(0, 8))

        # Ícone maior
        ctk.CTkLabel(
            frame_superior,
            text=config["icone"],
            font=ctk.CTkFont(size=20),
            text_color=config["cor"]
        ).pack(side="left")

        # Valor maior
        ctk.CTkLabel(
            frame_superior,
            text=str(config["valor"]),
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="right")

        # Título maior
        ctk.CTkLabel(
            frame_conteudo,
            text=config["titulo"],
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 4))

        # Descrição maior
        ctk.CTkLabel(
            frame_conteudo,
            text=config["desc"],
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray40")
        ).pack(anchor="w")

    def _criar_cards_metricas(self, metricas, metricas_logs):
        """Cria os cards com as métricas principais."""
        # Salva as métricas para reorganização responsiva
        self.ultimas_metricas = metricas
        self.ultimas_metricas_logs = metricas_logs
        
        # Limpar cards existentes
        for widget in self.frame_cards_linha1.winfo_children():
            widget.destroy()
        for widget in self.frame_cards_linha2.winfo_children():
            widget.destroy()

        # Definir cores que funcionam bem em ambos os temas
        cards_linha1 = [
            {
                "titulo": "Total de Clientes", 
                "valor": metricas["total_clientes"], 
                "cor": "#3B82F6", 
                "icone": "👥", 
                "desc": "Clientes cadastrados"
            },
            {
                "titulo": "Pedidos no Mês", 
                "valor": metricas["pedidos_mes"], 
                "cor": "#10B981", 
                "icone": "📦", 
                "desc": "Pedidos este mês"
            },
            {
                "titulo": "Ticket Médio", 
                "valor": __import__('utils').formatar_moeda(metricas["ticket_medio"]), 
                "cor": "#F59E0B", 
                "icone": "💰", 
                "desc": "Valor médio por pedido"
            },
            {
                "titulo": "Vendas no Mês", 
                "valor": __import__('utils').formatar_moeda(metricas["total_vendas_mes"]), 
                "cor": "#EF4444", 
                "icone": "📊", 
                "desc": "Faturamento mensal"
            },
        ]

        cards_linha2 = [
            {
                "titulo": "Novos Clientes", 
                "valor": metricas["clientes_novos_mes"], 
                "cor": "#8B5CF6", 
                "icone": "⭐", 
                "desc": "Clientes novos (mês)"
            },
            {
                "titulo": "Taxa de Conversão", 
                "valor": f'{metricas["taxa_conversao"]}%', 
                "cor": "#06B6D4", 
                "icone": "🎯", 
                "desc": "Pedidos concluídos"
            },
            {
                "titulo": "Arquivos de Log", 
                "valor": metricas_logs["total_arquivos_log"], 
                "cor": "#6B7280", 
                "icone": "📁", 
                "desc": "Total de logs"
            },
            {
                "titulo": "Logs Hoje", 
                "valor": metricas_logs["linhas_log_hoje"], 
                "cor": "#F97316", 
                "icone": "📝", 
                "desc": "Registros hoje"
            },
        ]

        # Criar cards
        for card_config in cards_linha1:
            self._criar_card_moderno(card_config, self.frame_cards_linha1)
        for card_config in cards_linha2:
            self._criar_card_moderno(card_config, self.frame_cards_linha2)

    def _criar_tabela_evolucao(self):
        """Cria a tabela de evolução mensal com textos maiores."""
        for widget in self.frame_evolucao.winfo_children():
            widget.destroy()

        # Cabeçalho maior
        lbl_titulo = ctk.CTkLabel(
            self.frame_evolucao,
            text="📈 Evolução de Pedidos (30 dias)",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lbl_titulo.pack(anchor="w", padx=15, pady=(15, 12))

        try:
            dados_evolucao = self.dashboard.get_evolucao_pedidos(30)
            
            if not dados_evolucao:
                ctk.CTkLabel(
                    self.frame_evolucao,
                    text="Nenhum dado disponível",
                    text_color=("gray50", "gray40"),
                    font=ctk.CTkFont(size=13)
                ).pack(expand=True, pady=25)
                return

            # Criar treeview com estilo adaptável e fontes maiores
            style = ttk.Style()
            if ctk.get_appearance_mode() == "Dark":
                style.configure("Custom.Treeview",
                    background="#2b2b2b",
                    foreground="white",
                    fieldbackground="#2b2b2b",
                    borderwidth=0,
                    font=('Segoe UI', 11))
                style.configure("Custom.Treeview.Heading",
                    background="#3b3b3b",
                    foreground="white",
                    relief="flat",
                    font=('Segoe UI', 12, 'bold'))
            else:
                style.configure("Custom.Treeview",
                    background="white",
                    foreground="black",
                    fieldbackground="white",
                    borderwidth=0,
                    font=('Segoe UI', 11))
                style.configure("Custom.Treeview.Heading",
                    background="#f0f0f0",
                    foreground="black",
                    relief="flat",
                    font=('Segoe UI', 12, 'bold'))

            # Container da tabela
            container_tabela = ctk.CTkFrame(self.frame_evolucao, fg_color="transparent")
            container_tabela.pack(fill="both", expand=True, padx=12, pady=(0, 12))

            tree = ttk.Treeview(
                container_tabela,
                columns=("Data", "Pedidos"),
                show="headings",
                height=10,
                style="Custom.Treeview"
            )

            tree.heading("Data", text="📅 Data")
            tree.heading("Pedidos", text="📦 Pedidos")

            tree.column("Data", width=120, anchor='center')
            tree.column("Pedidos", width=100, anchor='center')

            for data, total in dados_evolucao:
                tree.insert("", "end", values=(data, total))

            tree.pack(fill="both", expand=True)

        except Exception as e:
            ctk.CTkLabel(
                self.frame_evolucao,
                text=f"Erro ao carregar dados",
                text_color=("#EF4444", "#FCA5A5"),
                font=ctk.CTkFont(size=12)
            ).pack(padx=15, pady=20)

    def _criar_lista_status(self):
        """Cria a lista de status do sistema com textos maiores."""
        for widget in self.frame_status.winfo_children():
            widget.destroy()

        lbl_titulo = ctk.CTkLabel(
            self.frame_status,
            text="🟢 Status do Sistema",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lbl_titulo.pack(anchor="w", padx=15, pady=(15, 12))

        try:
            dados = self.dashboard.get_pedidos_por_status()
            
            if not dados:
                ctk.CTkLabel(
                    self.frame_status,
                    text="Nenhum pedido encontrado",
                    text_color=("gray50", "gray40"),
                    font=ctk.CTkFont(size=12)
                ).pack(pady=15)
                return

            # Container da lista
            lista_container = ctk.CTkFrame(self.frame_status, fg_color="transparent")
            lista_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

            for status, quantidade in dados:
                frame_item = ctk.CTkFrame(lista_container, fg_color="transparent")
                frame_item.pack(fill="x", pady=5)

                ctk.CTkLabel(
                    frame_item,
                    text=status,
                    font=ctk.CTkFont(size=12),
                ).pack(side="left")

                ctk.CTkLabel(
                    frame_item,
                    text=str(quantidade),
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=("#10B981", "#34D399")
                ).pack(side="right")

        except Exception as e:
            ctk.CTkLabel(
                self.frame_status,
                text=f"Erro: {str(e)}",
                text_color=("#EF4444", "#FCA5A5"),
                font=ctk.CTkFont(size=11)
            ).pack(padx=15, pady=12)

    def _criar_lista_top_clientes(self):
        """Cria a lista de top clientes com textos maiores."""
        for widget in self.frame_top_clientes.winfo_children():
            widget.destroy()

        lbl_titulo = ctk.CTkLabel(
            self.frame_top_clientes,
            text="🏆 Top Clientes",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lbl_titulo.pack(anchor="w", padx=15, pady=(15, 12))

        try:
            dados = self.dashboard.get_top_clientes(5)
            
            if not dados:
                ctk.CTkLabel(
                    self.frame_top_clientes,
                    text="Nenhum cliente com pedidos",
                    text_color=("gray50", "gray40"),
                    font=ctk.CTkFont(size=12)
                ).pack(pady=15)
                return

            # Container da lista
            lista_container = ctk.CTkFrame(self.frame_top_clientes, fg_color="transparent")
            lista_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

            for i, (nome, total_pedidos, total_gasto) in enumerate(dados, 1):
                frame_cliente = ctk.CTkFrame(lista_container, fg_color="transparent")
                frame_cliente.pack(fill="x", pady=4)

                # Posição e nome com fonte maior
                ctk.CTkLabel(
                    frame_cliente,
                    text=f"{i}º {nome[:18]}{'...' if len(nome) > 18 else ''}",
                    font=ctk.CTkFont(size=12),
                ).pack(side="left")

                # Valor com fonte maior
                from utils import formatar_moeda
                ctk.CTkLabel(
                    frame_cliente,
                    text=formatar_moeda(total_gasto or 0),
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=("#10B981", "#34D399")
                ).pack(side="right")

        except Exception as e:
            ctk.CTkLabel(
                self.frame_top_clientes,
                text=f"Erro: {str(e)}",
                text_color=("#EF4444", "#FCA5A5"),
                font=ctk.CTkFont(size=11)
            ).pack(padx=15, pady=12)

    def _atualizar_dashboard(self):
        """Atualiza todos os dados do dashboard."""
        try:
            metricas = self.dashboard.get_metricas_principais()
            metricas_logs = self.dashboard.get_metricas_logs()

            self._criar_cards_metricas(metricas, metricas_logs)
            self._criar_tabela_evolucao()
            self._criar_lista_status()
            self._criar_lista_top_clientes()

            from utils import formatar_moeda
            log_operacao(
                "DASHBOARD",
                "Dados atualizados",
                f"Pedidos: {metricas['pedidos_mes']}, Vendas: {formatar_moeda(metricas['total_vendas_mes'])}",
            )
        except Exception as e:
            log_erro(f"Erro ao atualizar dashboard: {str(e)}")

    def _ver_logs_detalhados(self):
        """Abre visualização de logs detalhados."""
        from views.logs_views import LogsView
        LogsView(self.master)

    def _log_manual(self):
        """Registra um log manual de atualização."""
        log_operacao("DASHBOARD", "Atualização manual solicitada pelo usuário")
        self._atualizar_dashboard()