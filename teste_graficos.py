"""
Script de teste para verificar se os gráficos estão funcionando
"""
import tkinter as tk
import customtkinter as ctk
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

def teste_grafico():
    root = ctk.CTk()
    root.title("Teste de Gráficos")
    root.geometry("800x600")
    
    frame = ctk.CTkFrame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Criar gráfico de teste
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.add_subplot(111)
    
    # Dados de teste
    datas = ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05']
    valores = [100, 150, 120, 180, 200]
    
    ax.bar(datas, valores, color='#3498db', alpha=0.8, edgecolor='black')
    ax.set_title('Teste de Gráfico de Barras', fontsize=14, fontweight='bold')
    ax.set_ylabel('Valores', fontsize=11)
    ax.set_xlabel('Datas', fontsize=11)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Adicionar valores nas barras
    for i, (data, valor) in enumerate(zip(datas, valores)):
        ax.text(i, valor + 5, str(valor), ha='center', va='bottom', fontweight='bold')
    
    fig.tight_layout()
    
    # Adicionar ao frame
    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Botão de fechar
    btn_fechar = ctk.CTkButton(
        frame,
        text="✅ Gráfico funcionando! Fechar",
        command=root.destroy,
        fg_color="#2ecc71",
        hover_color="#27ae60"
    )
    btn_fechar.pack(pady=10)
    
    print("✅ Gráfico gerado com sucesso!")
    print("Se você vê o gráfico na janela, os relatórios devem funcionar corretamente.")
    
    root.mainloop()

if __name__ == "__main__":
    print("Testando geração de gráficos...")
    teste_grafico()
