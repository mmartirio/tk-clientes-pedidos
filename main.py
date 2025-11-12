# main.py
import customtkinter as ctk
from tkinter import messagebox
from db import inicializar_banco
from views.cliente_views import ClientesView
from views.pedidos_views import PedidosView
from views.produtos_views import ProdutosView 
from views.dashboard_view import DashboardView
from views.agente_ai_views import AgenteIAView
from views.relatorios_views import RelatorioViews
from views.logs_views import LogsView
from logs import log_operacao, log_info, log_erro


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # === Configuração inicial de aparência ===
        ctk.set_appearance_mode("dark")  # Tema padrão inicial
        ctk.set_default_color_theme("blue")  # Tema de cor principal

        self.tema_atual = "dark"  # Controla o tema atual

        self.title("Sistema de Clientes & Pedidos")
        self.geometry("1200x900")
        self.resizable(True, True)
        
        # Centralizar janela
        self._centralizar_janela()
        
        # Variáveis de controle
        self.alteracoes_nao_salvas = False
        self.agente_ia_view = None
        
        # Listas para armazenar referências dos botões
        self.botoes_principais = []
        self.botoes_secundarios = []
        
        # Configurações de tamanho responsivo
        self.largura_base = 1200
        
        # Inicializa banco de dados
        inicializar_banco()

        log_operacao("SISTEMA", "Aplicação iniciada")

        # Cria interface principal
        self._criar_widgets()

        # Protege contra fechamento acidental
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar_janela)

        # Mostra dashboard ao iniciar
        self.after(100, self.mostrar_dashboard)

    def _centralizar_janela(self):
        """Centraliza a janela na tela."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _criar_widgets(self):
        """Cria a barra de ferramentas com botões responsivos."""
        self.toolbar_frame = ctk.CTkFrame(self, height=80)
        self.toolbar_frame.pack(fill="x", side="top")
        self.toolbar_frame.pack_propagate(False)

        # Um único container centralizado para todos os botões
        self.buttons_container = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        self.buttons_container.pack(expand=True, pady=10)

        self.botoes_principais.clear()
        self.botoes_secundarios.clear()

        botoes_config = [
            ("📊 Dashboard", self.mostrar_dashboard, "dashboard"),
            ("👥 Clientes", self.abrir_clientes, "clientes"),
            ("📦 Produtos", self.abrir_produtos, "produtos"),
            ("🧾 Pedidos", self.abrir_pedidos, "pedidos"),
            ("📋 Relatórios", self.abrir_relatorios, "relatorios"),
            ("📝 Logs", self._abrir_logs, "logs"),
            ("🤖 IA", self.abrir_ia, "ia"),
            ("☀️ Tema", self._alternar_tema, "tema")
        ]

        for texto, comando, tipo in botoes_config:
            btn = ctk.CTkButton(self.buttons_container, text=texto, command=comando)
            self._configurar_botao_toolbar_ctk(btn, tipo)
            btn.pack(side="left")
            self.botoes_principais.append(btn)
            if tipo == "tema":
                self.tema_button = btn

        self.frame_principal = ctk.CTkFrame(self)
        self.frame_principal.pack(fill="both", expand=True, padx=12, pady=12)

        self.bind("<Configure>", self._on_window_resize)
        self.after(100, self._ajustar_tamanho_botoes)

    def _configurar_botao_toolbar_ctk(self, botao, tipo):
        """Configura os botões da toolbar."""
        cores = {
            "dashboard": ("#2E86AB", "#1A5276"),
            "clientes": ("#27AE60", "#229954"),
            "produtos": ("#F39C12", "#D68910"),
            "pedidos": ("#9B59B6", "#8E44AD"),
            "relatorios": ("#E74C3C", "#CB4335"),
            "logs": ("#95A5A6", "#7F8C8D"),
            "ia": ("#16A085", "#138D75"),
            "tema": ("#7D3C98", "#6C3483")
        }
        if tipo in cores:
            botao.configure(
                fg_color=cores[tipo][0],
                hover_color=cores[tipo][1],
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold")
            )

    def _on_window_resize(self, event):
        if event.widget == self:
            self._ajustar_tamanho_botoes()

    def _ajustar_tamanho_botoes(self):
        try:
            largura_atual = self.winfo_width()
            if largura_atual < 1000:
                fator_escala, espacamento, tamanho_fonte = 0.8, 2, 10
            elif largura_atual < 1400:
                fator_escala, espacamento, tamanho_fonte = 1.0, 3, 11
            elif largura_atual < 1800:
                fator_escala, espacamento, tamanho_fonte = 1.2, 5, 12
            else:
                fator_escala, espacamento, tamanho_fonte = 1.4, 8, 13

            largura_botao = int(110 * fator_escala)
            altura_botao = int(35 * fator_escala)

            for botao in self.botoes_principais:
                botao.configure(
                    width=largura_botao,
                    height=altura_botao,
                    font=ctk.CTkFont(size=tamanho_fonte, weight="bold")
                )
                botao.pack_configure(padx=espacamento)

            # Ajustar botões secundários (ex.: Tema) com largura um pouco menor
            largura_sec = max(90, int(largura_botao * 0.9))
            for botao in self.botoes_secundarios:
                botao.configure(
                    width=largura_sec,
                    height=altura_botao,
                    font=ctk.CTkFont(size=tamanho_fonte, weight="bold")
                )
                botao.pack_configure(padx=espacamento)

            self._ultima_largura = largura_atual

        except Exception:
            pass

    def _alternar_tema(self):
        """Alterna entre tema claro e escuro usando CustomTkinter."""
        if self.tema_atual == "dark":
            ctk.set_appearance_mode("light")
            self.tema_atual = "light"
            if hasattr(self, 'tema_button'):
                self.tema_button.configure(text="🌙 Tema")
        else:
            ctk.set_appearance_mode("dark")
            self.tema_atual = "dark"
            if hasattr(self, 'tema_button'):
                self.tema_button.configure(text="☀️ Tema")

        log_operacao("SISTEMA", f"Tema alterado para: {self.tema_atual.upper()}")
        # Notifica todas as views/janelas para reaplicarem o tema
        try:
            self.event_generate("<<TemaAlterado>>", when="tail")
        except Exception:
            pass

    def _verificar_alteracoes_nao_salvas(self):
        return self.alteracoes_nao_salvas

    def _marcar_alteracoes_nao_salvas(self, estado=True):
        self.alteracoes_nao_salvas = estado
        if estado:
            titulo_atual = self.title()
            if " *" not in titulo_atual:
                self.title(titulo_atual + " *")

    def _ao_fechar_janela(self):
        if self._verificar_alteracoes_nao_salvas():
            resposta = messagebox.askyesnocancel(
                "Alterações Não Salvas",
                "Existem alterações não salvas no sistema.\n\n"
                "• Sim: Salvar e sair\n"
                "• Não: Sair sem salvar\n"
                "• Cancelar: Continuar editando"
            )
            if resposta is None:
                return
            elif resposta:
                self._salvar_alteracoes_pendentes()
                self.sair()
            else:
                self.sair()
        else:
            self.sair()

    def _salvar_alteracoes_pendentes(self):
        self.alteracoes_nao_salvas = False
        titulo_atual = self.title()
        if " *" in titulo_atual:
            self.title(titulo_atual.replace(" *", ""))
        log_operacao("SISTEMA", "Alterações pendentes salvas")

    def _abrir_logs(self):
        LogsView(self)
        log_operacao("NAVEGAÇÃO", "Visualizador de logs aberto")

    def limpar_frame(self):
        for widget in self.frame_principal.winfo_children():
            widget.destroy()

    def mostrar_dashboard(self):
        log_operacao("NAVEGAÇÃO", "Dashboard acessado")
        self.limpar_frame()
        DashboardView(self.frame_principal)

    def abrir_clientes(self):
        log_operacao("NAVEGAÇÃO", "Módulo Clientes acessado")
        self.limpar_frame()
        ClientesView(self.frame_principal)

    def abrir_produtos(self):
        log_operacao("NAVEGAÇÃO", "Módulo Produtos acessado")
        self.limpar_frame()
        ProdutosView(self.frame_principal)

    def abrir_pedidos(self):
        log_operacao("NAVEGAÇÃO", "Módulo Pedidos acessado")
        self.limpar_frame()
        PedidosView(self.frame_principal)

    def abrir_relatorios(self):
        log_operacao("NAVEGAÇÃO", "Módulo Relatórios acessado")
        self.limpar_frame()
        RelatorioViews(self.frame_principal)

    def abrir_ia(self):
        try:
            # Método corrigido - passar dados vazios/nulos
            self.agente_ia_view = AgenteIAView(self, None, None)
            self.agente_ia_view.mostrar()
            log_operacao("AGENTE_IA", "Janela aberta")
        except Exception as e:
            log_erro(f"Erro ao abrir IA: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao abrir assistente de IA: {str(e)}")

    def sair(self):
        if messagebox.askyesno("Sair", "Deseja realmente sair do sistema?"):
            log_operacao("SISTEMA", "Aplicação finalizada pelo usuário")
            if self.agente_ia_view:
                try:
                    if hasattr(self.agente_ia_view, 'janela') and self.agente_ia_view.janela:
                        self.agente_ia_view.janela.destroy()
                except:
                    pass
            self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()