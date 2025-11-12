# views/relatorio_views.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import os
import zipfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import customtkinter as ctk
import threading
import json
import numpy as np
from decimal import Decimal
import tempfile
import io
import sys
import uuid

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.units import cm, inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False
    print("Reportlab não disponível. Instale com: pip install reportlab")
except Exception as e:
    REPORTLAB_DISPONIVEL = False
    print(f"Erro ao importar reportlab: {e}")

from logs import log_operacao, log_erro
from agente_ia import agente_ia


class RelatorioViews:
    def __init__(self, master):
        self.master = master
        self.db_path = 'clientes_pedidos.db'
        self.styles = None
        # aplica tema atual e registra para reagir a mudanças globais
        self._aplicar_tema()
        try:
            # Ouve o evento virtual disparado pelo App quando o tema muda
            self.master.bind("<<TemaAlterado>>", self._on_tema_alterado)
        except Exception:
            pass
        self._criar_widgets()
        self._carregar_dados_iniciais()
    
    def _criar_arquivo_temp_png(self):
        """Cria um arquivo temporário PNG de forma segura para Windows"""
        temp_dir = tempfile.gettempdir()
        temp_filename = f"relatorio_grafico_{uuid.uuid4().hex}.png"
        temp_path = os.path.join(temp_dir, temp_filename)
        return temp_path
    
    def _salvar_grafico_para_pdf(self, fig, dpi=120):
        """Salva figura matplotlib em BytesIO para uso direto com ReportLab (SEM arquivo temporário)"""
        try:
            # Criar BytesIO e salvar a figura diretamente
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
            img_buffer.seek(0)
            
            # Retornar ImageReader que pode ser usado diretamente no Image do ReportLab
            return ImageReader(img_buffer)
            
        except Exception as e:
            print(f"Erro ao salvar gráfico em memória: {e}")
            raise
    
    def _formatar_moeda(self, valor):
        """Formata valor para padrão BRL (R$ 1.234,56)"""
        if valor is None:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        log_operacao("RELATORIOS", "Módulo de relatórios inicializado com CustomTkinter")

    # --- NOVOS MÉTODOS PARA AS TABELAS SOLICITADAS ---
    def _obter_tabela_clientes_cadastrados(self, data_inicio, data_fim):
        conn = self._conectar_db()
        c = conn.cursor()
        c.execute("""
            SELECT id, nome, email, telefone, date(created_at) as data_cadastro,
                   (SELECT COUNT(*) FROM pedidos WHERE cliente_id = clientes.id) as total_pedidos,
                   (SELECT SUM(total) FROM pedidos WHERE cliente_id = clientes.id) as valor_total_gasto
            FROM clientes 
            WHERE date(created_at) BETWEEN ? AND ? 
            ORDER BY created_at DESC
        """, (data_inicio, data_fim))
        clientes = c.fetchall()
        conn.close()
        return clientes

    def _obter_tabela_top_5_clientes(self, data_inicio, data_fim):
        conn = self._conectar_db()
        c = conn.cursor()
        c.execute("""
            SELECT c.id, c.nome, c.email, 
                   COUNT(p.id) as total_pedidos, 
                   SUM(p.total) as valor_total,
                   AVG(p.total) as ticket_medio
            FROM clientes c
            JOIN pedidos p ON c.id = p.cliente_id
            WHERE date(p.created_at) BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY valor_total DESC
            LIMIT 5
        """, (data_inicio, data_fim))
        top_clientes = c.fetchall()
        conn.close()
        return top_clientes

    def _obter_tabela_produtos_cadastrados(self):
        conn = self._conectar_db()
        c = conn.cursor()
        try:
            c.execute("""
                SELECT id, nome, descricao, preco, categoria, estoque, date(created_at)
                FROM produtos 
                ORDER BY created_at DESC
            """)
            produtos = c.fetchall()
        except sqlite3.OperationalError:
            produtos = []
        conn.close()
        return produtos

    def _obter_tabela_top_5_produtos(self, data_inicio, data_fim):
        conn = self._conectar_db()
        c = conn.cursor()
        try:
            c.execute("""
                SELECT p.id, p.nome, p.categoria,
                       SUM(ip.quantidade) as total_vendido,
                       SUM(ip.quantidade * ip.preco_unit) as valor_total,
                       COUNT(DISTINCT ip.pedido_id) as pedidos_com_produto
                FROM produtos p
                JOIN itens_pedido ip ON p.id = ip.produto_id
                JOIN pedidos ped ON ip.pedido_id = ped.id
                WHERE date(ped.created_at) BETWEEN ? AND ?
                GROUP BY p.id
                ORDER BY total_vendido DESC
                LIMIT 5
            """, (data_inicio, data_fim))
            top_produtos = c.fetchall()
        except sqlite3.OperationalError:
            top_produtos = []
        conn.close()
        return top_produtos

    def _obter_tabela_pedidos_completa(self, data_inicio, data_fim, status="Todos"):
        conn = self._conectar_db()
        c = conn.cursor()
        query = """
            SELECT 
                p.id as pedido_id,
                p.total,
                p.status,
                date(p.created_at) as data_pedido,
                c.id as cliente_id,
                c.nome as cliente_nome,
                c.email as cliente_email,
                c.telefone as cliente_telefone,
                (SELECT COUNT(*) FROM itens_pedido WHERE pedido_id = p.id) as total_itens
            FROM pedidos p
            LEFT JOIN clientes c ON p.cliente_id = c.id
            WHERE date(p.created_at) BETWEEN ? AND ?
        """
        params = [data_inicio, data_fim]
        if status != "Todos":
            query += " AND p.status = ?"
            params.append(status)
        query += " ORDER BY p.created_at DESC"
        c.execute(query, params)
        pedidos = c.fetchall()
        conn.close()
        return pedidos

    # --- MÉTODOS PARA ADICIONAR AS NOVAS TABELAS AOS RELATÓRIOS ---
    def _adicionar_secao_tabelas_completas(self, parent, data_inicio, data_fim, status):
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=10)
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="📋 TABELAS DETALHADAS DO SISTEMA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2c3e50"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        self._adicionar_tabela_clientes_cadastrados(frame_secao, data_inicio, data_fim)
        self._adicionar_tabela_top_5_clientes(frame_secao, data_inicio, data_fim)
        self._adicionar_tabela_produtos_cadastrados(frame_secao)
        self._adicionar_tabela_top_5_produtos(frame_secao, data_inicio, data_fim)
        self._adicionar_tabela_pedidos_completa(frame_secao, data_inicio, data_fim, status)

    def _adicionar_tabela_clientes_cadastrados(self, parent, data_inicio, data_fim):
        frame_tabela = ctk.CTkFrame(parent)
        frame_tabela.pack(fill=tk.X, pady=10, padx=5)
        ctk.CTkLabel(
            frame_tabela,
            text="👥 CLIENTES CADASTRADOS (Período Selecionado)",
            font=ctk.CTkFont(weight="bold"),
            text_color="#3498db"
        ).pack(anchor="w", pady=(10, 5))
        clientes = self._obter_tabela_clientes_cadastrados(data_inicio, data_fim)
        if clientes:
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.X, padx=5, pady=5)
            cols = ('ID', 'Nome', 'Email', 'Telefone', 'Data Cadastro', 'Total Pedidos', 'Valor Total Gasto')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8)
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for cliente in clientes:
                tree.insert('', tk.END, values=cliente)
        else:
            ctk.CTkLabel(
                frame_tabela,
                text="Nenhum cliente cadastrado no período selecionado.",
                text_color=("gray50", "gray70")
            ).pack(pady=10)

    def _adicionar_tabela_top_5_clientes(self, parent, data_inicio, data_fim):
        frame_tabela = ctk.CTkFrame(parent)
        frame_tabela.pack(fill=tk.X, pady=10, padx=5)
        ctk.CTkLabel(
            frame_tabela,
            text="🏆 TOP 5 CLIENTES (Maior Valor Gasto)",
            font=ctk.CTkFont(weight="bold"),
            text_color="#e74c3c"
        ).pack(anchor="w", pady=(10, 5))
        top_clientes = self._obter_tabela_top_5_clientes(data_inicio, data_fim)
        if top_clientes:
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.X, padx=5, pady=5)
            cols = ('ID', 'Nome', 'Email', 'Total Pedidos', 'Valor Total', 'Ticket Médio')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=6)
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for cliente in top_clientes:
                tree.insert('', tk.END, values=(
                    cliente[0], cliente[1], cliente[2], cliente[3],
                    self._formatar_moeda(cliente[4]) if cliente[4] else "R$ 0,00",
                    self._formatar_moeda(cliente[5]) if cliente[5] else "R$ 0,00"
                ))
        else:
            ctk.CTkLabel(
                frame_tabela,
                text="Nenhum dado de clientes top disponível.",
                text_color=("gray50", "gray70")
            ).pack(pady=10)

    def _adicionar_tabela_produtos_cadastrados(self, parent):
        frame_tabela = ctk.CTkFrame(parent)
        frame_tabela.pack(fill=tk.X, pady=10, padx=5)
        ctk.CTkLabel(
            frame_tabela,
            text="📦 PRODUTOS CADASTRADOS NO SISTEMA",
            font=ctk.CTkFont(weight="bold"),
            text_color="#2ecc71"
        ).pack(anchor="w", pady=(10, 5))
        produtos = self._obter_tabela_produtos_cadastrados()
        if produtos:
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.X, padx=5, pady=5)
            cols = ('ID', 'Nome', 'Descrição', 'Preço', 'Categoria', 'Estoque', 'Data Cadastro')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8)
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for produto in produtos:
                tree.insert('', tk.END, values=produto)
        else:
            ctk.CTkLabel(
                frame_tabela,
                text="Nenhum produto cadastrado no sistema ou tabela não disponível.",
                text_color=("gray50", "gray70")
            ).pack(pady=10)

    def _adicionar_tabela_top_5_produtos(self, parent, data_inicio, data_fim):
        frame_tabela = ctk.CTkFrame(parent)
        frame_tabela.pack(fill=tk.X, pady=10, padx=5)
        ctk.CTkLabel(
            frame_tabela,
            text="🔥 TOP 5 PRODUTOS MAIS VENDIDOS",
            font=ctk.CTkFont(weight="bold"),
            text_color="#f39c12"
        ).pack(anchor="w", pady=(10, 5))
        top_produtos = self._obter_tabela_top_5_produtos(data_inicio, data_fim)
        if top_produtos:
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.X, padx=5, pady=5)
            cols = ('ID', 'Nome', 'Categoria', 'Quantidade Vendida', 'Valor Total', 'Pedidos com Produto')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=6)
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for produto in top_produtos:
                tree.insert('', tk.END, values=(
                    produto[0], produto[1], produto[2], produto[3],
                    self._formatar_moeda(produto[4]) if produto[4] else "R$ 0,00",
                    produto[5]
                ))
        else:
            ctk.CTkLabel(
                frame_tabela,
                text="Nenhum dado de produtos top disponível ou tabelas não existem.",
                text_color=("gray50", "gray70")
            ).pack(pady=10)

    def _adicionar_tabela_pedidos_completa(self, parent, data_inicio, data_fim, status):
        frame_tabela = ctk.CTkFrame(parent)
        frame_tabela.pack(fill=tk.X, pady=10, padx=5)
        ctk.CTkLabel(
            frame_tabela,
            text="📋 PEDIDOS COMPLETOS COM DADOS DE CLIENTES",
            font=ctk.CTkFont(weight="bold"),
            text_color="#9b59b6"
        ).pack(anchor="w", pady=(10, 5))
        pedidos = self._obter_tabela_pedidos_completa(data_inicio, data_fim, status)
        if pedidos:
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            cols = ('ID Pedido', 'Valor', 'Status', 'Data', 
                   'ID Cliente', 'Cliente', 'Email', 'Telefone', 'Itens')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8)
            v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            tree.grid(row=0, column=0, sticky='nsew')
            v_scroll.grid(row=0, column=1, sticky='ns')
            h_scroll.grid(row=1, column=0, sticky='ew')
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for pedido in pedidos:
                tree.insert('', tk.END, values=(
                    pedido[0],  # ID Pedido
                    self._formatar_moeda(pedido[1]),  # Valor
                    pedido[2],  # Status
                    pedido[3],  # Data
                    pedido[4] or 'N/A',  # ID Cliente
                    pedido[5] or 'N/A',  # Cliente
                    pedido[6] or 'N/A',  # Email
                    pedido[7] or 'N/A',  # Telefone
                    pedido[8] or 0  # Itens
                ))
        else:
            ctk.CTkLabel(
                frame_tabela,
                text="Nenhum pedido encontrado no período selecionado.",
                text_color=("gray50", "gray70")
            ).pack(pady=10)

    # --- MÉTODOS PARA GRÁFICOS ADICIONAIS ---
    def _adicionar_graficos_adicionais(self, parent, data_inicio, data_fim):
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=10)
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="📊 GRÁFICOS ADICIONAIS - TABELAS DO SISTEMA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e67e22"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        try:
            self._adicionar_grafico_clientes_periodo(frame_secao, data_inicio, data_fim)
            self._adicionar_grafico_top_produtos(frame_secao, data_inicio, data_fim)
            self._adicionar_grafico_status_pedidos(frame_secao, data_inicio, data_fim)
        except Exception as e:
            ctk.CTkLabel(
                frame_secao,
                text=f"Erro ao gerar gráficos adicionais: {str(e)}",
                text_color="#e74c3c",
                font=ctk.CTkFont(size=10)
            ).pack(pady=10)

    def _adicionar_grafico_clientes_periodo(self, parent, data_inicio, data_fim):
        conn = self._conectar_db()
        c = conn.cursor()
        c.execute("""
            SELECT date(created_at), COUNT(*) 
            FROM clientes 
            WHERE date(created_at) BETWEEN ? AND ? 
            GROUP BY date(created_at) 
            ORDER BY date(created_at)
        """, (data_inicio, data_fim))
        dados = c.fetchall()
        conn.close()
        if dados:
            frame_grafico = ctk.CTkFrame(parent)
            frame_grafico.pack(fill=tk.X, pady=10, padx=10)
            ctk.CTkLabel(
                frame_grafico,
                text="📈 EVOLUÇÃO DE CADASTRO DE CLIENTES",
                font=ctk.CTkFont(weight="bold"),
                text_color="#3498db"
            ).pack(anchor="w", pady=(10, 5))
            fig = Figure(figsize=(10, 4), dpi=100)
            ax = fig.add_subplot(111)
            datas = [d[0] for d in dados]
            quantidades = [d[1] for d in dados]
            ax.bar(datas, quantidades, color='#3498db', alpha=0.8, edgecolor='black')
            ax.set_title('Evolução de Cadastro de Clientes por Dia', fontsize=12, fontweight='bold')
            ax.set_ylabel('Novos Clientes', fontsize=10)
            ax.set_xlabel('Data', fontsize=10)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
            for i, (data, valor) in enumerate(zip(datas, quantidades)):
                ax.text(i, valor + 0.1, str(valor), 
                       ha='center', va='bottom', fontweight='bold', fontsize=9)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, frame_grafico)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _adicionar_grafico_top_produtos(self, parent, data_inicio, data_fim):
        top_produtos = self._obter_tabela_top_5_produtos(data_inicio, data_fim)
        if top_produtos:
            frame_grafico = ctk.CTkFrame(parent)
            frame_grafico.pack(fill=tk.X, pady=10, padx=10)
            ctk.CTkLabel(
                frame_grafico,
                text="🔥 COMPARAÇÃO TOP 5 PRODUTOS MAIS VENDIDOS",
                font=ctk.CTkFont(weight="bold"),
                text_color="#e74c3c"
            ).pack(anchor="w", pady=(10, 5))
            fig = Figure(figsize=(10, 5), dpi=100)
            ax = fig.add_subplot(111)
            nomes = [p[1][:15] + '...' if len(p[1]) > 15 else p[1] for p in top_produtos]
            quantidades = [p[3] for p in top_produtos]
            valores = [float(p[4] or 0) for p in top_produtos]
            x_pos = np.arange(len(nomes))
            width = 0.35
            bars1 = ax.bar(x_pos - width/2, quantidades, width, label='Quantidade Vendida', 
                          color='#e74c3c', alpha=0.8)
            bars2 = ax.bar(x_pos + width/2, [v/100 for v in valores], width, label='Valor Total (R$/100)', 
                          color='#3498db', alpha=0.8)
            ax.set_xlabel('Produtos', fontsize=10)
            ax.set_ylabel('Quantidade / Valor (R$/100)', fontsize=10)
            ax.set_title('Comparação: Quantidade vs Valor - Top 5 Produtos', fontsize=12, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(nomes, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, frame_grafico)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _adicionar_grafico_status_pedidos(self, parent, data_inicio, data_fim):
        conn = self._conectar_db()
        c = conn.cursor()
        c.execute("""
            SELECT status, COUNT(*) 
            FROM pedidos 
            WHERE date(created_at) BETWEEN ? AND ? 
            GROUP BY status
        """, (data_inicio, data_fim))
        dados = c.fetchall()
        conn.close()
        if dados:
            frame_grafico = ctk.CTkFrame(parent)
            frame_grafico.pack(fill=tk.X, pady=10, padx=10)
            ctk.CTkLabel(
                frame_grafico,
                text="📋 DISTRIBUIÇÃO DE STATUS DOS PEDIDOS",
                font=ctk.CTkFont(weight="bold"),
                text_color="#2ecc71"
            ).pack(anchor="w", pady=(10, 5))
            fig = Figure(figsize=(8, 5), dpi=100)
            ax = fig.add_subplot(111)
            status = [d[0] for d in dados]
            quantidades = [d[1] for d in dados]
            cores = ['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6', '#34495e']
            wedges, texts, autotexts = ax.pie(quantidades, labels=status, autopct='%1.1f%%',
                                            colors=cores[:len(status)], startangle=90)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            ax.set_title('Distribuição de Pedidos por Status', fontsize=12, fontweight='bold')
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, frame_grafico)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # --- ATUALIZAÇÃO DOS MÉTODOS DE EXPORTAÇÃO PARA INCLUIR AS NOVAS TABELAS ---
    def _exportar_csv(self, tipo, data_inicio, data_fim, status="Todos"):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        if not filename:
            return
        try:
            self._mostrar_progresso(True)
            conn = self._conectar_db()
            c = conn.cursor()
            if tipo == "clientes":
                dados = self._obter_tabela_clientes_cadastrados(data_inicio, data_fim)
                colunas = ['ID', 'Nome', 'Email', 'Telefone', 'Data_Cadastro', 'Total_Pedidos', 'Valor_Total_Gasto']
            elif tipo == "pedidos":
                dados = self._obter_tabela_pedidos_completa(data_inicio, data_fim, status)
                colunas = ['ID_Pedido', 'Total', 'Status', 'Data_Pedido', 
                          'ID_Cliente', 'Cliente_Nome', 'Cliente_Email', 'Cliente_Telefone', 'Total_Itens']
            # ... (restante do código mantido igual) ...
            conn.close()
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(colunas)
                for linha in dados:
                    linha_formatada = []
                    for item in linha:
                        if item is None:
                            linha_formatada.append('')
                        elif isinstance(item, float):
                            linha_formatada.append(f"{item:.2f}")
                        else:
                            linha_formatada.append(str(item))
                    writer.writerow(linha_formatada)
            messagebox.showinfo("CSV Exportado", f"Relatório {tipo} exportado com sucesso:\n{filename}")
            log_operacao("RELATORIOS", f"CSV exportado: {filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar CSV: {e}")
            log_erro(f"Erro ao exportar CSV: {e}")
        finally:
            self._mostrar_progresso(False)

    def _aplicar_tema(self):
        # Não força tema; usa o modo global atual do CustomTkinter
        modo = ctk.get_appearance_mode()  # "Light" ou "Dark"
        try:
            ctk.set_default_color_theme("blue")
        except Exception:
            pass
        # Cores auxiliares dependentes do tema
        is_dark = str(modo).lower().startswith("dark")
        self._cor_texto_principal = "#ffffff" if is_dark else "#1f2937"
        self._cor_texto_secundario = "#e5e7eb" if is_dark else "#374151"
        self._cor_frame_secundario = ("gray90", "gray20")
        # Atualiza widgets já criados, se existirem
        if hasattr(self, "lbl_titulo"):
            self.lbl_titulo.configure(text_color=self._cor_texto_principal)
        if hasattr(self, "frame_explicacao"):
            try:
                self.frame_explicacao.configure(fg_color=self._cor_frame_secundario)
            except Exception:
                pass

    def _on_tema_alterado(self, event=None):
        # Reaplica tema e atualiza elementos visuais dinâmicos
        self._aplicar_tema()

    def _conectar_db(self):
        return sqlite3.connect(self.db_path)

    def _criar_widgets(self):
        self.main_frame = ctk.CTkFrame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.lbl_titulo = ctk.CTkLabel(
            self.main_frame,
            text="📊 Relatórios Inteligentes",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=getattr(self, "_cor_texto_principal", "#ffffff")
        )
        self.lbl_titulo.pack(pady=(0, 15))

        self.frame_explicacao = ctk.CTkFrame(self.main_frame, fg_color=getattr(self, "_cor_frame_secundario", ("gray90", "gray20")))
        self.frame_explicacao.pack(fill=tk.X, pady=(0, 10))
        
        texto_explicativo = """💡 SISTEMA INTELIGENTE DE RELATÓRIOS

• Relatórios completos com tabelas, gráficos e análises
• Exportação em CSV e Visualização
• Análise de crescimento, riscos e oportunidades
• Planos de ação com estimativas de crescimento"""
        
        lbl_explicacao = ctk.CTkLabel(
            self.frame_explicacao, 
            text=texto_explicativo,
            font=ctk.CTkFont(size=12),
            justify=tk.LEFT,
            wraplength=700
        )
        lbl_explicacao.pack(padx=10, pady=10)

        frame_controles = ctk.CTkFrame(self.main_frame)
        frame_controles.pack(fill=tk.X, pady=(0, 10))

        frame_tipo = ctk.CTkFrame(frame_controles)
        frame_tipo.pack(fill=tk.X, pady=8, padx=10)
        ctk.CTkLabel(frame_tipo, text="Tipo de Relatório:", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT)
        self.tipo_relatorio = ctk.StringVar(value="geral")
        
        tipos = [
            ("👥 Clientes", "clientes"),
            ("📦 Pedidos", "pedidos"),
            ("💰 Financeiro", "financeiro"),
            ("📊 Estatísticas", "estatisticas"),
            ("🎯 Geral Completo", "geral")
        ]
        
        tipo_frame = ctk.CTkFrame(frame_tipo)
        tipo_frame.pack(side=tk.LEFT, padx=(10, 0))
        for txt, val in tipos:
            ctk.CTkRadioButton(tipo_frame, text=txt, variable=self.tipo_relatorio, 
                              value=val).pack(side=tk.LEFT, padx=8)

        frame_periodo = ctk.CTkFrame(frame_controles)
        frame_periodo.pack(fill=tk.X, pady=8, padx=10)
        ctk.CTkLabel(frame_periodo, text="Período:", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT)
        self.periodo = ctk.StringVar(value="30_dias")
        
        periodo_frame = ctk.CTkFrame(frame_periodo)
        periodo_frame.pack(side=tk.LEFT, padx=(10, 0))
        periodos = [
            ("📅 Mês Atual", "mes_atual"),
            ("🗓️ Últimos 7 Dias", "7_dias"),
            ("📊 Últimos 30 Dias", "30_dias"),
            ("🎛️ Personalizado", "personalizado")
        ]
        for txt, val in periodos:
            ctk.CTkRadioButton(periodo_frame, text=txt, variable=self.periodo, 
                              value=val, command=self._toggle_datas_personalizadas).pack(side=tk.LEFT, padx=8)

        self.frame_datas = ctk.CTkFrame(frame_controles)
        self.frame_datas.pack(fill=tk.X, pady=8, padx=10)
        ctk.CTkLabel(self.frame_datas, text="De:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.data_inicio = ctk.CTkEntry(self.frame_datas, width=120, placeholder_text="YYYY-MM-DD")
        self.data_inicio.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.data_inicio.pack(side=tk.LEFT, padx=5)
        
        ctk.CTkLabel(self.frame_datas, text="Até:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.data_fim = ctk.CTkEntry(self.frame_datas, width=120, placeholder_text="YYYY-MM-DD")
        self.data_fim.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.data_fim.pack(side=tk.LEFT, padx=5)
        
        self.data_inicio.configure(state="disabled")
        self.data_fim.configure(state="disabled")

        frame_status = ctk.CTkFrame(frame_controles)
        frame_status.pack(fill=tk.X, pady=8, padx=10)
        ctk.CTkLabel(frame_status, text="Status (Pedidos):", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT)
        self.status_filtro = ctk.CTkComboBox(frame_status, 
                                           values=["Todos", "Concluído", "Pendente", "Cancelado"], 
                                           width=180)
        self.status_filtro.set("Todos")
        self.status_filtro.pack(side=tk.LEFT, padx=10)

        frame_formato = ctk.CTkFrame(frame_controles)
        frame_formato.pack(fill=tk.X, pady=8, padx=10)
        ctk.CTkLabel(frame_formato, text="Formato de Saída:", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT)
        self.formato = ctk.StringVar(value="tela")
        
        formato_frame = ctk.CTkFrame(frame_formato)
        formato_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        formatos = [("👁️ Visualização", "tela"), ("💾 CSV", "csv"), ("🤖 PDF + IA", "pdf_ia")]
        
        for txt, val in formatos:
            btn = ctk.CTkRadioButton(formato_frame, text=txt, variable=self.formato, 
                                   value=val)
            btn.pack(side=tk.LEFT, padx=8)

        frame_botoes = ctk.CTkFrame(frame_controles)
        frame_botoes.pack(fill=tk.X, pady=12, padx=10)
        
        botoes_config = [
            ("🚀 Gerar Relatório", self._gerar_relatorio, "primary"),
            ("🔄 Atualizar Dados", self._carregar_dados_iniciais, "secondary"),
            ("🤖 Análise Completa IA", self._analise_completa_ia, "success"),
            ("🧹 Limpar Tudo", self._limpar_resultados, "error")
        ]
        
        for texto, comando, estilo in botoes_config:
            if estilo == "primary":
                fg_color = "#2b5797"
            elif estilo == "success":
                fg_color = "#28a745"
            elif estilo == "warning":
                fg_color = "#ffc107"
            elif estilo == "error":
                fg_color = "#dc3545"
            else:
                fg_color = "#6c757d"
                
            btn = ctk.CTkButton(
                frame_botoes, 
                text=texto, 
                command=comando,
                fg_color=fg_color,
                hover_color=self._escurecer_cor(fg_color),
                font=ctk.CTkFont(weight="bold")
            )
            btn.pack(side=tk.LEFT, padx=6)

        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()

        self.frame_resultados = ctk.CTkFrame(self.main_frame)
        self.frame_resultados.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        # Container inicia vazio - análises serão exibidas ao clicar nos botões

    def _escurecer_cor(self, cor, fator=0.8):
        if cor.startswith('#'):
            cor = cor[1:]
        r = int(cor[0:2], 16)
        g = int(cor[2:4], 16)
        b = int(cor[4:6], 16)
        r = max(0, min(255, int(r * fator)))
        g = max(0, min(255, int(g * fator)))
        b = max(0, min(255, int(b * fator)))
        return f'#{r:02x}{g:02x}{b:02x}'

    def _toggle_datas_personalizadas(self):
        if self.periodo.get() == "personalizado":
            self.data_inicio.configure(state="normal")
            self.data_fim.configure(state="normal")
        else:
            self.data_inicio.configure(state="disabled")
            self.data_fim.configure(state="disabled")

    def _carregar_dados_iniciais(self):
        try:
            self._mostrar_progresso(True)
            conn = self._conectar_db()
            c = conn.cursor()
            primeiro_dia = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            c.execute("SELECT COUNT(*) FROM clientes")
            clientes = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pedidos WHERE created_at >= ?", (primeiro_dia,))
            pedidos = c.fetchone()[0]
            
            c.execute("SELECT SUM(total) FROM pedidos WHERE created_at >= ?", (primeiro_dia,))
            faturamento = c.fetchone()[0] or 0
            
            conn.close()
            self._atualizar_tela_inicial(clientes, pedidos, faturamento)
            log_operacao("RELATORIOS", "Dados iniciais carregados")
        except Exception as e:
            log_erro(f"Erro ao carregar dados iniciais: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar dados iniciais:\n{e}")
        finally:
            self._mostrar_progresso(False)

    def _mostrar_progresso(self, mostrar):
        if mostrar:
            self.progress_bar.pack(fill=tk.X, pady=(5, 0))
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

    def _mostrar_tela_inicial(self):
        self._limpar_resultados()
        
        frame_central = ctk.CTkFrame(self.frame_resultados, fg_color="transparent")
        frame_central.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        if not REPORTLAB_DISPONIVEL:
            aviso_pdf = "\n⚠️ **ATENÇÃO:** A funcionalidade de exportação PDF não está disponível.\nPara habilitar, instale: pip install reportlab\n"
        else:
            aviso_pdf = ""
            
        mensagem_boas_vindas = f"""🚀 RELATÓRIOS COMPLETOS COM ANÁLISES AVANÇADAS

📋 **Relatórios Disponíveis:**

🎯 **RELATÓRIO GERAL COMPLETO:**
• Tabelas detalhadas de clientes, produtos e pedidos
• Gráficos interativos com legendas e análises
• Métricas de crescimento e performance
• Análise de riscos e pontos de atenção
• Plano de ação com estimativas de crescimento

📊 **RELATÓRIOS ESPECÍFICOS:**
• 👥 Clientes: Cadastros, segmentação e comportamento
• 📦 Pedidos: Vendas, status e histórico detalhado
• 💰 Financeiro: Faturamento, ticket médio e evolução
• 📈 Estatísticas: Métricas, tendências e insights

🤖 **ANÁLISES INTELIGENTES:**
- Identificação automática de oportunidades
- Análise de pontos fracos e riscos
- Recomendações personalizadas
- Projeções de crescimento
- Planos de ação executivos

{aviso_pdf}"""
        
        texto_widget = ctk.CTkTextbox(frame_central, font=ctk.CTkFont(size=13), wrap=tk.WORD)
        texto_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        texto_widget.insert("1.0", mensagem_boas_vindas)
        texto_widget.configure(state="disabled")

    def _atualizar_tela_inicial(self, clientes, pedidos, faturamento):
        """Método removido - cards de visão geral não são mais exibidos"""
        pass

    def _limpar_resultados(self):
        for widget in self.frame_resultados.winfo_children():
            widget.destroy()

    def _obter_datas_periodo(self):
        periodo = self.periodo.get()
        if periodo == "mes_atual":
            d1 = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        elif periodo == "7_dias":
            d1 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif periodo == "30_dias":
            d1 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            d1 = self.data_inicio.get()
        d2 = self.data_fim.get()
        return d1, d2

    def _gerar_relatorio(self):
        tipo = self.tipo_relatorio.get()
        formato = self.formato.get()
        data_inicio, data_fim = self._obter_datas_periodo()
        status = self.status_filtro.get()

        try:
            log_operacao("RELATORIOS", f"Gerando relatório: {tipo} ({formato}) {data_inicio} a {data_fim}")
            
            self._mostrar_progresso(True)
            
            if formato == "pdf_ia":
                self._exportar_pdf_com_ia(tipo, data_inicio, data_fim, status)
            elif tipo == "geral":
                if formato == "tela":
                    self._mostrar_relatorio_geral_completo(data_inicio, data_fim, status)
                else:
                    self._exportar_csv_geral_completo(data_inicio, data_fim, status)
            else:
                if formato == "csv":
                    self._exportar_csv(tipo, data_inicio, data_fim, status)
                else:
                    self._mostrar_relatorio_tela(tipo, data_inicio, data_fim, status)

        except Exception as e:
            log_erro(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{e}")
        finally:
            self._mostrar_progresso(False)

    def _exportar_csv(self, tipo, data_inicio, data_fim, status="Todos"):
        """Exporta relatório individual em CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        if not filename:
            return

        try:
            self._mostrar_progresso(True)
            conn = self._conectar_db()
            c = conn.cursor()
            
            if tipo == "clientes":
                query = """
                    SELECT id, nome, email, telefone, date(created_at) 
                    FROM clientes 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    ORDER BY created_at DESC
                """
                c.execute(query, (data_inicio, data_fim))
                dados = c.fetchall()
                colunas = ['ID', 'Nome', 'Email', 'Telefone', 'Data_Cadastro']
                
            elif tipo == "pedidos":
                query = """
                    SELECT p.id, c.nome, p.total, p.status, date(p.created_at) 
                    FROM pedidos p 
                    LEFT JOIN clientes c ON p.cliente_id = c.id
                    WHERE date(p.created_at) BETWEEN ? AND ?
                """
                params = [data_inicio, data_fim]
                if status != "Todos":
                    query += " AND p.status = ?"
                    params.append(status)
                query += " ORDER BY p.created_at DESC"
                
                c.execute(query, params)
                dados = c.fetchall()
                colunas = ['ID_Pedido', 'Cliente', 'Total', 'Status', 'Data_Pedido']
                
            elif tipo == "financeiro":
                query = """
                    SELECT date(created_at), COUNT(*), SUM(total), AVG(total) 
                    FROM pedidos 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    GROUP BY date(created_at) 
                    ORDER BY date(created_at)
                """
                c.execute(query, (data_inicio, data_fim))
                dados = c.fetchall()
                colunas = ['Data', 'Total_Pedidos', 'Faturamento_Total', 'Ticket_Medio']
                
            elif tipo == "estatisticas":
                c.execute("SELECT COUNT(*) FROM clientes")
                total_clientes = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM pedidos")
                total_pedidos = c.fetchone()[0]
                c.execute("SELECT SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
                faturamento = c.fetchone()[0] or 0
                
                dados = [
                    ('Total_Clientes', total_clientes),
                    ('Total_Pedidos', total_pedidos),
                    ('Faturamento_Periodo', faturamento)
                ]
                colunas = ['Metrica', 'Valor']
            
            conn.close()
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(colunas)
                
                for linha in dados:
                    if tipo == "estatisticas":
                        writer.writerow([linha[0], linha[1]])
                    else:
                        linha_formatada = []
                        for item in linha:
                            if item is None:
                                linha_formatada.append('')
                            elif isinstance(item, float):
                                linha_formatada.append(f"{item:.2f}")
                            else:
                                linha_formatada.append(str(item))
                        writer.writerow(linha_formatada)
            
            messagebox.showinfo("CSV Exportado", f"Relatório {tipo} exportado com sucesso:\n{filename}")
            log_operacao("RELATORIOS", f"CSV exportado: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar CSV: {e}")
            log_erro(f"Erro ao exportar CSV: {e}")
        finally:
            self._mostrar_progresso(False)

    def _exportar_csv_geral_completo(self, data_inicio, data_fim, status="Todos"):
        """Exporta relatório geral completo em CSV com layout horizontal organizado"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"relatorio_geral_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        if not filename:
            return

        try:
            self._mostrar_progresso(True)
            conn = self._conectar_db()
            c = conn.cursor()

            # Coletar dados de CLIENTES
            c.execute("""
                SELECT id, nome, email, telefone, date(created_at) 
                FROM clientes 
                WHERE date(created_at) BETWEEN ? AND ? 
                ORDER BY created_at DESC
            """, (data_inicio, data_fim))
            clientes = c.fetchall()
            
            # Coletar dados de PEDIDOS
            query_pedidos = """
                SELECT p.id, c.nome, p.total, p.status, date(p.created_at) 
                FROM pedidos p 
                LEFT JOIN clientes c ON p.cliente_id = c.id
                WHERE date(p.created_at) BETWEEN ? AND ?
            """
            params = [data_inicio, data_fim]
            if status != "Todos":
                query_pedidos += " AND p.status = ?"
                params.append(status)
            query_pedidos += " ORDER BY p.created_at DESC"
            c.execute(query_pedidos, params)
            pedidos = c.fetchall()
            
            # Coletar dados FINANCEIROS
            c.execute("""
                SELECT date(created_at), COUNT(*), SUM(total), AVG(total) 
                FROM pedidos 
                WHERE date(created_at) BETWEEN ? AND ? 
                GROUP BY date(created_at) 
                ORDER BY date(created_at)
            """, (data_inicio, data_fim))
            financeiro = c.fetchall()
            
            # Coletar ESTATÍSTICAS
            c.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM pedidos")
            total_pedidos = c.fetchone()[0]
            c.execute("SELECT COUNT(*), SUM(total), AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                     (data_inicio, data_fim))
            stats_periodo = c.fetchone()

            # Escrever CSV com layout horizontal
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Cabeçalho
                writer.writerow(['RELATÓRIO GERAL COMPLETO'] + [''] * 19)
                writer.writerow([f'Período: {data_inicio} a {data_fim}'] + [''] * 19)
                writer.writerow([f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}'] + [''] * 19)
                writer.writerow([''] * 20)
                writer.writerow([''] * 20)
                
                # Linha com títulos das seções
                writer.writerow([
                    '=== CLIENTES ===', '', '', '', '', '',
                    '=== PEDIDOS ===', '', '', '', '', '',
                    '=== FINANCEIRO ===', '', '', '', '',
                    '=== RESUMO EXECUTIVO ===', '', ''
                ])
                
                # Linha com cabeçalhos das colunas
                writer.writerow([
                    'ID', 'Nome', 'Email', 'Telefone', 'Data_Cadastro', '',
                    'ID_Pedido', 'Cliente', 'Total', 'Status', 'Data_Pedido', '',
                    'Data', 'Qtd_Pedidos', 'Faturamento_Dia', 'Ticket_Medio_Dia', '',
                    'Item', 'Valor', ''
                ])
                
                # Determinar número máximo de linhas
                max_linhas = max(len(clientes), len(pedidos), len(financeiro), 5)
                
                # Escrever dados linha por linha
                for i in range(max_linhas):
                    linha = []
                    
                    # CLIENTES (6 colunas)
                    if i < len(clientes):
                        cliente = clientes[i]
                        linha.extend([
                            cliente[0],  # ID
                            cliente[1],  # Nome
                            cliente[2],  # Email
                            cliente[3] or '',  # Telefone
                            cliente[4]  # Data
                        ])
                    else:
                        linha.extend(['', '', '', '', ''])
                    linha.append('')  # Espaço
                    
                    # PEDIDOS (6 colunas)
                    if i < len(pedidos):
                        pedido = pedidos[i]
                        linha.extend([
                            pedido[0],  # ID
                            pedido[1] or '',  # Cliente
                            f"{pedido[2]:.2f}",  # Total
                            pedido[3] or '',  # Status
                            pedido[4]  # Data
                        ])
                    else:
                        linha.extend(['', '', '', '', ''])
                    linha.append('')  # Espaço
                    
                    # FINANCEIRO (5 colunas)
                    if i < len(financeiro):
                        fin = financeiro[i]
                        linha.extend([
                            fin[0],  # Data
                            fin[1],  # Qtd
                            f"{fin[2] or 0:.2f}",  # Faturamento
                            f"{fin[3] or 0:.2f}"  # Ticket Médio
                        ])
                    else:
                        linha.extend(['', '', '', ''])
                    linha.append('')  # Espaço
                    
                    # RESUMO EXECUTIVO (3 colunas)
                    if i == 0:
                        linha.extend(['Período_Analisado', f'{data_inicio} a {data_fim}'])
                    elif i == 1:
                        linha.extend(['Total_Clientes_Novos', len(clientes)])
                    elif i == 2:
                        linha.extend(['Total_Pedidos_Periodo', len(pedidos)])
                    elif i == 3:
                        linha.extend(['Faturamento_Total', f"{stats_periodo[1] or 0:.2f}"])
                    else:
                        linha.extend(['', ''])
                    linha.append('')  # Espaço final
                    
                    writer.writerow(linha)
                
                # Adicionar seção de ESTATÍSTICAS no final
                writer.writerow([''] * 20)
                writer.writerow(['=== ESTATÍSTICAS ==='] + [''] * 19)
                writer.writerow(['Métrica', 'Valor'] + [''] * 18)
                writer.writerow(['Total_Clientes', total_clientes] + [''] * 18)
                writer.writerow(['Total_Pedidos_Geral', total_pedidos] + [''] * 18)
                writer.writerow(['Pedidos_Periodo', stats_periodo[0] or 0] + [''] * 18)
                writer.writerow(['Faturamento_Periodo', f"{stats_periodo[1] or 0:.2f}"] + [''] * 18)
                writer.writerow(['Ticket_Medio_Periodo', f"{stats_periodo[2] or 0:.2f}"] + [''] * 18)

            conn.close()
            messagebox.showinfo("CSV Exportado", f"Relatório geral exportado com sucesso:\n{filename}")
            log_operacao("RELATORIOS", f"CSV geral exportado: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar CSV geral: {e}")
            log_erro(f"Erro ao exportar CSV geral: {e}")
        finally:
            self._mostrar_progresso(False)

    def _exportar_pdf(self, tipo, data_inicio, data_fim, status="Todos"):
        """Exporta relatório individual em PDF"""
        if not REPORTLAB_DISPONIVEL:
            messagebox.showerror("PDF Não Disponível", "Instale reportlab: pip install reportlab")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        if not filename:
            return

        try:
            self._mostrar_progresso(True)
            
            if self.styles is None:
                self.styles = getSampleStyleSheet()
            
            doc = SimpleDocTemplate(filename, pagesize=A4,
                                  topMargin=2*cm, bottomMargin=2*cm,
                                  leftMargin=2*cm, rightMargin=2*cm)
            story = []
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                textColor=colors.HexColor('#2c3e50')
            )
            
            story.append(Paragraph(f"RELATÓRIO DE {tipo.upper()}", title_style))
            story.append(Paragraph(f"Período: {data_inicio} a {data_fim}", self.styles['Normal']))
            story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            conn = self._conectar_db()
            c = conn.cursor()
            
            if tipo == "clientes":
                c.execute("""
                    SELECT id, nome, email, telefone, date(created_at) 
                    FROM clientes 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    ORDER BY created_at DESC
                """, (data_inicio, data_fim))
                dados = c.fetchall()
                
                if dados:
                    story.append(Paragraph("LISTA DE CLIENTES", self.styles['Heading2']))
                    data = [['ID', 'Nome', 'Email', 'Telefone', 'Data Cadastro']]
                    for linha in dados:
                        data.append([str(x) if x is not None else '' for x in linha])
                    
                    table = Table(data, repeatRows=1)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,0), 10),
                        ('FONTSIZE', (0,1), (-1,-1), 8),
                        ('BOTTOMPADDING', (0,0), (-1,0), 12),
                        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                        ('GRID', (0,0), (-1,-1), 1, colors.black)
                    ]))
                    story.append(table)
                else:
                    story.append(Paragraph("Nenhum cliente encontrado no período.", self.styles['Normal']))
                    
            elif tipo == "pedidos":
                query = """
                    SELECT p.id, c.nome, p.total, p.status, date(p.created_at) 
                    FROM pedidos p 
                    LEFT JOIN clientes c ON p.cliente_id = c.id
                    WHERE date(p.created_at) BETWEEN ? AND ?
                """
                params = [data_inicio, data_fim]
                if status != "Todos":
                    query += " AND p.status = ?"
                    params.append(status)
                query += " ORDER BY p.created_at DESC"
                
                c.execute(query, params)
                dados = c.fetchall()
                
                if dados:
                    story.append(Paragraph("LISTA DE PEDIDOS", self.styles['Heading2']))
                    data = [['ID', 'Cliente', 'Total', 'Status', 'Data']]
                    for linha in dados:
                        data.append([
                            str(linha[0]),
                            linha[1] or '',
                            f"R$ {linha[2]:.2f}",
                            linha[3] or '',
                            linha[4]
                        ])
                    
                    table = Table(data, repeatRows=1)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2ecc71')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,0), 10),
                        ('FONTSIZE', (0,1), (-1,-1), 8),
                        ('BOTTOMPADDING', (0,0), (-1,0), 12),
                        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                        ('GRID', (0,0), (-1,-1), 1, colors.black)
                    ]))
                    story.append(table)
                else:
                    story.append(Paragraph("Nenhum pedido encontrado no período.", self.styles['Normal']))
            
            elif tipo == "financeiro":
                c.execute("""
                    SELECT date(created_at), COUNT(*), SUM(total), AVG(total) 
                    FROM pedidos 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    GROUP BY date(created_at) 
                    ORDER BY date(created_at)
                """, (data_inicio, data_fim))
                dados = c.fetchall()
                
                if dados:
                    story.append(Paragraph("EVOLUÇÃO FINANCEIRA DIÁRIA", self.styles['Heading2']))
                    data = [['Data', 'Pedidos', 'Faturamento', 'Ticket Médio']]
                    for linha in dados:
                        data.append([
                            linha[0],
                            str(linha[1]),
                            self._formatar_moeda(linha[2] or 0),
                            self._formatar_moeda(linha[3] or 0)
                        ])
                    
                    table = Table(data, repeatRows=1)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e74c3c')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,0), 10),
                        ('FONTSIZE', (0,1), (-1,-1), 8),
                        ('BOTTOMPADDING', (0,0), (-1,0), 12),
                        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                        ('GRID', (0,0), (-1,-1), 1, colors.black)
                    ]))
                    story.append(table)
                else:
                    story.append(Paragraph("Nenhum dado financeiro no período.", self.styles['Normal']))
            
            elif tipo == "estatisticas":
                c.execute("SELECT COUNT(*) FROM clientes")
                total_clientes = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM pedidos")
                total_pedidos = c.fetchone()[0]
                c.execute("SELECT COUNT(*), SUM(total), AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                         (data_inicio, data_fim))
                stats = c.fetchone()
                
                story.append(Paragraph("ESTATÍSTICAS GERAIS", self.styles['Heading2']))
                
                estatisticas = [
                    ("Total de Clientes", str(total_clientes)),
                    ("Total de Pedidos", str(total_pedidos)),
                    ("Pedidos no Período", str(stats[0] or 0)),
                    ("Faturamento do Período", self._formatar_moeda(stats[1] or 0)),
                    ("Ticket Médio", self._formatar_moeda(stats[2] or 0))
                ]
                
                for titulo, valor in estatisticas:
                    story.append(Paragraph(f"<b>{titulo}:</b> {valor}", self.styles['Normal']))
                    story.append(Spacer(1, 5))
            
            conn.close()
            story.append(Spacer(1, 20))
            story.append(Paragraph("Relatório gerado automaticamente pelo Sistema de Gestão", 
                                 self.styles['Italic']))
            
            doc.build(story)
            messagebox.showinfo("PDF Exportado", f"Relatório {tipo} exportado com sucesso:\n{filename}")
            log_operacao("RELATORIOS", f"PDF exportado: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {e}")
            log_erro(f"Erro ao exportar PDF: {e}")
        finally:
            self._mostrar_progresso(False)

    def _exportar_pdf_geral_completo(self, data_inicio, data_fim, status="Todos"):
        """Exporta relatório geral completo em PDF"""
        if not REPORTLAB_DISPONIVEL:
            messagebox.showerror("PDF Não Disponível", "Instale reportlab: pip install reportlab")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"relatorio_geral_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        if not filename:
            return

        try:
            self._mostrar_progresso(True)
            
            if self.styles is None:
                self.styles = getSampleStyleSheet()
            
            doc = SimpleDocTemplate(filename, pagesize=A4,
                                  topMargin=2*cm, bottomMargin=2*cm,
                                  leftMargin=2*cm, rightMargin=2*cm)
            story = []
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.HexColor('#2c3e50'),
                alignment=1
            )
            
            story.append(Paragraph("RELATÓRIO GERAL COMPLETO", title_style))
            story.append(Paragraph(f"Período: {data_inicio} a {data_fim}", self.styles['Heading2']))
            story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", self.styles['Normal']))
            story.append(Spacer(1, 30))
            
            conn = self._conectar_db()
            c = conn.cursor()
            
            # RESUMO EXECUTIVO
            story.append(Paragraph("RESUMO EXECUTIVO", self.styles['Heading2']))
            story.append(Spacer(1, 10))
            
            c.execute("SELECT COUNT(*) FROM clientes WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            novos_clientes = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            total_pedidos = c.fetchone()[0]
            
            c.execute("SELECT SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            faturamento_total = c.fetchone()[0] or 0
            
            c.execute("SELECT AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            ticket_medio = c.fetchone()[0] or 0
            
            resumo_data = [
                ['Métrica', 'Valor'],
                ['Novos Clientes', str(novos_clientes)],
                ['Total de Pedidos', str(total_pedidos)],
                ['Faturamento Total', f"R$ {faturamento_total:.2f}"],
                ['Ticket Médio', f"R$ {ticket_medio:.2f}"]
            ]
            
            resumo_table = Table(resumo_data)
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('FONTSIZE', (0,1), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(resumo_table)
            story.append(Spacer(1, 30))
            
            # CLIENTES
            story.append(Paragraph("CLIENTES - ÚLTIMOS CADASTROS", self.styles['Heading2']))
            c.execute("""
                SELECT id, nome, email, date(created_at) 
                FROM clientes 
                WHERE date(created_at) BETWEEN ? AND ? 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (data_inicio, data_fim))
            clientes = c.fetchall()
            
            if clientes:
                clientes_data = [['ID', 'Nome', 'Email', 'Data Cadastro']]
                for cliente in clientes:
                    clientes_data.append([str(x) if x is not None else '' for x in cliente])
                
                clientes_table = Table(clientes_data, repeatRows=1)
                clientes_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2ecc71')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 9),
                    ('FONTSIZE', (0,1), (-1,-1), 8),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                story.append(clientes_table)
            else:
                story.append(Paragraph("Nenhum cliente cadastrado no período.", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # PEDIDOS
            story.append(Paragraph("PEDIDOS - ÚLTIMOS REGISTROS", self.styles['Heading2']))
            query_pedidos = """
                SELECT p.id, c.nome, p.total, p.status, date(p.created_at) 
                FROM pedidos p 
                LEFT JOIN clientes c ON p.cliente_id = c.id
                WHERE date(p.created_at) BETWEEN ? AND ?
            """
            params = [data_inicio, data_fim]
            if status != "Todos":
                query_pedidos += " AND p.status = ?"
                params.append(status)
            query_pedidos += " ORDER BY p.created_at DESC LIMIT 10"
            
            c.execute(query_pedidos, params)
            pedidos = c.fetchall()
            
            if pedidos:
                pedidos_data = [['ID', 'Cliente', 'Total', 'Status', 'Data']]
                for pedido in pedidos:
                    pedidos_data.append([
                        str(pedido[0]),
                        pedido[1] or '',
                        self._formatar_moeda(pedido[2]),
                        pedido[3] or '',
                        pedido[4]
                    ])
                
                pedidos_table = Table(pedidos_data, repeatRows=1)
                pedidos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 9),
                    ('FONTSIZE', (0,1), (-1,-1), 8),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                story.append(pedidos_table)
            else:
                story.append(Paragraph("Nenhum pedido encontrado no período.", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # ESTATÍSTICAS COMPLETAS
            story.append(Paragraph("ESTATÍSTICAS DETALHADAS", self.styles['Heading2']))
            
            c.execute("SELECT COUNT(*) FROM clientes")
            total_clientes_geral = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM pedidos")
            total_pedidos_geral = c.fetchone()[0]
            c.execute("SELECT COUNT(*), SUM(total), AVG(total), MIN(total), MAX(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                     (data_inicio, data_fim))
            stats_detalhadas = c.fetchone()
            
            estatisticas_data = [
                ['Métrica', 'Valor'],
                ['Base Total de Clientes', str(total_clientes_geral)],
                ['Total Geral de Pedidos', str(total_pedidos_geral)],
                ['Pedidos no Período', str(stats_detalhadas[0] or 0)],
                ['Faturamento Total', self._formatar_moeda(stats_detalhadas[1] or 0)],
                ['Ticket Médio', self._formatar_moeda(stats_detalhadas[2] or 0)],
                ['Menor Pedido', self._formatar_moeda(stats_detalhadas[3] or 0)],
                ['Maior Pedido', self._formatar_moeda(stats_detalhadas[4] or 0)]
            ]
            
            estatisticas_table = Table(estatisticas_data)
            estatisticas_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#9b59b6')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('FONTSIZE', (0,1), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('BACKGROUND', (0,1), (-1,-1), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(estatisticas_table)
            
            story.append(Spacer(1, 30))
            
            # GRÁFICOS
            story.append(Paragraph("ANÁLISES GRÁFICAS", self.styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Gerar gráficos como imagens temporárias
            try:
                # Gráfico 1: Evolução do Faturamento
                c.execute("""
                    SELECT date(created_at), SUM(total) 
                    FROM pedidos 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    GROUP BY date(created_at) 
                    ORDER BY date(created_at)
                """, (data_inicio, data_fim))
                dados_evolucao = c.fetchall()
                
                if dados_evolucao:
                    fig1, ax1 = plt.subplots(figsize=(7, 3.5))
                    datas = [d[0] for d in dados_evolucao]
                    valores = [float(d[1] or 0) for d in dados_evolucao]
                    ax1.plot(datas, valores, marker='o', linewidth=2, color='#3498db', label='Faturamento')
                    ax1.set_title('Evolução do Faturamento Diário', fontsize=11, fontweight='bold')
                    ax1.set_ylabel('Faturamento (R$)', fontsize=9)
                    ax1.set_xlabel('Data', fontsize=9)
                    ax1.tick_params(axis='x', rotation=45, labelsize=7)
                    ax1.grid(True, alpha=0.3)
                    ax1.legend()
                    plt.tight_layout()
                    
                    # Salvar gráfico em memória (BytesIO) - SEM arquivo temporário
                    img1_reader = self._salvar_grafico_para_pdf(fig1, dpi=100)
                    plt.close(fig1)
                    
                    story.append(Paragraph("Gráfico 1: Evolução do Faturamento", self.styles['Heading3']))
                    story.append(Image(img1_reader, width=14*cm, height=7*cm))
                    story.append(Spacer(1, 15))
                
                # Gráfico 2: Distribuição por Status
                c.execute("""
                    SELECT status, COUNT(*) 
                    FROM pedidos 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    GROUP BY status
                """, (data_inicio, data_fim))
                dados_status = c.fetchall()
                
                if dados_status:
                    fig2, ax2 = plt.subplots(figsize=(6, 3.5))
                    status = [d[0] for d in dados_status]
                    quantidades = [d[1] for d in dados_status]
                    cores = ['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6']
                    
                    bars = ax2.bar(status, quantidades, color=cores[:len(status)], alpha=0.8, edgecolor='black')
                    ax2.set_title('Distribuição de Pedidos por Status', fontsize=11, fontweight='bold')
                    ax2.set_ylabel('Quantidade', fontsize=9)
                    ax2.tick_params(axis='x', labelsize=8)
                    ax2.grid(True, alpha=0.3, axis='y')
                    
                    for bar, valor in zip(bars, quantidades):
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                f'{valor}', ha='center', va='bottom', fontweight='bold', fontsize=8)
                    
                    plt.tight_layout()
                    
                    # Salvar gráfico em memória (BytesIO) - SEM arquivo temporário
                    img2_reader = self._salvar_grafico_para_pdf(fig2, dpi=100)
                    plt.close(fig2)
                    
                    story.append(Paragraph("Gráfico 2: Distribuição por Status", self.styles['Heading3']))
                    story.append(Image(img2_reader, width=12*cm, height=7*cm))
                    story.append(Spacer(1, 15))
                
                # Gráfico 3: Top 5 Clientes
                top_clientes_graf = self._obter_tabela_top_5_clientes(data_inicio, data_fim)
                if top_clientes_graf:
                    fig3, ax3 = plt.subplots(figsize=(7, 3.5))
                    nomes = [c[1][:15] + '...' if len(c[1]) > 15 else c[1] for c in top_clientes_graf]
                    valores = [float(c[4] or 0) for c in top_clientes_graf]
                    
                    bars = ax3.barh(nomes, valores, color='#e74c3c', alpha=0.8, edgecolor='black')
                    ax3.set_title('Top 5 Clientes por Valor Gasto', fontsize=11, fontweight='bold')
                    ax3.set_xlabel('Valor Total (R$)', fontsize=9)
                    ax3.tick_params(axis='y', labelsize=8)
                    ax3.grid(True, alpha=0.3, axis='x')
                    
                    for bar, valor in zip(bars, valores):
                        width = bar.get_width()
                        ax3.text(width + max(valores)*0.01, bar.get_y() + bar.get_height()/2.,
                                f'R$ {valor:.2f}', ha='left', va='center', fontweight='bold', fontsize=7)
                    
                    plt.tight_layout()
                    
                    # Salvar gráfico em memória (BytesIO) - SEM arquivo temporário
                    img3_reader = self._salvar_grafico_para_pdf(fig3, dpi=100)
                    plt.close(fig3)
                    
                    story.append(Paragraph("Gráfico 3: Top 5 Clientes", self.styles['Heading3']))
                    story.append(Image(img3_reader, width=14*cm, height=7*cm))
                    story.append(Spacer(1, 15))
                        
            except Exception as e:
                story.append(Paragraph(f"Nota: Alguns gráficos não puderam ser gerados ({str(e)})", self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            story.append(Spacer(1, 30))
            story.append(Paragraph("*** FIM DO RELATÓRIO ***", self.styles['Heading2']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Relatório gerado automaticamente - Sistema de Gestão Comercial", 
                                 self.styles['Italic']))
            
            conn.close()
            doc.build(story)
            messagebox.showinfo("PDF Exportado", f"Relatório geral exportado com sucesso:\n{filename}")
            log_operacao("RELATORIOS", f"PDF geral exportado: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar PDF geral: {e}")
            log_erro(f"Erro ao exportar PDF geral: {e}")
        finally:
            self._mostrar_progresso(False)

    def _exportar_pdf_com_ia(self, tipo, data_inicio, data_fim, status="Todos"):
        """Exporta PDF com análise da IA incorporada"""
        if not REPORTLAB_DISPONIVEL:
            messagebox.showerror("PDF Não Disponível", "Instale reportlab: pip install reportlab")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"relatorio_ia_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        if not filename:
            return
            
        def gerar_pdf_com_ia():
            try:
                self._mostrar_progresso(True)
                
                dados_ia = self._coletar_dados_para_ia(data_inicio, data_fim)
                pergunta = f"""
                Com base nestes dados de negócio, forneça uma análise executiva completa incluindo:
                - Resumo executivo
                - Análise de crescimento
                - Identificação de riscos
                - Oportunidades
                - Plano de ação
                - Estimativas de crescimento

                Dados: {dados_ia}
                """
                
                analise_ia, erro_ia = agente_ia.enviar_pergunta_com_contexto(pergunta)
                
                if erro_ia:
                    self.master.after(0, lambda: messagebox.showerror("Erro IA", f"Erro na análise: {erro_ia}"))
                    return
                
                self.master.after(0, lambda: self._criar_pdf_com_ia(filename, tipo, data_inicio, data_fim, status, analise_ia))
                
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Erro", f"Erro ao gerar PDF com IA: {e}"))
            finally:
                self.master.after(0, lambda: self._mostrar_progresso(False))

        threading.Thread(target=gerar_pdf_com_ia, daemon=True).start()

    def _criar_pdf_com_ia(self, filename, tipo, data_inicio, data_fim, status, analise_ia):
        """Cria o PDF com a análise da IA incorporada + gráficos e tabelas completas"""
        try:
            if self.styles is None:
                self.styles = getSampleStyleSheet()
                
            doc = SimpleDocTemplate(filename, pagesize=A4, 
                                   leftMargin=1.5*cm, rightMargin=1.5*cm, 
                                   topMargin=1.5*cm, bottomMargin=1.5*cm)
            story = []
            
            # CABEÇALHO COM FUNDO AZUL
            header_style = ParagraphStyle('header', 
                                        parent=self.styles['Heading1'], 
                                        alignment=1,  # Centralizado
                                        fontSize=18, 
                                        textColor=colors.white,
                                        spaceAfter=10)
            
            header_data = [[Paragraph(f"RELATÓRIO DE {tipo.upper()}", header_style)]]
            header_table = Table(header_data, colWidths=[18*cm])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1e3a8a')),
                ('TOPPADDING', (0,0), (-1,-1), 15),
                ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 5))
            
            # Info do período em tabela
            info_style = ParagraphStyle('info', parent=self.styles['Normal'], fontSize=9, textColor=colors.HexColor('#374151'))
            info_data = [[
                Paragraph(f"<b>Período:</b> {data_inicio} a {data_fim}", info_style),
                Paragraph(f"<b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", info_style)
            ]]
            info_table = Table(info_data, colWidths=[9*cm, 9*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f3f4f6')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            conn = self._conectar_db()
            c = conn.cursor()
            
            # 1. RESUMO EXECUTIVO - CARDS EM LINHA
            section_style = ParagraphStyle('section', 
                                         parent=self.styles['Heading2'], 
                                         fontSize=14,
                                         textColor=colors.HexColor('#1e3a8a'),
                                         spaceAfter=10,
                                         leftIndent=0)
            
            story.append(Paragraph("RESUMO EXECUTIVO", section_style))
            story.append(Spacer(1, 10))
            
            c.execute("SELECT COUNT(*) FROM clientes WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            novos_clientes = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            total_pedidos = c.fetchone()[0]
            
            c.execute("SELECT SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            faturamento_total = c.fetchone()[0] or 0
            
            c.execute("SELECT AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
            ticket_medio = c.fetchone()[0] or 0
            
            # Cards em formato de 4 colunas
            card_label_style = ParagraphStyle('card_label', parent=self.styles['Normal'], 
                                            fontSize=8, textColor=colors.HexColor('#6b7280'), alignment=1)
            card_value_style = ParagraphStyle('card_value', parent=self.styles['Normal'], 
                                            fontSize=16, textColor=colors.HexColor('#1e3a8a'), 
                                            fontName='Helvetica-Bold', alignment=1)
            
            cards_data = [
                [
                    Paragraph("Novos Clientes", card_label_style),
                    Paragraph("Total de Pedidos", card_label_style),
                    Paragraph("Faturamento Total", card_label_style),
                    Paragraph("Ticket Médio", card_label_style)
                ],
                [
                    Paragraph(str(novos_clientes), card_value_style),
                    Paragraph(str(total_pedidos), card_value_style),
                    Paragraph(f"R$ {faturamento_total:,.2f}", card_value_style),
                    Paragraph(f"R$ {ticket_medio:,.2f}", card_value_style)
                ]
            ]
            
            cards_table = Table(cards_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
            cards_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
                ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
                ('TOPPADDING', (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ]))
            story.append(cards_table)
            story.append(Spacer(1, 25))
            
            # 2. CLIENTES CADASTRADOS
            story.append(Paragraph("CLIENTES CADASTRADOS NO PERÍODO", section_style))
            story.append(Spacer(1, 10))
            
            clientes = self._obter_tabela_clientes_cadastrados(data_inicio, data_fim)
            if clientes:
                clientes_data = [['ID', 'Nome', 'Email', 'Telefone', 'Data', 'Pedidos', 'Total Gasto']]
                for cliente in clientes[:15]:
                    clientes_data.append([
                        str(cliente[0]),
                        (cliente[1][:18] + '...') if len(cliente[1]) > 18 else cliente[1],
                        (cliente[2][:22] + '...') if len(cliente[2]) > 22 else cliente[2],
                        cliente[3] or '',
                        cliente[4],
                        str(cliente[5] or 0),
                        f"R$ {cliente[6]:.2f}" if cliente[6] else "R$ 0"
                    ])
                
                clientes_table = Table(clientes_data, repeatRows=1, colWidths=[1*cm, 3*cm, 3.5*cm, 2.5*cm, 2*cm, 1.5*cm, 2*cm])
                clientes_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('ALIGN', (5,0), (6,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 8),
                    ('FONTSIZE', (0,1), (-1,-1), 7),
                    ('TOPPADDING', (0,0), (-1,0), 8),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('TOPPADDING', (0,1), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                    ('BACKGROUND', (0,1), (-1,-1), colors.white),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb'))
                ]))
                story.append(clientes_table)
            else:
                story.append(Paragraph("Nenhum cliente cadastrado no período.", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # 3. TOP 5 CLIENTES
            story.append(Paragraph("TOP 5 CLIENTES - MAIOR VALOR GASTO", section_style))
            story.append(Spacer(1, 10))
            
            top_clientes = self._obter_tabela_top_5_clientes(data_inicio, data_fim)
            if top_clientes:
                top_clientes_data = [['Rank', 'Nome', 'Email', 'Pedidos', 'Valor Total', 'Ticket Médio']]
                rank = 1
                for cliente in top_clientes:
                    top_clientes_data.append([
                        f"#{rank}",
                        (cliente[1][:22] + '...') if cliente[1] and len(cliente[1]) > 22 else (cliente[1] or ''),
                        (cliente[2][:25] + '...') if cliente[2] and len(cliente[2]) > 25 else (cliente[2] or ''),
                        str(cliente[3]),
                        self._formatar_moeda(cliente[4]) if cliente[4] else "R$ 0,00",
                        self._formatar_moeda(cliente[5]) if cliente[5] else "R$ 0,00"
                    ])
                    rank += 1
                
                top_clientes_table = Table(top_clientes_data, repeatRows=1, colWidths=[1.5*cm, 4*cm, 4.5*cm, 2*cm, 2.5*cm, 2.5*cm])
                top_clientes_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#059669')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('ALIGN', (0,0), (0,-1), 'CENTER'),
                    ('ALIGN', (3,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 8),
                    ('FONTSIZE', (0,1), (-1,-1), 7),
                    ('TOPPADDING', (0,0), (-1,0), 8),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('TOPPADDING', (0,1), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                    ('BACKGROUND', (0,1), (-1,-1), colors.white),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0fdf4')]),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb'))
                ]))
                story.append(top_clientes_table)
            
            story.append(Spacer(1, 20))
            
            # 4. PEDIDOS DETALHADOS
            story.append(Paragraph("PEDIDOS RECENTES", section_style))
            story.append(Spacer(1, 10))
            
            pedidos = self._obter_tabela_pedidos_completa(data_inicio, data_fim, status)
            if pedidos:
                pedidos_data = [['ID', 'Cliente', 'Valor', 'Status', 'Data', 'Itens']]
                for pedido in pedidos[:15]:
                    pedidos_data.append([
                        str(pedido[0]),
                        (pedido[5][:25] + '...') if pedido[5] and len(pedido[5]) > 25 else (pedido[5] or 'N/A'),
                        f"R$ {pedido[1]:.2f}",
                        pedido[2] or '',
                        pedido[3],
                        str(pedido[8] or 0)
                    ])
                
                pedidos_table = Table(pedidos_data, repeatRows=1, colWidths=[1*cm, 4.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 1.5*cm])
                pedidos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#7c3aed')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('ALIGN', (0,0), (0,-1), 'CENTER'),
                    ('ALIGN', (2,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 8),
                    ('FONTSIZE', (0,1), (-1,-1), 7),
                    ('TOPPADDING', (0,0), (-1,0), 8),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('TOPPADDING', (0,1), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                    ('BACKGROUND', (0,1), (-1,-1), colors.white),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#faf5ff')]),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb'))
                ]))
                story.append(pedidos_table)
            
            story.append(Spacer(1, 30))
            
            # 5. GRÁFICOS
            story.append(Paragraph("ANÁLISES GRÁFICAS", section_style))
            story.append(Spacer(1, 15))
            
            try:
                # Gráfico 1: Evolução do Faturamento
                c.execute("""
                    SELECT date(created_at), SUM(total) 
                    FROM pedidos 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    GROUP BY date(created_at) 
                    ORDER BY date(created_at)
                """, (data_inicio, data_fim))
                dados_evolucao = c.fetchall()
                
                if dados_evolucao:
                    fig1, ax1 = plt.subplots(figsize=(8, 4))
                    datas = [d[0] for d in dados_evolucao]
                    valores = [float(d[1] or 0) for d in dados_evolucao]
                    ax1.plot(datas, valores, marker='o', linewidth=2.5, color='#1e3a8a', markersize=6, label='Faturamento')
                    ax1.fill_between(datas, valores, alpha=0.2, color='#1e3a8a')
                    ax1.set_title('Evolução do Faturamento Diário', fontsize=12, fontweight='bold', color='#1e3a8a', pad=15)
                    ax1.set_ylabel('Faturamento (R$)', fontsize=10, fontweight='bold')
                    ax1.set_xlabel('Data', fontsize=10, fontweight='bold')
                    ax1.tick_params(axis='x', rotation=45, labelsize=8)
                    ax1.tick_params(axis='y', labelsize=8)
                    ax1.grid(True, alpha=0.2, linestyle='--')
                    ax1.spines['top'].set_visible(False)
                    ax1.spines['right'].set_visible(False)
                    plt.tight_layout()
                    
                    # Salvar gráfico em memória (BytesIO) - SEM arquivo temporário
                    img1_reader = self._salvar_grafico_para_pdf(fig1, dpi=120)
                    plt.close(fig1)
                    
                    graph_title_style = ParagraphStyle('graph_title', parent=self.styles['Normal'], 
                                                      fontSize=10, textColor=colors.HexColor('#374151'),
                                                      fontName='Helvetica-Bold', spaceAfter=8)
                    story.append(Paragraph("Gráfico: Evolução do Faturamento", graph_title_style))
                    story.append(Image(img1_reader, width=16*cm, height=8*cm))
                    story.append(Spacer(1, 20))
                
                # Gráfico 2: Distribuição por Status
                c.execute("""
                    SELECT status, COUNT(*) 
                    FROM pedidos 
                    WHERE date(created_at) BETWEEN ? AND ? 
                    GROUP BY status
                """, (data_inicio, data_fim))
                dados_status = c.fetchall()
                
                if dados_status:
                    fig2, ax2 = plt.subplots(figsize=(8, 4))
                    status_list = [d[0] for d in dados_status]
                    quantidades = [d[1] for d in dados_status]
                    cores = ['#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6']
                    
                    bars = ax2.bar(status_list, quantidades, color=cores[:len(status_list)], alpha=0.85, edgecolor='white', linewidth=2)
                    ax2.set_title('Distribuição de Pedidos por Status', fontsize=12, fontweight='bold', color='#1e3a8a', pad=15)
                    ax2.set_ylabel('Quantidade', fontsize=10, fontweight='bold')
                    ax2.tick_params(axis='x', labelsize=9)
                    ax2.tick_params(axis='y', labelsize=8)
                    ax2.grid(True, alpha=0.2, axis='y', linestyle='--')
                    ax2.spines['top'].set_visible(False)
                    ax2.spines['right'].set_visible(False)
                    
                    for bar, valor in zip(bars, quantidades):
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                                f'{valor}', ha='center', va='bottom', fontweight='bold', fontsize=10)
                    
                    plt.tight_layout()
                    
                    # Salvar gráfico em memória (BytesIO) - SEM arquivo temporário
                    img2_reader = self._salvar_grafico_para_pdf(fig2, dpi=120)
                    plt.close(fig2)
                    
                    story.append(Paragraph("Gráfico: Distribuição por Status", graph_title_style))
                    story.append(Image(img2_reader, width=16*cm, height=8*cm))
                    story.append(Spacer(1, 20))
                
                # Gráfico 3: Top 5 Clientes
                if top_clientes:
                    fig3, ax3 = plt.subplots(figsize=(8, 4))
                    nomes = [c[1][:18] + '...' if len(c[1]) > 18 else c[1] for c in top_clientes]
                    valores_graf = [float(c[4] or 0) for c in top_clientes]
                    
                    bars = ax3.barh(nomes, valores_graf, color='#059669', alpha=0.85, edgecolor='white', linewidth=2)
                    ax3.set_title('Top 5 Clientes por Valor Gasto', fontsize=12, fontweight='bold', color='#1e3a8a', pad=15)
                    ax3.set_xlabel('Valor Total (R$)', fontsize=10, fontweight='bold')
                    ax3.tick_params(axis='y', labelsize=9)
                    ax3.tick_params(axis='x', labelsize=8)
                    ax3.grid(True, alpha=0.2, axis='x', linestyle='--')
                    ax3.spines['top'].set_visible(False)
                    ax3.spines['right'].set_visible(False)
                    
                    for bar, valor in zip(bars, valores_graf):
                        width = bar.get_width()
                        ax3.text(width + max(valores_graf)*0.02, bar.get_y() + bar.get_height()/2.,
                                f'R$ {valor:,.2f}', ha='left', va='center', fontweight='bold', fontsize=9)
                    
                    plt.tight_layout()
                    
                    # Salvar gráfico em memória (BytesIO) - SEM arquivo temporário
                    img3_reader = self._salvar_grafico_para_pdf(fig3, dpi=120)
                    plt.close(fig3)
                    
                    story.append(Paragraph("Gráfico: Top 5 Clientes", graph_title_style))
                    story.append(Image(img3_reader, width=16*cm, height=8*cm))
                    story.append(Spacer(1, 25))
                        
            except Exception as e:
                story.append(Paragraph(f"⚠ Alguns gráficos não puderam ser gerados: {str(e)}", self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            # 6. ANÁLISE DA IA
            story.append(Spacer(1, 30))
            
            ia_header_style = ParagraphStyle('ia_header', 
                                           parent=self.styles['Heading2'], 
                                           fontSize=14,
                                           textColor=colors.white,
                                           alignment=0)
            
            ia_header_data = [[Paragraph("ANÁLISE DA INTELIGÊNCIA ARTIFICIAL", ia_header_style)]]
            ia_header_table = Table(ia_header_data, colWidths=[18*cm])
            ia_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#059669')),
                ('TOPPADDING', (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('LEFTPADDING', (0,0), (-1,-1), 15),
            ]))
            story.append(ia_header_table)
            story.append(Spacer(1, 15))
            
            ia_content_style = ParagraphStyle('ia_content', 
                                            parent=self.styles['Normal'], 
                                            fontSize=9,
                                            textColor=colors.HexColor('#1f2937'),
                                            alignment=4,  # Justificado
                                            leading=14)
            
            paragrafos = analise_ia.split('\n')
            for p in paragrafos:
                if p.strip():
                    story.append(Paragraph(p.strip(), ia_content_style))
                    story.append(Spacer(1, 8))
            
            # RODAPÉ
            conn.close()
            story.append(Spacer(1, 30))
            
            footer_style = ParagraphStyle('footer', 
                                        parent=self.styles['Normal'], 
                                        fontSize=8,
                                        textColor=colors.HexColor('#6b7280'),
                                        alignment=1)
            story.append(Paragraph(f"Relatório gerado pelo Sistema de Gestão em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Relatório gerado automaticamente com análise de IA - Sistema de Gestão Comercial", 
                                 self.styles['Italic']))
            
            doc.build(story)
            messagebox.showinfo("PDF Completo + IA Exportado", 
                              f"Relatório completo com análise IA, tabelas e gráficos exportado:\n{filename}")
            log_operacao("RELATORIOS", f"PDF IA completo exportado: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar PDF com IA: {e}")
            log_erro(f"Erro ao criar PDF com IA: {e}")

    def _coletar_dados_para_ia(self, data_inicio, data_fim):
        """Coleta dados estruturados para análise da IA"""
        conn = self._conectar_db()
        c = conn.cursor()
        
        dados = {
            'periodo': f"{data_inicio} a {data_fim}",
            'clientes': {},
            'pedidos': {},
            'financeiro': {},
            'estatisticas': {}
        }
        
        c.execute("SELECT COUNT(*) FROM clientes WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        dados['clientes']['novos'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM clientes")
        dados['clientes']['total'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*), SUM(total), AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        pedidos_info = c.fetchone()
        dados['pedidos'] = {
            'quantidade': pedidos_info[0],
            'faturamento': float(pedidos_info[1] or 0),
            'ticket_medio': float(pedidos_info[2] or 0)
        }
        
        c.execute("SELECT status, COUNT(*) FROM pedidos WHERE date(created_at) BETWEEN ? AND ? GROUP BY status", 
                 (data_inicio, data_fim))
        dados['pedidos']['status'] = dict(c.fetchall())
        
        c.execute("""SELECT date(created_at), COUNT(*), SUM(total) FROM pedidos 
                     WHERE date(created_at) BETWEEN ? AND ? GROUP BY date(created_at) 
                     ORDER BY date(created_at)""", (data_inicio, data_fim))
        dados['financeiro']['evolucao_diaria'] = c.fetchall()
        
        conn.close()
        
        return json.dumps(dados, indent=2, ensure_ascii=False)

    def _analise_completa_ia(self):
        """Gera análise completa com IA incluindo plano de ação"""
        try:
            data_inicio, data_fim = self._obter_datas_periodo()
            
            dados_completos = self._coletar_dados_analise_completa(data_inicio, data_fim)
            
            pergunta = f"""
            Com base nestes dados de negócio, forneça uma análise executiva completa:

            DADOS DO PERÍODO {data_inicio} a {data_fim}:
            {dados_completos}

            ESTRUTURA DA ANÁLISE:

            1. RESUMO EXECUTIVO
            - Performance geral do período
            - Principais conquistas
            - Pontos de atenção

            2. ANÁLISE DE CRESCIMENTO
            - Taxas de crescimento (clientes, vendas, faturamento)
            - Comparativo com períodos anteriores
            - Tendências identificadas

            3. IDENTIFICAÇÃO DE RISCOS
            - Principais riscos operacionais
            - Pontos fracos identificados
            - Ameaças ao crescimento

            4. OPORTUNIDADES
            - Áreas com maior potencial
            - Segmentos promissores
            - Oportunidades de otimização

            5. PLANO DE AÇÃO
            - Ações prioritárias para os próximos 30 dias
            - Estratégias para os próximos 90 dias
            - Metas realistas para os próximos 6 meses

            6. ESTIMATIVAS DE CRESCIMENTO
            - Projeções conservadoras, realistas e otimistas
            - Fatores que podem impactar as projeções
            - Recomendações para maximizar resultados

            Forneça a análise em formato executivo, com dados concretos e recomendações acionáveis.
            """
            
            self._mostrar_progresso(True)
            
            def analise_ia_thread():
                try:
                    resposta, erro = agente_ia.enviar_pergunta_com_contexto(pergunta)
                    self.master.after(0, self._exibir_analise_completa_ia, resposta, erro, data_inicio, data_fim)
                except Exception as e:
                    self.master.after(0, lambda: messagebox.showerror("Erro IA", f"Erro na análise: {e}"))
                finally:
                    self.master.after(0, lambda: self._mostrar_progresso(False))
            
            threading.Thread(target=analise_ia_thread, daemon=True).start()
            
        except Exception as e:
            self._mostrar_progresso(False)
            messagebox.showerror("Erro", f"Erro ao gerar análise completa: {e}")

    def _coletar_dados_analise_completa(self, data_inicio, data_fim):
        """Coleta dados completos para análise da IA"""
        conn = self._conectar_db()
        c = conn.cursor()
        
        dados = {
            'periodo': f"{data_inicio} a {data_fim}",
            'clientes': {},
            'pedidos': {},
            'financeiro': {},
            'produtos': {},
            'comparativo': {}
        }
        
        # Dados de clientes
        c.execute("SELECT COUNT(*) FROM clientes WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        dados['clientes']['novos'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM clientes")
        dados['clientes']['total'] = c.fetchone()[0]
        
        # Dados de pedidos
        c.execute("SELECT COUNT(*), SUM(total), AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        pedidos_info = c.fetchone()
        dados['pedidos'] = {
            'quantidade': pedidos_info[0] or 0,
            'faturamento': float(pedidos_info[1] or 0),
            'ticket_medio': float(pedidos_info[2] or 0)
        }
        
        # Pedidos por status
        c.execute("SELECT status, COUNT(*) FROM pedidos WHERE date(created_at) BETWEEN ? AND ? GROUP BY status", 
                 (data_inicio, data_fim))
        dados['pedidos']['status'] = dict(c.fetchall())
        
        # Evolução diária
        c.execute("""SELECT date(created_at), COUNT(*), SUM(total) FROM pedidos 
                     WHERE date(created_at) BETWEEN ? AND ? GROUP BY date(created_at) 
                     ORDER BY date(created_at)""", (data_inicio, data_fim))
        dados['financeiro']['evolucao_diaria'] = c.fetchall()
        
        # Produtos mais vendidos
        try:
            c.execute("""SELECT p.nome, SUM(ip.quantidade), SUM(ip.quantidade * ip.preco_unit) 
                         FROM itens_pedido ip 
                         JOIN produtos p ON ip.produto_id = p.id 
                         JOIN pedidos ped ON ip.pedido_id = ped.id 
                         WHERE date(ped.created_at) BETWEEN ? AND ? 
                         GROUP BY p.id ORDER BY SUM(ip.quantidade) DESC LIMIT 10""", 
                     (data_inicio, data_fim))
            dados['produtos']['top_vendidos'] = c.fetchall()
        except:
            dados['produtos']['top_vendidos'] = []
        
        # Dados comparativos (período anterior)
        periodo_anterior_inicio = (datetime.strptime(data_inicio, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        periodo_anterior_fim = (datetime.strptime(data_inicio, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        
        c.execute("SELECT COUNT(*), SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (periodo_anterior_inicio, periodo_anterior_fim))
        periodo_anterior = c.fetchone()
        dados['comparativo'] = {
            'pedidos_anterior': periodo_anterior[0] or 0,
            'faturamento_anterior': float(periodo_anterior[1] or 0)
        }
        
        conn.close()
        
        return json.dumps(dados, indent=2, ensure_ascii=False)

    def _exibir_analise_completa_ia(self, resposta, erro, data_inicio, data_fim):
        """Exibe a análise completa da IA"""
        self._limpar_resultados()
        
        frame = ctk.CTkFrame(self.frame_resultados)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        titulo = ctk.CTkLabel(
            frame,
            text=f"🤖 ANÁLISE EXECUTIVA COMPLETA - {data_inicio} a {data_fim}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2b5797"
        )
        titulo.pack(pady=(0, 15))
        
        if erro:
            ctk.CTkLabel(
                frame,
                text=f"❌ Erro na análise: {erro}",
                text_color="#dc3545",
                font=ctk.CTkFont(size=12)
            ).pack(pady=10)
            return
        
        texto_area = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=12), wrap=tk.WORD)
        texto_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        texto_area.insert("1.0", resposta)
        texto_area.configure(state="disabled")

    def _gerar_graficos_detalhados(self):
        """Gera visualização detalhada apenas com gráficos"""
        try:
            data_inicio, data_fim = self._obter_datas_periodo()
            
            self._limpar_resultados()
            
            frame_scroll = ctk.CTkScrollableFrame(self.frame_resultados)
            frame_scroll.pack(fill=tk.BOTH, expand=True)
            
            titulo = ctk.CTkLabel(
                frame_scroll,
                text=f"📈 ANÁLISE GRÁFICA DETALHADA - {data_inicio} a {data_fim}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#2c3e50"
            )
            titulo.pack(pady=(10, 20))
            
            self._adicionar_secao_graficos_detalhados(frame_scroll, data_inicio, data_fim)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar gráficos: {e}")

    def _adicionar_secao_graficos_detalhados(self, parent, data_inicio, data_fim):
        """Adiciona seção com gráficos detalhados expandidos"""
        try:
            conn = self._conectar_db()
            c = conn.cursor()
            
            # Evolução diária de faturamento
            c.execute("""
                SELECT date(created_at), SUM(total) 
                FROM pedidos 
                WHERE date(created_at) BETWEEN ? AND ? 
                GROUP BY date(created_at) 
                ORDER BY date(created_at)
            """, (data_inicio, data_fim))
            dados_evolucao = c.fetchall()
            
            # Distribuição por status
            c.execute("""
                SELECT status, COUNT(*) 
                FROM pedidos 
                WHERE date(created_at) BETWEEN ? AND ? 
                GROUP BY status
            """, (data_inicio, data_fim))
            dados_status = c.fetchall()
            
            # Top clientes
            c.execute("""
                SELECT c.nome, COUNT(p.id), SUM(p.total)
                FROM clientes c
                JOIN pedidos p ON c.id = p.cliente_id
                WHERE date(p.created_at) BETWEEN ? AND ?
                GROUP BY c.id
                ORDER BY SUM(p.total) DESC
                LIMIT 8
            """, (data_inicio, data_fim))
            top_clientes = c.fetchall()
            
            # Evolução de novos clientes
            c.execute("""
                SELECT date(created_at), COUNT(*)
                FROM clientes
                WHERE date(created_at) BETWEEN ? AND ?
                GROUP BY date(created_at)
                ORDER BY date(created_at)
            """, (data_inicio, data_fim))
            evolucao_clientes = c.fetchall()
            
            conn.close()
            
            # Gráfico 1: Evolução do faturamento
            if dados_evolucao:
                frame_grafico1 = ctk.CTkFrame(parent)
                frame_grafico1.pack(fill=tk.X, pady=10, padx=10)
                
                ctk.CTkLabel(
                    frame_grafico1,
                    text="📊 EVOLUÇÃO DO FATURAMENTO DIÁRIO",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#3498db"
                ).pack(anchor="w", pady=(10, 5))
                
                fig1 = Figure(figsize=(12, 5), dpi=100)
                ax1 = fig1.add_subplot(111)
                
                datas = [d[0] for d in dados_evolucao]
                valores = [float(d[1] or 0) for d in dados_evolucao]
                
                ax1.plot(datas, valores, marker='o', linewidth=2, markersize=6, 
                        color='#3498db', label='Faturamento Diário')
                ax1.fill_between(datas, valores, alpha=0.3, color='#3498db')
                ax1.set_title('Evolução do Faturamento Diário', fontsize=14, fontweight='bold', pad=20)
                ax1.set_ylabel('Faturamento (R$)', fontsize=12, fontweight='bold')
                ax1.set_xlabel('Data', fontsize=12, fontweight='bold')
                ax1.grid(True, alpha=0.3)
                ax1.legend(fontsize=10)
                ax1.tick_params(axis='x', rotation=45)
                
                # Adicionar valor em cada ponto
                for i, (data, valor) in enumerate(zip(datas, valores)):
                    ax1.annotate(f'R$ {valor:,.0f}', (data, valor), 
                               textcoords="offset points", xytext=(0,10), 
                               ha='center', fontsize=8, fontweight='bold')
                
                fig1.tight_layout()
                
                canvas1 = FigureCanvasTkAgg(fig1, frame_grafico1)
                canvas1.draw()
                canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Gráfico 2: Distribuição por status
            if dados_status:
                frame_grafico2 = ctk.CTkFrame(parent)
                frame_grafico2.pack(fill=tk.X, pady=10, padx=10)
                
                ctk.CTkLabel(
                    frame_grafico2,
                    text="📋 DISTRIBUIÇÃO DE PEDIDOS POR STATUS",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#2ecc71"
                ).pack(anchor="w", pady=(10, 5))
                
                fig2 = Figure(figsize=(10, 6), dpi=100)
                ax2 = fig2.add_subplot(111)
                
                status = [d[0] for d in dados_status]
                quantidades = [d[1] for d in dados_status]
                cores = ['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6', '#34495e', '#9b59b6']
                
                bars = ax2.bar(status, quantidades, color=cores[:len(status)], alpha=0.8, edgecolor='black')
                ax2.set_title('Distribuição de Pedidos por Status', fontsize=14, fontweight='bold', pad=20)
                ax2.set_ylabel('Quantidade de Pedidos', fontsize=12, fontweight='bold')
                ax2.set_xlabel('Status', fontsize=12, fontweight='bold')
                
                # Adicionar valores e porcentagens nas barras
                total_pedidos = sum(quantidades)
                for bar, valor in zip(bars, quantidades):
                    height = bar.get_height()
                    porcentagem = (valor / total_pedidos) * 100
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{valor}\n({porcentagem:.1f}%)', 
                            ha='center', va='bottom', fontweight='bold', fontsize=9)
                
                fig2.tight_layout()
                
                canvas2 = FigureCanvasTkAgg(fig2, frame_grafico2)
                canvas2.draw()
                canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Gráfico 3: Top clientes
            if top_clientes:
                frame_grafico3 = ctk.CTkFrame(parent)
                frame_grafico3.pack(fill=tk.X, pady=10, padx=10)
                
                ctk.CTkLabel(
                    frame_grafico3,
                    text="🏆 TOP CLIENTES POR VALOR DE COMPRAS",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#e74c3c"
                ).pack(anchor="w", pady=(10, 5))
                
                fig3 = Figure(figsize=(12, 6), dpi=100)
                ax3 = fig3.add_subplot(111)
                
                clientes_nomes = [d[0][:20] + '...' if len(d[0]) > 20 else d[0] for d in top_clientes]
                valores_clientes = [float(d[2] or 0) for d in top_clientes]
                pedidos_clientes = [d[1] for d in top_clientes]
                
                y_pos = np.arange(len(clientes_nomes))
                
                bars = ax3.barh(y_pos, valores_clientes, color='#e74c3c', alpha=0.8, edgecolor='black')
                ax3.set_yticks(y_pos)
                ax3.set_yticklabels(clientes_nomes, fontsize=10)
                ax3.set_title('Top Clientes por Valor de Compras', fontsize=14, fontweight='bold', pad=20)
                ax3.set_xlabel('Valor Total Gasto (R$)', fontsize=12, fontweight='bold')
                
                # Adicionar valores nas barras
                for i, (bar, valor, pedidos) in enumerate(zip(bars, valores_clientes, pedidos_clientes)):
                    width = bar.get_width()
                    ax3.text(width + max(valores_clientes)*0.01, bar.get_y() + bar.get_height()/2.,
                            f'R$ {valor:,.0f}\n({pedidos} pedidos)', 
                            ha='left', va='center', fontweight='bold', fontsize=9)
                
                fig3.tight_layout()
                
                canvas3 = FigureCanvasTkAgg(fig3, frame_grafico3)
                canvas3.draw()
                canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Gráfico 4: Evolução de novos clientes
            if evolucao_clientes:
                frame_grafico4 = ctk.CTkFrame(parent)
                frame_grafico4.pack(fill=tk.X, pady=10, padx=10)
                
                ctk.CTkLabel(
                    frame_grafico4,
                    text="👥 EVOLUÇÃO DE NOVOS CLIENTES",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#9b59b6"
                ).pack(anchor="w", pady=(10, 5))
                
                fig4 = Figure(figsize=(12, 5), dpi=100)
                ax4 = fig4.add_subplot(111)
                
                datas_clientes = [d[0] for d in evolucao_clientes]
                novos_clientes = [d[1] for d in evolucao_clientes]
                
                ax4.bar(datas_clientes, novos_clientes, color='#9b59b6', alpha=0.8, edgecolor='black')
                ax4.set_title('Evolução de Novos Clientes por Dia', fontsize=14, fontweight='bold', pad=20)
                ax4.set_ylabel('Novos Clientes', fontsize=12, fontweight='bold')
                ax4.set_xlabel('Data', fontsize=12, fontweight='bold')
                ax4.tick_params(axis='x', rotation=45)
                ax4.grid(True, alpha=0.3)
                
                # Adicionar valores nas barras
                for i, (data, valor) in enumerate(zip(datas_clientes, novos_clientes)):
                    ax4.text(i, valor + 0.1, str(valor), 
                           ha='center', va='bottom', fontweight='bold', fontsize=9)
                
                fig4.tight_layout()
                
                canvas4 = FigureCanvasTkAgg(fig4, frame_grafico4)
                canvas4.draw()
                canvas4.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
        except Exception as e:
            ctk.CTkLabel(
                parent,
                text=f"Erro ao gerar gráficos: {str(e)}",
                text_color="#e74c3c",
                font=ctk.CTkFont(size=10)
            ).pack(pady=10)

    def _mostrar_relatorio_geral_completo(self, data_inicio, data_fim, status="Todos"):
        """Exibe relatório geral completo com tabelas, gráficos e análises"""
        self._limpar_resultados()
        
        frame_scroll = ctk.CTkScrollableFrame(self.frame_resultados)
        frame_scroll.pack(fill=tk.BOTH, expand=True)
        
        titulo = ctk.CTkLabel(
            frame_scroll,
            text=f"📊 RELATÓRIO GERAL COMPLETO - {data_inicio} a {data_fim}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2c3e50"
        )
        titulo.pack(pady=(10, 5))
        
        periodo_label = ctk.CTkLabel(
            frame_scroll,
            text=f"Período de análise: {data_inicio} à {data_fim}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        periodo_label.pack(pady=(0, 20))

        # 1. RESUMO EXECUTIVO
        self._adicionar_secao_resumo_executivo(frame_scroll, data_inicio, data_fim)
        
        # 2. DADOS DE CLIENTES
        self._adicionar_secao_clientes(frame_scroll, data_inicio, data_fim)
        
        # 3. DADOS DE PEDIDOS
        self._adicionar_secao_pedidos(frame_scroll, data_inicio, data_fim, status)
        
        # 4. ANÁLISE FINANCEIRA
        self._adicionar_secao_financeira(frame_scroll, data_inicio, data_fim)
        
        # 5. ESTATÍSTICAS E MÉTRICAS
        self._adicionar_secao_estatisticas(frame_scroll, data_inicio, data_fim)
        
        # 6. NOVAS TABELAS COMPLETAS
        self._adicionar_secao_tabelas_completas(frame_scroll, data_inicio, data_fim, status)
        
        # 7. GRÁFICOS DETALHADOS
        self._adicionar_secao_graficos(frame_scroll, data_inicio, data_fim)
        
        # 8. NOVOS GRÁFICOS ADICIONAIS
        self._adicionar_graficos_adicionais(frame_scroll, data_inicio, data_fim)
        
        # 9. ANÁLISE DE TENDÊNCIAS
        self._adicionar_secao_tendencias(frame_scroll, data_inicio, data_fim)
        
        # 10. PLANO DE AÇÃO
        self._adicionar_secao_plano_acao(frame_scroll, data_inicio, data_fim)

    def _adicionar_secao_resumo_executivo(self, parent, data_inicio, data_fim):
        """Adiciona seção de resumo executivo"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="🎯 RESUMO EXECUTIVO",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2b5797"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM clientes WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        novos_clientes = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        total_pedidos = c.fetchone()[0]
        
        c.execute("SELECT SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        faturamento_total = c.fetchone()[0] or 0
        
        c.execute("SELECT AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        ticket_medio = c.fetchone()[0] or 0
        
        conn.close()
        
        frame_metricas = ctk.CTkFrame(frame_secao)
        frame_metricas.pack(fill=tk.X, pady=10)
        
        metricas = [
            ("👥 Novos Clientes", novos_clientes, "#3498db", "Clientes cadastrados no período"),
            ("📦 Total de Pedidos", total_pedidos, "#2ecc71", "Volume total de vendas"),
            ("💰 Faturamento", f"R$ {faturamento_total:,.2f}", "#e74c3c", "Receita total gerada"),
            ("🎫 Ticket Médio", f"R$ {ticket_medio:,.2f}", "#9b59b6", "Valor médio por pedido")
        ]
        
        for i, (titulo, valor, cor, descricao) in enumerate(metricas):
            if i % 2 == 0:
                frame_linha = ctk.CTkFrame(frame_metricas)
                frame_linha.pack(fill=tk.X, pady=2)
            
            card = ctk.CTkFrame(
                frame_linha,
                border_width=1,
                border_color=cor,
                corner_radius=8
            )
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            ctk.CTkLabel(
                card,
                text=titulo,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=cor
            ).pack(pady=(8, 2))
            
            ctk.CTkLabel(
                card,
                text=str(valor),
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(pady=(0, 5))
            
            ctk.CTkLabel(
                card,
                text=descricao,
                font=ctk.CTkFont(size=9),
                text_color=("gray50", "gray70")
            ).pack(pady=(0, 8))

    def _adicionar_secao_clientes(self, parent, data_inicio, data_fim):
        """Adiciona seção de análise de clientes"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="👥 ANÁLISE DE CLIENTES",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3498db"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("""
            SELECT id, nome, email, telefone, date(created_at) 
            FROM clientes 
            WHERE date(created_at) BETWEEN ? AND ? 
            ORDER BY created_at DESC 
            LIMIT 15
        """, (data_inicio, data_fim))
        clientes = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM clientes WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        novos_clientes = c.fetchone()[0]
        
        conn.close()
        
        if clientes:
            frame_tabela = ctk.CTkFrame(frame_secao)
            frame_tabela.pack(fill=tk.X, pady=10)
            
            ctk.CTkLabel(
                frame_tabela,
                text=f"📋 Últimos {len(clientes)} Clientes Cadastrados",
                font=ctk.CTkFont(weight="bold")
            ).pack(anchor="w", pady=(0, 10))
            
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.X, padx=5, pady=5)
            
            cols = ('ID', 'Nome', 'Email', 'Telefone', 'Data Cadastro')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8)
            
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            for cliente in clientes:
                tree.insert('', tk.END, values=cliente)
        
        frame_metrics = ctk.CTkFrame(frame_secao)
        frame_metrics.pack(fill=tk.X, pady=10)
        
        metricas_clientes = [
            ("Total de Clientes", total_clientes),
            ("Novos no Período", novos_clientes),
            ("Taxa de Crescimento", f"{(novos_clientes/total_clientes*100 if total_clientes > 0 else 0):.1f}%")
        ]
        
        for titulo, valor in metricas_clientes:
            metric_frame = ctk.CTkFrame(frame_metrics)
            metric_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            ctk.CTkLabel(
                metric_frame,
                text=titulo,
                font=ctk.CTkFont(size=10)
            ).pack(pady=(5, 2))
            
            ctk.CTkLabel(
                metric_frame,
                text=str(valor),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#3498db"
            ).pack(pady=(0, 5))

    def _adicionar_secao_pedidos(self, parent, data_inicio, data_fim, status):
        """Adiciona seção de análise de pedidos"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="📦 ANÁLISE DE PEDIDOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2ecc71"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        conn = self._conectar_db()
        c = conn.cursor()
        
        query = """
            SELECT p.id, c.nome, p.total, p.status, date(p.created_at) 
            FROM pedidos p 
            LEFT JOIN clientes c ON p.cliente_id = c.id
            WHERE date(p.created_at) BETWEEN ? AND ?
        """
        params = [data_inicio, data_fim]
        
        if status != "Todos":
            query += " AND p.status = ?"
            params.append(status)
        
        query += " ORDER BY p.created_at DESC LIMIT 15"
        
        c.execute(query, params)
        pedidos = c.fetchall()
        
        c.execute("SELECT COUNT(*), SUM(total), AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        stats_pedidos = c.fetchone()
        
        c.execute("SELECT status, COUNT(*) FROM pedidos WHERE date(created_at) BETWEEN ? AND ? GROUP BY status", 
                 (data_inicio, data_fim))
        status_distribuicao = c.fetchall()
        
        conn.close()
        
        if pedidos:
            frame_tabela = ctk.CTkFrame(frame_secao)
            frame_tabela.pack(fill=tk.X, pady=10)
            
            ctk.CTkLabel(
                frame_tabela,
                text=f"📋 Últimos {len(pedidos)} Pedidos",
                font=ctk.CTkFont(weight="bold")
            ).pack(anchor="w", pady=(0, 10))
            
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.X, padx=5, pady=5)
            
            cols = ('ID', 'Cliente', 'Valor', 'Status', 'Data')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8)
            
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            for pedido in pedidos:
                tree.insert('', tk.END, values=(
                    pedido[0], 
                    pedido[1] or 'N/A', 
                    f"R$ {pedido[2]:,.2f}", 
                    pedido[3], 
                    pedido[4]
                ))
        
        total_pedidos = stats_pedidos[0] or 0
        faturamento = stats_pedidos[1] or 0
        ticket_medio = stats_pedidos[2] or 0
        
        frame_metrics = ctk.CTkFrame(frame_secao)
        frame_metrics.pack(fill=tk.X, pady=10)
        
        metricas_pedidos = [
            ("Total de Pedidos", total_pedidos),
            ("Faturamento", f"R$ {faturamento:,.2f}"),
            ("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        ]
        
        for titulo, valor in metricas_pedidos:
            metric_frame = ctk.CTkFrame(frame_metrics)
            metric_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            ctk.CTkLabel(
                metric_frame,
                text=titulo,
                font=ctk.CTkFont(size=10)
            ).pack(pady=(5, 2))
            
            ctk.CTkLabel(
                metric_frame,
                text=str(valor),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#2ecc71"
            ).pack(pady=(0, 5))
        
        if status_distribuicao:
            frame_status = ctk.CTkFrame(frame_secao)
            frame_status.pack(fill=tk.X, pady=10)
            
            ctk.CTkLabel(
                frame_status,
                text="📊 Distribuição por Status",
                font=ctk.CTkFont(weight="bold")
            ).pack(anchor="w", pady=(0, 5))
            
            for status_item, count in status_distribuicao:
                status_frame = ctk.CTkFrame(frame_status)
                status_frame.pack(fill=tk.X, padx=5, pady=2)
                
                ctk.CTkLabel(
                    status_frame,
                    text=f"{status_item}: {count} pedidos ({count/total_pedidos*100:.1f}%)",
                    font=ctk.CTkFont(size=10)
                ).pack(anchor="w", padx=10, pady=2)

    def _adicionar_secao_financeira(self, parent, data_inicio, data_fim):
        """Adiciona seção de análise financeira"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="💰 ANÁLISE FINANCEIRA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("""
            SELECT date(created_at), COUNT(*), SUM(total), AVG(total) 
            FROM pedidos 
            WHERE date(created_at) BETWEEN ? AND ? 
            GROUP BY date(created_at) 
            ORDER BY date(created_at)
        """, (data_inicio, data_fim))
        evolucao = c.fetchall()
        
        c.execute("""
            SELECT 
                COUNT(*) as total_pedidos,
                SUM(total) as faturamento_total,
                AVG(total) as ticket_medio,
                MIN(total) as menor_pedido,
                MAX(total) as maior_pedido
            FROM pedidos 
            WHERE date(created_at) BETWEEN ? AND ?
        """, (data_inicio, data_fim))
        stats = c.fetchone()
        
        conn.close()
        
        if stats:
            total_pedidos, faturamento_total, ticket_medio, menor_pedido, maior_pedido = stats
            
            frame_metrics = ctk.CTkFrame(frame_secao)
            frame_metrics.pack(fill=tk.X, pady=10)
            
            metricas_financeiras = [
                ("Faturamento Total", f"R$ {faturamento_total or 0:,.2f}"),
                ("Ticket Médio", f"R$ {ticket_medio or 0:,.2f}"),
                ("Maior Pedido", f"R$ {maior_pedido or 0:,.2f}"),
                ("Menor Pedido", f"R$ {menor_pedido or 0:,.2f}")
            ]
            
            for i in range(0, len(metricas_financeiras), 2):
                frame_linha = ctk.CTkFrame(frame_metrics)
                frame_linha.pack(fill=tk.X, pady=2)
                
                for j in range(2):
                    if i + j < len(metricas_financeiras):
                        titulo, valor = metricas_financeiras[i + j]
                        metric_frame = ctk.CTkFrame(frame_linha)
                        metric_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
                        
                        ctk.CTkLabel(
                            metric_frame,
                            text=titulo,
                            font=ctk.CTkFont(size=10)
                        ).pack(pady=(5, 2))
                        
                        ctk.CTkLabel(
                            metric_frame,
                            text=valor,
                            font=ctk.CTkFont(size=11, weight="bold"),
                            text_color="#e74c3c"
                        ).pack(pady=(0, 5))
        
        if evolucao:
            frame_tabela = ctk.CTkFrame(frame_secao)
            frame_tabela.pack(fill=tk.X, pady=10)
            
            ctk.CTkLabel(
                frame_tabela,
                text="📈 Evolução Diária",
                font=ctk.CTkFont(weight="bold")
            ).pack(anchor="w", pady=(0, 10))
            
            tree_frame = ctk.CTkFrame(frame_tabela)
            tree_frame.pack(fill=tk.X, padx=5, pady=5)
            
            cols = ('Data', 'Pedidos', 'Faturamento', 'Ticket Médio')
            tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=6)
            
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            
            for dia in evolucao:
                tree.insert('', tk.END, values=(
                    dia[0],
                    dia[1],
                    f"R$ {dia[2] or 0:,.2f}",
                    f"R$ {dia[3] or 0:,.2f}"
                ))

    def _adicionar_secao_estatisticas(self, parent, data_inicio, data_fim):
        """Adiciona seção de estatísticas e métricas"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="📊 ESTATÍSTICAS E MÉTRICAS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#9b59b6"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("""
            SELECT c.nome, COUNT(p.id) as total_pedidos, SUM(p.total) as valor_total
            FROM clientes c
            LEFT JOIN pedidos p ON c.id = p.cliente_id
            WHERE date(p.created_at) BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY valor_total DESC
            LIMIT 5
        """, (data_inicio, data_fim))
        top_clientes = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos_geral = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        pedidos_periodo = c.fetchone()[0]
        
        c.execute("SELECT SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        faturamento_periodo = c.fetchone()[0] or 0
        
        conn.close()
        
        if top_clientes:
            frame_top = ctk.CTkFrame(frame_secao)
            frame_top.pack(fill=tk.X, pady=10)
            
            ctk.CTkLabel(
                frame_top,
                text="🏆 Top 5 Clientes por Valor",
                font=ctk.CTkFont(weight="bold")
            ).pack(anchor="w", pady=(0, 5))
            
            for i, (nome, pedidos, valor) in enumerate(top_clientes, 1):
                cliente_frame = ctk.CTkFrame(frame_top)
                cliente_frame.pack(fill=tk.X, padx=5, pady=2)
                
                ctk.CTkLabel(
                    cliente_frame,
                    text=f"{i}º {nome} - {pedidos} pedidos - R$ {valor or 0:,.2f}",
                    font=ctk.CTkFont(size=10)
                ).pack(anchor="w", padx=10, pady=3)
        
        frame_geral = ctk.CTkFrame(frame_secao)
        frame_geral.pack(fill=tk.X, pady=10)
        
        metricas_gerais = [
            ("Base Total de Clientes", total_clientes),
            ("Pedidos no Período", pedidos_periodo),
            ("Total Geral de Pedidos", total_pedidos_geral),
            ("Faturamento do Período", f"R$ {faturamento_periodo:,.2f}")
        ]
        
        for i in range(0, len(metricas_gerais), 2):
            frame_linha = ctk.CTkFrame(frame_geral)
            frame_linha.pack(fill=tk.X, pady=2)
            
            for j in range(2):
                if i + j < len(metricas_gerais):
                    titulo, valor = metricas_gerais[i + j]
                    metric_frame = ctk.CTkFrame(frame_linha)
                    metric_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
                    
                    ctk.CTkLabel(
                        metric_frame,
                        text=titulo,
                        font=ctk.CTkFont(size=10)
                    ).pack(pady=(5, 2))
                    
                    ctk.CTkLabel(
                        metric_frame,
                        text=str(valor),
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color="#9b59b6"
                    ).pack(pady=(0, 5))

    def _adicionar_secao_graficos(self, parent, data_inicio, data_fim):
        """Adiciona seção com gráficos detalhados"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="📈 GRÁFICOS DETALHADOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f39c12"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        try:
            conn = self._conectar_db()
            c = conn.cursor()
            
            c.execute("""
                SELECT date(created_at), SUM(total) 
                FROM pedidos 
                WHERE date(created_at) BETWEEN ? AND ? 
                GROUP BY date(created_at) 
                ORDER BY date(created_at)
            """, (data_inicio, data_fim))
            dados_evolucao = c.fetchall()
            
            c.execute("""
                SELECT status, COUNT(*) 
                FROM pedidos 
                WHERE date(created_at) BETWEEN ? AND ? 
                GROUP BY status
            """, (data_inicio, data_fim))
            dados_status = c.fetchall()
            
            conn.close()
            
            if dados_evolucao or dados_status:
                frame_graficos = ctk.CTkFrame(frame_secao)
                frame_graficos.pack(fill=tk.BOTH, expand=True, pady=10)
                
                if dados_evolucao:
                    fig1 = Figure(figsize=(10, 4), dpi=100)
                    ax1 = fig1.add_subplot(111)
                    
                    datas = [d[0] for d in dados_evolucao]
                    valores = [float(d[1] or 0) for d in dados_evolucao]
                    
                    ax1.plot(datas, valores, marker='o', linewidth=2, markersize=4, 
                            color='#3498db', label='Faturamento Diário')
                    ax1.set_title('Evolução do Faturamento Diário', fontsize=12, fontweight='bold')
                    ax1.set_ylabel('Faturamento (R$)', fontsize=10)
                    ax1.set_xlabel('Data', fontsize=10)
                    ax1.grid(True, alpha=0.3)
                    ax1.legend()
                    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
                    fig1.tight_layout()
                    
                    canvas1 = FigureCanvasTkAgg(fig1, frame_graficos)
                    canvas1.draw()
                    canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
                if dados_status:
                    fig2 = Figure(figsize=(8, 4), dpi=100)
                    ax2 = fig2.add_subplot(111)
                    
                    status = [d[0] for d in dados_status]
                    quantidades = [d[1] for d in dados_status]
                    cores = ['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6']
                    
                    bars = ax2.bar(status, quantidades, color=cores[:len(status)], alpha=0.8)
                    ax2.set_title('Distribuição de Pedidos por Status', fontsize=12, fontweight='bold')
                    ax2.set_ylabel('Quantidade de Pedidos', fontsize=10)
                    
                    for bar, valor in zip(bars, quantidades):
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                f'{valor}', ha='center', va='bottom', fontweight='bold')
                    
                    fig2.tight_layout()
                    
                    canvas2 = FigureCanvasTkAgg(fig2, frame_graficos)
                    canvas2.draw()
                    canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                    
        except Exception as e:
            ctk.CTkLabel(
                frame_secao,
                text=f"Erro ao gerar gráficos: {str(e)}",
                text_color="#e74c3c",
                font=ctk.CTkFont(size=10)
            ).pack(pady=10)

    def _adicionar_secao_tendencias(self, parent, data_inicio, data_fim):
        """Adiciona seção de análise de tendências"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="🔍 ANÁLISE DE TENDÊNCIAS E RISCOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e67e22"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        conn = self._conectar_db()
        c = conn.cursor()
        
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
        data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
        dias_periodo = (data_fim_dt - data_inicio_dt).days
        
        periodo_anterior_inicio = (data_inicio_dt - timedelta(days=dias_periodo)).strftime("%Y-%m-%d")
        periodo_anterior_fim = (data_inicio_dt - timedelta(days=1)).strftime("%Y-%m-%d")
        
        c.execute("SELECT COUNT(*), SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        atual = c.fetchone()
        
        c.execute("SELECT COUNT(*), SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (periodo_anterior_inicio, periodo_anterior_fim))
        anterior = c.fetchone()
        
        conn.close()
        
        pedidos_atual = atual[0] or 0
        faturamento_atual = atual[1] or 0
        pedidos_anterior = anterior[0] or 0
        faturamento_anterior = anterior[1] or 0
        
        variacao_pedidos = ((pedidos_atual - pedidos_anterior) / pedidos_anterior * 100) if pedidos_anterior > 0 else 0
        variacao_faturamento = ((faturamento_atual - faturamento_anterior) / faturamento_anterior * 100) if faturamento_anterior > 0 else 0
        
        analise_tendencias = []
        
        if variacao_pedidos > 0:
            analise_tendencias.append(f"📈 Crescimento de {variacao_pedidos:.1f}% no volume de pedidos")
        else:
            analise_tendencias.append(f"📉 Queda de {abs(variacao_pedidos):.1f}% no volume de pedidos")
        
        if variacao_faturamento > 0:
            analise_tendencias.append(f"💰 Crescimento de {variacao_faturamento:.1f}% no faturamento")
        else:
            analise_tendencias.append(f"💸 Queda de {abs(variacao_faturamento):.1f}% no faturamento")
        
        riscos = []
        if variacao_pedidos < -10:
            riscos.append("Queda significativa no volume de pedidos requer atenção imediata")
        if variacao_faturamento < -15:
            riscos.append("Queda acentuada no faturamento indica possíveis problemas operacionais")
        if pedidos_atual == 0:
            riscos.append("Nenhum pedido no período - verificar problemas no sistema ou operação")
        
        for item in analise_tendencias:
            item_frame = ctk.CTkFrame(frame_secao)
            item_frame.pack(fill=tk.X, padx=5, pady=2)
            ctk.CTkLabel(
                item_frame,
                text=item,
                font=ctk.CTkFont(size=10)
            ).pack(anchor="w", padx=10, pady=3)
        
        if riscos:
            ctk.CTkLabel(
                frame_secao,
                text="⚠️ PONTOS DE ATENÇÃO IDENTIFICADOS:",
                font=ctk.CTkFont(weight="bold"),
                text_color="#e74c3c"
            ).pack(anchor="w", pady=(10, 5))
            
            for risco in riscos:
                risco_frame = ctk.CTkFrame(frame_secao, fg_color="#fee")
                risco_frame.pack(fill=tk.X, padx=5, pady=2)
                ctk.CTkLabel(
                    risco_frame,
                    text=f"• {risco}",
                    font=ctk.CTkFont(size=10),
                    text_color="#c0392b"
                ).pack(anchor="w", padx=10, pady=3)

    def _adicionar_secao_plano_acao(self, parent, data_inicio, data_fim):
        """Adiciona seção com plano de ação"""
        frame_secao = ctk.CTkFrame(parent)
        frame_secao.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        titulo_secao = ctk.CTkLabel(
            frame_secao,
            text="🎯 PLANO DE AÇÃO E PROJEÇÕES",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#27ae60"
        )
        titulo_secao.pack(anchor="w", pady=(10, 5))
        
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*), SUM(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        dados = c.fetchone()
        
        conn.close()
        
        pedidos_periodo = dados[0] or 0
        faturamento_periodo = dados[1] or 0
        
        dias_periodo = (datetime.strptime(data_fim, "%Y-%m-%d") - datetime.strptime(data_inicio, "%Y-%m-%d")).days + 1
        pedidos_dia = pedidos_periodo / dias_periodo if dias_periodo > 0 else 0
        faturamento_dia = faturamento_periodo / dias_periodo if dias_periodo > 0 else 0
        
        plano_acao = [
            ("🎯 PRÓXIMOS 30 DIAS", [
                f"Meta: Aumentar ticket médio em 10%",
                f"Ação: Implementar upsell estratégico",
                f"Meta: Aumentar base de clientes em 15%",
                f"Ação: Campanha de captação segmentada"
            ]),
            ("📊 PRÓXIMOS 90 DIAS", [
                f"Meta: Crescimento de 25% no faturamento",
                f"Ação: Expansão de portfólio de produtos",
                f"Meta: Redução de 20% em pedidos cancelados", 
                f"Ação: Melhoria no pós-venda"
            ]),
            ("🚀 PRÓXIMOS 6 MESES", [
                f"Meta: Dobrar o faturamento atual",
                f"Ação: Expansão para novos mercados",
                f"Meta: Atingir 50% de retenção de clientes",
                f"Ação: Programa de fidelidade"
            ])
        ]
        
        projecoes = [
            ("Projeção Conservadora", 0.10),
            ("Projeção Realista", 0.25),
            ("Projeção Otimista", 0.40)
        ]
        
        frame_projecoes = ctk.CTkFrame(frame_secao)
        frame_projecoes.pack(fill=tk.X, pady=10)
        
        ctk.CTkLabel(
            frame_projecoes,
            text="📈 PROJEÇÕES DE CRESCIMENTO (6 MESES):",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        for nome, taxa in projecoes:
            faturamento_projetado = faturamento_periodo * (1 + taxa) * 2
            proj_frame = ctk.CTkFrame(frame_projecoes)
            proj_frame.pack(fill=tk.X, padx=5, pady=2)
            
            ctk.CTkLabel(
                proj_frame,
                text=f"{nome}: R$ {faturamento_projetado:,.2f} ({taxa*100:.0f}% de crescimento)",
                font=ctk.CTkFont(size=10, weight="bold")
            ).pack(anchor="w", padx=10, pady=3)
        
        for fase, acoes in plano_acao:
            frame_fase = ctk.CTkFrame(frame_secao)
            frame_fase.pack(fill=tk.X, pady=5)
            
            ctk.CTkLabel(
                frame_fase,
                text=fase,
                font=ctk.CTkFont(weight="bold"),
                text_color="#27ae60"
            ).pack(anchor="w", pady=(5, 5))
            
            for acao in acoes:
                acao_frame = ctk.CTkFrame(frame_fase)
                acao_frame.pack(fill=tk.X, padx=10, pady=1)
                ctk.CTkLabel(
                    acao_frame,
                    text=f"• {acao}",
                    font=ctk.CTkFont(size=10)
                ).pack(anchor="w", padx=5, pady=2)

    def _mostrar_relatorio_tela(self, tipo, data_inicio, data_fim, status="Todos"):
        """Exibe relatório individual na tela"""
        self._limpar_resultados()
        
        frame_scroll = ctk.CTkScrollableFrame(self.frame_resultados)
        frame_scroll.pack(fill=tk.BOTH, expand=True)
        
        titulos = {
            "clientes": "👥 Relatório de Clientes",
            "pedidos": "📦 Relatório de Pedidos", 
            "financeiro": "💰 Relatório Financeiro",
            "estatisticas": "📊 Relatório de Estatísticas"
        }
        
        titulo = ctk.CTkLabel(
            frame_scroll, 
            text=titulos.get(tipo, "Relatório"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2c3e50"
        )
        titulo.pack(pady=10)
        
        periodo_label = ctk.CTkLabel(
            frame_scroll,
            text=f"📅 Período: {data_inicio} à {data_fim}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        periodo_label.pack(pady=(0, 15))

        if tipo == "clientes":
            self._gerar_relatorio_clientes_tela(frame_scroll, data_inicio, data_fim)
        elif tipo == "pedidos":
            self._gerar_relatorio_pedidos_tela(frame_scroll, data_inicio, data_fim, status)
        elif tipo == "financeiro":
            self._gerar_relatorio_financeiro_tela(frame_scroll, data_inicio, data_fim)
        else:
            self._gerar_relatorio_estatisticas_tela(frame_scroll, data_inicio, data_fim)

    def _gerar_relatorio_clientes_tela(self, parent, data_inicio, data_fim):
        """Gera relatório de clientes na tela"""
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("""
            SELECT id, nome, email, telefone, date(created_at) 
            FROM clientes 
            WHERE date(created_at) BETWEEN ? AND ? 
            ORDER BY created_at DESC
        """, (data_inicio, data_fim))
        clientes = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM clientes WHERE date(created_at) BETWEEN ? AND ?", (data_inicio, data_fim))
        total = c.fetchone()[0]
        
        conn.close()

        frame_stats = ctk.CTkFrame(parent)
        frame_stats.pack(fill=tk.X, pady=(10, 15))
        
        ctk.CTkLabel(
            frame_stats, 
            text=f"📊 Total de Clientes no Período: {total}", 
            font=ctk.CTkFont(weight="bold"),
            text_color="#2c3e50"
        ).pack(anchor="w", padx=10, pady=5)

        if not clientes:
            ctk.CTkLabel(
                parent, 
                text="Nenhum cliente encontrado no período selecionado.",
                text_color=("gray50", "gray70")
            ).pack(pady=20)
            return

        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        cols = ('ID', 'Nome', 'Email', 'Telefone', 'Data Cadastro')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=12)
        
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, minwidth=80)
        
        for row in clientes:
            tree.insert('', tk.END, values=row)

    def _gerar_relatorio_pedidos_tela(self, parent, data_inicio, data_fim, status="Todos"):
        """Gera relatório de pedidos na tela"""
        conn = self._conectar_db()
        c = conn.cursor()
        
        query = """
            SELECT p.id, c.nome, p.total, p.status, date(p.created_at) 
            FROM pedidos p 
            LEFT JOIN clientes c ON p.cliente_id = c.id
            WHERE date(p.created_at) BETWEEN ? AND ?
        """
        params = [data_inicio, data_fim]
        
        if status != "Todos":
            query += " AND p.status = ?"
            params.append(status)
        
        query += " ORDER BY p.created_at DESC"
        
        c.execute(query, params)
        pedidos = c.fetchall()
        
        c.execute("SELECT COUNT(*), SUM(total), AVG(total) FROM pedidos WHERE date(created_at) BETWEEN ? AND ?", 
                 (data_inicio, data_fim))
        stats = c.fetchone()
        
        conn.close()

        frame_stats = ctk.CTkFrame(parent)
        frame_stats.pack(fill=tk.X, pady=(10, 15))
        
        stats_text = f"📊 Total de Pedidos: {stats[0] or 0} • Valor Total: R$ {stats[1] or 0:.2f} • Ticket Médio: R$ {stats[2] or 0:.2f}"
        ctk.CTkLabel(
            frame_stats, 
            text=stats_text,
            font=ctk.CTkFont(weight="bold"),
            text_color="#2c3e50"
        ).pack(anchor="w", padx=10, pady=5)

        if not pedidos:
            ctk.CTkLabel(
                parent, 
                text="Nenhum pedido encontrado no período selecionado.",
                text_color=("gray50", "gray70")
            ).pack(pady=20)
            return

        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        cols = ('ID', 'Cliente', 'Valor', 'Status', 'Data')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=12)
        
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, minwidth=80)
        
        for row in pedidos:
            tree.insert('', tk.END, values=(
                row[0], 
                row[1] or '', 
                f"R$ {row[2] or 0:.2f}", 
                row[3] or '', 
                row[4]
            ))

    def _gerar_relatorio_financeiro_tela(self, parent, data_inicio, data_fim):
        """Gera relatório financeiro na tela"""
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("""
            SELECT COUNT(*), SUM(total), AVG(total), MIN(total), MAX(total) 
            FROM pedidos 
            WHERE date(created_at) BETWEEN ? AND ?
        """, (data_inicio, data_fim))
        stats = c.fetchone()
        
        c.execute("""
            SELECT date(created_at), COUNT(*), SUM(total) 
            FROM pedidos 
            WHERE date(created_at) BETWEEN ? AND ? 
            GROUP BY date(created_at) 
            ORDER BY date(created_at)
        """, (data_inicio, data_fim))
        evolucao = c.fetchall()
        
        conn.close()

        frame_stats = ctk.CTkFrame(parent)
        frame_stats.pack(fill=tk.X, pady=(10, 15))
        
        principal_text = f"💰 Pedidos: {stats[0] or 0} • Faturamento: R$ {stats[1] or 0:.2f} • Ticket Médio: R$ {stats[2] or 0:.2f}"
        ctk.CTkLabel(
            frame_stats, 
            text=principal_text,
            font=ctk.CTkFont(weight="bold"),
            text_color="#2c3e50"
        ).pack(anchor="w", padx=10, pady=5)

        if evolucao:
            table_frame = ctk.CTkFrame(parent)
            table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            cols = ('Data', 'Pedidos', 'Faturamento')
            tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=12)
            
            v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
            h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            
            tree.grid(row=0, column=0, sticky='nsew')
            v_scroll.grid(row=0, column=1, sticky='ns')
            h_scroll.grid(row=1, column=0, sticky='ew')
            
            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)
            
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=120, minwidth=80)
            
            for row in evolucao:
                tree.insert('', tk.END, values=(
                    row[0], 
                    row[1], 
                    f"R$ {row[2] or 0:.2f}"
                ))
        else:
            ctk.CTkLabel(
                parent, 
                text="Nenhum dado financeiro no período.",
                text_color=("gray50", "gray70")
            ).pack(pady=20)

    def _gerar_relatorio_estatisticas_tela(self, parent, data_inicio, data_fim):
        """Gera relatório de estatísticas na tela"""
        conn = self._conectar_db()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = c.fetchone()[0]
        
        c.execute("""
            SELECT COUNT(*), SUM(total), AVG(total) 
            FROM pedidos 
            WHERE date(created_at) BETWEEN ? AND ?
        """, (data_inicio, data_fim))
        stats_periodo = c.fetchone()
        
        c.execute("""
            SELECT c.nome, COUNT(p.id), SUM(p.total) 
            FROM clientes c 
            LEFT JOIN pedidos p ON c.id = p.cliente_id 
            WHERE date(p.created_at) BETWEEN ? AND ? 
            GROUP BY c.id 
            ORDER BY SUM(p.total) DESC 
            LIMIT 5
        """, (data_inicio, data_fim))
        top_clientes = c.fetchall()
        
        conn.close()

        frame_principal = ctk.CTkFrame(parent)
        frame_principal.pack(fill=tk.X, pady=(10, 15))
        
        principal_text = (f"👥 Clientes: {total_clientes} • Pedidos: {total_pedidos} • "
                          f"Pedidos no período: {stats_periodo[0] or 0} • Faturamento período: R$ {stats_periodo[1] or 0:.2f}")
        ctk.CTkLabel(
            frame_principal, 
            text=principal_text,
            font=ctk.CTkFont(weight="bold"),
            text_color="#2c3e50"
        ).pack(anchor="w", padx=10, pady=5)

        if top_clientes:
            frame_top = ctk.CTkFrame(parent)
            frame_top.pack(fill=tk.X, pady=10, padx=10)
            
            ctk.CTkLabel(
                frame_top,
                text="🏆 Top Clientes do Período",
                font=ctk.CTkFont(weight="bold"),
                text_color="#e74c3c"
            ).pack(anchor="w", pady=(10, 5))
            
            for i, (nome, pedidos, total) in enumerate(top_clientes, 1):
                cliente_frame = ctk.CTkFrame(frame_top)
                cliente_frame.pack(fill=tk.X, padx=5, pady=2)
                
                texto = f"{i}º {nome} — {pedidos} pedidos — R$ {total or 0:.2f}"
                ctk.CTkLabel(
                    cliente_frame,
                    text=texto,
                    font=ctk.CTkFont(size=11)
                ).pack(anchor="w", padx=10, pady=5)

    def _agendar_atualizacao(self):
        """Agenda atualização automática dos dados"""
        try:
            if self.frame_resultados.winfo_exists():
                self.frame_resultados.after(300000, self._agendar_atualizacao)  # 5 minutos
        except Exception:
            pass