import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import json
import os
from datetime import datetime

class Pessoa:
    def __init__(self, nome):
        self.nome = nome
        self.despesas = []
        
    def adicionar_despesa(self, descricao, valor):
        self.despesas.append({"descricao": descricao, "valor": valor})
        
    def total(self):
        return sum(item["valor"] for item in self.despesas)
        
    def to_dict(self):
        return {
            "nome": self.nome,
            "despesas": self.despesas,
            "total": self.total()
        }

class FaturaAvancadaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Faturas - v2.0")
        self.root.geometry("900x700")
        
        # Configuração do tema
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("Heading.TLabel", font=("Arial", 14, "bold"))
        self.style.configure("Result.TLabel", font=("Arial", 12))
        self.style.configure("Primary.TButton", background="#4CAF50", foreground="white")
        self.style.configure("Secondary.TButton", background="#f0f0f0")
        
        # Variáveis
        self.pessoas = {}
        self.historico = []
        self.arquivo_atual = None
        
        # Criar interface
        self.criar_interface()
        
    def criar_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior - barra de ferramentas
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=5)
        
        # Botões da barra de ferramentas
        ttk.Button(toolbar_frame, text="Novo", command=self.novo_arquivo, style="Secondary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Abrir", command=self.abrir_arquivo, style="Secondary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Salvar", command=self.salvar_arquivo, style="Secondary.TButton").pack(side=tk.LEFT, padx=2)
        
        # Frame para o título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=10)
        ttk.Label(title_frame, text="Calculadora de Faturas por Pessoa", 
                  style="Heading.TLabel").pack()
        
        # Frame de conteúdo - dividido em duas colunas
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Coluna esquerda - entrada de texto
        left_frame = ttk.Frame(content_frame, padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_frame, text="Insira os itens (um por linha):").pack(anchor=tk.W)
        
        # Área de texto com rolagem
        text_frame = ttk.Frame(left_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.text_area = tk.Text(text_frame, height=25, width=50, font=("Consolas", 11))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Entrada para o nome da pessoa
        pessoa_frame = ttk.Frame(left_frame)
        pessoa_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(pessoa_frame, text="Nome da pessoa:").pack(side=tk.LEFT, padx=5)
        self.pessoa_entry = ttk.Entry(pessoa_frame, width=20)
        self.pessoa_entry.pack(side=tk.LEFT, padx=5)
        self.pessoa_entry.insert(0, "Geral")
        
        # Botões de ação
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Processar Faturas", 
                  command=self.processar_faturas, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar", 
                  command=self.limpar_texto).pack(side=tk.LEFT, padx=5)
        
        # Coluna direita - resultados
        right_frame = ttk.Frame(content_frame, padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_frame, text="Resultados:").pack(anchor=tk.W)
        
        # Área de resultados com rolagem
        result_frame = ttk.Frame(right_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_area = tk.Text(result_frame, height=25, width=40, font=("Consolas", 11), state="disabled")
        result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_area.yview)
        self.result_area.configure(yscrollcommand=result_scrollbar.set)
        
        self.result_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Resumo dos totais
        self.total_label = ttk.Label(right_frame, text="Total: R$ 0,00", style="Result.TLabel")
        self.total_label.pack(anchor=tk.W, pady=10)
        
        # Botões de ação para resultados
        result_button_frame = ttk.Frame(right_frame)
        result_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(result_button_frame, text="Exportar Resultados", 
                  command=self.exportar_resultados).pack(side=tk.LEFT, padx=5)
        
        # Barra de status
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def processar_faturas(self):
        texto = self.text_area.get("1.0", tk.END).strip()
        linhas = texto.splitlines()
        nome_pessoa = self.pessoa_entry.get().strip()
        
        if not nome_pessoa:
            messagebox.showerror("Erro", "Por favor, insira o nome da pessoa.")
            return
            
        if not texto:
            messagebox.showerror("Erro", "Por favor, insira os itens da fatura.")
            return
            
        # Criar ou obter pessoa
        if nome_pessoa not in self.pessoas:
            self.pessoas[nome_pessoa] = Pessoa(nome_pessoa)
            
        pessoa = self.pessoas[nome_pessoa]
        
        # Processar despesas
        total_processado = 0.0
        resultado = f"Despesas de {nome_pessoa}:\n"
        resultado += "-" * 40 + "\n"
        
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
                
            # Procura valor no formato "XX,XX" ou "X.XXX,XX" no final da linha
            match = re.search(r"([\d.]+,\d{2})$", linha)
            
            if match:
                # Extrair descrição e valor
                valor_str = match.group(1)
                descricao = linha[:linha.rfind(valor_str)].strip()
                
                # Converter valor para float
                valor_float = float(valor_str.replace(".", "").replace(",", "."))
                
                # Adicionar à pessoa
                pessoa.adicionar_despesa(descricao, valor_float)
                total_processado += valor_float
                
                resultado += f"{descricao}: R$ {valor_float:.2f}\n"
            else:
                resultado += f"{linha}: Formato inválido\n"
                
        # Exibir resultados
        resultado += "-" * 40 + "\n"
        resultado += f"Subtotal para {nome_pessoa}: R$ {total_processado:.2f}\n\n"
        
        # Calcular total geral
        total_geral = sum(p.total() for p in self.pessoas.values())
        resultado += "Resumo por pessoa:\n"
        resultado += "-" * 40 + "\n"
        
        for nome, p in self.pessoas.items():
            resultado += f"{nome}: R$ {p.total():.2f}\n"
            
        resultado += "-" * 40 + "\n"
        resultado += f"TOTAL GERAL: R$ {total_geral:.2f}"
        
        # Atualizar interface
        self.result_area.config(state="normal")
        self.result_area.delete("1.0", tk.END)
        self.result_area.insert("1.0", resultado)
        self.result_area.config(state="disabled")
        
        self.total_label.config(text=f"Total Geral: R$ {total_geral:.2f}")
        
        # Adicionar ao histórico
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.historico.append({
            "timestamp": timestamp,
            "pessoa": nome_pessoa,
            "total": total_processado
        })
        
        self.status_var.set(f"Processado com sucesso: {len(linhas)} itens para {nome_pessoa}")
        
    def limpar_texto(self):
        self.text_area.delete("1.0", tk.END)
        
    def novo_arquivo(self):
        if messagebox.askyesno("Novo", "Deseja criar um novo arquivo? Os dados não salvos serão perdidos."):
            self.pessoas = {}
            self.historico = []
            self.arquivo_atual = None
            self.text_area.delete("1.0", tk.END)
            self.result_area.config(state="normal")
            self.result_area.delete("1.0", tk.END)
            self.result_area.config(state="disabled")
            self.total_label.config(text="Total: R$ 0,00")
            self.status_var.set("Novo arquivo criado")
            
    def abrir_arquivo(self):
        filename = filedialog.askopenfilename(
            title="Abrir Arquivo",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os Arquivos", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.pessoas = {}
                for pessoa_data in data.get("pessoas", []):
                    nome = pessoa_data["nome"]
                    pessoa = Pessoa(nome)
                    for despesa in pessoa_data.get("despesas", []):
                        pessoa.adicionar_despesa(despesa["descricao"], despesa["valor"])
                    self.pessoas[nome] = pessoa
                    
                self.historico = data.get("historico", [])
                self.arquivo_atual = filename
                
                # Atualizar interface
                total_geral = sum(p.total() for p in self.pessoas.values())
                resultado = "Arquivo carregado com sucesso!\n\n"
                resultado += "Resumo por pessoa:\n"
                resultado += "-" * 40 + "\n"
                
                for nome, p in self.pessoas.items():
                    resultado += f"{nome}: R$ {p.total():.2f}\n"
                    
                resultado += "-" * 40 + "\n"
                resultado += f"TOTAL GERAL: R$ {total_geral:.2f}"
                
                self.result_area.config(state="normal")
                self.result_area.delete("1.0", tk.END)
                self.result_area.insert("1.0", resultado)
                self.result_area.config(state="disabled")
                
                self.total_label.config(text=f"Total Geral: R$ {total_geral:.2f}")
                self.status_var.set(f"Arquivo aberto: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao abrir o arquivo: {str(e)}")
                
    def salvar_arquivo(self):
        if not self.arquivo_atual:
            filename = filedialog.asksaveasfilename(
                title="Salvar Como",
                defaultextension=".json",
                filetypes=[("Arquivos JSON", "*.json"), ("Todos os Arquivos", "*.*")]
            )
            if not filename:
                return
            self.arquivo_atual = filename
            
        try:
            data = {
                "pessoas": [p.to_dict() for p in self.pessoas.values()],
                "historico": self.historico,
                "data_salvamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.arquivo_atual, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.status_var.set(f"Arquivo salvo: {os.path.basename(self.arquivo_atual)}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {str(e)}")
            
    def exportar_resultados(self):
        if not self.pessoas:
            messagebox.showinfo("Informação", "Não há resultados para exportar.")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Exportar Resultados",
            defaultextension=".txt",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("RELATÓRIO DE DESPESAS\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                    
                    for nome, pessoa in self.pessoas.items():
                        f.write(f"Despesas de {nome}:\n")
                        f.write("-" * 50 + "\n")
                        
                        for despesa in pessoa.despesas:
                            f.write(f"{despesa['descricao']}: R$ {despesa['valor']:.2f}\n")
                            
                        f.write("-" * 50 + "\n")
                        f.write(f"Subtotal para {nome}: R$ {pessoa.total():.2f}\n\n")
                    
                    total_geral = sum(p.total() for p in self.pessoas.values())
                    f.write("=" * 50 + "\n")
                    f.write(f"TOTAL GERAL: R$ {total_geral:.2f}\n")
                    
                self.status_var.set(f"Resultados exportados para: {os.path.basename(filename)}")
                messagebox.showinfo("Sucesso", "Resultados exportados com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar resultados: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FaturaAvancadaApp(root)
    root.mainloop()