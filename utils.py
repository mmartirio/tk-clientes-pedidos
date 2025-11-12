# utils.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import re
import os


def registrar_log(mensagem):
    """Registra uma mensagem de log em arquivo local."""
    try:
        # Criar pasta logs se não existir
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        log_file = f"logs/sistema_clientes_pedidos_{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensagem}\n")
    except Exception as e:
        print(f"Erro ao registrar log: {e}")


def mostrar_erro(titulo, mensagem):
    """Exibe mensagem de erro e registra log."""
    registrar_log(f"ERRO - {titulo}: {mensagem}")
    messagebox.showerror(titulo, mensagem)


def mostrar_info(titulo, mensagem):
    """Exibe mensagem informativa e registra log."""
    registrar_log(f"INFO - {titulo}: {mensagem}")
    messagebox.showinfo(titulo, mensagem)


def validar_email(email):
    """Valida formato simples de e-mail."""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def validar_telefone(telefone):
    """Valida telefone com 8–15 dígitos numéricos."""
    return bool(re.match(r"^\d{8,15}$", telefone))


def confirmar_acao(titulo, mensagem):
    """Exibe caixa de confirmação e retorna True/False."""
    registrar_log(f"CONFIRMAÇÃO - {titulo}: {mensagem}")
    return messagebox.askyesno(titulo, mensagem)


def formatar_moeda(valor):
    """Formata valor como moeda brasileira."""
    try:
        return f"R$ {float(valor):.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return "R$ 0,00"


def validar_data(data_str):
    """Valida formato de data YYYY-MM-DD."""
    try:
        datetime.strptime(data_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def obter_data_atual():
    """Retorna a data atual no formato YYYY-MM-DD."""
    return datetime.now().strftime('%Y-%m-%d')


def calcular_dias_entre_datas(data_inicio, data_fim):
    """Calcula dias entre duas datas."""
    try:
        inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        fim = datetime.strptime(data_fim, '%Y-%m-%d')
        return (fim - inicio).days
    except ValueError:
        return 0