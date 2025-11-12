"""Visualizador de logs usando customtkinter, respeitando o tema atual."""
# views/logs_views.py
import customtkinter as ctk
import tkinter as tk  # ainda utilizado para constantes, Text e messagebox
from tkinter import messagebox
import os
from datetime import datetime
from logs import log_operacao, log_erro


class LogsView:
    def __init__(self, master):
        self.master = master
        self._criar_janela()

    def _criar_janela(self):
        """Cria a janela de visualização de logs com botões padrão (minimizar, maximizar e fechar)."""
        # Respeita o tema já definido no main (não força modo/claro escuro aqui)
        self.janela = ctk.CTkToplevel(self.master)
        self.janela.title("📝 Visualizador de Logs")
        self.janela.geometry("900x700")
        self.janela.minsize(700, 500)

        # 🔹 Garante que a janela tenha barra de título completa com todos os botões
        self.janela.overrideredirect(False)  # garante título e botões padrão
        self.janela.resizable(True, True)
        self.janela.attributes('-toolwindow', False)  # garante barra completa no Windows

        # 🔹 Remove "transient" e "grab_set" (eles ocultam os botões em alguns sistemas)
        # self.janela.transient(self.master)
        # self.janela.grab_set()

        # ========== FRAME PRINCIPAL ===========
        main_frame = ctk.CTkFrame(self.janela)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        titulo = ctk.CTkLabel(
            main_frame,
            text="📝 Logs do Sistema em Tempo Real",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        titulo.pack(pady=(0, 15), anchor="w")

        # ========== FRAME DE CONTROLES ==========
        frame_controles_superior = ctk.CTkFrame(main_frame)
        frame_controles_superior.pack(fill=tk.X, pady=(0, 10))

        botoes_acao = [
            ("🔄 Atualizar", self._atualizar_logs),
            ("🗑️ Limpar Tela", self._limpar_tela),
            ("📁 Abrir Pasta", self._abrir_pasta_logs),
            ("🔍 Limpar Busca", self._limpar_busca)
        ]

        for texto, comando in botoes_acao:
            ctk.CTkButton(frame_controles_superior, text=texto, command=comando).pack(side=tk.LEFT, padx=6)

        # ========== FRAME DE BUSCA ==========
        frame_busca = ctk.CTkFrame(main_frame)
        frame_busca.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(frame_busca, text="Buscar nos Logs", font=ctk.CTkFont(weight="bold")).pack(anchor="w")

        frame_busca_linha = ctk.CTkFrame(frame_busca)
        frame_busca_linha.pack(fill=tk.X, pady=(6, 0))

        ctk.CTkLabel(frame_busca_linha, text="Texto:").pack(side=tk.LEFT, padx=(0, 5))

        self.entry_busca = ctk.CTkEntry(frame_busca_linha, width=350)
        self.entry_busca.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_busca.bind('<Return>', lambda e: self._executar_busca())

        ctk.CTkButton(frame_busca_linha, text="Buscar", command=self._executar_busca, width=120).pack(side=tk.LEFT, padx=6)
        self.label_resultados = ctk.CTkLabel(frame_busca_linha, text="Nenhuma busca")
        self.label_resultados.pack(side=tk.RIGHT, padx=(10, 0))

        # ========== ÁREA DE LOGS ==========
        frame_logs = ctk.CTkFrame(main_frame)
        frame_logs.pack(fill=tk.BOTH, expand=True)

        ctk.CTkLabel(frame_logs, text="Logs do Sistema", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 6), padx=2)

        # Container para Text + Scrollbar (usamos tk.Text para manter suporte a tags de highlight)
        logs_container = ctk.CTkFrame(frame_logs)
        logs_container.pack(fill=tk.BOTH, expand=True)
        logs_container.grid_rowconfigure(0, weight=1)
        logs_container.grid_columnconfigure(0, weight=1)

        # Cores de acordo com o tema atual
        modo = ctk.get_appearance_mode()
        if modo == "Dark":
            bg_text = "#1e1e1e"
            fg_text = "#eaeaea"
        else:
            bg_text = "#f8f9fa"
            fg_text = "#2c3e50"

        self.texto_logs = tk.Text(
            logs_container,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=bg_text,
            fg=fg_text,
            padx=10,
            pady=10,
            insertbackground=fg_text
        )
        self.texto_logs.grid(row=0, column=0, sticky="nsew")

        scroll_y = ctk.CTkScrollbar(logs_container, command=self.texto_logs.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.texto_logs.configure(yscrollcommand=scroll_y.set)

        # Tag para destaque de busca
        self.texto_logs.tag_config('highlight', background='#ffd54f', foreground='black')

        # ========== BARRA DE STATUS ==========
        frame_status = ctk.CTkFrame(main_frame)
        frame_status.pack(fill=tk.X, pady=(5, 0))

        self.status_var = tk.StringVar(value="Pronto - Use F5 para atualizar | Ctrl+F para buscar")
        ctk.CTkLabel(
            frame_status,
            textvariable=self.status_var,
            anchor="w"
        ).pack(fill=tk.X, padx=4, pady=4)

        # ========== ATALHOS DE TECLADO ==========
        self.janela.bind('<F5>', lambda e: self._atualizar_logs())
        self.janela.bind('<Control-f>', lambda e: self._focar_busca())

        # Variáveis de controle
        self.texto_busca_atual = ""

        # Carregar logs iniciais
        self._atualizar_logs()
        self._agendar_atualizacao()
        self._centralizar_janela()
        self._trazer_para_frente()

        # Evento de fechar janela
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)

        # Logar abertura do visualizador
        log_operacao("LOGS_VIEW", "Janela de logs aberta")

        # Ícone (opcional)
        try:
            self.janela.iconbitmap("icon.ico")
        except:
            pass

    # ================= MÉTODOS AUXILIARES =================

    def _centralizar_janela(self):
        self.janela.update_idletasks()
        width = self.janela.winfo_width()
        height = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (width // 2)
        y = (self.janela.winfo_screenheight() // 2) - (height // 2)
        self.janela.geometry(f"+{x}+{y}")

    def _focar_busca(self):
        self.entry_busca.focus_set()
        try:
            # CTkEntry suporta seleção via método .selection_range
            self.entry_busca.select_clear()
            self.entry_busca.selection_range(0, tk.END)
        except Exception:
            pass

    def _executar_busca(self):
        texto_busca = self.entry_busca.get().strip()
        if not texto_busca:
            self.status_var.set("Digite um texto para buscar")
            return

        self._limpar_highlights()
        ocorrencias = []
        self.texto_busca_atual = texto_busca
        content = self.texto_logs.get(1.0, tk.END)
        start_idx = "1.0"

        while True:
            start_idx = self.texto_logs.search(texto_busca, start_idx, stopindex=tk.END)
            if not start_idx:
                break
            end_idx = f"{start_idx}+{len(texto_busca)}c"
            ocorrencias.append((start_idx, end_idx))
            self.texto_logs.tag_add('highlight', start_idx, end_idx)
            start_idx = end_idx

        total = len(ocorrencias)
        if total > 0:
            self.label_resultados.config(text=f"{total} ocorrência(s)")
            self.status_var.set(f"{total} ocorrência(s) de '{texto_busca}'")
            self.texto_logs.see(ocorrencias[0][0])
            log_operacao("LOGS_VIEW", "Busca executada", detalhes=f"texto='{texto_busca}' ocorrencias={total}")
        else:
            self.label_resultados.config(text="Nenhuma ocorrência")
            self.status_var.set(f"'{texto_busca}' não encontrado")
            log_operacao("LOGS_VIEW", "Busca sem resultados", detalhes=f"texto='{texto_busca}'")

    def _limpar_busca(self):
        self._limpar_highlights()
        self.entry_busca.delete(0, tk.END)
        self.texto_busca_atual = ""
        self.label_resultados.config(text="Nenhuma busca")
        self.status_var.set("Busca limpa")
        log_operacao("LOGS_VIEW", "Busca limpa")

    def _limpar_highlights(self):
        self.texto_logs.tag_remove('highlight', '1.0', tk.END)

    def _atualizar_logs(self):
        try:
            logs_texto = self._ler_logs_atuais()
            self.texto_logs.delete(1.0, tk.END)
            self.texto_logs.insert(1.0, logs_texto)

            if self.texto_busca_atual:
                self.entry_busca.delete(0, tk.END)
                self.entry_busca.insert(0, self.texto_busca_atual)
                self._executar_busca()
            else:
                self.texto_logs.see(tk.END)

            linhas = len(logs_texto.split('\n'))
            self.status_var.set(f"Logs atualizados - {linhas} linhas")
            log_operacao("LOGS_VIEW", "Logs atualizados na interface")

        except Exception as e:
            log_erro(f"Erro ao atualizar logs: {str(e)}")
            self.texto_logs.delete(1.0, tk.END)
            self.texto_logs.insert(1.0, f"❌ Erro ao carregar logs: {str(e)}")
            self.status_var.set("Erro ao carregar logs")

    def _ler_logs_atuais(self):
        data_atual = datetime.now().strftime("%Y-%m-%d")
        log_file = f'logs/sistema_clientes_pedidos_{data_atual}.log'

        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    stats = os.stat(log_file)
                    tamanho_kb = stats.st_size / 1024
                    info = f"📄 Arquivo: {log_file} | Tamanho: {tamanho_kb:.1f} KB | Atualização: {datetime.now().strftime('%H:%M:%S')}\n"
                    info += "=" * 80 + "\n"
                    return info + conteudo
            except Exception as e:
                return f"❌ Erro ao ler arquivo de log: {str(e)}"
        else:
            return "📝 Nenhum log encontrado para hoje.\nOs logs aparecerão aqui automaticamente."

    def _limpar_tela(self):
        self.texto_logs.delete(1.0, tk.END)
        self._limpar_busca()
        self.status_var.set("Tela limpa")
        log_operacao("LOGS_VIEW", "Tela de logs limpa")

    def _abrir_pasta_logs(self):
        try:
            if os.path.exists('logs'):
                os.startfile('logs')
                self.status_var.set("Pasta de logs aberta")
            else:
                messagebox.showinfo("Info", "Pasta de logs não encontrada.")
                self.status_var.set("Pasta de logs não encontrada")
            log_operacao("LOGS_VIEW", "Pasta de logs aberta")
        except Exception as e:
            log_erro(f"Erro ao abrir pasta de logs: {str(e)}")
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {str(e)}")
            self.status_var.set(f"Erro ao abrir pasta: {str(e)}")

    def _agendar_atualizacao(self):
        try:
            if self.janela.winfo_exists():
                self._atualizar_logs()
                self.janela.after(5000, self._agendar_atualizacao)
        except tk.TclError:
            pass

    def _fechar(self):
        try:
            log_operacao("LOGS_VIEW", "Janela de logs fechada")
        finally:
            self.janela.destroy()

    def _trazer_para_frente(self):
        """Garante que a janela de logs abra na frente da principal sem ficar sempre no topo."""
        try:
            self.janela.lift()
            self.janela.focus_force()
            # Coloca no topo momentaneamente para garantir foco/ordem, depois desliga
            self.janela.attributes('-topmost', True)
            self.janela.after(200, lambda: self.janela.attributes('-topmost', False))
        except Exception:
            pass
