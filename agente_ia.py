# agente_ia.py - Versão Otimizada para qwen2.5:0.5b
import requests
import json
import time
import sqlite3
from logs import log_operacao, log_erro, log_ia, log_ia_erro
from db import consultar, consultar_um, executar_comando

class AgenteIA:
    def __init__(self):
        self.url_ollama = "http://localhost:11434"
        self.modelo = "qwen2.5:0.5b"  # 🚀 Modelo mais leve!
        self.conectado = False
        self.erro_memoria = False
        self.timeout = 15  # ⏱️ Timeout reduzido - modelo é rápido!
        self.modelo_disponivel = False
        
    def testar_conexao(self):
        """Testa conexão com Ollama - otimizado para modelo leve"""
        try:
            # Testa conexão básica com timeout curto
            response = requests.get(f"{self.url_ollama}/api/tags", timeout=5)
            if response.status_code == 200:
                self.conectado = True
                
                # Verifica se o modelo está disponível
                try:
                    dados = response.json()
                    modelos = dados.get('models', [])
                    modelo_nomes = [modelo.get('name', '') for modelo in modelos]
                    
                    # Verifica se nosso modelo está na lista
                    self.modelo_disponivel = any(
                        self.modelo in nome for nome in modelo_nomes
                    )
                    
                    if self.modelo_disponivel:
                        log_operacao("AGENTE_IA", f"✅ Conexão estabelecida - Modelo {self.modelo} disponível")
                    else:
                        log_erro(f"AGENTE_IA: Modelo {self.modelo} não encontrado. Modelos disponíveis: {modelo_nomes}")
                    
                except Exception as e:
                    log_erro(f"AGENTE_IA: Erro ao processar lista de modelos: {e}")
                    self.modelo_disponivel = False
                
                return True
            else:
                self.conectado = False
                self.modelo_disponivel = False
                log_erro(f"AGENTE_IA: Ollama respondeu com status: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.conectado = False
            self.modelo_disponivel = False
            log_erro("AGENTE_IA: ❌ Não foi possível conectar com Ollama")
            return False
        except requests.exceptions.Timeout:
            self.conectado = False
            self.modelo_disponivel = False
            log_erro("AGENTE_IA: ⏱️ Timeout na conexão com Ollama")
            return False
        except Exception as e:
            self.conectado = False
            self.modelo_disponivel = False
            log_erro(f"AGENTE_IA: 🔥 Erro inesperado na conexão: {e}")
            return False

    # ========== MÉTODOS DE CONSULTA AO BANCO DE DADOS ==========

    def consultar_estatisticas_sistema(self):
        """Consulta estatísticas gerais do sistema"""
        try:
            estatisticas = {}
            
            # Total de clientes
            resultado = consultar_um("SELECT COUNT(*) FROM clientes")
            estatisticas['total_clientes'] = resultado[0] if resultado else 0
            
            # Total de produtos
            resultado = consultar_um("SELECT COUNT(*) FROM produtos")
            estatisticas['total_produtos'] = resultado[0] if resultado else 0
            
            # Total de pedidos
            resultado = consultar_um("SELECT COUNT(*) FROM pedidos")
            estatisticas['total_pedidos'] = resultado[0] if resultado else 0
            
            # Pedidos por status
            pedidos_status = consultar("""
                SELECT status, COUNT(*) as quantidade 
                FROM pedidos 
                GROUP BY status
            """)
            estatisticas['pedidos_por_status'] = dict(pedidos_status) if pedidos_status else {}
            
            # Valor total de vendas
            resultado = consultar_um("SELECT SUM(total) FROM pedidos WHERE status = 'Concluído'")
            estatisticas['vendas_totais'] = float(resultado[0]) if resultado and resultado[0] else 0.0
            
            # Ticket médio
            if estatisticas['total_pedidos'] > 0:
                estatisticas['ticket_medio'] = estatisticas['vendas_totais'] / estatisticas['total_pedidos']
            else:
                estatisticas['ticket_medio'] = 0.0
            
            return estatisticas
            
        except Exception as e:
            log_erro(f"AGENTE_IA: Erro ao consultar estatísticas: {e}")
            return {}

    def consultar_clientes_recentes(self, limite=3):
        """Consulta os clientes mais recentes"""
        try:
            clientes = consultar("""
                SELECT id, nome, email, telefone, created_at 
                FROM clientes 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limite,))
            
            clientes_formatados = []
            for cliente in clientes:
                clientes_formatados.append({
                    'id': cliente[0],
                    'nome': cliente[1],
                    'email': cliente[2],
                    'telefone': cliente[3],
                    'data_cadastro': cliente[4]
                })
            
            return clientes_formatados
        except Exception as e:
            log_erro(f"AGENTE_IA: Erro ao consultar clientes: {e}")
            return []

    def consultar_pedidos_recentes(self, limite=3):
        """Consulta os pedidos mais recentes"""
        try:
            pedidos = consultar("""
                SELECT p.id, c.nome, p.data, p.total, p.status 
                FROM pedidos p 
                LEFT JOIN clientes c ON p.cliente_id = c.id 
                ORDER BY p.created_at DESC 
                LIMIT ?
            """, (limite,))
            
            pedidos_formatados = []
            for pedido in pedidos:
                pedidos_formatados.append({
                    'id': pedido[0],
                    'cliente': pedido[1],
                    'data': pedido[2],
                    'total': float(pedido[3]),
                    'status': pedido[4]
                })
            
            return pedidos_formatados
        except Exception as e:
            log_erro(f"AGENTE_IA: Erro ao consultar pedidos: {e}")
            return []

    def consultar_produtos_estoque(self, limite=4):
        """Consulta produtos e estoque"""
        try:
            produtos = consultar("""
                SELECT id, nome, preco, estoque 
                FROM produtos 
                ORDER BY estoque DESC
                LIMIT ?
            """, (limite,))
            
            produtos_formatados = []
            for produto in produtos:
                produtos_formatados.append({
                    'id': produto[0],
                    'nome': produto[1],
                    'preco': float(produto[2]),
                    'estoque': produto[3]
                })
            
            return produtos_formatados
        except Exception as e:
            log_erro(f"AGENTE_IA: Erro ao consultar produtos: {e}")
            return []

    def _coletar_dados_sistema(self):
        """Coleta dados do sistema - otimizado para modelo leve"""
        dados = {
            'estatisticas': self.consultar_estatisticas_sistema(),
            'clientes_recentes': self.consultar_clientes_recentes(3),
            'pedidos_recentes': self.consultar_pedidos_recentes(3),
            'produtos_estoque': self.consultar_produtos_estoque(4)
        }
        return dados

    # ========== MÉTODO PRINCIPAL OTIMIZADO ==========

    def enviar_pergunta_com_contexto(self, pergunta, contexto_adicional=None):
        """
        Envia pergunta para o Ollama - OTIMIZADO para qwen2.5:0.5b
        """
        if not self.testar_conexao():
            return None, "Ollama não está conectado"
        
        if not self.modelo_disponivel:
            return None, f"Modelo {self.modelo} não está disponível"
        
        try:
            # Coleta dados do sistema
            dados_sistema = self._coletar_dados_sistema()
            contexto_bd = self._formatar_contexto_banco_dados(dados_sistema)
            
            # 🎯 PROMPT OTIMIZADO para modelo leve - MAIS CURTO E DIRETO
            prompt = f"""Dados do sistema:
{contexto_bd}

Pergunta: {pergunta}

Instruções: Responda de forma CURTA, DIRETA e PRÁTICA. Use apenas os dados fornecidos."""
            
            log_operacao("AGENTE_IA", f"Enviando pergunta para {self.modelo}: {pergunta[:80]}...")
            
            # ⚡ CONFIGURAÇÕES OTIMIZADAS para modelo leve
            payload = {
                "model": self.modelo,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 250,  # 🔽 REDUZIDO - modelo é pequeno
                    "temperature": 0.4,  # 📊 Um pouco mais criativo
                    "top_k": 30,         # 🎯 Mais focado
                    "top_p": 0.8         # 📈 Balance criatividade/qualidade
                }
            }
            
            # ⏱️ TIMEOUT CURTO - modelo é rápido!
            response = requests.post(
                f"{self.url_ollama}/api/generate",
                json=payload,
                timeout=self.timeout  # 15 segundos
            )
            
            if response.status_code == 200:
                resultado = response.json()
                resposta = resultado.get('response', '').strip()
                
                if not resposta:
                    erro_msg = "IA retornou resposta vazia"
                    log_erro(f"AGENTE_IA_ERRO: {erro_msg}")
                    return None, erro_msg
                
                log_ia(f"✅ Resposta recebida ({len(resposta)} caracteres) em {resultado.get('total_duration', 0)/1e9:.1f}s")
                return resposta, None
                
            else:
                erro_msg = f"Erro Ollama {response.status_code}"
                try:
                    erro_json = response.json()
                    erro_detalhe = erro_json.get('error', '')
                    erro_msg += f": {erro_detalhe}"
                except:
                    erro_msg += f": {response.text}"
                
                log_erro(f"AGENTE_IA_ERRO: {erro_msg}")
                return None, erro_msg
                
        except requests.exceptions.Timeout:
            erro_msg = f"Timeout - Ollama não respondeu em {self.timeout} segundos"
            log_erro(f"AGENTE_IA_ERRO: {erro_msg}")
            return None, erro_msg
        except requests.exceptions.ConnectionError:
            erro_msg = "Erro de conexão - Ollama pode ter parado"
            log_erro(f"AGENTE_IA_ERRO: {erro_msg}")
            self.conectado = False
            return None, erro_msg
        except Exception as e:
            erro_msg = f"Erro inesperado: {str(e)}"
            log_erro(f"AGENTE_IA_ERRO: {erro_msg}")
            return None, erro_msg

    def _formatar_contexto_banco_dados(self, dados_sistema):
        """Formata dados do BD de forma CONCISA para modelo leve"""
        contexto = "=== DADOS DO SISTEMA ===\n"
        
        # Estatísticas (formato compacto)
        stats = dados_sistema['estatisticas']
        contexto += f"Clientes: {stats.get('total_clientes', 0)} | "
        contexto += f"Produtos: {stats.get('total_produtos', 0)} | "
        contexto += f"Pedidos: {stats.get('total_pedidos', 0)}\n"
        contexto += f"Vendas: R$ {stats.get('vendas_totais', 0):.2f} | "
        contexto += f"Ticket: R$ {stats.get('ticket_medio', 0):.2f}\n"
        
        # Dados recentes (apenas se existirem)
        if dados_sistema['clientes_recentes']:
            contexto += "Clientes recentes: "
            nomes = [c['nome'] for c in dados_sistema['clientes_recentes']]
            contexto += ", ".join(nomes) + "\n"
        
        if dados_sistema['pedidos_recentes']:
            contexto += "Pedidos recentes: "
            pedidos = [f"#{p['id']}(R${p['total']:.0f})" for p in dados_sistema['pedidos_recentes']]
            contexto += ", ".join(pedidos) + "\n"
        
        if dados_sistema['produtos_estoque']:
            contexto += "Produtos: "
            produtos = [f"{p['nome']}({p['estoque']})" for p in dados_sistema['produtos_estoque']]
            contexto += ", ".join(produtos)
        
        return contexto

    # ========== MÉTODOS COMPATÍVEIS ==========

    def enviar_pergunta(self, pergunta):
        """Método original mantido para compatibilidade"""
        return self.enviar_pergunta_com_contexto(pergunta)

    def testar_modelo(self):
        """Testa se o modelo responde - OTIMIZADO para modelo leve"""
        if not self.testar_conexao():
            return False, "Sem conexão"
        
        if not self.modelo_disponivel:
            return False, f"Modelo {self.modelo} não disponível"
        
        # Teste RÁPIDO com modelo leve
        try:
            payload = {
                "model": self.modelo,
                "prompt": "Diga apenas 'OK'",
                "stream": False,
                "options": {
                    "num_predict": 5,
                    "temperature": 0.1
                }
            }
            
            response = requests.post(
                f"{self.url_ollama}/api/generate",
                json=payload,
                timeout=8  # ⏱️ Timeout bem curto para teste
            )
            
            if response.status_code == 200:
                resultado = response.json()
                resposta = resultado.get('response', '').strip()
                tempo_resposta = resultado.get('total_duration', 0) / 1e9
                
                if resposta:
                    log_operacao("AGENTE_IA", f"✅ Modelo testado - Resposta em {tempo_resposta:.1f}s: {resposta}")
                    return True, f"Modelo respondendo em {tempo_resposta:.1f}s"
                else:
                    return False, "Resposta vazia do modelo"
            else:
                return False, f"Erro HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout no teste"
        except Exception as e:
            return False, f"Erro no teste: {str(e)}"

    # ... (mantenha os métodos analisar_cliente, analisar_pedidos, sugerir_produtos 
    # e métodos _basico exatamente como estavam anteriormente)

    def analisar_cliente(self, dados_cliente):
        """Análise do cliente usando IA real"""
        teste_ok, mensagem = self.testar_modelo()
        if not teste_ok:
            log_erro(f"AGENTE_IA: Não é possível usar IA - {mensagem}")
            return self._analisar_cliente_basico(dados_cliente)
        
        info_cliente = ""
        for key, value in dados_cliente.items():
            if value:
                info_cliente += f"{key}: {value}\n"
        
        contexto_adicional = f"DADOS CLIENTE:\n{info_cliente}"
        prompt = "Analise este cliente e dê insights úteis de forma curta."
        
        resposta, erro = self.enviar_pergunta_com_contexto(prompt, contexto_adicional)
        if erro:
            log_erro(f"AGENTE_IA: Erro na análise do cliente: {erro}")
            return self._analisar_cliente_basico(dados_cliente)
        return resposta

    def analisar_pedidos(self, dados_pedidos):
        """Análise dos pedidos usando IA real"""
        teste_ok, mensagem = self.testar_modelo()
        if not teste_ok:
            log_erro(f"AGENTE_IA: Não é possível usar IA - {mensagem}")
            return self._analisar_pedidos_basico(dados_pedidos)
        
        total_pedidos = len(dados_pedidos)
        total_valor = sum(pedido.get('valor_total', 0) for pedido in dados_pedidos)
        
        contexto_adicional = f"PEDIDOS: {total_pedidos} | VALOR: R$ {total_valor:.2f}"
        prompt = "Analise estes pedidos de forma curta com insights."
        
        resposta, erro = self.enviar_pergunta_com_contexto(prompt, contexto_adicional)
        if erro:
            log_erro(f"AGENTE_IA: Erro na análise de pedidos: {erro}")
            return self._analisar_pedidos_basico(dados_pedidos)
        return resposta

    def sugerir_produtos(self, dados_cliente, produtos=None):
        """Sugestão de produtos usando IA real"""
        teste_ok, mensagem = self.testar_modelo()
        if not teste_ok:
            log_erro(f"AGENTE_IA: Não é possível usar IA - {mensagem}")
            return self._sugerir_produtos_basico(dados_cliente)
        
        info_cliente = ""
        for key, value in dados_cliente.items():
            if value:
                info_cliente += f"{key}: {value}\n"
        
        contexto_adicional = f"CLIENTE:\n{info_cliente}"
        prompt = "Sugira produtos para este cliente de forma prática."
        
        resposta, erro = self.enviar_pergunta_com_contexto(prompt, contexto_adicional)
        if erro:
            log_erro(f"AGENTE_IA: Erro na sugestão de produtos: {erro}")
            return self._sugerir_produtos_basico(dados_cliente)
        return resposta

    def _analisar_cliente_basico(self, dados_cliente):
        if not dados_cliente:
            return "Não há dados de cliente disponíveis."
        
        cliente = dados_cliente
        analise = "**📊 Análise Básica do Cliente**\n\n"
        
        if cliente.get('nome'):
            analise += f"**Nome:** {cliente['nome']}\n"
        if cliente.get('email'):
            analise += f"**Email:** {cliente['email']}\n"
        if cliente.get('telefone'):
            analise += f"**Telefone:** {cliente['telefone']}\n"
        
        analise += "\n💡 *Para análise mais detalhada, verifique a conexão com a IA*"
        return analise

    def _analisar_pedidos_basico(self, dados_pedidos):
        if not dados_pedidos:
            return "Não há dados de pedidos disponíveis."
        
        total_pedidos = len(dados_pedidos)
        analise = f"**📦 Análise Básica dos Pedidos**\n\n**Total:** {total_pedidos} pedidos\n"
        
        if total_pedidos > 0:
            total_gasto = sum(pedido.get('valor_total', 0) for pedido in dados_pedidos)
            ticket_medio = total_gasto / total_pedidos
            analise += f"**Valor Total:** R$ {total_gasto:.2f}\n"
            analise += f"**Ticket Médio:** R$ {ticket_medio:.2f}\n"
        
        analise += "\n💡 *Para análise mais detalhada, verifique a conexão com a IA*"
        return analise

    def _sugerir_produtos_basico(self, dados_cliente):
        if not dados_cliente:
            return "Não há dados de cliente disponíveis."
        
        return "**🎯 Sugestões de Produtos**\n\n💡 *Para sugestões personalizadas, verifique a conexão com a IA*"

    def trocar_modelo(self, novo_modelo):
        self.modelo = novo_modelo
        self.erro_memoria = False
        self.modelo_disponivel = False
        log_operacao("AGENTE_IA", f"Modelo alterado para: {novo_modelo}")
        return self.testar_conexao()

    def get_estatisticas(self):
        return {
            "conectado": self.conectado,
            "modelo": self.modelo,
            "modelo_disponivel": self.modelo_disponivel,
            "erro_memoria": self.erro_memoria,
            "url": self.url_ollama,
            "timeout": self.timeout
        }

# Instância global
agente_ia = AgenteIA()