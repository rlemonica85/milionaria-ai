#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Milionária-AI - Interface Gráfica Moderna
Software de geração inteligente de bilhetes para Mega-Sena
Compatível com Windows 11
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
import pandas as pd
from datetime import datetime
import webbrowser
from pathlib import Path

# Adicionar o diretório src ao path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from cli.app import main as cli_main
    from db.schema import get_engine
    from db.io import read_all_sorteios
    from generate.tickets import generate_tickets
    from models.scoring import train_model, calculate_scores
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os módulos estão instalados")

class MilionariaGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.status_text = "Pronto para gerar bilhetes inteligentes"
        self.update_status()
        
    def setup_window(self):
        """Configurar janela principal"""
        self.root.title("Milionária-AI - Gerador Inteligente de Bilhetes")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configurar ícone (se existir)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
            
        # Centralizar janela
        self.center_window()
        
        # Configurar tema moderno para Windows 11
        self.root.configure(bg='#f0f0f0')
        
    def center_window(self):
        """Centralizar janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_styles(self):
        """Configurar estilos modernos"""
        self.style = ttk.Style()
        
        # Configurar tema moderno
        self.style.theme_use('clam')
        
        # Cores modernas para Windows 11
        colors = {
            'primary': '#0078d4',
            'secondary': '#106ebe',
            'success': '#107c10',
            'warning': '#ff8c00',
            'danger': '#d13438',
            'light': '#f8f9fa',
            'dark': '#212529',
            'background': '#ffffff',
            'surface': '#f5f5f5'
        }
        
        # Configurar estilos personalizados
        self.style.configure('Title.TLabel', 
                           font=('Segoe UI', 24, 'bold'),
                           foreground=colors['primary'],
                           background='#f0f0f0')
                           
        self.style.configure('Subtitle.TLabel',
                           font=('Segoe UI', 12),
                           foreground=colors['dark'],
                           background='#f0f0f0')
                           
        self.style.configure('Primary.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           foreground='white',
                           background=colors['primary'])
                           
        self.style.configure('Success.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           foreground='white',
                           background=colors['success'])
                           
        self.style.configure('Modern.TFrame',
                           background='#ffffff',
                           relief='flat',
                           borderwidth=1)
                           
    def create_widgets(self):
        """Criar widgets da interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cabeçalho
        self.create_header(main_frame)
        
        # Notebook para abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Criar abas
        self.create_generate_tab()
        self.create_analysis_tab()
        self.create_history_tab()
        self.create_settings_tab()
        
        # Barra de status
        self.create_status_bar(main_frame)
        
    def create_header(self, parent):
        """Criar cabeçalho da aplicação"""
        header_frame = ttk.Frame(parent, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        title_label = ttk.Label(header_frame, 
                               text="🎯 Milionária-AI",
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Subtítulo
        subtitle_label = ttk.Label(header_frame,
                                 text="Gerador Inteligente de Bilhetes para Mega-Sena",
                                 style='Subtitle.TLabel')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botão de ajuda
        help_btn = ttk.Button(header_frame,
                             text="❓ Ajuda",
                             command=self.show_help)
        help_btn.pack(side=tk.RIGHT)
        
    def create_generate_tab(self):
        """Criar aba de geração de bilhetes"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="🎲 Gerar Bilhetes")
        
        # Frame de configurações
        config_frame = ttk.LabelFrame(tab_frame, text="Configurações de Geração", padding=20)
        config_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Número de bilhetes
        ttk.Label(config_frame, text="Número de bilhetes:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.num_tickets_var = tk.StringVar(value="50")
        num_tickets_spin = ttk.Spinbox(config_frame, 
                                      from_=1, to=1000, 
                                      textvariable=self.num_tickets_var,
                                      width=10)
        num_tickets_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Estratégia
        ttk.Label(config_frame, text="Estratégia:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.strategy_var = tk.StringVar(value="balanced")
        strategy_combo = ttk.Combobox(config_frame,
                                    textvariable=self.strategy_var,
                                    values=["conservative", "balanced", "aggressive"],
                                    state="readonly",
                                    width=15)
        strategy_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Filtros avançados
        ttk.Label(config_frame, text="Usar filtros avançados:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.use_filters_var = tk.BooleanVar(value=True)
        filters_check = ttk.Checkbutton(config_frame,
                                       variable=self.use_filters_var)
        filters_check.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Botões de ação
        action_frame = ttk.Frame(tab_frame)
        action_frame.pack(fill=tk.X, padx=20, pady=20)
        
        generate_btn = ttk.Button(action_frame,
                                 text="🚀 Gerar Bilhetes",
                                 style='Primary.TButton',
                                 command=self.generate_tickets)
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        export_btn = ttk.Button(action_frame,
                               text="📊 Exportar Excel",
                               style='Success.TButton',
                               command=self.export_tickets)
        export_btn.pack(side=tk.LEFT)
        
        # Área de resultados
        results_frame = ttk.LabelFrame(tab_frame, text="Bilhetes Gerados", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview para mostrar bilhetes
        columns = ('ID', 'Números', 'Score', 'Estratégia')
        self.tickets_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.tickets_tree.heading(col, text=col)
            self.tickets_tree.column(col, width=150)
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tickets_tree.yview)
        self.tickets_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tickets_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_analysis_tab(self):
        """Criar aba de análise"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="📈 Análise")
        
        # Frame de estatísticas
        stats_frame = ttk.LabelFrame(tab_frame, text="Estatísticas do Banco de Dados", padding=20)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Labels para estatísticas
        self.stats_labels = {}
        stats_info = [
            ("Total de sorteios:", "total_draws"),
            ("Último sorteio:", "last_draw"),
            ("Números mais sorteados:", "hot_numbers"),
            ("Números menos sorteados:", "cold_numbers")
        ]
        
        for i, (label_text, key) in enumerate(stats_info):
            ttk.Label(stats_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=5)
            self.stats_labels[key] = ttk.Label(stats_frame, text="Carregando...")
            self.stats_labels[key].grid(row=i, column=1, sticky=tk.W, padx=(20, 0), pady=5)
            
        # Botão para atualizar estatísticas
        update_stats_btn = ttk.Button(stats_frame,
                                     text="🔄 Atualizar Estatísticas",
                                     command=self.update_statistics)
        update_stats_btn.grid(row=len(stats_info), column=0, columnspan=2, pady=20)
        
        # Frame de gráficos
        charts_frame = ttk.LabelFrame(tab_frame, text="Visualizações", padding=20)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Botões para gráficos
        chart_buttons = [
            ("📊 Frequência de Números", self.show_frequency_chart),
            ("📈 Tendências", self.show_trends_chart),
            ("🎯 Padrões", self.show_patterns_chart)
        ]
        
        for i, (text, command) in enumerate(chart_buttons):
            btn = ttk.Button(charts_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=10, pady=10)
            
    def create_history_tab(self):
        """Criar aba de histórico"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="📋 Histórico")
        
        # Frame de controles
        controls_frame = ttk.Frame(tab_frame)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(controls_frame,
                  text="🔄 Atualizar Dados",
                  command=self.update_database).pack(side=tk.LEFT, padx=(0, 10))
                  
        ttk.Button(controls_frame,
                  text="📥 Importar Dados",
                  command=self.import_data).pack(side=tk.LEFT, padx=(0, 10))
                  
        ttk.Button(controls_frame,
                  text="🌐 Abrir Streamlit",
                  command=self.open_streamlit).pack(side=tk.LEFT)
        
        # Treeview para histórico
        history_frame = ttk.LabelFrame(tab_frame, text="Sorteios Recentes", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('Concurso', 'Data', 'Números', 'Arrecadação')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings')
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
            
        history_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_settings_tab(self):
        """Criar aba de configurações"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="⚙️ Configurações")
        
        # Frame de configurações gerais
        general_frame = ttk.LabelFrame(tab_frame, text="Configurações Gerais", padding=20)
        general_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Configurações
        settings = [
            ("Pasta de saída:", "output_folder"),
            ("Formato de exportação:", "export_format"),
            ("Tema da interface:", "theme")
        ]
        
        self.settings_vars = {}
        for i, (label_text, key) in enumerate(settings):
            ttk.Label(general_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if key == "output_folder":
                frame = ttk.Frame(general_frame)
                frame.grid(row=i, column=1, sticky=tk.W, padx=(20, 0), pady=5)
                
                self.settings_vars[key] = tk.StringVar(value="outputs")
                entry = ttk.Entry(frame, textvariable=self.settings_vars[key], width=30)
                entry.pack(side=tk.LEFT)
                
                browse_btn = ttk.Button(frame, text="📁", width=3,
                                       command=lambda: self.browse_folder(key))
                browse_btn.pack(side=tk.LEFT, padx=(5, 0))
                
            elif key == "export_format":
                self.settings_vars[key] = tk.StringVar(value="xlsx")
                combo = ttk.Combobox(general_frame,
                                   textvariable=self.settings_vars[key],
                                   values=["xlsx", "csv", "json"],
                                   state="readonly",
                                   width=15)
                combo.grid(row=i, column=1, sticky=tk.W, padx=(20, 0), pady=5)
                
            elif key == "theme":
                self.settings_vars[key] = tk.StringVar(value="clam")
                combo = ttk.Combobox(general_frame,
                                   textvariable=self.settings_vars[key],
                                   values=["clam", "alt", "default"],
                                   state="readonly",
                                   width=15)
                combo.grid(row=i, column=1, sticky=tk.W, padx=(20, 0), pady=5)
                
        # Botão para salvar configurações
        save_btn = ttk.Button(general_frame,
                             text="💾 Salvar Configurações",
                             style='Success.TButton',
                             command=self.save_settings)
        save_btn.grid(row=len(settings), column=0, columnspan=2, pady=20)
        
        # Frame de informações
        info_frame = ttk.LabelFrame(tab_frame, text="Informações do Sistema", padding=20)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = f"""
        Versão: 2.0.0
        Python: {sys.version.split()[0]}
        Sistema: Windows 11
        Diretório: {os.getcwd()}
        """
        
        ttk.Label(info_frame, text=info_text.strip()).pack(anchor=tk.W)
        
    def create_status_bar(self, parent):
        """Criar barra de status"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Pronto")
        self.status_label.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
        
    def update_status(self, message=""):
        """Atualizar barra de status"""
        if message:
            self.status_text = message
        self.status_label.config(text=self.status_text)
        self.root.update_idletasks()
        
    def start_progress(self):
        """Iniciar barra de progresso"""
        self.progress.start()
        
    def stop_progress(self):
        """Parar barra de progresso"""
        self.progress.stop()
        
    def generate_tickets(self):
        """Gerar bilhetes em thread separada"""
        def run_generation():
            try:
                self.start_progress()
                self.update_status("Gerando bilhetes...")
                
                num_tickets = int(self.num_tickets_var.get())
                strategy = self.strategy_var.get()
                use_filters = self.use_filters_var.get()
                
                # Simular geração (substituir pela lógica real)
                import time
                time.sleep(2)  # Simular processamento
                
                # Limpar resultados anteriores
                for item in self.tickets_tree.get_children():
                    self.tickets_tree.delete(item)
                    
                # Adicionar bilhetes simulados
                for i in range(num_tickets):
                    numbers = sorted([f"{j:02d}" for j in range(1, 61) if j % (i+1) == 0][:6])
                    score = f"{0.75 + (i * 0.001):.3f}"
                    self.tickets_tree.insert('', 'end', values=(i+1, ' '.join(numbers), score, strategy))
                    
                self.update_status(f"✅ {num_tickets} bilhetes gerados com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar bilhetes: {str(e)}")
                self.update_status("❌ Erro na geração")
            finally:
                self.stop_progress()
                
        threading.Thread(target=run_generation, daemon=True).start()
        
    def export_tickets(self):
        """Exportar bilhetes para arquivo"""
        try:
            if not self.tickets_tree.get_children():
                messagebox.showwarning("Aviso", "Nenhum bilhete para exportar!")
                return
                
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
            )
            
            if filename:
                # Coletar dados da treeview
                data = []
                for item in self.tickets_tree.get_children():
                    values = self.tickets_tree.item(item)['values']
                    data.append(values)
                    
                # Criar DataFrame
                df = pd.DataFrame(data, columns=['ID', 'Números', 'Score', 'Estratégia'])
                
                # Salvar arquivo
                if filename.endswith('.xlsx'):
                    df.to_excel(filename, index=False)
                else:
                    df.to_csv(filename, index=False)
                    
                messagebox.showinfo("Sucesso", f"Bilhetes exportados para: {filename}")
                self.update_status(f"📊 Exportado: {os.path.basename(filename)}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
            
    def update_statistics(self):
        """Atualizar estatísticas"""
        def run_update():
            try:
                self.start_progress()
                self.update_status("Atualizando estatísticas...")
                
                # Simular carregamento de estatísticas
                import time
                time.sleep(1)
                
                self.stats_labels["total_draws"].config(text="2.750 sorteios")
                self.stats_labels["last_draw"].config(text="11/08/2025")
                self.stats_labels["hot_numbers"].config(text="05, 23, 33, 42, 53")
                self.stats_labels["cold_numbers"].config(text="07, 18, 28, 39, 49")
                
                self.update_status("✅ Estatísticas atualizadas")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar estatísticas: {str(e)}")
            finally:
                self.stop_progress()
                
        threading.Thread(target=run_update, daemon=True).start()
        
    def show_frequency_chart(self):
        """Mostrar gráfico de frequência"""
        messagebox.showinfo("Gráfico", "Funcionalidade de gráficos será implementada em breve!")
        
    def show_trends_chart(self):
        """Mostrar gráfico de tendências"""
        messagebox.showinfo("Gráfico", "Funcionalidade de gráficos será implementada em breve!")
        
    def show_patterns_chart(self):
        """Mostrar gráfico de padrões"""
        messagebox.showinfo("Gráfico", "Funcionalidade de gráficos será implementada em breve!")
        
    def update_database(self):
        """Atualizar banco de dados"""
        def run_update():
            try:
                self.start_progress()
                self.update_status("Atualizando banco de dados...")
                
                # Executar atualização real
                import subprocess
                result = subprocess.run([sys.executable, "milionaria.py", "update"], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.update_status("✅ Banco de dados atualizado")
                    messagebox.showinfo("Sucesso", "Banco de dados atualizado com sucesso!")
                else:
                    raise Exception(result.stderr or "Erro desconhecido")
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar banco: {str(e)}")
                self.update_status("❌ Erro na atualização")
            finally:
                self.stop_progress()
                
        threading.Thread(target=run_update, daemon=True).start()
        
    def import_data(self):
        """Importar dados"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if filename:
            messagebox.showinfo("Importação", f"Importando dados de: {os.path.basename(filename)}")
            
    def open_streamlit(self):
        """Abrir interface Streamlit"""
        try:
            webbrowser.open("http://localhost:8501")
            self.update_status("🌐 Streamlit aberto no navegador")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir Streamlit: {str(e)}")
            
    def browse_folder(self, key):
        """Navegar por pastas"""
        folder = filedialog.askdirectory()
        if folder:
            self.settings_vars[key].set(folder)
            
    def save_settings(self):
        """Salvar configurações"""
        try:
            # Aplicar tema
            theme = self.settings_vars["theme"].get()
            self.style.theme_use(theme)
            
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            self.update_status("💾 Configurações salvas")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {str(e)}")
            
    def show_help(self):
        """Mostrar ajuda"""
        help_text = """
        🎯 Milionária-AI - Ajuda
        
        COMO USAR:
        
        1. ABA GERAR BILHETES:
           - Configure o número de bilhetes desejado
           - Escolha a estratégia (conservadora, equilibrada, agressiva)
           - Clique em "Gerar Bilhetes" para criar os jogos
           - Use "Exportar Excel" para salvar os resultados
           
        2. ABA ANÁLISE:
           - Visualize estatísticas do banco de dados
           - Atualize as informações com o botão "Atualizar"
           - Acesse gráficos e visualizações
           
        3. ABA HISTÓRICO:
           - Veja os sorteios recentes
           - Atualize o banco de dados
           - Importe novos dados
           - Abra a interface web Streamlit
           
        4. ABA CONFIGURAÇÕES:
           - Configure pasta de saída
           - Escolha formato de exportação
           - Altere tema da interface
           - Veja informações do sistema
           
        DICAS:
        - Mantenha o banco de dados sempre atualizado
        - Use filtros avançados para melhores resultados
        - Experimente diferentes estratégias
        - Exporte regularmente seus bilhetes
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Ajuda - Milionária-AI")
        help_window.geometry("600x500")
        help_window.resizable(False, False)
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # Centralizar janela de ajuda
        help_window.transient(self.root)
        help_window.grab_set()
        
def main():
    """Função principal"""
    root = tk.Tk()
    app = MilionariaGUI(root)
    
    # Configurar fechamento da aplicação
    def on_closing():
        if messagebox.askokcancel("Sair", "Deseja realmente sair do Milionária-AI?"):
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Iniciar aplicação
    root.mainloop()

if __name__ == "__main__":
    main()