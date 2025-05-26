import os
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk

class MinerUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Signum Miner UI")
        self.master.geometry("800x600")

        self.config_path = tk.StringVar(value="config.yaml")

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.config_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="Config")
        self.notebook.add(self.logs_tab, text="Logs")

        path_frame = ttk.Frame(self.config_tab)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(path_frame, text="Config Path:").pack(side=tk.LEFT)
        ttk.Entry(path_frame, textvariable=self.config_path, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(path_frame, text="Browse", command=self.browse_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="Load", command=self.load_config).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="Save", command=self.save_config).pack(side=tk.LEFT)

        self.text = scrolledtext.ScrolledText(self.config_tab, width=80, height=20)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(self.logs_tab, width=80, height=20, state=tk.DISABLED)
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
        except OSError as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        try:
            with open(self.config_path.get(), 'w') as f:
                f.write(self.text.get('1.0', tk.END))
            messagebox.showinfo("Saved", "Config saved")
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


def main():
    root = tk.Tk()
    app = MinerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
