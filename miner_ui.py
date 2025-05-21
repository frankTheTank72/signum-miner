import os
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

class MinerUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Signum Miner UI")

        self.config_path = tk.StringVar(value="config.yaml")
        path_frame = tk.Frame(master)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(path_frame, text="Config Path:").pack(side=tk.LEFT)
        tk.Entry(path_frame, textvariable=self.config_path, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(path_frame, text="Browse", command=self.browse_config).pack(side=tk.LEFT, padx=5)
        tk.Button(path_frame, text="Load", command=self.load_config).pack(side=tk.LEFT)
        tk.Button(path_frame, text="Save", command=self.save_config).pack(side=tk.LEFT)

        self.text = scrolledtext.ScrolledText(master, width=80, height=20)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        log_label = tk.Label(master, text="Logs:")
        log_label.pack(anchor=tk.W, padx=5)
        self.log_text = scrolledtext.ScrolledText(master, width=80, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        self.run_btn = tk.Button(btn_frame, text="Run Miner", command=self.toggle_miner)
        self.run_btn.pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Quit", command=master.quit).pack(side=tk.RIGHT)

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

    def toggle_miner(self):
        if self.process:
            self.stop_miner()
        else:
            self.start_miner()

    def start_miner(self):
        cmd = [os.path.join('.', 'signum-miner'), '-c', self.config_path.get()]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self.run_btn.config(text="Stop Miner")
            threading.Thread(target=self.enqueue_output, daemon=True).start()
        except OSError as e:
            messagebox.showerror("Error", f"Failed to start miner: {e}")
            self.process = None

    def stop_miner(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            self.run_btn.config(text="Run Miner")

    def enqueue_output(self):
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            self.log_queue.put(line)
        self.process = None
        self.run_btn.config(text="Run Miner")

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
