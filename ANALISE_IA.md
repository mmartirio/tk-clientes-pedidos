# 🤖 Análise de Pedidos com IA

## Visão Geral

A função `analisar_pedidos()` localizada em `utils.py` integra com o agente de IA central do projeto (`agente_ia.py`) para gerar insights automáticos sobre o desempenho de vendas.

## Dados Retornados

A análise fornece três categorias de informações:

### 1. Produtos Mais Vendidos (Top 10)
Para cada produto:
- **produto**: Nome do produto
- **quantidade_vendida**: Total de unidades vendidas
- **num_pedidos**: Número de pedidos contendo o produto
- **receita**: Receita total gerada pelo produto
- **preco_medio**: Preço médio praticado

### 2. Métricas Gerais
- **total_pedidos**: Quantidade total de pedidos no período
- **receita_total**: Soma de todas as vendas
- **ticket_medio**: Valor médio por pedido

### 3. Insights da IA
Análise textual gerada pelo modelo de IA com:
- Oportunidades identificadas
- Riscos potenciais
- Recomendações práticas e objetivas
- Próximos passos sugeridos

## Prompt Utilizado

O seguinte prompt é enviado ao agente de IA junto com os dados consolidados:

```
Analise estes dados de vendas e traga os principais insights em até 300 palavras, 
com foco em ações práticas: oportunidades, riscos, recomendações objetivas e próximos passos.
```

**Contexto incluído automaticamente:**
- Métricas gerais (pedidos, receita, ticket médio)
- Top 10 produtos com detalhamento completo (quantidade, pedidos, receita, preço médio)

## Configuração Técnica

### Agente de IA
- **Servidor**: Ollama local em http://localhost:11434
- **Modelo padrão**: `qwen2.5:0.5b` (otimizado para performance)
- **Arquivo**: `agente_ia.py`
- **Método**: `enviar_pergunta_com_contexto(pergunta, contexto_adicional)`

### Parâmetros da Função

```python
analisar_pedidos(
    db_path='clientes_pedidos.db',  # Caminho do banco SQLite
    modelo=None,                      # Modelo IA (None usa padrão)
    periodo_dias=30                   # Período de análise em dias
)
```

### Retorno

```python
{
    'produtos_mais_vendidos': [
        {
            'produto': str,
            'quantidade_vendida': int,
            'num_pedidos': int,
            'receita': float,
            'preco_medio': float
        },
        # ... até 10 produtos
    ],
    'metricas': {
        'total_pedidos': int,
        'receita_total': float,
        'ticket_medio': float
    },
    'analise_ia': str,  # Texto gerado pela IA
    'sucesso': bool,
    'erro': str | None
}
```

## Interface do Usuário

### Acesso
1. Navegar para o módulo **Pedidos** no menu principal
2. Clicar no botão **"Analisar Pedidos"** (centralizado ao lado de Cadastro e Listar)

### Fluxo de Execução
1. **Carregamento**: Exibe "Análise de pedidos está sendo gerada..."
2. **Processamento**: Consulta banco de dados e envia dados para IA
3. **Resultado**: Substitui tela de carregamento pela análise completa

### Visualização
- Widget de texto com **rolagem automática** (CTkTextbox)
- Formatação fixa em fonte **Courier New** para alinhamento
- Formato BRL para valores monetários: **R$ 1.234,56**
- Somente leitura (não editável)
- Estrutura organizada:
  - Cabeçalho com título e período
  - Seção de métricas gerais
  - Lista top 10 produtos formatada
  - Insights da IA em texto corrido

### Tratamento de Erros
- Se IA indisponível: exibe dados consolidados sem análise textual
- Se erro no banco: retorna à tela de cadastro com mensagem
- Logs automáticos registrados em `logs/`

## Exemplo de Saída

```
═══════════════════════════════════════
ANÁLISE DE PEDIDOS - ÚLTIMOS 30 DIAS
═══════════════════════════════════════

MÉTRICAS GERAIS

- Total de pedidos: 86
- Receita total: R$ 124.567,89
- Ticket médio: R$ 1.448,46

TOP 10 PRODUTOS MAIS VENDIDOS

1. Notebook Dell Inspiron
   - Quantidade vendida: 15
   - Presente em 15 pedidos
   - Receita: R$ 67.485,00
   - Preço médio: R$ 4.499,00

2. Mouse Logitech MX Master
   - Quantidade vendida: 28
   - Presente em 22 pedidos
   - Receita: R$ 8.372,00
   - Preço médio: R$ 299,00

[...]

═══════════════════════════════════════
INSIGHTS DA IA
═══════════════════════════════════════

[Texto gerado pela IA com análise contextualizada]
```

## Integração com o Sistema

- **Módulo principal**: `views/pedidos_views.py`
- **Método handler**: `_analisar_pedidos()`
- **Container de exibição**: `self.container_conteudo` (compartilhado com Cadastro e Listar)
- **Logs**: Registrados automaticamente via `logs.py`

## Dependências

- `sqlite3`: consultas ao banco de dados
- `datetime`, `timedelta`: cálculo de períodos
- `agente_ia`: módulo de integração com IA
- `customtkinter`: interface gráfica moderna

---

**Autor**: Marcos Santos Martirio  
**Disciplina**: Desenvolvimento Rápido em Python  
**Professor**: Mariano  
**Data**: Novembro/2025
