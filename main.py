import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import platform
import threading


class PythonRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Multi-File Runner")
        self.root.geometry("900x650")
        
        self.selected_files = []  # full paths
        
        self.create_widgets()
    
    def create_widgets(self):
        # Top controls
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")
        
        ttk.Button(top_frame, text="Add Files", command=self.select_files).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Add Folder", command=self.select_folder).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Clear All", command=self.clear_list).pack(side="left", padx=5)
        
        # File list
        list_frame = ttk.LabelFrame(self.root, text="Selected Python Files", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.listbox = tk.Listbox(list_frame, selectmode="extended", height=20, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom controls
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill="x")
        
        ttk.Button(bottom_frame, text="▶ Run Selected", command=self.run_selected).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="▶ Run All", command=self.run_all).pack(side="left", padx=5)
        
        # Status
        self.status = ttk.Label(self.root, text="Ready - You can select files from different folders at once", 
                               relief="sunken", anchor="w")
        self.status.pack(fill="x", padx=10, pady=5)
    
    def select_files(self):
        """Select multiple .py files from anywhere (different folders OK)"""
        files = filedialog.askopenfilenames(
            title="Select Python Files (Hold Ctrl/Cmd to select multiple)",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        added = 0
        for f in files:
            if f.endswith('.py') and f not in self.selected_files:
                self.selected_files.append(f)
                # Show filename + parent folder for clarity
                parent = os.path.basename(os.path.dirname(f))
                display = f"{os.path.basename(f)}  [{parent}]" if parent else os.path.basename(f)
                self.listbox.insert("end", display)
                added += 1
        
        self.update_status(f"Added {added} file(s)")
    
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if not folder:
            return
        
        added = 0
        for root_dir, _, files in os.walk(folder):  # Now recursive!
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root_dir, file)
                    if full_path not in self.selected_files:
                        self.selected_files.append(full_path)
                        rel_path = os.path.relpath(full_path, folder)
                        self.listbox.insert("end", f"{file}  [{rel_path}]")
                        added += 1
        
        self.update_status(f"Added {added} .py file(s) from folder (recursive)")
    
    def remove_selected(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return
        
        # Remove from highest index to lowest to avoid shifting
        for idx in sorted(selected_indices, reverse=True):
            self.listbox.delete(idx)
            del self.selected_files[idx]
        
        self.update_status(f"Removed {len(selected_indices)} item(s)")
    
    def clear_list(self):
        if messagebox.askyesno("Clear All", "Remove all files from the list?"):
            self.selected_files.clear()
            self.listbox.delete(0, "end")
            self.update_status("List cleared")
    
    def update_status(self, text):
        self.status.config(text=text)
        self.root.after(4000, lambda: self.status.config(
            text="Ready - You can select files from different folders at once"))
    
    def run_script(self, script_path):
        try:
            abs_path = os.path.abspath(script_path)
            dir_path = os.path.dirname(abs_path)
            filename = os.path.basename(abs_path)
            
            system = platform.system()
            
            if system == "Windows":
                cmd = f'start cmd /k "cd /d "{dir_path}" && python "{filename}"'
                subprocess.Popen(cmd, shell=True)
                
            elif system == "Darwin":  # macOS
                script_cmd = f'cd "{dir_path}" && python3 "{filename}"'
                subprocess.Popen(['open', '-a', 'Terminal', '-n', '--args', 
                                'bash', '-c', script_cmd + '; exec bash'])
                
            elif system == "Linux":
                script_cmd = f'cd "{dir_path}" && python3 "{filename}" && exec $SHELL'
                for term in ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]:
                    try:
                        if term == "gnome-terminal":
                            subprocess.Popen([term, '--', 'bash', '-c', script_cmd])
                        else:
                            subprocess.Popen([term, '-e', f'bash -c "{script_cmd}"'])
                        break
                    except FileNotFoundError:
                        continue
                else:
                    subprocess.Popen(['python3', abs_path])
            else:
                subprocess.Popen(['python', abs_path])
                
        except Exception as e:
            messagebox.showerror("Run Error", f"Failed to run:\n{script_path}\n\n{str(e)}")
    
    def run_selected(self):
        indices = self.listbox.curselection()
        if not indices:
            messagebox.showwarning("Nothing selected", "Please select file(s) first.")
            return
        
        for idx in indices:
            threading.Thread(target=self.run_script, 
                           args=(self.selected_files[idx],), 
                           daemon=True).start()
        
        self.update_status(f"Started {len(indices)} script(s)")
    
    def run_all(self):
        if not self.selected_files:
            messagebox.showwarning("Empty", "No files to run.")
            return
        
        for path in self.selected_files:
            threading.Thread(target=self.run_script, args=(path,), daemon=True).start()
        
        self.update_status(f"Started all {len(self.selected_files)} script(s)")


if __name__ == "__main__":
    root = tk.Tk()
    app = PythonRunnerApp(root)
    root.mainloop()