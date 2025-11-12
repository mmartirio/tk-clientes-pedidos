# dashboard.py
import sqlite3
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from logs import log_operacao, log_erro

class Dashboard:
    def __init__(self, db_path='clientes_pedidos.db'):
        self.db_path = db_path
    
    def _conectar_db(self):
        return sqlite3.connect(self.db_path)
    
    def get_metricas_principais(self):
        """Retorna as métricas principais para o dashboard."""
        try:
            conn = self._conectar_db()
            cursor = conn.cursor()
            
            # Total de clientes
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = cursor.fetchone()[0]
            
            # Total de pedidos no mês atual
            primeiro_dia_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            cursor.execute(
                "SELECT COUNT(*) FROM pedidos WHERE created_at >= ?", 
                (primeiro_dia_mes,)
            )
            pedidos_mes = cursor.fetchone()[0]
            
            # Ticket médio (valor médio dos pedidos)
            cursor.execute("SELECT AVG(total) FROM pedidos WHERE total > 0")
            ticket_medio = cursor.fetchone()[0] or 0
            
            # Total de vendas no mês
            cursor.execute(
                "SELECT SUM(total) FROM pedidos WHERE created_at >= ? AND total > 0", 
                (primeiro_dia_mes,)
            )
            total_vendas_mes = cursor.fetchone()[0] or 0
            
            # Clientes novos no mês
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE created_at >= ?", (primeiro_dia_mes,))
            clientes_novos_mes = cursor.fetchone()[0]
            
            # Pedidos por status (para cálculo de conversão)
            cursor.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status")
            pedidos_status = cursor.fetchall()
            total_pedidos = sum([qtd for _, qtd in pedidos_status])
            pedidos_concluidos = sum([qtd for status, qtd in pedidos_status if status and status.lower() in ['concluído', 'concluido', 'finalizado', 'entregue']])
            
            # Taxa de conversão
            taxa_conversao = (pedidos_concluidos / total_pedidos * 100) if total_pedidos > 0 else 0
            
            conn.close()
            
            log_operacao("DASHBOARD", "Métricas principais calculadas", 
                        f"Clientes: {total_clientes}, Pedidos mês: {pedidos_mes}")
            
            return {
                'total_clientes': total_clientes,
                'pedidos_mes': pedidos_mes,
                'ticket_medio': round(ticket_medio, 2),
                'total_vendas_mes': round(total_vendas_mes, 2),
                'clientes_novos_mes': clientes_novos_mes,
                'taxa_conversao': round(taxa_conversao, 1),
                'pedidos_concluidos': pedidos_concluidos,
                'total_pedidos': total_pedidos
            }
            
        except Exception as e:
            log_erro(f"Erro ao calcular métricas do dashboard: {str(e)}")
            return self._get_metricas_default()
    
    def _get_metricas_default(self):
        """Retorna métricas padrão em caso de erro."""
        return {
            'total_clientes': 0,
            'pedidos_mes': 0,
            'ticket_medio': 0,
            'total_vendas_mes': 0,
            'clientes_novos_mes': 0,
            'taxa_conversao': 0,
            'pedidos_concluidos': 0,
            'total_pedidos': 0
        }
    
    def get_evolucao_pedidos(self, dias=30):
        """Retorna evolução de pedidos nos últimos dias."""
        try:
            conn = self._conectar_db()
            cursor = conn.cursor()
            
            data_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT date(created_at) as data, COUNT(*) as total
                FROM pedidos 
                WHERE created_at >= ?
                GROUP BY date(created_at)
                ORDER BY data
            """, (data_limite,))
            
            resultados = cursor.fetchall()
            conn.close()
            
            log_operacao("DASHBOARD", "Evolução de pedidos consultada", f"{len(resultados)} registros")
            
            return resultados
            
        except Exception as e:
            log_erro(f"Erro ao buscar evolução de pedidos: {str(e)}")
            return []
    
    def get_pedidos_por_status(self):
        """Retorna distribuição de pedidos por status."""
        try:
            conn = self._conectar_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, COUNT(*) as total
                FROM pedidos
                GROUP BY status
            """)
            
            resultados = cursor.fetchall()
            conn.close()
            
            return resultados
            
        except Exception as e:
            log_erro(f"Erro ao buscar pedidos por status: {str(e)}")
            return []
    
    def get_top_clientes(self, limite=5):
        """Retorna os clientes que mais fizeram pedidos."""
        try:
            conn = self._conectar_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.nome, COUNT(p.id) as total_pedidos, SUM(p.total) as total_gasto
                FROM clientes c
                LEFT JOIN pedidos p ON c.id = p.cliente_id
                GROUP BY c.id, c.nome
                ORDER BY total_pedidos DESC
                LIMIT ?
            """, (limite,))
            
            resultados = cursor.fetchall()
            conn.close()
            
            return resultados
            
        except Exception as e:
            log_erro(f"Erro ao buscar top clientes: {str(e)}")
            return []
    
    def get_metricas_logs(self):
        """Retorna métricas relacionadas aos logs."""
        try:
            # Conta arquivos de log na pasta logs
            if os.path.exists('logs'):
                arquivos_log = [f for f in os.listdir('logs') if f.endswith('.log')]
                total_arquivos_log = len(arquivos_log)
                
                # Tenta contar linhas do log atual
                data_atual = datetime.now().strftime("%Y-%m-%d")
                log_hoje = f'logs/sistema_clientes_pedidos_{data_atual}.log'
                
                if os.path.exists(log_hoje):
                    with open(log_hoje, 'r', encoding='utf-8') as f:
                        linhas_log = len(f.readlines())
                else:
                    linhas_log = 0
            else:
                total_arquivos_log = 0
                linhas_log = 0
            
            return {
                'total_arquivos_log': total_arquivos_log,
                'linhas_log_hoje': linhas_log
            }
            
        except Exception as e:
            log_erro(f"Erro ao buscar métricas de logs: {str(e)}")
            return {'total_arquivos_log': 0, 'linhas_log_hoje': 0}
        
    def _log_manual(self):
        """Registra um log manual de atualização."""
        log_operacao("DASHBOARD", "Atualização manual solicitada pelo usuário")
        self._atualizar_dashboard()
        messagebox.showinfo("Dashboard", "Dados atualizados com sucesso!")