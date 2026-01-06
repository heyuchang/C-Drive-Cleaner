import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from cleaner_core import SystemCleaner
from migrator import SystemMigrator
import os

class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("C盘一键清理 & 迁移工具")
        self.root.geometry("650x500")
        self.root.resizable(False, False)
        
        self.cleaner = SystemCleaner()
        self.migrator = SystemMigrator()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Cleanup
        self.cleanup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cleanup_frame, text="垃圾清理")
        self.setup_cleanup_ui(self.cleanup_frame)
        
        # Tab 2: Migration
        self.migration_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.migration_frame, text="大文件迁移")
        self.setup_migration_ui(self.migration_frame)
        
    # ================= Cleanup Tab =================
    def setup_cleanup_ui(self, parent):
        # Top Frame for Status
        status_frame = ttk.Frame(parent, padding="20")
        status_frame.pack(fill=tk.X)
        
        ttk.Label(status_frame, text="可释放空间:", font=("Microsoft YaHei", 12)).pack(anchor=tk.W)
        self.size_label = ttk.Label(status_frame, text="0.00 MB", font=("Microsoft YaHei", 24, "bold"), foreground="#0078D7")
        self.size_label.pack(anchor=tk.W)
        
        # Middle Frame for Logs
        log_frame = ttk.Frame(parent, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=10, state='disabled', font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom Frame for Buttons
        btn_frame = ttk.Frame(parent, padding="20")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.scan_btn = ttk.Button(btn_frame, text="开始扫描", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.clean_btn = ttk.Button(btn_frame, text="立即清理", command=self.start_clean, state='disabled')
        self.clean_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=5, side=tk.BOTTOM)

    # ================= Migration Tab =================
    def setup_migration_ui(self, parent):
        # 1. Info Area
        info_frame = ttk.LabelFrame(parent, text="功能说明", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(info_frame, text="将桌面、下载、文档等个人文件夹迁移到其他磁盘 (如 D盘)。\n这样可以大大减轻C盘负担，且重装系统不丢失数据。", wraplength=600).pack(anchor=tk.W)
        
        # 2. Target Selection
        target_frame = ttk.Frame(parent, padding="10")
        target_frame.pack(fill=tk.X)
        ttk.Label(target_frame, text="目标位置:").pack(side=tk.LEFT)
        
        self.target_path_var = tk.StringVar()
        self.target_entry = ttk.Entry(target_frame, textvariable=self.target_path_var, width=40)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(target_frame, text="浏览...", command=self.browse_target).pack(side=tk.LEFT)
        
        # 3. Folder List
        list_frame = ttk.LabelFrame(parent, text="选择要迁移的文件夹", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Checkboxes
        self.folder_vars = {}
        self.folder_checks = {}
        
        # We need to refresh this list dynamically
        self.mig_scroll_frame = ttk.Frame(list_frame)
        self.mig_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_migration_list()
        
        # 4. Action Buttons
        action_frame = ttk.Frame(parent, padding="20")
        action_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(action_frame, text="刷新状态", command=self.refresh_migration_list).pack(side=tk.LEFT)
        self.migrate_btn = ttk.Button(action_frame, text="开始迁移", command=self.start_migration)
        self.migrate_btn.pack(side=tk.RIGHT)

    def browse_target(self):
        path = filedialog.askdirectory(title=r"选择迁移目标文件夹 (例如 D:\UserFiles)")
        if path:
            self.target_path_var.set(path)

    def refresh_migration_list(self):
        # Clear existing
        for widget in self.mig_scroll_frame.winfo_children():
            widget.destroy()
            
        results = self.migrator.get_scan_results()
        self.folder_vars = {}
        
        row = 0
        for item in results:
            key = item["key"]
            size_str = self.migrator.get_formatted_size(item["size"])
            status = "已迁移" if item["is_migrated"] else "在C盘"
            
            var = tk.BooleanVar(value=False)
            self.folder_vars[key] = var
            
            # Checkbox
            chk = ttk.Checkbutton(self.mig_scroll_frame, text=f"{item['name']} ({key})", variable=var)
            if item["is_migrated"]:
                chk.config(state='disabled')
                status += f" ({item['path']})"
            else:
                chk.config(state='normal')
                
            chk.grid(row=row, column=0, sticky="w", padx=5, pady=2)
            
            # Info Label
            info_text = f"大小: {size_str} | 状态: {status}"
            ttk.Label(self.mig_scroll_frame, text=info_text, foreground="#666").grid(row=row, column=1, sticky="w", padx=10)
            
            # Details Button
            if not item["is_migrated"]:
                ttk.Button(self.mig_scroll_frame, text="详情", width=6, 
                           command=lambda p=item['path'], n=item['name']: self.show_folder_details(p, n)
                          ).grid(row=row, column=2, sticky="w", padx=5)

            row += 1

    def show_folder_details(self, path, name):
        # Create a new top-level window
        details_win = tk.Toplevel(self.root)
        details_win.title(f"{name} - 大文件分析 (Top 50)")
        details_win.geometry("600x400")
        
        # Treeview for file list
        columns = ("name", "size", "path")
        tree = ttk.Treeview(details_win, columns=columns, show="headings")
        tree.heading("name", text="文件名")
        tree.heading("size", text="大小")
        tree.heading("path", text="完整路径")
        
        tree.column("name", width=150)
        tree.column("size", width=100)
        tree.column("path", width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(details_win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load data in thread to avoid freezing
        def load_data():
            files = self.migrator.get_large_files(path, limit=50)
            for f in files:
                size_str = self.migrator.get_formatted_size(f['size'])
                tree.insert("", tk.END, values=(f['name'], size_str, f['path']))
                
        threading.Thread(target=load_data, daemon=True).start()

    def start_migration(self):
        target_root = self.target_path_var.get().strip()
        if not target_root:
            messagebox.showwarning("提示", r"请先选择目标位置 (例如 D:\UserFiles)")
            return
            
        if not os.path.exists(target_root):
            try:
                os.makedirs(target_root)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建目标目录: {e}")
                return

        # Collect selected
        to_migrate = []
        for key, var in self.folder_vars.items():
            if var.get():
                to_migrate.append(key)
                
        if not to_migrate:
            messagebox.showwarning("提示", "请选择至少一个要迁移的文件夹")
            return
            
        if not messagebox.askyesno("确认迁移", f"即将迁移 {len(to_migrate)} 个文件夹到 {target_root}。\n\n这可能需要一些时间，且迁移过程中请勿运行相关程序。\n\n确定继续吗？"):
            return
            
        # Start Thread
        threading.Thread(target=self.run_migration, args=(to_migrate, target_root), daemon=True).start()

    def run_migration(self, folders, target_root):
        self.migrate_btn.config(state='disabled')
        success_count = 0
        
        for folder in folders:
            # Simple progress dialog substitute via msgbox or log? 
            # We don't have a log area in Migration tab, let's use a popup or just print to console/status?
            # Let's verify via refresh.
            
            # Actually, let's just log to the cleanup tab's log for now or show a message box at the end.
            # Ideally we should add a log area to migration tab too, but keeping it simple.
            
            res, msg = self.migrator.migrate_folder(folder, target_root)
            if res:
                success_count += 1
            else:
                self.root.after(0, lambda m=msg, f=folder: messagebox.showerror("迁移失败", f"迁移 {f} 失败: {m}"))
                
        self.root.after(0, lambda: self.finish_migration(success_count, len(folders)))

    def finish_migration(self, success, total):
        self.refresh_migration_list()
        self.migrate_btn.config(state='normal')
        messagebox.showinfo("完成", f"迁移完成！成功: {success}/{total}\n\n建议重启电脑以确保所有程序识别新路径。")

    # ================= Shared / Helper =================
    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
    def update_size_label(self, size_bytes):
        formatted = self.cleaner.get_formatted_size(size_bytes)
        self.size_label.config(text=formatted)

    def start_scan(self):
        self.scan_btn.config(state='disabled')
        self.clean_btn.config(state='disabled')
        self.progress.start(10)
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END) 
        self.log_text.config(state='disabled')
        self.log("正在初始化扫描...")
        
        threading.Thread(target=self.run_scan, daemon=True).start()
        
    def run_scan(self):
        def callback(msg, current_size):
            self.root.after(0, lambda: self.log(msg))
            
        total_size = self.cleaner.scan(callback=callback) 
        self.root.after(0, self.finish_scan, total_size)

    def finish_scan(self, total_size):
        self.progress.stop()
        self.update_size_label(total_size)
        
        self.log("\n")
        self.log("================= 扫描结果分析 =================")
        
        if total_size > 0:
            for category, details in self.cleaner.scan_details.items():
                if details['size'] > 0:
                    size_str = self.cleaner.get_formatted_size(details['size'])
                    self.log(f"【{category}】")
                    self.log(f"  - 占用空间: {size_str}")
                    self.log(f"  - 文件数量: {details['count']}")
                    self.log(f"  - 说明: {details['desc']}")
                    self.log("-" * 40)
            
            self.log(f"总计发现: {len(self.cleaner.scanned_files)} 个文件。")
            self.log("\n建议：以上文件均属于安全清理范围，不影响系统稳定性，请放心清理。")
            self.clean_btn.config(state='normal')
        else:
            self.log("未发现垃圾文件，您的系统非常干净！")
            
        self.scan_btn.config(state='normal')

    def start_clean(self):
        if not messagebox.askyesno("确认", "确定要删除这些文件吗？此操作不可撤销。"):
            return
            
        self.scan_btn.config(state='disabled')
        self.clean_btn.config(state='disabled')
        self.progress.start(10)
        
        threading.Thread(target=self.run_clean, daemon=True).start()

    def run_clean(self):
        def callback(msg, freed_space):
            self.root.after(0, lambda: self.log(msg))

        freed, errors = self.cleaner.clean(callback=callback)
        self.root.after(0, self.finish_clean, freed, errors)

    def finish_clean(self, freed, errors):
        self.progress.stop()
        self.update_size_label(0)
        self.log(f"----------------------------------------")
        self.log(f"清理完成！释放空间: {self.cleaner.get_formatted_size(freed)}")
        if errors > 0:
            self.log(f"注意: 有 {errors} 个文件无法删除（可能正在被使用）。")
        
        self.scan_btn.config(state='normal')
        self.clean_btn.config(state='disabled')
