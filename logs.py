# logs.py
import logging
import os
from datetime import datetime
from typing import Any, Callable, Optional

# Imports opcionais de UI para instrumentação automática (não obrigatórios)
try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None

try:  # customtkinter é opcional
    import customtkinter as ctk
except Exception:  # pragma: no cover
    ctk = None

class SafeStreamHandler(logging.StreamHandler):
    """StreamHandler que ignora erros de flush (OSError errno 22)."""
    def flush(self):
        try:
            super().flush()
        except (OSError, ValueError):
            # Ignora erros de flush em streams inválidos
            pass

class SistemaLogs:
    def __init__(self, nome_aplicacao="sistema_clientes_pedidos"):
        self.nome_aplicacao = nome_aplicacao
        self.logger = None
        self._configurar_logs()
    
    def _configurar_logs(self):
        """Configura o sistema de logs."""
        # Cria pasta de logs se não existir
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Nome do arquivo com data
        data_atual = datetime.now().strftime("%Y-%m-%d")
        log_file = f'logs/{self.nome_aplicacao}_{data_atual}.log'
        
        # Configuração do logger
        logger = logging.getLogger(self.nome_aplicacao)
        logger.setLevel(logging.INFO)
        
        # Evita duplicação de handlers
        if logger.handlers:
            logger.handlers.clear()
        
        # Formatação
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para arquivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Handler para console (com tratamento de erro de flush)
        console_handler = SafeStreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Adiciona handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.logger = logger
    
    def log_info(self, mensagem):
        """Registra log de informação."""
        if self.logger:
            self.logger.info(mensagem)
    
    def log_erro(self, mensagem):
        """Registra log de erro."""
        if self.logger:
            self.logger.error(mensagem)
    
    def log_warning(self, mensagem):
        """Registra log de aviso."""
        if self.logger:
            self.logger.warning(mensagem)
    
    def log_acesso(self, usuario, acao):
        """Registra log de acesso específico."""
        mensagem = f"USUÁRIO: {usuario} - AÇÃO: {acao}"
        self.log_info(mensagem)
    
    def log_operacao(self, modulo, operacao, detalhes=""):
        """Registra log de operação do sistema."""
        mensagem = f"OPERACAO: {modulo} - {operacao}"
        if detalhes:
            mensagem += f" - DETALHES: {detalhes}"
        self.log_info(mensagem)
    
    def log_ia(self, acao, detalhes="", modelo=""):
        """Registra log específico para operações de IA."""
        mensagem = f"AGENTE_IA: {acao}"
        if modelo:
            mensagem += f" - MODELO: {modelo}"
        if detalhes:
            mensagem += f" - DETALHES: {detalhes}"
        self.log_info(mensagem)
    
    def log_ia_erro(self, acao, erro, modelo=""):
        """Registra log de erro específico para IA."""
        mensagem = f"AGENTE_IA_ERRO: {acao} - ERRO: {erro}"
        if modelo:
            mensagem += f" - MODELO: {modelo}"
        self.log_erro(mensagem)
    
    def log_ia_pergunta(self, pergunta, tokens_utilizados=0, tempo_resposta=0, modelo=""):
        """Registra log de perguntas processadas pela IA."""
        mensagem = f"AGENTE_IA_PERGUNTA: {pergunta[:100]}..."
        if tokens_utilizados:
            mensagem += f" - TOKENS: {tokens_utilizados}"
        if tempo_resposta:
            mensagem += f" - TEMPO: {tempo_resposta:.2f}s"
        if modelo:
            mensagem += f" - MODELO: {modelo}"
        self.log_info(mensagem)
    
    def log_ia_resposta(self, pergunta, resposta, tokens_utilizados=0, tempo_resposta=0, modelo=""):
        """Registra log de respostas da IA."""
        mensagem = f"AGENTE_IA_RESPOSTA: Pergunta: {pergunta[:50]}... | Resposta: {resposta[:100]}..."
        if tokens_utilizados:
            mensagem += f" - TOKENS: {tokens_utilizados}"
        if tempo_resposta:
            mensagem += f" - TEMPO: {tempo_resposta:.2f}s"
        if modelo:
            mensagem += f" - MODELO: {modelo}"
        self.log_info(mensagem)
    
    def log_ia_conexao(self, status, modelo="", detalhes=""):
        """Registra log de status de conexão com IA."""
        mensagem = f"AGENTE_IA_CONEXAO: {status}"
        if modelo:
            mensagem += f" - MODELO: {modelo}"
        if detalhes:
            mensagem += f" - DETALHES: {detalhes}"
        
        if "conectado" in status.lower() or "sucesso" in status.lower():
            self.log_info(mensagem)
        else:
            self.log_erro(mensagem)
    
    def log_ia_analise(self, tipo_analise, resultado, tempo_processamento=0, modelo=""):
        """Registra log de análises realizadas pela IA."""
        mensagem = f"AGENTE_IA_ANALISE: {tipo_analise} - RESULTADO: {resultado}"
        if tempo_processamento:
            mensagem += f" - TEMPO: {tempo_processamento:.2f}s"
        if modelo:
            mensagem += f" - MODELO: {modelo}"
        self.log_info(mensagem)

    # =====================
    # UI: Instrumentação Automática (tkinter/customtkinter)
    # =====================
    def instrument_ui(self, root: Any, modulo: str = "UI", incluir_children: bool = True):
        """Instrumenta widgets tkinter/customtkinter para gerar logs automáticos.

        - Buttons/CTkButton: loga cliques e envolve o 'command' para log antes/depois
        - Entry/CTkEntry: loga texto ao pressionar Enter e ao perder foco (se alterado)
        - Combobox: loga seleção
        - Checkbutton/Radiobutton/CTkSwitch/CTkCheckBox: loga alternância
        - Treeview: loga seleção
        - Notebook: loga troca de abas

        Chame uma vez após criar a UI principal:
            logs.sistema_logs.instrument_ui(root)
        """
        if root is None:
            return
        try:
            # Evita instrumentar o mesmo widget múltiplas vezes
            if getattr(root, "_autolog_instrumented", False):
                pass
            else:
                setattr(root, "_autolog_instrumented", True)
                self._instrument_widget(root, modulo)

            if incluir_children and hasattr(root, "winfo_children"):
                for child in root.winfo_children():
                    self.instrument_ui(child, modulo, incluir_children)
        except Exception as e:  # nunca quebra a UI por causa do log
            self.log_warning(f"INSTRUMENTACAO_UI_FALHOU: {e}")

    # -------- Internos --------
    def _widget_path(self, widget: Any) -> str:
        try:
            # Gera uma identificação amigável
            cls = widget.__class__.__name__
            name = getattr(widget, "_name", None) or getattr(widget, "_w", "")
            text = None
            # tenta pegar texto do widget (quando existir)
            for key in ("text",):
                try:
                    val = widget.cget(key)
                    if val:
                        text = str(val)
                        break
                except Exception:
                    pass
            parts = [p for p in [cls, name, text] if p]
            return "|".join(parts)
        except Exception:
            return str(widget)

    def _wrap_command(self, widget: Any, cmd: Callable, modulo: str) -> Callable:
        def _wrapped(*args, **kwargs):
            info = self._widget_path(widget)
            self.log_operacao(modulo, "COMMAND_IN", detalhes=info)
            try:
                return cmd(*args, **kwargs)
            finally:
                self.log_operacao(modulo, "COMMAND_OUT", detalhes=info)
        return _wrapped

    def _maybe_wrap_command(self, widget: Any, modulo: str):
        # Tenta capturar e envolver o 'command' do widget (tk, ttk, ctk)
        get_ok = False
        current = None
        # obter
        for getter in (
            lambda w: w.cget("command"),
            lambda w: getattr(w, "command", None),
        ):
            try:
                current = getter(widget)
                get_ok = True
                break
            except Exception:
                continue
        if not get_ok:
            return
        # valida callable
        if not callable(current):
            return
        # definir
        wrapped = self._wrap_command(widget, current, modulo)
        for setter in (
            lambda w, cb: w.configure(command=cb),
            lambda w, cb: setattr(w, "command", cb),
        ):
            try:
                setter(widget, wrapped)
                # Marca para evitar dupla
                setattr(widget, "_autolog_cmd_wrapped", True)
                break
            except Exception:
                continue

    def _bind(self, widget: Any, sequence: str, handler: Callable):
        try:
            widget.bind(sequence, handler, add=True)
        except Exception:
            try:
                widget.bind(sequence, handler)
            except Exception:
                pass

    def _instrument_widget(self, widget: Any, modulo: str):
        wcls = widget.__class__.__name__
        wclass = None
        try:
            wclass = widget.winfo_class()
        except Exception:
            wclass = None

        info = self._widget_path(widget)

        # 1) Tenta envolver command se existir (Buttons, Check, Radio, Menus, CTk components)
        self._maybe_wrap_command(widget, modulo)

        # 2) Eventos específicos por tipo/assinatura
        # Buttons (mesmo sem command)
        if any(k in (wcls, wclass) for k in ("Button", "TButton", "CTkButton")):
            self._bind(widget, "<ButtonRelease-1>", lambda e, i=info: self.log_operacao(modulo, "CLICK", detalhes=i))

        # Entries
        if any(k in (wcls, wclass) for k in ("Entry", "TEntry", "CTkEntry")):
            # Armazena último valor
            try:
                setattr(widget, "_autolog_last_value", widget.get())
            except Exception:
                setattr(widget, "_autolog_last_value", "")

            def on_return(e, w=widget):
                try:
                    val = w.get()
                except Exception:
                    val = ""
                self.log_operacao(modulo, "ENTRY_RETURN", detalhes=f"{self._widget_path(w)} -> '{val}'")

            def on_focus_out(e, w=widget):
                try:
                    val = w.get()
                except Exception:
                    val = ""
                last = getattr(w, "_autolog_last_value", None)
                if val != last:
                    self.log_operacao(modulo, "ENTRY_CHANGE", detalhes=f"{self._widget_path(w)} -> '{val}'")
                    setattr(w, "_autolog_last_value", val)

            self._bind(widget, "<Return>", on_return)
            self._bind(widget, "<FocusOut>", on_focus_out)

        # Combobox
        if any(k in (wcls, wclass) for k in ("Combobox", "TCombobox")):
            def on_combo(e, w=widget):
                try:
                    val = w.get()
                except Exception:
                    val = ""
                self.log_operacao(modulo, "COMBO_SELECT", detalhes=f"{self._widget_path(w)} -> '{val}'")
            self._bind(widget, "<<ComboboxSelected>>", on_combo)

        # Treeview seleção
        if any(k in (wcls, wclass) for k in ("Treeview",)):
            def on_tree(e, w=widget):
                try:
                    sel = w.selection()
                except Exception:
                    sel = []
                self.log_operacao(modulo, "TREE_SELECT", detalhes=f"{self._widget_path(w)} -> {list(sel)}")
            self._bind(widget, "<<TreeviewSelect>>", on_tree)

        # Notebook tab change
        if any(k in (wcls, wclass) for k in ("Notebook", "TNotebook")):
            def on_tab(e, w=widget):
                try:
                    idx = w.index("current")
                except Exception:
                    idx = -1
                self.log_operacao(modulo, "TAB_CHANGED", detalhes=f"{self._widget_path(w)} -> {idx}")
            self._bind(widget, "<<NotebookTabChanged>>", on_tab)

# Instância global para uso em todo o sistema
sistema_logs = SistemaLogs()

# Funções de conveniência para uso rápido
def log_info(mensagem):
    sistema_logs.log_info(mensagem)

def log_erro(mensagem):
    sistema_logs.log_erro(mensagem)

def log_warning(mensagem):
    sistema_logs.log_warning(mensagem)

def log_acesso(usuario, acao):
    sistema_logs.log_acesso(usuario, acao)

def log_operacao(modulo, operacao, detalhes=""):
    sistema_logs.log_operacao(modulo, operacao, detalhes)

# Funções específicas para IA
def log_ia(acao, detalhes="", modelo=""):
    sistema_logs.log_ia(acao, detalhes, modelo)

def log_ia_erro(acao, erro, modelo=""):
    sistema_logs.log_ia_erro(acao, erro, modelo)

def log_ia_pergunta(pergunta, tokens_utilizados=0, tempo_resposta=0, modelo=""):
    sistema_logs.log_ia_pergunta(pergunta, tokens_utilizados, tempo_resposta, modelo)

def log_ia_resposta(pergunta, resposta, tokens_utilizados=0, tempo_resposta=0, modelo=""):
    sistema_logs.log_ia_resposta(pergunta, resposta, tokens_utilizados, tempo_resposta, modelo)

def log_ia_conexao(status, modelo="", detalhes=""):
    sistema_logs.log_ia_conexao(status, modelo, detalhes)

def log_ia_analise(tipo_analise, resultado, tempo_processamento=0, modelo=""):
    sistema_logs.log_ia_analise(tipo_analise, resultado, tempo_processamento, modelo)

# Função de compatibilidade para código existente
def log_ia_operacao(acao, detalhes="", modelo=""):
    """Alias para log_ia - mantém compatibilidade"""
    sistema_logs.log_ia(acao, detalhes, modelo)

# =====================
# Atalho público para instrumentação de UI
# =====================
def enable_ui_autolog(root: Any, modulo: str = "UI"):
    """Ativa logs automáticos de ações de UI no widget raiz informado.

    Exemplo de uso após construir a janela/principal:
        from logs import enable_ui_autolog
        enable_ui_autolog(root, modulo="RELATORIOS")
    """
    try:
        sistema_logs.instrument_ui(root, modulo=modulo)
    except Exception as e:
        sistema_logs.log_warning(f"ENABLE_UI_AUTOLOG_FALHOU: {e}")