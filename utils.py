# utils.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import re
import os
import sqlite3



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


def _to_float(valor):
    try:
        return float(valor)
    except Exception:
        return 0.0


def formatar_moeda(valor):
    """Formata valor em BRL: R$ 1.234,56."""
    try:
        v = _to_float(valor)
        return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return "R$ 0,00"


def formatar_numero_brl(valor):
    """Formata valor numérico com vírgula (sem prefixo R$), ex: 1.234,56."""
    try:
        v = _to_float(valor)
        return f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return "0,00"


def parse_moeda(texto):
    """Converte textos como 'R$ 1.234,56' ou '1234,56' para float 1234.56.
    Aceita espaços, pontos de milhar e vírgula decimal.
    """
    if texto is None:
        return 0.0
    try:
        s = str(texto).strip()
        # remove símbolo e espaços
        s = re.sub(r"[^0-9,.-]", "", s)
        # se houver mais de uma vírgula, mantém apenas a última como decimal
        if s.count(',') > 1:
            last = s.rfind(',')
            s = s[:last].replace(',', '') + s[last:]
        # remove pontos de milhar
        s = s.replace('.', '')
        # troca vírgula por ponto para float
        s = s.replace(',', '.')
        return float(s) if s not in ('', '-', '.', ',') else 0.0
    except Exception:
        return 0.0


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


def analisar_pedidos(db_path='clientes_pedidos.db', modelo=None, periodo_dias=30):
    """
    Analisa pedidos usando o agente_ia central do projeto para identificar produtos mais vendidos e gerar insights.
    
    Args:
        db_path: Caminho do banco de dados SQLite
        modelo: (opcional) nome do modelo a ser usado pelo agente_ia (se None, usa o padrão do agente)
        periodo_dias: Período em dias para análise (padrão: 30 dias)
    
    Returns:
        dict: {
            'produtos_mais_vendidos': list,
            'analise_ia': str,
            'metricas': dict,
            'sucesso': bool,
            'erro': str (se houver)
        }
    """

    
    # Usar o agente de IA centralizado do projeto
    try:
        from agente_ia import agente_ia as ia
        # Se um modelo foi especificado, tentar trocar no agente
        if modelo:
            try:
                ia.trocar_modelo(modelo)
                registrar_log(f"AGENTE_IA - Modelo definido para: {modelo}")
            except Exception as e:
                registrar_log(f"AGENTE_IA - Falha ao trocar modelo '{modelo}': {e}")
    except Exception:
        ia = None
    
    resultado = {
        'produtos_mais_vendidos': [],
        'analise_ia': '',
        'metricas': {},
        'sucesso': False,
        'erro': None
    }
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Data limite para análise
        data_limite = (datetime.now() - timedelta(days=periodo_dias)).strftime('%Y-%m-%d')
        
        # Buscar produtos mais vendidos no período
        query = """
            SELECT 
                p.nome as produto,
                SUM(ip.quantidade) as total_vendido,
                COUNT(DISTINCT ip.pedido_id) as num_pedidos,
                SUM(ip.quantidade * ip.preco_unit) as receita_total,
                AVG(ip.preco_unit) as preco_medio
            FROM itens_pedido ip
            INNER JOIN produtos p ON ip.produto_id = p.id
            INNER JOIN pedidos ped ON ip.pedido_id = ped.id
            WHERE ped.data >= ?
            GROUP BY p.id, p.nome
            ORDER BY total_vendido DESC
            LIMIT 10
        """
        
        cursor.execute(query, (data_limite,))
        produtos = cursor.fetchall()
        
        # Métricas gerais
        cursor.execute("""
            SELECT 
                COUNT(*) as total_pedidos,
                SUM(total) as receita_total,
                AVG(total) as ticket_medio
            FROM pedidos
            WHERE data >= ?
        """, (data_limite,))
        metricas = cursor.fetchone()
        
        conn.close()
        
        # Formatar dados dos produtos
        produtos_formatados = []
        for prod in produtos:
            produtos_formatados.append({
                'produto': prod[0],
                'quantidade_vendida': int(prod[1]),
                'num_pedidos': int(prod[2]),
                'receita': float(prod[3]),
                'preco_medio': float(prod[4])
            })
        
        resultado['produtos_mais_vendidos'] = produtos_formatados
        resultado['metricas'] = {
            'total_pedidos': int(metricas[0]) if metricas[0] else 0,
            'receita_total': float(metricas[1]) if metricas[1] else 0.0,
            'ticket_medio': float(metricas[2]) if metricas[2] else 0.0
        }
        
    # Preparar contexto de dados para o Agente IA
        dados_texto = f"""Análise de Vendas - Últimos {periodo_dias} dias:

MÉTRICAS GERAIS:
- Total de pedidos: {resultado['metricas']['total_pedidos']}
- Receita total: R$ {resultado['metricas']['receita_total']:,.2f}
- Ticket médio: R$ {resultado['metricas']['ticket_medio']:,.2f}

TOP 10 PRODUTOS MAIS VENDIDOS:
"""
        
        for i, prod in enumerate(produtos_formatados[:10], 1):
            dados_texto += f"\n{i}. {prod['produto']}"
            dados_texto += f"\n   - Quantidade vendida: {prod['quantidade_vendida']} unidades"
            dados_texto += f"\n   - Presente em {prod['num_pedidos']} pedidos"
            dados_texto += f"\n   - Receita gerada: R$ {prod['receita']:,.2f}"
            dados_texto += f"\n   - Preço médio: R$ {prod['preco_medio']:,.2f}\n"
        
        pergunta = (
            "Analise estes dados de vendas e traga os principais insights em até 300 palavras, "
            "com foco em ações práticas: oportunidades, riscos, recomendações objetivas e próximos passos."
        )

        # Usar o agente_ia se disponível; caso contrário, retornar análise básica
        if ia is None:
            resultado['analise_ia'] = (
                "Análise via IA indisponível: módulo agente_ia não pôde ser carregado. "
                "Mostrando apenas dados tabulados."
            )
        else:
            try:
                ok, msg = ia.testar_modelo()
                if not ok:
                    registrar_log(f"AGENTE_IA - Indisponível: {msg}")
                    resultado['analise_ia'] = (
                        f"IA indisponível no momento ({msg}). Exibindo dados consolidados sem análise textual."
                    )
                else:
                    resposta, erro = ia.enviar_pergunta_com_contexto(pergunta, contexto_adicional=dados_texto)
                    if erro:
                        registrar_log(f"AGENTE_IA - Erro ao gerar análise: {erro}")
                        resultado['analise_ia'] = (
                            f"Falha ao gerar análise com IA: {erro}. Exibindo apenas dados."
                        )
                    else:
                        resultado['analise_ia'] = resposta
            except Exception as e:
                registrar_log(f"AGENTE_IA - Exceção inesperada: {e}")
                resultado['analise_ia'] = (
                    f"Erro inesperado ao usar IA: {e}. Exibindo apenas dados."
                )
        
        # Mesmo se a IA estiver indisponível, os dados já foram calculados com sucesso
        resultado['sucesso'] = True
        
    except sqlite3.Error as e:
        resultado['erro'] = f"Erro no banco de dados: {str(e)}"
        resultado['sucesso'] = False
        registrar_log(f"ERRO DB - analisar_pedidos: {e}")
    except Exception as e:
        resultado['erro'] = f"Erro inesperado: {str(e)}"
        resultado['sucesso'] = False
        registrar_log(f"ERRO - analisar_pedidos: {e}")
    
    return resultado