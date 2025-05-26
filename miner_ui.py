import os
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import yaml

class MinerUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Signum Miner UI")
        self.master.geometry("800x600")

        # Dark theme colors
        self.dark_bg = "#2b2b2b"
        self.fg_color = "#1e90ff"

        self.master.configure(bg=self.dark_bg)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=self.dark_bg, foreground=self.fg_color,
                        fieldbackground=self.dark_bg)
        style.configure('TFrame', background=self.dark_bg)
        style.configure('TButton', background="#3c3f41", foreground=self.fg_color)
        style.map('TButton', background=[('active', '#454545')])
        style.configure('TCheckbutton', background=self.dark_bg,
                        foreground=self.fg_color)

        self.config_path = tk.StringVar(value="config.yaml")
        self.config_data = {}

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.config_tab = ttk.Frame(self.notebook)
        self.options_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="Config")
        self.notebook.add(self.options_tab, text="Options")
        self.notebook.add(self.logs_tab, text="Logs")

        path_frame = ttk.Frame(self.config_tab)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(path_frame, text="Config Path:").pack(side=tk.LEFT)
        ttk.Entry(path_frame, textvariable=self.config_path, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(path_frame, text="Browse", command=self.browse_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="Load", command=self.load_config).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="Save", command=self.save_config).pack(side=tk.LEFT)

        self.text = scrolledtext.ScrolledText(self.config_tab, width=80, height=20,
                                             bg=self.dark_bg, fg=self.fg_color,
                                             insertbackground=self.fg_color)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Options tab - scrollable frame
        self.options_canvas = tk.Canvas(self.options_tab, bg=self.dark_bg, highlightthickness=0)
        self.options_scroll = ttk.Scrollbar(self.options_tab, orient=tk.VERTICAL,
                                            command=self.options_canvas.yview)
        self.options_frame = ttk.Frame(self.options_canvas)
        self.options_frame.bind(
            "<Configure>",
            lambda e: self.options_canvas.configure(scrollregion=self.options_canvas.bbox("all"))
        )
        self.options_canvas.create_window((0, 0), window=self.options_frame, anchor="nw")
        self.options_canvas.configure(yscrollcommand=self.options_scroll.set)
        self.options_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.options_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.option_widgets = {}

        save_opts = ttk.Button(self.options_tab, text="Save Options", command=self.save_options)
        save_opts.pack(side=tk.BOTTOM, pady=5)

        self.log_text = scrolledtext.ScrolledText(self.logs_tab, width=80, height=20, state=tk.DISABLED)
        self.log_text.configure(bg=self.dark_bg, fg=self.fg_color, insertbackground=self.fg_color)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        self.start_btn = ttk.Button(btn_frame, text="Start Miner", command=self.start_miner)
        self.start_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(btn_frame, text="Stop Miner", command=self.stop_miner, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Quit", command=master.quit).pack(side=tk.RIGHT)

        self.status_var = tk.StringVar(value="Idle")
        status_bar = ttk.Label(master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.process = None
        self.log_queue = queue.Queue()
        self.load_config()
        self.update_logs()

    def browse_config(self):
        path = filedialog.askopenfilename(initialfile=self.config_path.get())
        if path:
            self.config_path.set(path)
            self.load_config()

    def load_config(self):
        try:
            with open(self.config_path.get(), 'r') as f:
                data = f.read()
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, data)
            self.config_data = yaml.safe_load(data) or {}
            self.populate_options()
        except OSError as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        try:
            with open(self.config_path.get(), 'w') as f:
                f.write(self.text.get('1.0', tk.END))
            messagebox.showinfo("Saved", "Config saved")
            self.config_data = yaml.safe_load(self.text.get('1.0', tk.END)) or {}
            self.populate_options()
        except OSError as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def start_miner(self):
        cmd = [os.path.join('.', 'signum-miner'), '-c', self.config_path.get()]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set("Mining...")
            threading.Thread(target=self.enqueue_output, daemon=True).start()
        except OSError as e:
            messagebox.showerror("Error", f"Failed to start miner: {e}")
            self.process = None

    def stop_miner(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopped")

    def enqueue_output(self):
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            self.log_queue.put(line)
        self.process = None
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopped")

    def update_logs(self):
        while not self.log_queue.empty():
            line = self.log_queue.get_nowait()
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, line)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.master.after(100, self.update_logs)

    def populate_options(self):
        for w in self.options_frame.winfo_children():
            w.destroy()
        self.option_widgets.clear()
        for row, (key, val) in enumerate(self.config_data.items()):
            ttk.Label(self.options_frame, text=key).grid(row=row, column=0, sticky='w', padx=5, pady=2)
            if isinstance(val, bool):
                var = tk.BooleanVar(value=val)
                cb = ttk.Checkbutton(self.options_frame, variable=var)
                cb.grid(row=row, column=1, sticky='w')
                self.option_widgets[key] = ('bool', var)
            elif isinstance(val, (int, float, str)):
                var = tk.StringVar(value=str(val))
                entry = ttk.Entry(self.options_frame, textvariable=var, width=40)
                entry.grid(row=row, column=1, sticky='we', padx=5)
                self.option_widgets[key] = ('scalar', var, type(val))
            else:
                txt = scrolledtext.ScrolledText(self.options_frame, height=3, width=40,
                                                bg=self.dark_bg, fg=self.fg_color,
                                                insertbackground=self.fg_color)
                txt.insert(tk.END, yaml.dump(val))
                txt.grid(row=row, column=1, sticky='we', padx=5)
                self.option_widgets[key] = ('text', txt)

    def save_options(self):
        for key, widget_info in self.option_widgets.items():
            kind = widget_info[0]
            if kind == 'bool':
                var = widget_info[1]
                self.config_data[key] = bool(var.get())
            elif kind == 'scalar':
                var, typ = widget_info[1], widget_info[2]
                value = var.get()
                try:
                    if typ is int:
                        self.config_data[key] = int(value)
                    elif typ is float:
                        self.config_data[key] = float(value)
                    else:
                        self.config_data[key] = value
                except ValueError:
                    self.config_data[key] = value
            else:
                txt = widget_info[1]
                try:
                    self.config_data[key] = yaml.safe_load(txt.get('1.0', tk.END))
                except yaml.YAMLError:
                    self.config_data[key] = txt.get('1.0', tk.END)
        with open(self.config_path.get(), 'w') as f:
            yaml.dump(self.config_data, f, sort_keys=False)
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, yaml.dump(self.config_data, sort_keys=False))
        messagebox.showinfo('Saved', 'Config saved')


def main():
    root = tk.Tk()
    app = MinerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
