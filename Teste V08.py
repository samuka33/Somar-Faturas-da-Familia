import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import re
import json
import os
from datetime import datetime


class Pessoa:
    def __init__(self, nome):
        self.nome = nome
        # Cada despesa é armazenada como: {"raw_line": <texto digitado>, "valor": <valor numérico>}
        self.despesas = []
        self.pago = 0.0

    def adicionar_despesa(self, raw_line, valor):
        self.despesas.append({"raw_line": raw_line, "valor": valor})

    def total(self):
        return sum(item["valor"] for item in self.despesas)

    def to_dict(self):
        return {
            "nome": self.nome,
            "despesas": [{"raw_line": d["raw_line"], "valor": d["valor"]} for d in self.despesas],
            "total": self.total(),
            "pago": self.pago
        }


class FaturaAvancadaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Faturas - v2.1")
        self.root.geometry("1200x900")
        self.root.minsize(1200, 900)

        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Temas
        self.tema_claro = {
            "bg_color": "#ffffff",
            "text_color": "#000000",
            "accent_color": "#0078d7",
            "button_color": "#e0e0e0",
            "frame_color": "#f2f2f2",
            "highlight_color": "#dcdcdc",
            "input_bg": "#ffffff"
        }
        self.tema_escuro = {
            "bg_color": "#2e2e2e",
            "text_color": "#ffffff",
            "accent_color": "#4a90e2",
            "button_color": "#3e3e3e",
            "frame_color": "#4b4b4b",
            "highlight_color": "#5a5a5a",
            "input_bg": "#3e3e3e"
        }
        self.aplicar_tema(self.tema_claro)

        # Dados – self.pessoas guarda os objetos; self.historico_order guarda a ordem de exibição na aba Histório
        self.pessoas = {}
        self.historico_order = []  # Lista com nomes (strings) na ordem desejada na aba Histórico
        self.arquivo_atual = None

        self.criar_interface()

    def aplicar_tema(self, tema):
        self.bg_color = tema["bg_color"]
        self.text_color = tema["text_color"]
        self.accent_color = tema["accent_color"]
        self.button_color = tema["button_color"]
        self.frame_color = tema["frame_color"]
        self.highlight_color = tema["highlight_color"]
        self.input_bg = tema["input_bg"]

        self.style.configure("TFrame", background=self.frame_color)
        self.style.configure("TLabel", background=self.frame_color, foreground=self.text_color)
        self.style.configure("TButton", background=self.button_color, foreground=self.text_color, padding=6, relief="flat")
        self.style.map("TButton", background=[("active", self.highlight_color)])
        self.style.configure("Heading.TLabel", font=("Arial", 14, "bold"), foreground=self.text_color, background=self.frame_color)
        self.style.configure("Result.TLabel", font=("Arial", 12), foreground=self.text_color, background=self.frame_color)
        self.style.configure("Primary.TButton", background=self.accent_color, foreground=self.text_color)
        self.style.map("Primary.TButton", background=[("active", "#005a9e")])
        self.style.configure("Secondary.TButton", background=self.button_color, foreground=self.text_color)
        self.style.map("TEntry", fieldbackground=self.input_bg, foreground=self.text_color)
        self.style.configure("TCombobox", fieldbackground=self.input_bg, background=self.button_color, foreground=self.text_color)
        self.style.map("TCombobox", fieldbackground=[("readonly", self.input_bg)])
        self.style.configure("Treeview", background=self.input_bg, foreground=self.text_color, fieldbackground=self.input_bg)
        self.style.map("Treeview", background=[("selected", self.accent_color)])

        self.root.configure(bg=self.bg_color)
        try:
            self.text_area.config(bg=self.input_bg, fg=self.text_color, insertbackground=self.text_color)
            self.result_area.config(bg=self.input_bg, fg=self.text_color)
        except Exception:
            pass

    def criar_interface(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Barra de ferramentas
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=5)
        ttk.Button(toolbar_frame, text="Novo", command=self.novo_arquivo, style="Secondary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Abrir", command=self.abrir_arquivo, style="Secondary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Salvar", command=self.salvar_arquivo, style="Secondary.TButton").pack(side=tk.LEFT, padx=2)

        # Botões de tema
        tema_frame = ttk.Frame(toolbar_frame)
        tema_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Button(tema_frame, text="Tema Claro", command=lambda: self.aplicar_tema(self.tema_claro), style="Secondary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(tema_frame, text="Tema Escuro", command=lambda: self.aplicar_tema(self.tema_escuro), style="Secondary.TButton").pack(side=tk.LEFT, padx=2)

        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=10)
        ttk.Label(title_frame, text="Calculadora de Faturas por Pessoa", style="Heading.TLabel").pack()

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Aba Faturas
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Faturas")

        # Aba Histórico (apenas pessoa e total)
        history_tab = ttk.Frame(self.notebook)
        self.notebook.add(history_tab, text="Histórico")
        self.criar_aba_historico(history_tab)

        # Aba Pagamentos (permanece inalterada)
        pagamento_tab = ttk.Frame(self.notebook)
        self.notebook.add(pagamento_tab, text="Pagamentos")
        self.criar_aba_pagamentos(pagamento_tab)

        # Área de entrada na aba Faturas – coluna esquerda
        left_frame = ttk.Frame(main_tab, padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(left_frame, text="Insira os itens (um por linha):").pack(anchor=tk.W)
        text_frame = ttk.Frame(left_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_area = tk.Text(text_frame, height=25, width=50, font=("Consolas", 11),
                                  bg=self.input_bg, fg=self.text_color, insertbackground=self.text_color)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        pessoa_frame = ttk.Frame(left_frame)
        pessoa_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pessoa_frame, text="Nome da pessoa:").pack(side=tk.LEFT, padx=5)
        self.pessoa_entry = ttk.Entry(pessoa_frame, width=20)
        self.pessoa_entry.pack(side=tk.LEFT, padx=5)
        self.pessoa_entry.insert(0, "Geral")

        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Processar Fatura",
                   command=self.processar_faturas, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar", command=self.limpar_texto, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)

        # Área de resultados na aba Faturas – coluna direita
        right_frame = ttk.Frame(main_tab, padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        ttk.Label(right_frame, text="Resultados:").pack(anchor=tk.W)
        result_frame = ttk.Frame(right_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.result_area = tk.Text(result_frame, height=25, width=40, font=("Consolas", 11),
                                    bg=self.input_bg, fg=self.text_color, state="disabled")
        result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_area.yview)
        self.result_area.configure(yscrollcommand=result_scrollbar.set)
        self.result_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.total_label = ttk.Label(right_frame, text="Total: R$ 0,00", style="Result.TLabel")
        self.total_label.pack(anchor=tk.W, pady=10)
        result_button_frame = ttk.Frame(right_frame)
        result_button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(result_button_frame, text="Exportar Resultados", command=self.exportar_resultados).pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def criar_aba_historico(self, parent_frame):
        # Nesta aba, exibimos somente pessoa e total
        filter_frame = ttk.Frame(parent_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filter_frame, text="Filtrar por pessoa:").pack(side=tk.LEFT, padx=(0, 5))
        self.filtro_pessoa_var = tk.StringVar()
        self.filtro_pessoa_combobox = ttk.Combobox(filter_frame, textvariable=self.filtro_pessoa_var, state="readonly", width=20)
        self.filtro_pessoa_combobox.pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Aplicar Filtro", command=self.filtrar_historico).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Limpar Filtro", command=self.limpar_filtro).pack(side=tk.LEFT, padx=5)

        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        columns = ("pessoa", "total")
        self.history_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.history_tree.heading("pessoa", text="Pessoa")
        self.history_tree.heading("total", text="Total")
        self.history_tree.column("pessoa", width=150)
        self.history_tree.column("total", width=100, anchor=tk.E)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind para drag & drop reordenando os itens
        self.history_tree.bind("<ButtonPress-1>", self.on_history_button_press)
        self.history_tree.bind("<B1-Motion>", self.on_history_motion)
        self.history_tree.bind("<ButtonRelease-1>", self.on_history_button_release)
        # Bind duplo clique para abrir os detalhes para edição
        self.history_tree.bind("<Double-1>", lambda event: self.ver_detalhes_historico())

        # Botões de ação na aba Histórico
        details_frame = ttk.Frame(parent_frame)
        details_frame.pack(fill=tk.X, pady=5)
        ttk.Button(details_frame, text="Ver Detalhes", command=self.ver_detalhes_historico).pack(side=tk.LEFT, padx=5)
        ttk.Button(details_frame, text="Deletar Pessoa", command=self.deletar_pessoa).pack(side=tk.LEFT, padx=5)
        ttk.Button(details_frame, text="Carregar na Fatura", command=self.carregar_contas_fatura).pack(side=tk.LEFT, padx=5)
        ttk.Button(details_frame, text="Adicionar Pessoa", command=self.adicionar_pessoa).pack(side=tk.LEFT, padx=5)

    def on_history_button_press(self, event):
        # Inicia o drag-and-drop
        item = self.history_tree.identify_row(event.y)
        if item:
            self.dragging_item = item

    def on_history_motion(self, event):
        if not hasattr(self, "dragging_item"):
            return
        # Identifica o item alvo conforme o mouse se move
        target_item = self.history_tree.identify_row(event.y)
        if target_item and target_item != self.dragging_item:
            target_index = self.history_tree.index(target_item)
            self.history_tree.move(self.dragging_item, "", target_index)

    def on_history_button_release(self, event):
        # Ao soltar o botão, atualiza a ordem baseada nos iids dos itens
        new_order = list(self.history_tree.get_children())
        self.historico_order = new_order
        self.dragging_item = None
        self.status_var.set("Ordem do histórico atualizada.")

    def criar_aba_pagamentos(self, parent_frame):
        columns = ("pessoa", "fatura", "pago", "falta")
        self.pagamento_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")
        self.pagamento_tree.heading("pessoa", text="Pessoa")
        self.pagamento_tree.heading("fatura", text="Fatura")
        self.pagamento_tree.heading("pago", text="Pago")
        self.pagamento_tree.heading("falta", text="Falta")
        self.pagamento_tree.column("pessoa", width=150)
        self.pagamento_tree.column("fatura", width=100, anchor=tk.E)
        self.pagamento_tree.column("pago", width=100, anchor=tk.E)
        self.pagamento_tree.column("falta", width=100, anchor=tk.E)
        self.pagamento_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.pagamento_tree.bind("<Double-1>", self.editar_pagamento)
        self.atualizar_pagamentos()

    def atualizar_pagosthis(self):  # Temporary function name not used; see atualizar_pagamentos
        pass

    def atualizar_pagamentos(self):
        for item in self.pagamento_tree.get_children():
            self.pagamento_tree.delete(item)
        for nome, pessoa in self.pessoas.items():
            total_fatura = pessoa.total()
            valor_pago = pessoa.pago
            falta = total_fatura - valor_pago
            self.pagamento_tree.insert("", tk.END,
                                       values=(nome,
                                               f"R$ {total_fatura:.2f}",
                                               f"R$ {valor_pago:.2f}",
                                               f"R$ {falta:.2f}"))

    def editar_pagamento(self, event):
        selected_item = self.pagamento_tree.focus()
        if not selected_item:
            return
        valores = self.pagamento_tree.item(selected_item, "values")
        nome = valores[0]
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Editar pagamento de {nome}")
        tk.Label(edit_win, text="Valor Pago:").pack(side=tk.LEFT, padx=5, pady=5)
        entry_pago = ttk.Entry(edit_win, width=10)
        entry_pago.pack(side=tk.LEFT, padx=5, pady=5)
        entry_pago.insert(0, valores[2].replace("R$", "").strip())
        def salvar_edicao():
            try:
                novo_pago = float(entry_pago.get().replace(",", "."))
                if nome in self.pessoas:
                    self.pessoas[nome].pago = novo_pago
                self.atualizar_pagamentos()
                edit_win.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido para o pagamento.")
        ttk.Button(edit_win, text="Salvar", command=salvar_edicao).pack(side=tk.LEFT, padx=5, pady=5)

    def carregar_contas_fatura(self):
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showinfo("Informação", "Selecione um item no histórico.")
            return
        pessoa_nome = selected_item[0]  # Como usamos o iid como o nome da pessoa
        if pessoa_nome in self.pessoas:
            linhas = [d["raw_line"] for d in self.pessoas[pessoa_nome].despesas]
            texto = "\n".join(linhas)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", texto)
            self.pessoa_entry.delete(0, tk.END)
            self.pessoa_entry.insert(0, pessoa_nome)
            self.notebook.select(0)
            self.status_var.set(f"Carregado faturas de '{pessoa_nome}' na aba Faturas.")
        else:
            messagebox.showerror("Erro", "Pessoa não encontrada.")

    def adicionar_pessoa(self):
        novo_nome = simpledialog.askstring("Adicionar Pessoa", "Digite o nome da nova pessoa:")
        if not novo_nome or novo_nome.strip() == "":
            messagebox.showerror("Erro", "Nome inválido.")
            return
        novo_nome = novo_nome.strip()
        if novo_nome in self.pessoas:
            messagebox.showerror("Erro", "Pessoa já existe.")
            return
        self.pessoas[novo_nome] = Pessoa(novo_nome)
        # Adiciona o nome ao final da ordem do histórico
        self.historico_order.append(novo_nome)
        self.atualizar_historico()
        self.atualizar_pagamentos()
        self.status_var.set(f"Pessoa '{novo_nome}' adicionada com sucesso.")

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
        if nome_pessoa not in self.pessoas:
            self.pessoas[nome_pessoa] = Pessoa(nome_pessoa)
            # Se for nova, adiciona na ordem do histórico
            self.historico_order.append(nome_pessoa)
        else:
            # Para atualização, redefine as faturas
            self.pessoas[nome_pessoa].despesas = []
        pessoa = self.pessoas[nome_pessoa]
        total_processado = 0.0
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            match = re.search(r"([\d.]+,\d{2})$", linha)
            if match:
                valor_str = match.group(1)
                try:
                    valor_float = float(valor_str.replace(".", "").replace(",", "."))
                except ValueError:
                    continue
                total_processado += valor_float
                pessoa.adicionar_despesa(raw_line=linha, valor=valor_float)
        self.atualizar_historico()
        self.atualizar_resultados()
        self.status_var.set(f"Processado com sucesso: {len(linhas)} itens para {nome_pessoa}")

    def limpar_texto(self):
        self.text_area.delete("1.0", tk.END)

    def filtrar_historico(self):
        # Se houver filtro, exibe somente os nomes que contenham o filtro (caso-insensitivo)
        filtro = self.filtro_pessoa_var.get()
        self.history_tree.delete(*self.history_tree.get_children())
        if filtro and filtro != "Todos":
            ordem = [nome for nome in self.historico_order if filtro.lower() in nome.lower()]
        else:
            ordem = self.historico_order
        for pessoa in ordem:
            if pessoa in self.pessoas:
                total_format = f"R$ {self.pessoas[pessoa].total():.2f}"
                self.history_tree.insert("", tk.END, iid=pessoa, values=(pessoa, total_format))
        self.status_var.set(f"Histórico filtrado por: {filtro if filtro else 'Todos'}")

    def limpar_filtro(self):
        self.filtro_pessoa_var.set("")
        self.atualizar_historico()

    def atualizar_historico(self):
        self.history_tree.delete(*self.history_tree.get_children())
        for pessoa in self.historico_order:
            if pessoa in self.pessoas:
                total_format = f"R$ {self.pessoas[pessoa].total():.2f}"
                self.history_tree.insert("", tk.END, iid=pessoa, values=(pessoa, total_format))
        self.status_var.set("Histórico atualizado")
        self.atualizar_resultados()
        self.atualizar_pagamentos()

    def ver_detalhes_historico(self):
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showinfo("Informação", "Selecione um item do histórico para ver detalhes.")
            return
        pessoa_nome = selected_item[0]
        if pessoa_nome not in self.pessoas:
            messagebox.showerror("Erro", "Pessoa não encontrada.")
            return
        registro = {"pessoa": pessoa_nome, "total": self.pessoas[pessoa_nome].total(), "timestamp": ""}
        # Abre a janela de detalhes já em modo editável
        detalhes_win = tk.Toplevel(self.root)
        detalhes_win.title("Detalhes e Edição")
        detalhes_win.geometry("600x500")
        detalhes_win.minsize(600, 500)
        detalhes_win.resizable(True, True)
        detalhes_win.configure(bg=self.bg_color)
        frame = ttk.Frame(detalhes_win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Pessoa:", style="Result.TLabel").pack(anchor=tk.W, pady=2)
        nome_entry = ttk.Entry(frame, width=30)
        nome_entry.pack(anchor=tk.W, pady=2)
        nome_entry.insert(0, registro["pessoa"])

        ttk.Label(frame, text=f"Total: R$ {registro['total']:.2f}", style="Result.TLabel").pack(anchor=tk.W, pady=2)

        ttk.Label(frame, text="Despesas:", style="Heading.TLabel").pack(anchor=tk.W, pady=(10, 5))
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        text_area = tk.Text(text_frame, height=10, width=50, font=("Consolas", 11),
                            bg=self.input_bg, fg=self.text_color)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        despesa_text = ""
        for d in self.pessoas[registro["pessoa"]].despesas:
            despesa_text += d["raw_line"] + "\n"
        text_area.insert(tk.END, despesa_text)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Ao fechar a janela, salva automaticamente as alterações
        def on_close():
            novo_nome = nome_entry.get().strip()
            if novo_nome == "":
                messagebox.showerror("Erro", "O nome não pode ser vazio.")
                return
            old_nome = registro["pessoa"]
            if novo_nome != old_nome:
                if novo_nome in self.pessoas:
                    messagebox.showerror("Erro", f"Já existe uma pessoa com o nome '{novo_nome}'.")
                    return
                # Altera o nome na estrutura de dados e na ordem do histórico
                pessoa_obj = self.pessoas.pop(old_nome)
                pessoa_obj.nome = novo_nome
                self.pessoas[novo_nome] = pessoa_obj
                index = self.historico_order.index(old_nome)
                self.historico_order[index] = novo_nome
                registro["pessoa"] = novo_nome
            novo_texto = text_area.get("1.0", tk.END).strip()
            novas_despesas = []
            total_novo = 0.0
            for linha in novo_texto.splitlines():
                linha = linha.strip()
                if not linha:
                    continue
                match = re.search(r'([\d.,]+)$', linha)
                if not match:
                    continue
                try:
                    valor_float = float(match.group(1).replace(".", "").replace(",", "."))
                except ValueError:
                    continue
                novas_despesas.append({"raw_line": linha, "valor": valor_float})
                total_novo += valor_float
            self.pessoas[registro["pessoa"]].despesas = novas_despesas
            self.atualizar_historico()
            self.atualizar_resultados()
            detalhes_win.destroy()

        detalhes_win.protocol("WM_DELETE_WINDOW", on_close)

    def deletar_pessoa(self):
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showinfo("Informação", "Selecione um item do histórico para deletar a pessoa.")
            return
        pessoa_nome = selected_item[0]
        confirm = messagebox.askyesno("Confirmação", f"Tem certeza que deseja deletar a pessoa '{pessoa_nome}' e todos os seus registros?")
        if confirm:
            if pessoa_nome in self.pessoas:
                del self.pessoas[pessoa_nome]
            if pessoa_nome in self.historico_order:
                self.historico_order.remove(pessoa_nome)
            self.atualizar_historico()
            self.atualizar_pagamentos()
            self.atualizar_resultados()
            self.status_var.set(f"Pessoa '{pessoa_nome}' deletada com sucesso.")

    def atualizar_resultados(self):
        resultado = ""
        if self.pessoas:
            resultado += "Resumo por pessoa:\n"
            resultado += "-" * 40 + "\n"
            for nome, p in self.pessoas.items():
                resultado += f"{nome}: R$ {p.total():.2f}\n"
            total_geral = sum(p.total() for p in self.pessoas.values())
            resultado += "-" * 40 + "\n"
            resultado += f"TOTAL GERAL: R$ {total_geral:.2f}"
        else:
            resultado = "Sem resultados."
            total_geral = 0.0
        self.result_area.config(state="normal")
        self.result_area.delete("1.0", tk.END)
        self.result_area.insert("1.0", resultado)
        self.result_area.config(state="disabled")
        self.total_label.config(text=f"Total Geral: R$ {total_geral:.2f}")
        self.root.update_idletasks()

    def novo_arquivo(self):
        if messagebox.askyesno("Novo", "Deseja criar um novo arquivo? Os dados não salvos serão perdidos."):
            self.pessoas = {}
            self.historico_order = []
            self.arquivo_atual = None
            self.text_area.delete("1.0", tk.END)
            self.result_area.config(state="normal")
            self.result_area.delete("1.0", tk.END)
            self.result_area.config(state="disabled")
            self.total_label.config(text="Total: R$ 0,00")
            self.status_var.set("Novo arquivo criado")
            self.atualizar_historico()

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
                self.historico_order = []
                for pessoa_data in data.get("pessoas", []):
                    nome = pessoa_data["nome"]
                    pessoa = Pessoa(nome)
                    for despesa in pessoa_data.get("despesas", []):
                        pessoa.adicionar_despesa(raw_line=despesa["raw_line"], valor=despesa["valor"])
                    pessoa.pago = pessoa_data.get("pago", 0.0)
                    self.pessoas[nome] = pessoa
                    self.historico_order.append(nome)
                self.arquivo_atual = filename
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
                self.atualizar_historico()
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
                            f.write(f"{despesa['raw_line']}\n")
                        f.write("-" * 50 + "\n")
                        f.write(f"TOTAL: R$ {pessoa.total():.2f}\n\n")
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
