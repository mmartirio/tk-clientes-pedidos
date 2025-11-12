# views/agente_ai_views.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
from agente_ia import agente_ia
from logs import log_operacao, log_erro, log_ia, log_ia_erro


class AgenteIAView:
    def __init__(self, parent, dados_cliente=None, dados_pedidos=None):
        self.parent = parent
        self.dados_cliente = dados_cliente or {}
        self.dados_pedidos = dados_pedidos or []
        self.janela = None
        self.ia_conectada = False
        self.ia_funcionando = False
        self.contador_mensagens_total = 0
        
        log_operacao("AGENTE_IA_VIEW", "Inicializada")

    def mostrar(self):
        """Mostra a janela do agente IA"""
        if self.janela and self.janela.winfo_exists():
            self.janela.lift()
            self.janela.focus_force()
            return
        
        # Criar janela
        self.janela = ctk.CTkToplevel(self.parent)
        self.janela.title("🤖 Assistente IA Local")
        self.janela.geometry("1000x800")
        self.janela.resizable(True, True)
        
        # Configurações para manter a janela aberta
        self.janela.transient(self.parent)
        self.janela.grab_set()
        self.janela.focus_force()
        
        # Centralizar
        self._centralizar_janela()
        
        # Configurar grid
        self.janela.grid_columnconfigure(0, weight=1)
        self.janela.grid_rowconfigure(0, weight=1)
        
        self._criar_interface()
        self._verificar_conexao_inicial()
        
        log_operacao("AGENTE_IA_VIEW", "Janela exibida")

    def _centralizar_janela(self):
        """Centraliza a janela na tela"""
        self.janela.update_idletasks()
        width = 1000
        height = 800
        x = (self.janela.winfo_screenwidth() // 2) - (width // 2)
        y = (self.janela.winfo_screenheight() // 2) - (height // 2)
        self.janela.geometry(f'{width}x{height}+{x}+{y}')

    def _criar_interface(self):
        """Cria a interface do usuário"""
        # Frame principal
        main_frame = ctk.CTkFrame(self.janela, corner_radius=12)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)  # Área do chat tem peso 1

        # ===== STATUS E AÇÕES (MOVIDO PARA CIMA) =====
        status_actions_frame = ctk.CTkFrame(main_frame, corner_radius=10, height=100)
        status_actions_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        status_actions_frame.grid_propagate(False)
        status_actions_frame.grid_columnconfigure(1, weight=1)
        
        # Status da IA (lado esquerdo)
        status_container = ctk.CTkFrame(status_actions_frame, fg_color="transparent")
        status_container.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        # Status info
        status_info_frame = ctk.CTkFrame(status_container, fg_color="transparent")
        status_info_frame.grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(status_info_frame, text="Status:", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=2, pady=2)
        
        self.status_label = ctk.CTkLabel(status_info_frame, text="Verificando...", text_color="orange")
        self.status_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ctk.CTkLabel(status_info_frame, text="Modelo:", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, sticky="w", padx=2, pady=2)
        
        self.modelo_label = ctk.CTkLabel(status_info_frame, text="qwen2.5:0.5b")
        self.modelo_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Indicador visual de status
        self.status_indicator = ctk.CTkLabel(status_container, text="●", text_color="orange", 
                                           font=ctk.CTkFont(size=20))
        self.status_indicator.grid(row=0, column=1, padx=15, pady=2)
        
        # Botões de ação (lado direito)
        actions_container = ctk.CTkFrame(status_actions_frame, fg_color="transparent")
        actions_container.grid(row=0, column=1, sticky="e", padx=15, pady=10)
        
        ctk.CTkButton(
            actions_container, 
            text="🔄 Verificar Conexão", 
            command=self._verificar_conexao,
            width=140,
            height=35,
            corner_radius=8
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            actions_container,
            text="🔄 Tentar Novamente", 
            command=self._tentar_reconexao_manual,
            width=140,
            height=35,
            fg_color="#f39c12",
            hover_color="#e67e22",
            corner_radius=8
        ).pack(side="left", padx=3)
        
        # ===== ÁREA DE CONVERSA (ALTURA AUMENTADA) =====
        chat_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        chat_frame.grid_rowconfigure(1, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)
        
        # Cabeçalho do chat
        chat_header = ctk.CTkFrame(chat_frame, fg_color="transparent", height=40)
        chat_header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        chat_header.grid_propagate(False)
        chat_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(chat_header, text="💬 Conversa com a IA", 
                    font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Contador de mensagens
        self.contador_mensagens = ctk.CTkLabel(chat_header, text="0 mensagens", 
                                              text_color="gray", font=ctk.CTkFont(size=11))
        self.contador_mensagens.grid(row=0, column=1, sticky="e", padx=5, pady=5)
        
        # Área de texto com scroll - ALTURA AUMENTADA
        text_container = ctk.CTkFrame(chat_frame, fg_color="transparent")
        text_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        self.texto_chat = ctk.CTkTextbox(
            text_container,
            wrap="word",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            border_width=1,
            border_color="#bdc3c7"
        )
        self.texto_chat.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(text_container, command=self.texto_chat.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.texto_chat.configure(yscrollcommand=scrollbar.set)
        
        # Adicionar mensagem inicial
        self._adicionar_mensagem_chat("sistema", """
🤖 **Assistente IA Local - Qwen2.5 0.5B**

Bem-vindo! Estou aqui para ajudá-lo com análises de dados do sistema.

**📊 Funcionalidades:**
• Análise de clientes e pedidos
• Consulta ao banco de dados em tempo real
• Sugestões baseadas em dados reais
• Estatísticas do sistema

**🚀 Vamos começar! Faça uma pergunta sobre seus dados.**
        """)
        
        # ===== ÁREA DE PERGUNTAS =====
        pergunta_frame = ctk.CTkFrame(main_frame, corner_radius=10, height=100)
        pergunta_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        pergunta_frame.grid_propagate(False)
        pergunta_frame.grid_columnconfigure(0, weight=1)
        
        # Frame da caixa de perguntas com botão enviar
        input_container = ctk.CTkFrame(pergunta_frame, fg_color="transparent")
        input_container.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        input_container.grid_columnconfigure(0, weight=1)
        
        # Caixa de texto para perguntas
        self.caixa_pergunta = ctk.CTkTextbox(
            input_container,
            wrap="word",
            height=60,
            font=ctk.CTkFont(size=12),
            border_width=1,
            border_color="#3498db",
            corner_radius=8
        )
        self.caixa_pergunta.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        self.caixa_pergunta.bind("<Return>", self._on_enter_pressed)
        self.caixa_pergunta.bind("<KeyPress>", self._on_key_press)
        
        # Adicionar label de instrução acima da caixa de texto
        instrucao_label = ctk.CTkLabel(
            input_container,
            text="Digite sua pergunta e pressione Enter para enviar",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        instrucao_label.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        
        # Botão enviar REDONDO com seta
        self.btn_enviar = ctk.CTkButton(
            input_container,
            text="↑",  # Seta para cima
            command=self._fazer_pergunta,
            height=60,
            width=60,
            fg_color="#27ae60",
            hover_color="#219955",
            corner_radius=30,  # Totalmente redondo
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.btn_enviar.grid(row=0, column=1, padx=5, pady=5)
        
        # ===== RODAPÉ =====
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=40)
        footer_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        footer_frame.grid_propagate(False)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # Status de processamento
        self.status_processamento = ctk.CTkLabel(
            footer_frame, 
            text="💡 Verificando conexão...", 
            text_color="orange",
            font=ctk.CTkFont(size=11)
        )
        self.status_processamento.grid(row=0, column=0, sticky="w", padx=15, pady=5)

    def _on_key_press(self, event):
        """Controla o comportamento da tecla Enter"""
        if event.state == 0 and event.keysym == "Return":
            # Enter sem Ctrl - prevenir nova linha e enviar
            self._fazer_pergunta()
            return "break"  # Previne o comportamento padrão

    def _on_enter_pressed(self, event):
        """Handler específico para Enter"""
        self._fazer_pergunta()
        return "break"  # Previne a quebra de linha

    def _atualizar_contador_mensagens(self):
        """Atualiza o contador de mensagens"""
        self.contador_mensagens.configure(text=f"{self.contador_mensagens_total} mensagens")

    def _verificar_conexao_inicial(self):
        """Verifica conexão inicial com Ollama"""
        def verificar():
            # Primeiro teste básico de conexão
            sucesso = agente_ia.testar_conexao()
            if sucesso:
                # Se conectou, testa se realmente responde
                self.janela.after(0, self._testar_resposta_ia)
            else:
                self.janela.after(0, lambda: self._processar_resultado_conexao(False))
        
        threading.Thread(target=verificar, daemon=True).start()

    def _verificar_conexao(self):
        """Verifica conexão com Ollama"""
        self.status_processamento.configure(text="🔄 Verificando conexão...", text_color="orange")
        self.status_indicator.configure(text_color="orange")
        
        def verificar():
            sucesso = agente_ia.testar_conexao()
            if sucesso:
                # Se conectou, testa se realmente responde
                self.janela.after(0, self._testar_resposta_ia)
            else:
                self.janela.after(0, lambda: self._processar_resultado_conexao(False))
        
        threading.Thread(target=verificar, daemon=True).start()

    def _tentar_reconexao_manual(self):
        """Tenta reconexão manual quando solicitado pelo usuário"""
        self.status_processamento.configure(text="🔄 Tentando reconectar...", text_color="orange")
        self.status_indicator.configure(text_color="orange")
        self._adicionar_mensagem_chat("sistema", "Tentando reconectar com a IA...")
        
        def reconectar():
            # Primeiro testa conexão básica
            sucesso = agente_ia.testar_conexao()
            if sucesso:
                # Se conectou, testa resposta
                self.janela.after(0, self._testar_resposta_ia)
            else:
                self.janela.after(0, lambda: self._processar_resultado_conexao(False))
        
        threading.Thread(target=reconectar, daemon=True).start()

    def _processar_resultado_conexao(self, sucesso):
        """Processa resultado da verificação de conexão"""
        if not sucesso:
            self.ia_conectada = False
            self.ia_funcionando = False
            self.status_label.configure(text="❌ Sem conexão", text_color="red")
            self.status_indicator.configure(text_color="red")
            self.status_processamento.configure(text="💡 Modo básico ativo", text_color="orange")
            
            self._adicionar_mensagem_chat("sistema",
                "**💡 Modo Básico Ativo**\n\n"
                "Não foi possível conectar com a IA Ollama.\n\n"
                "**Mas não se preocupe!** Posso ajudá-lo com:\n"
                "• Análises básicas de clientes\n"
                "• Análises básicas de pedidos\n"
                "• Sugestões gerais\n"
                "• Consultas ao banco de dados\n\n"
                "*Para análises avançadas, verifique a conexão com a IA.*"
            )
        else:
            # Conexão básica OK, mas ainda precisa testar resposta
            self.ia_conectada = True
            self.status_label.configure(text="🔄 Testando resposta...", text_color="orange")
            self.status_indicator.configure(text_color="orange")

    def _testar_resposta_ia(self):
        """Testa se a IA realmente responde"""
        def testar():
            try:
                # Usa o método testar_modelo otimizado do agente_ia
                teste_ok, mensagem = agente_ia.testar_modelo()
                
                if teste_ok:
                    log_operacao("AGENTE_IA_VIEW", f"IA testada com sucesso: {mensagem}")
                    self.janela.after(0, self._mostrar_ia_funcionando)
                else:
                    log_erro(f"AGENTE_IA_VIEW: Falha no teste da IA: {mensagem}")
                    self.janela.after(0, lambda: self._mostrar_conexao_com_erro(mensagem))
                    
            except Exception as e:
                error_msg = str(e)
                log_erro(f"AGENTE_IA_VIEW: Exceção no teste da IA: {error_msg}")
                self.janela.after(0, lambda err=error_msg: self._mostrar_conexao_com_erro(err))
        
        threading.Thread(target=testar, daemon=True).start()

    def _mostrar_ia_funcionando(self):
        """Mostra que a IA está realmente funcionando"""
        self.ia_conectada = True
        self.ia_funcionando = True
        stats = agente_ia.get_estatisticas()
        
        self.status_label.configure(text="✅ Conectado", text_color="green")
        self.status_indicator.configure(text_color="green")
        self.modelo_label.configure(text=stats.get("modelo", "qwen2.5:0.5b"))
        self.status_processamento.configure(text="✅ IA conectada e pronta", text_color="green")
        
        self._adicionar_mensagem_chat("sistema", 
            "**✅ IA Ollama Conectada!**\n\n"
            f"Modelo: {stats.get('modelo', 'qwen2.5:0.5b')}\n"
            "Status: **Funcionando perfeitamente**\n\n"
            "Agora você pode fazer perguntas e usar análises avançadas com IA!"
        )

    def _mostrar_conexao_com_erro(self, erro):
        """Mostra que há conexão mas com erro"""
        self.ia_conectada = True
        self.ia_funcionando = False
        stats = agente_ia.get_estatisticas()
        
        self.status_label.configure(text="⚠️ Problema na IA", text_color="orange")
        self.status_indicator.configure(text_color="orange")
        self.status_processamento.configure(text="❌ IA não está respondendo", text_color="red")
        
        # Mensagem mais informativa
        mensagem_erro = f"**⚠️ Problema na IA**\n\n"
        mensagem_erro += f"Ollama está rodando mas a IA não está respondendo corretamente.\n\n"
        
        if erro:
            mensagem_erro += f"**Erro detectado:** {erro}\n\n"
        
        mensagem_erro += "**Possíveis causas:**\n"
        mensagem_erro += "• Modelo não carregado corretamente\n"
        mensagem_erro += "• Falta de memória\n"
        mensagem_erro += "• Problema no modelo específico\n\n"
        
        mensagem_erro += "**Soluções:**\n"
        mensagem_erro += "1. Verifique se o modelo está baixado: `ollama list`\n"
        mensagem_erro += "2. Se não estiver, baixe: `ollama pull {stats.get('modelo', 'qwen2.5:0.5b')}`\n"
        mensagem_erro += "3. Reinicie o Ollama: `ollama serve`\n"
        mensagem_erro += "4. Verifique a memória disponível\n\n"
        
        mensagem_erro += "**Enquanto isso, usando modo básico por segurança.**\n"
        
        self._adicionar_mensagem_chat("erro", mensagem_erro)

    def _adicionar_mensagem_chat(self, tipo, mensagem):
        """Adiciona mensagem formatada ao chat"""
        timestamp = time.strftime("%H:%M:%S")
        self.contador_mensagens_total += 1
        
        if tipo == "sistema":
            prefixo = "🤖 Sistema"
            tag = "sistema"
        elif tipo == "usuario":
            prefixo = "👤 Você" 
            tag = "usuario"
        elif tipo == "ia":
            prefixo = "🤖 IA"
            tag = "ia"
        elif tipo == "erro":
            prefixo = "❌ Erro"
            tag = "erro"
        elif tipo == "assistente":
            prefixo = "💡 Assistente"
            tag = "assistente"
        else:
            prefixo = "💬 Mensagem"
            tag = "padrao"
        
        # Configurar tags para cores
        self.texto_chat.tag_config("sistema", foreground="#3498db")
        self.texto_chat.tag_config("usuario", foreground="#2ecc71")
        self.texto_chat.tag_config("ia", foreground="#9b59b6")
        self.texto_chat.tag_config("erro", foreground="#e74c3c")
        self.texto_chat.tag_config("assistente", foreground="#f39c12")
        
        self.texto_chat.insert("end", f"[{timestamp}] {prefixo}:\n", tag)
        self.texto_chat.insert("end", f"{mensagem}\n")
        self.texto_chat.insert("end", "─" * 80 + "\n\n")
        
        # Rolagem automática para o final
        self.texto_chat.see("end")
        self._atualizar_contador_mensagens()

    def _fazer_pergunta(self):
        """Processa pergunta do usuário usando o novo método com contexto"""
        pergunta = self.caixa_pergunta.get("1.0", "end-1c").strip()
        if not pergunta:
            messagebox.showwarning("Aviso", "Digite uma pergunta!")
            return
        
        # Limpar caixa de pergunta
        self.caixa_pergunta.delete("1.0", "end")
        
        self._adicionar_mensagem_chat("usuario", pergunta)
        
        if self.ia_funcionando:
            self.status_processamento.configure(text="🔄 Processando com IA...", text_color="orange")
        else:
            self.status_processamento.configure(text="🔄 Processando...", text_color="orange")
        
        def processar():
            if self.ia_funcionando:
                # Usa o novo método com contexto do banco de dados
                try:
                    resposta, erro = agente_ia.enviar_pergunta_com_contexto(pergunta)
                    if erro:
                        # Se erro, usa assistente
                        resposta_assistente = self._obter_resposta_assistente(pergunta)
                        self.janela.after(0, lambda: self._exibir_resposta_assistente(resposta_assistente))
                        # Tenta reconexão automática
                        self._tentar_reconexao_automatica()
                    else:
                        self.janela.after(0, lambda: self._exibir_resposta_ia(resposta))
                except Exception as e:
                    resposta_assistente = self._obter_resposta_assistente(pergunta)
                    self.janela.after(0, lambda: self._exibir_resposta_assistente(resposta_assistente))
            else:
                # Usa modo assistente quando IA não está funcionando
                resposta = self._obter_resposta_assistente(pergunta)
                self.janela.after(0, lambda: self._exibir_resposta_assistente(resposta))
        
        threading.Thread(target=processar, daemon=True).start()

    def _tentar_reconexao_automatica(self):
        """Tenta reconexão automática se detectar problemas"""
        def reconectar():
            time.sleep(2)
            sucesso = agente_ia.testar_conexao()
            if sucesso:
                self.janela.after(0, self._testar_resposta_ia)
        
        threading.Thread(target=reconectar, daemon=True).start()

    def _obter_resposta_assistente(self, pergunta):
        """Obtém resposta do assistente - SEMPRE funciona"""
        pergunta_lower = pergunta.lower()
        
        # Análise de cliente
        if any(palavra in pergunta_lower for palavra in ['cliente', 'clientes', 'dados cliente', 'informações cliente', 'analisar cliente']):
            return self._gerar_analise_cliente_assistente()

        # Análise de pedidos
        elif any(palavra in pergunta_lower for palavra in ['pedido', 'pedidos', 'vendas', 'histórico', 'analisar pedidos']):
            return self._gerar_analise_pedidos_assistente()

        # Sugestão de produtos
        elif any(palavra in pergunta_lower for palavra in ['sugerir', 'sugestão', 'produto', 'produtos', 'recomendar']):
            return self._gerar_sugestao_produtos_assistente()

        # Estatísticas do BD
        elif any(palavra in pergunta_lower for palavra in ['estatística', 'estatisticas', 'dados', 'banco', 'bd', 'relatório']):
            return "Para ver estatísticas detalhadas do sistema, faça perguntas específicas sobre clientes, pedidos ou produtos."

        # Perguntas sobre conexão
        elif any(palavra in pergunta_lower for palavra in ['conectado', 'conexão', 'ollama', 'funcionando', 'status']):
            return self._gerar_status_conexao()

        # Perguntas gerais
        elif any(palavra in pergunta_lower for palavra in ['ola', 'olá', 'oi', 'help', 'ajuda', 'como usar']):
            return self._gerar_resposta_ajuda()

        # Resposta inteligente para perguntas conceituais sobre pedidos
        elif any(palavra in pergunta_lower for palavra in ['o que é pedido', 'significado de pedido', 'definicao de pedido']):
            return self._gerar_explicacao_pedido()

        # Resposta inteligente para perguntas conceituais gerais
        elif any(palavra in pergunta_lower for palavra in ['que é', 'o que é', 'o que sao', 'defin', 'significado', 'conceito']):
            return self._gerar_resposta_explicativa(pergunta)

        # Resposta padrão
        else:
            return self._gerar_resposta_padrao(pergunta)

    def _gerar_explicacao_pedido(self):
        """Gera explicação sobre o que é um pedido"""
        return """
**📦 O que é um Pedido?**

Um **pedido** é uma solicitação formal feita por um cliente para adquirir produtos ou serviços de uma empresa.

**Elementos de um pedido:**
• **Cliente** - Quem faz o pedido
• **Produtos/Serviços** - O que está sendo solicitado
• **Valor** - Preço total do pedido
• **Status** - Situação atual (pendente, processando, concluído, etc.)
• **Data** - Quando foi realizado

**No contexto deste sistema:**
Estou analisando os pedidos dos seus clientes para identificar:
• Padrões de compra
• Valor médio dos pedidos
• Status e andamento
• Oportunidades de melhoria

💡 *Posso ajudar analisando o histórico de pedidos dos seus clientes!*
"""

    def _gerar_resposta_explicativa(self, pergunta):
        """Gera resposta explicativa para perguntas conceituais"""
        pergunta_lower = pergunta.lower()
        
        if 'produto' in pergunta_lower:
            return """
**📦 O que é um Produto?**

Um **produto** é qualquer item ou serviço que pode ser oferecido para satisfazer necessidades ou desejos dos clientes.

**Tipos de produtos:**
• **Produtos físicos** - Itens tangíveis (eletrônicos, roupas, etc.)
• **Serviços** - Atividades intangíveis (consultoria, suporte, etc.)
• **Produtos digitais** - Software, cursos online, ebooks

💡 *Posso ajudar analisando o perfil dos seus clientes para sugerir produtos relevantes!*
"""
        elif 'cliente' in pergunta_lower:
            return """
**👤 O que é um Cliente?**

Um **cliente** é uma pessoa ou organização que compra produtos ou serviços de uma empresa.

**Tipos de clientes:**
• **Clientes ativos** - Realizam compras regularmente
• **Clientes inativos** - Não compram há algum tempo  
• **Clientes potenciais** - Interessados mas ainda não compraram

💡 *Posso analisar os dados dos seus clientes para identificar padrões e oportunidades!*
"""
        else:
            return f"""
**🤔 Sobre sua pergunta:** "{pergunta}"

No momento estou focado em ajudar com análises práticas dos seus dados:

• **Clientes** - Informações e histórico
• **Pedidos** - Análise de vendas  
• **Sugestões** - Recomendações de produtos
• **Estatísticas** - Dados do sistema

Para explicações mais detalhadas sobre conceitos, recomendo conectar a IA Ollama.

💡 *Faça perguntas específicas sobre seus dados para obter respostas mais úteis!*
"""

    def _gerar_resposta_padrao(self, pergunta):
        """Gera resposta padrão personalizada"""
        return f"""
**💭 Sobre: "{pergunta}"**

Posso ajudá-lo com:

• **Análises** de clientes e pedidos
• **Sugestões** baseadas nos dados
• **Relatórios** básicos
• **Estatísticas** do sistema

**Experimente perguntar sobre:**
- "Quantos clientes temos?"
- "Quais são os pedidos recentes?"
- "Sugerir produtos para um cliente"
- "Analisar vendas do sistema"

💡 *Estou aqui para ajudar com informações práticas sobre seus dados!*
"""

    def _gerar_analise_cliente_assistente(self):
        """Gera análise básica do cliente"""
        if not self.dados_cliente:
            return "Não há dados de cliente disponíveis para análise."
        
        cliente = self.dados_cliente
        analise = "**📊 Análise do Cliente**\n\n"
        
        # Informações básicas
        if cliente.get('nome'):
            analise += f"**Nome:** {cliente['nome']}\n"
        if cliente.get('email'):
            analise += f"**Email:** {cliente['email']}\n"
        if cliente.get('telefone'):
            analise += f"**Telefone:** {cliente['telefone']}\n"
        
        # Estatísticas
        total_pedidos = len(self.dados_pedidos)
        analise += f"\n**Total de Pedidos:** {total_pedidos}\n"
        
        if total_pedidos > 0:
            total_gasto = sum(pedido.get('valor_total', 0) for pedido in self.dados_pedidos)
            ticket_medio = total_gasto / total_pedidos
            analise += f"**Total Gasto:** R$ {total_gasto:.2f}\n"
            analise += f"**Ticket Médio:** R$ {ticket_medio:.2f}\n"
        
        if not self.ia_funcionando:
            analise += "\n💡 *Para análise mais detalhada, conecte a IA*"
        
        return analise

    def _gerar_analise_pedidos_assistente(self):
        """Gera análise básica dos pedidos"""
        if not self.dados_pedidos:
            return "Não há dados de pedidos disponíveis."
        
        analise = "**📦 Análise dos Pedidos**\n\n"
        total_pedidos = len(self.dados_pedidos)
        analise += f"**Total de Pedidos:** {total_pedidos}\n"
        
        if total_pedidos > 0:
            total_gasto = sum(pedido.get('valor_total', 0) for pedido in self.dados_pedidos)
            ticket_medio = total_gasto / total_pedidos
            
            analise += f"**Valor Total:** R$ {total_gasto:.2f}\n"
            analise += f"**Ticket Médio:** R$ {ticket_medio:.2f}\n"
            
            # Status dos pedidos
            status_count = {}
            for pedido in self.dados_pedidos:
                status = pedido.get('status', 'Desconhecido')
                status_count[status] = status_count.get(status, 0) + 1
            
            if status_count:
                analise += "\n**Status dos Pedidos:**\n"
                for status, count in status_count.items():
                    analise += f"• {status}: {count}\n"
        
        if not self.ia_funcionando:
            analise += "\n💡 *Para análise mais detalhada, conecte a IA*"
        
        return analise

    def _gerar_sugestao_produtos_assistente(self):
        """Gera sugestão básica de produtos"""
        if not self.dados_cliente:
            return "Não há dados de cliente disponíveis para sugestões."
        
        analise = "**🎯 Sugestões de Produtos**\n\n"
        
        if self.dados_pedidos:
            total_gasto = sum(pedido.get('valor_total', 0) for pedido in self.dados_pedidos)
            ticket_medio = total_gasto / len(self.dados_pedidos)
            
            if ticket_medio > 500:
                analise += "**Perfil:** Cliente Premium 💎\n"
                analise += "**Sugestões:** Produtos exclusivos, serviços premium\n"
            elif ticket_medio > 200:
                analise += "**Perfil:** Cliente Intermediário ⭐\n"
                analise += "**Sugestões:** Produtos de valor médio, pacotes promocionais\n"
            else:
                analise += "**Perfil:** Cliente Básico 👍\n"
                analise += "**Sugestões:** Produtos populares, ofertas especiais\n"
        else:
            analise += "**Perfil:** Novo Cliente 🆕\n"
            analise += "**Sugestões:** Produtos de introdução, ofertas de boas-vindas\n"
        
        if not self.ia_funcionando:
            analise += "\n💡 *Para sugestões personalizadas, conecte a IA*"
        
        return analise

    def _gerar_status_conexao(self):
        """Gera status da conexão"""
        if self.ia_funcionando:
            stats = agente_ia.get_estatisticas()
            return f"**✅ IA Funcionando**\n\nModelo: {stats.get('modelo', 'N/A')}\nStatus: Respondendo perfeitamente"
        elif self.ia_conectada:
            return "**⚠️ IA Conectada com Problemas**\n\nA IA está conectada mas não está respondendo corretamente."
        else:
            return "**💡 Modo Básico**\n\nIA não conectada. Trabalhando com análises básicas dos dados."

    def _gerar_resposta_ajuda(self):
        """Gera resposta de ajuda"""
        return """
**🤖 Assistente de Ajuda**

**Funcionalidades:**
• Análise de clientes
• Análise de pedidos  
• Sugestões de produtos
• Consulta ao banco de dados
• Estatísticas do sistema

**Comandos úteis:**
• "Analisar cliente" - Dados do cliente
• "Analisar pedidos" - Resumo de pedidos
• "Sugerir produtos" - Recomendações
• "Estatísticas" - Dados do sistema

💡 *Estou aqui para ajudar! Faça perguntas sobre seus dados.*
"""

    def _exibir_resposta_ia(self, resposta):
        """Exibe resposta da IA real"""
        self._adicionar_mensagem_chat("ia", resposta)
        self.status_processamento.configure(text="✅ Resposta da IA", text_color="green")

    def _exibir_resposta_assistente(self, resposta):
        """Exibe resposta do assistente"""
        self._adicionar_mensagem_chat("assistente", resposta)
        self.status_processamento.configure(text="💡 Resposta do assistente", text_color="green")

    def _fechar(self):
        """Fecha a janela"""
        if self.janela:
            log_operacao("AGENTE_IA_VIEW", "Janela fechada pelo usuário")
            self.janela.destroy()
            self.janela = None