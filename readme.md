# 🧠 TK Clientes & Pedidos + IA (CustomTkinter)# 🧠 Tkinter Clientes & Pedidos + IA



Aplicativo em Python com CustomTkinter + SQLite para gerenciar clientes, produtos e pedidos, com relatórios avançados (CSV, PDF + IA) e sistema de logs instrumentado automaticamente.Aplicativo simples em **Python + Tkinter + SQLite** para gerenciamento de **clientes e pedidos**, com modelagem básica e uso responsável de **IA** para acelerar o desenvolvimento.



------



## 📦 Requisitos## 📁 Estrutura do Projeto



- Python 3.10+tk-clientes-pedidos/

- Dependências (instale com o comando abaixo):├─ main.py # Interface principal do app

├─ db.py # Inicialização e acesso ao banco SQLite

```powershell├─ models.py # Modelos de dados (Cliente, Pedido, ItemPedido)

pip install -r requirements.txt├─ utils.py # Funções auxiliares e logs

```│ ├─ clientes_view.py # Formulário e listagem de clientes

│ └─ pedidos_view.py # Formulário de criação de pedidos

---# 🧠 TK Clientes & Pedidos + IA (CustomTkinter)



## ▶️ Como executar (Windows / PowerShell)Aplicativo em Python com CustomTkinter + SQLite para gerenciar clientes, produtos e pedidos, com relatórios avançados (CSV, PDF + IA) e sistema de logs instrumentado automaticamente.



1) Opcional: criar e ativar venv---

```powershell

python -m venv .venv## 📦 Requisitos

.\.venv\Scripts\Activate.ps1

```- Python 3.10+

- Dependências (instale com o comando abaixo):

2) Instalar dependências

```powershell```powershell

pip install -r requirements.txtpip install -r requirements.txt

``````



3) Executar o app---

```powershell

python main.py## ▶️ Como executar (Windows / PowerShell)

```

1) Opcional: criar e ativar venv

---```powershell

python -m venv .venv

## 🖥️ Interface e Tema.\.venv\Scripts\Activate.ps1

- Interface em CustomTkinter (moderna) com tema escuro por padrão.```

- O visualizador de logs abre sempre na frente da janela principal.

- Container de resultados dos relatórios inicia vazio (sem cards iniciais).2) Instalar dependências

```powershell

---pip install -r requirements.txt

```

## 📊 Relatórios

- CSV Geral no layout horizontal (Clientes | Pedidos | Financeiro | Resumo) — compatível com Excel.3) Executar o app

- Formatação monetária BRL (R$ 1.234,56) em toda a interface e nos relatórios.```powershell

- PDF + IA: gráficos gerados em memória (BytesIO + ReportLab ImageReader), sem arquivos temporários.python main.py

- Exportações disponíveis no módulo `views/relatorios_views.py`.```



------



## 🤖 IA integrada (opcional)## 🖥️ Interface e Tema

- Usa Ollama local em http://localhost:11434.- Interface em CustomTkinter (moderna) com tema escuro por padrão.

- Modelo padrão: `qwen2.5:0.5b` (leve e rápido).- O visualizador de logs abre sempre na frente da janela principal.

- Arquivo: `agente_ia.py`.- Container de resultados dos relatórios inicia vazio (sem cards iniciais).

- Para análises executivas, gere PDF + IA em Relatórios.

---

---

## 📊 Relatórios

## 📝 Logs e Auditoria- CSV Geral no layout horizontal (Clientes | Pedidos | Financeiro | Resumo) — compatível com Excel.

- `logs.py` centraliza os logs do projeto e grava em `logs/sistema_clientes_pedidos_YYYY-MM-DD.log`.- Formatação monetária BRL (R$ 1.234,56) em toda a interface e nos relatórios.

- Visualizador: `views/logs_views.py` (CustomTkinter), com busca e destaque.- PDF + IA: gráficos gerados em memória (BytesIO + ReportLab ImageReader), sem arquivos temporários.

- Auto-logs de UI: ative após montar a tela com:- Exportações disponíveis no módulo `views/relatorios_views.py`.



```python---

from logs import enable_ui_autolog

enable_ui_autolog(root, modulo="APP")## 🤖 IA integrada (opcional)

```- Usa Ollama local em http://localhost:11434.

- Modelo padrão: `qwen2.5:0.5b` (leve e rápido).

- O autolog registra:- Arquivo: `agente_ia.py`.

  - Cliques em botões (inclui command antes/depois)- Para análises executivas, gere PDF + IA em Relatórios.

  - Edição de Entry (Enter e ao sair do campo se alterado)

  - Seleção em Combobox, Treeview e troca de abas em Notebook---



---## � Logs e Auditoria

- `logs.py` centraliza os logs do projeto e grava em `logs/sistema_clientes_pedidos_YYYY-MM-DD.log`.

## 📁 Estrutura do Projeto- Visualizador: `views/logs_views.py` (CustomTkinter), com busca e destaque.

- Auto-logs de UI: ative após montar a tela com:

```

tk-clientes-pedidos/```python

├── agente_ia.pyfrom logs import enable_ui_autolog

├── dashboard.pyenable_ui_autolog(root, modulo="APP")

├── db.py```

├── logs.py

├── main.py- O autolog registra:

├── models.py  - Cliques em botões (inclui command antes/depois)

├── popular_dados_exemplo.py  - Edição de Entry (Enter e ao sair do campo se alterado)

├── readme.md  - Seleção em Combobox, Treeview e troca de abas em Notebook

├── requirements.txt

├── Structure.md---

├── utils.py

├── __pycache__/## � Estrutura do Projeto

├── logs/

│   └──```

└── views/tk-clientes-pedidos/

    ├── __init__.py├── agente_ia.py

    ├── agente_ai_views.py├── dashboard.py

    ├── cliente_views.py├── db.py

    ├── dashboard_view.py├── logs.py

    ├── logs_views.py├── main.py

    ├── pedidos_views.py├── models.py

    ├── produtos_views.py├── popular_dados_exemplo.py

    ├── relatorios_views.py├── readme.md

    └── __pycache__/├── requirements.txt

```├── Structure.md

├── utils.py

---├── __pycache__/

├── logs/

## 🛠️ Alterações recentes (Nov/2025)│   └──

- Relatórios CSV reorganizados no formato horizontal (como no exemplo anexado).└── views/

- BRL aplicado de forma consistente em toda a UI e relatórios.    ├── __init__.py

- PDF+IA restabelecido (sem opção de PDF simples); gráficos via memória.    ├── agente_ai_views.py

- `logs_views.py` migrado para CustomTkinter e abre em primeiro plano.    ├── cliente_views.py

- `logs.py` ganhou `enable_ui_autolog` para logar ações da interface.    ├── dashboard_view.py

    ├── logs_views.py

---    ├── pedidos_views.py

    ├── produtos_views.py

## ✅ Dicas / Solução de Problemas    ├── relatorios_views.py

- Erros com PDF: verifique se `reportlab` está instalado (requirements).    └── __pycache__/

- IA não responde: confirme Ollama rodando e o modelo `qwen2.5:0.5b` disponível.```

- CSV no Excel: o arquivo usa `;` como separador e BOM UTF-8 para acentuação correta.

---

---

## 🛠️ Alterações recentes (Nov/2025)

Autor: Marcos Santos Martirio  - Relatórios CSV reorganizados no formato horizontal (como no exemplo anexado).

Data: Novembro / 2025- BRL aplicado de forma consistente em toda a UI e relatórios.

- PDF+IA restabelecido (sem opção de PDF simples); gráficos via memória.
- `logs_views.py` migrado para CustomTkinter e abre em primeiro plano.
- `logs.py` ganhou `enable_ui_autolog` para logar ações da interface.

---

## ✅ Dicas / Solução de Problemas
- Erros com PDF: verifique se `reportlab` está instalado (requirements).
- IA não responde: confirme Ollama rodando e o modelo `qwen2.5:0.5b` disponível.
- CSV no Excel: o arquivo usa `;` como separador e BOM UTF-8 para acentuação correta.

---

Autor: Marcos Santos Martirio  
Disciplina: Desenvolvimento Rápido em Python  
Professor: Mariano  
Data: Novembro / 2025


