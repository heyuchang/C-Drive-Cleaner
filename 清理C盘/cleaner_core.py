import os
import shutil
import glob
import platform

class SystemCleaner:
    def __init__(self):
        self.total_size = 0
        self.scanned_files = [] # List of (path, size) tuples
        self.scan_details = {} # Dictionary to store details per category
        self.is_scanning = False
        
        # Define target directories to clean with metadata
        self.targets = [
            {
                "path": os.environ.get('TEMP'),
                "name": "用户临时文件 (User Temp)",
                "desc": "各类软件运行时产生的临时缓存，通常可以安全删除。"
            },
            {
                "path": os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
                "name": "系统临时文件 (System Temp)",
                "desc": "Windows系统运行产生的临时数据，重启后通常无用。"
            },
            {
                "path": os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch'),
                "name": "预读取文件 (Prefetch)",
                "desc": "系统为加快启动速度生成的缓存，定期清理有助于解决系统卡顿。"
            },
            {
                "path": os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'SoftwareDistribution', 'Download'),
                "name": "Windows更新缓存",
                "desc": "Windows Update下载的安装包，更新完成后可以删除以释放大量空间。"
            }
        ]

    def get_formatted_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def scan(self, callback=None):
        """
        Scans target directories for junk files.
        callback: function to call with (current_path, found_size) updates
        """
        self.total_size = 0
        self.scanned_files = []
        self.scan_details = {} # Reset details
        self.is_scanning = True
        
        print("Starting scan...")
        
        for target in self.targets:
            target_path = target["path"]
            category_name = target["name"]
            
            # Initialize category details
            self.scan_details[category_name] = {
                "desc": target["desc"],
                "size": 0,
                "count": 0,
                "files": []
            }
            
            if not target_path or not os.path.exists(target_path):
                continue
                
            try:
                # Walk through directory
                for root, dirs, files in os.walk(target_path):
                    if not self.is_scanning: break
                    
                    for name in files:
                        try:
                            file_path = os.path.join(root, name)
                            # Skip if it's a symbolic link to avoid following outside
                            if os.path.islink(file_path):
                                continue
                                
                            size = os.path.getsize(file_path)
                            self.total_size += size
                            
                            # Add to flat list for cleaning
                            self.scanned_files.append((file_path, size)) 
                            
                            # Add to detailed stats
                            self.scan_details[category_name]["size"] += size
                            self.scan_details[category_name]["count"] += 1
                            
                            if callback:
                                # Send full path instead of just name for clarity
                                callback(f"Found [{category_name}]: {file_path}", self.total_size)
                        except (PermissionError, OSError):
                            continue
            except (PermissionError, OSError):
                continue

        print(f"Scan complete. Found {len(self.scanned_files)} files, Total: {self.get_formatted_size(self.total_size)}")
        return self.total_size

    def clean(self, callback=None):
        """
        Deletes the scanned files.
        callback: function to call with (status_message, freed_space)
        """
        freed_space = 0
        errors = 0
        
        for file_path, size in self.scanned_files:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    freed_space += size
                    if callback:
                        callback(f"Deleted: {file_path}", freed_space)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    if callback:
                        callback(f"Deleted Dir: {file_path}", freed_space)
            except Exception as e:
                errors += 1
                if callback:
                     callback(f"Skipped (In Use): {file_path}", freed_space)
        
        # Clean empty directories in targets
        for target in self.targets:
             target_path = target["path"]
             if not target_path or not os.path.exists(target_path): continue
             for root, dirs, files in os.walk(target_path, topdown=False):
                for name in dirs:
                    try:
                        dir_path = os.path.join(root, name)
                        os.rmdir(dir_path)
                    except:
                        pass

        return freed_space, errors
