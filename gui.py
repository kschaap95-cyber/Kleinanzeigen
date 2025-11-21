import tkinter as tk
from tkinter import ttk, messagebox
from manager import SearchManager
import threading
from categories import CATEGORIES
import queue
import sys
import datetime

class ConsoleRedirector:
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Kleinanzeigen Bot")
        self.root.geometry("700x650")
        
        # Console Queue
        self.log_queue = queue.Queue()
        sys.stdout = ConsoleRedirector(self.log_queue)
        sys.stderr = ConsoleRedirector(self.log_queue)
        
        self.manager = SearchManager()
        
        # Theme State
        self.dark_mode = False
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam' supports color customization well
        
        self.create_widgets()
        self.update_search_list()
        
        # Apply initial theme
        self.apply_theme()
        
        # Console Window Reference
        self.console_window = None
        self.console_text = None
        
        # Start checking queue
        self.check_log_queue()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            bg_color = "#2d2d2d"
            fg_color = "#ffffff"
            field_bg = "#3d3d3d"
            select_bg = "#555555"
            
            self.root.configure(bg=bg_color)
            self.style.configure(".", background=bg_color, foreground=fg_color, fieldbackground=field_bg)
            self.style.configure("TLabel", background=bg_color, foreground=fg_color)
            self.style.configure("TButton", background=field_bg, foreground=fg_color, borderwidth=1)
            self.style.map("TButton", background=[("active", select_bg)])
            self.style.configure("TEntry", fieldbackground=field_bg, foreground=fg_color)
            self.style.configure("TCombobox", fieldbackground=field_bg, foreground=fg_color, arrowcolor=fg_color)
            self.style.map("TCombobox", fieldbackground=[("readonly", field_bg)], selectbackground=[("readonly", select_bg)])
            self.style.configure("TLabelframe", background=bg_color, foreground=fg_color)
            self.style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)
            self.style.configure("TCheckbutton", background=bg_color, foreground=fg_color)
            
            # Treeview
            self.style.configure("Treeview", background=field_bg, foreground=fg_color, fieldbackground=field_bg)
            self.style.map("Treeview", background=[("selected", select_bg)], foreground=[("selected", fg_color)])
            self.style.configure("Treeview.Heading", background=bg_color, foreground=fg_color, relief="flat")
            self.style.map("Treeview.Heading", background=[("active", select_bg)])
            
        else:
            # Light Mode (Default 'clam' colors or system default)
            # Resetting to default 'clam' is easiest by just clearing specific configs or setting standard light colors
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            field_bg = "#ffffff"
            select_bg = "#0078d7"
            
            self.root.configure(bg=bg_color)
            self.style.configure(".", background=bg_color, foreground=fg_color, fieldbackground=field_bg)
            self.style.configure("TLabel", background=bg_color, foreground=fg_color)
            self.style.configure("TButton", background="#e1e1e1", foreground=fg_color, borderwidth=1)
            self.style.map("TButton", background=[("active", "#c7c7c7")])
            self.style.configure("TEntry", fieldbackground=field_bg, foreground=fg_color)
            self.style.configure("TCombobox", fieldbackground=field_bg, foreground=fg_color, arrowcolor=fg_color)
            self.style.map("TCombobox", fieldbackground=[("readonly", field_bg)], selectbackground=[("readonly", select_bg)])
            self.style.configure("TLabelframe", background=bg_color, foreground=fg_color)
            self.style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)
            self.style.configure("TCheckbutton", background=bg_color, foreground=fg_color)
            
            # Treeview
            self.style.configure("Treeview", background=field_bg, foreground=fg_color, fieldbackground=field_bg)
            self.style.map("Treeview", background=[("selected", select_bg)], foreground=[("selected", "#ffffff")])
            self.style.configure("Treeview.Heading", background="#e1e1e1", foreground=fg_color, relief="raised")
            self.style.map("Treeview.Heading", background=[("active", "#c7c7c7")])

        # Update Console Window if open
        if self.console_text:
            c_bg = "#1e1e1e" if self.dark_mode else "#ffffff"
            c_fg = "#ffffff" if self.dark_mode else "#000000"
            self.console_text.configure(bg=c_bg, fg=c_fg)
            if self.console_window:
                self.console_window.configure(bg=bg_color)

    def check_log_queue(self):
        while not self.log_queue.empty():
            try:
                text = self.log_queue.get_nowait()
                if self.console_text:
                    self.console_text.configure(state="normal")
                    self.console_text.insert("end", text)
                    self.console_text.see("end")
                    self.console_text.configure(state="disabled")
            except queue.Empty:
                break
        self.root.after(100, self.check_log_queue)

    def show_console(self):
        if self.console_window is not None and self.console_window.winfo_exists():
            self.console_window.lift()
            return

        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Bot Konsole")
        self.console_window.geometry("600x400")
        
        # Apply current theme bg
        bg_color = "#2d2d2d" if self.dark_mode else "#f0f0f0"
        self.console_window.configure(bg=bg_color)
        
        c_bg = "#1e1e1e" if self.dark_mode else "#ffffff"
        c_fg = "#ffffff" if self.dark_mode else "#000000"
        
        self.console_text = tk.Text(self.console_window, state="disabled", wrap="word", bg=c_bg, fg=c_fg, font=("Consolas", 9))
        self.console_text.pack(fill="both", expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.console_window, orient="vertical", command=self.console_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.console_text.configure(yscrollcommand=scrollbar.set)
        self.console_text.pack(side="left", fill="both", expand=True)

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.root, text="Neue Suche", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(input_frame, text="Suchbegriff:").grid(row=0, column=0, sticky="w")
        self.entry_query = ttk.Entry(input_frame, width=30)
        self.entry_query.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(input_frame, text="Ort / PLZ:").grid(row=1, column=0, sticky="w")
        self.entry_location = ttk.Entry(input_frame, width=30)
        self.entry_location.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(input_frame, text="Radius (km):").grid(row=2, column=0, sticky="w")
        self.entry_radius = ttk.Entry(input_frame, width=10)
        self.entry_radius.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.entry_radius.insert(0, "0")
        
        ttk.Label(input_frame, text="Kategorie:").grid(row=3, column=0, sticky="w")
        self.combo_category = ttk.Combobox(input_frame, values=list(CATEGORIES.keys()), state="readonly", width=27)
        self.combo_category.grid(row=3, column=1, padx=5, pady=2)
        self.combo_category.set("Alle Kategorien")
        
        ttk.Label(input_frame, text="Filter (optional):").grid(row=4, column=0, sticky="w")
        self.entry_filter = ttk.Entry(input_frame, width=30)
        self.entry_filter.grid(row=4, column=1, padx=5, pady=2)
        ttk.Label(input_frame, text="(Kommagetrennt, sucht auch in Beschreibung)").grid(row=4, column=2, sticky="w", padx=5)
        
        self.var_notify = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, text="Benachrichtigungen an", variable=self.var_notify).grid(row=5, column=0, columnspan=2, sticky="w")
        
        ttk.Button(input_frame, text="Hinzufügen", command=self.add_search).grid(row=5, column=1, sticky="e", pady=5)
        
        # List Frame
        list_frame = ttk.LabelFrame(self.root, text="Aktive Suchen", padding="10")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("query", "location", "category", "filter", "notify")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("query", text="Suchbegriff")
        self.tree.heading("location", text="Ort")
        self.tree.heading("category", text="Kategorie")
        self.tree.heading("filter", text="Filter")
        self.tree.heading("notify", text="Benachrichtigung")
        
        self.tree.column("query", width=150)
        self.tree.column("location", width=100)
        self.tree.column("category", width=150)
        self.tree.column("filter", width=150)
        self.tree.column("notify", width=100)
        
        self.tree.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Control Frame
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill="x")
        
        # Interval Settings
        ttk.Label(control_frame, text="Intervall (Min):").pack(side="left", padx=2)
        self.entry_interval = ttk.Entry(control_frame, width=5)
        self.entry_interval.pack(side="left", padx=5)
        # Load current interval (convert seconds to minutes)
        current_min = max(1, int(self.manager.interval / 60))
        self.entry_interval.insert(0, str(current_min))
        
        self.btn_start = ttk.Button(control_frame, text="Bot Starten", command=self.start_bot)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ttk.Button(control_frame, text="Bot Stoppen", command=self.stop_bot, state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="Ergebnisse", command=self.show_results).pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="Konsole", command=self.show_console).pack(side="right", padx=5)
        ttk.Button(control_frame, text="Toggle Notify", command=self.toggle_notify).pack(side="right", padx=5)
        ttk.Button(control_frame, text="Löschen", command=self.delete_search).pack(side="right", padx=5)
        
        # Dark Mode Toggle (Top Right of Control Frame or Menu? Let's put it in Control Frame for now)
        ttk.Button(control_frame, text="Dark Mode", command=self.toggle_theme).pack(side="right", padx=5)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")

    def show_results(self):
        top = tk.Toplevel(self.root)
        top.title("Gefundene Ergebnisse")
        top.geometry("800x600")
        
        columns = ("title", "price", "location", "link")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        tree.heading("title", text="Titel")
        tree.heading("price", text="Preis")
        tree.heading("location", text="Ort")
        tree.heading("link", text="Link")
        
        tree.column("title", width=300)
        tree.column("price", width=100)
        tree.column("location", width=150)
        tree.column("link", width=200)
        
        tree.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Populate
        for ad in self.manager.found_ads:
            tree.insert("", "end", values=(ad['title'], ad['price'], ad['location'], ad['link']))
            
        def on_double_click(event):
            item = tree.selection()
            if not item:
                return
            values = tree.item(item, "values")
            link = values[3]
            import webbrowser
            webbrowser.open(link)
            
        tree.bind("<Double-1>", on_double_click)
        
        ttk.Label(top, text="Doppelklick auf Eintrag öffnet Link").pack(pady=5)

    def add_search(self):
        query = self.entry_query.get()
        location = self.entry_location.get()
        radius = self.entry_radius.get()
        category_name = self.combo_category.get()
        category_id = CATEGORIES.get(category_name, "0")
        
        filter_str = self.entry_filter.get()
        filter_keywords = [k.strip() for k in filter_str.split(',')] if filter_str else []
        
        notify = self.var_notify.get()
        
        if not query:
            messagebox.showerror("Fehler", "Bitte Suchbegriff eingeben.")
            return
            
        self.manager.add_search(query, location, radius, category_id, filter_keywords, notify)
        self.update_search_list()
        self.entry_query.delete(0, "end")
        self.entry_filter.delete(0, "end")
        
    def delete_search(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        for item in selected:
            index = self.tree.index(item)
            self.manager.remove_search(index)
            
        self.update_search_list()

    def toggle_notify(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        for item in selected:
            index = self.tree.index(item)
            self.manager.toggle_notifications(index)
            
        self.update_search_list()

    def update_search_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for search in self.manager.searches:
            # Reverse lookup category name
            cat_id = search.get('category_id', "0")
            cat_name = next((k for k, v in CATEGORIES.items() if v == cat_id), "Unbekannt")
            filters = ", ".join(search.get('filter_keywords', []))
            notify_status = "An" if search.get('notifications', True) else "Aus"
            
            self.tree.insert("", "end", values=(search['query'], search['location'], cat_name, filters, notify_status))

    def start_bot(self):
        try:
            interval_min = int(self.entry_interval.get())
            if interval_min < 1:
                raise ValueError
            self.manager.interval = interval_min * 60
            self.manager.save_config()
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültiges Intervall (Minuten) eingeben.")
            return

        self.manager.start_monitoring()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.status_var.set(f"Bot läuft... (Intervall: {interval_min} Min)")

    def stop_bot(self):
        self.manager.stop_monitoring()
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_var.set("Bot gestoppt.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
