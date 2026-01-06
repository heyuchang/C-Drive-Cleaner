import os
import shutil
import winreg
import ctypes
from ctypes import windll, wintypes

class SystemMigrator:
    def __init__(self):
        self.user_folders = {
            "Desktop": {
                "reg_name": "Desktop",
                "guid": "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}",
                "desc": "桌面文件"
            },
            "Downloads": {
                "reg_name": "{374DE290-123F-4565-9164-39C4925E467B}",
                "guid": "{374DE290-123F-4565-9164-39C4925E467B}",
                "desc": "下载文件夹"
            },
            "Documents": {
                "reg_name": "Personal",
                "guid": "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}", 
                "desc": "我的文档"
            },
            "Pictures": {
                "reg_name": "My Pictures",
                "guid": "{33E28130-4E1E-4676-835A-98395C3BC3BB}",
                "desc": "图片"
            },
            "Videos": {
                "reg_name": "My Video",
                "guid": "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}",
                "desc": "视频"
            },
            "Music": {
                "reg_name": "My Music",
                "guid": "{4BD8D571-6D19-48D3-BE97-422220080E43}",
                "desc": "音乐"
            }
        }
        
    def get_folder_path(self, reg_name):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            )
            path, _ = winreg.QueryValueEx(key, reg_name)
            winreg.CloseKey(key)
            return os.path.expandvars(path)
        except Exception as e:
            print(f"Error reading registry for {reg_name}: {e}")
            return None

    def get_folder_size(self, path):
        total_size = 0
        if not path or not os.path.exists(path):
            return 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        except:
            pass
        return total_size

    def get_scan_results(self):
        results = []
        for key, info in self.user_folders.items():
            current_path = self.get_folder_path(info["reg_name"])
            if current_path and os.path.exists(current_path):
                # Check if it's already on a non-C drive (simple check)
                is_migrated = not current_path.lower().startswith("c:")
                
                results.append({
                    "key": key,
                    "name": info["desc"],
                    "path": current_path,
                    "size": self.get_folder_size(current_path),
                    "is_migrated": is_migrated
                })
        return results

    def migrate_folder(self, folder_key, target_root, callback=None):
        r"""
        Migrates a specific folder to target_root (e.g., D:\UserFiles)
        """
        info = self.user_folders.get(folder_key)
        if not info:
            return False, "Unknown folder type"

        current_path = self.get_folder_path(info["reg_name"])
        if not current_path or not os.path.exists(current_path):
            return False, "Source folder not found"

        # Create new path, e.g., D:\UserFiles\Downloads
        new_path = os.path.join(target_root, folder_key)
        
        # 1. Self-inclusion Check
        if os.path.abspath(new_path).lower().startswith(os.path.abspath(current_path).lower()):
             return False, "目标路径不能在源文件夹内部 (Recursion Error)"

        if os.path.abspath(current_path).lower() == os.path.abspath(new_path).lower():
            return False, "源路径与目标路径相同"

        try:
            # 2. Copy files
            if callback: callback(f"Copying files from {current_path} to {new_path}...")
            
            # Using shutil.copytree with dirs_exist_ok=True to merge/copy
            shutil.copytree(current_path, new_path, dirs_exist_ok=True)
            
            # 3. Update Registry
            if callback: callback("Updating Registry...")
            self.set_registry_path(info["reg_name"], new_path)
            
            # 4. Notify System (Refresh Explorer Icons)
            try:
                # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)
            except:
                pass
                
            # 5. Delete Source Files (To free up space)
            if callback: callback("Cleaning up old files...")
            try:
                # We iterate and remove to avoid removing the root folder if it's special/junction,
                # or just remove the content. 
                # Actually, standard behavior is to leave the old empty folder or remove it if possible.
                # Let's try to remove content first.
                for root, dirs, files in os.walk(current_path, topdown=False):
                    for name in files:
                        try:
                            os.remove(os.path.join(root, name))
                        except: pass
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except: pass
                # Try remove root
                try:
                    os.rmdir(current_path)
                except: pass
            except Exception as e:
                print(f"Cleanup warning: {e}")

            if callback: callback(f"Migration of {folder_key} successful!")
            return True, "Success"
            
        except Exception as e:
            return False, str(e)

    def set_registry_path(self, reg_name, new_path):
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, reg_name, 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)

    def get_formatted_size(self, size_bytes):
        # Reusing helper
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def get_large_files(self, path, limit=50):
        """
        Returns a list of dictionaries [{'name':..., 'path':..., 'size':...}, ...]
        Sorted by size descending.
        """
        files_list = []
        if not path or not os.path.exists(path):
            return files_list

        try:
            for root, dirs, files in os.walk(path):
                for name in files:
                    try:
                        file_path = os.path.join(root, name)
                        if os.path.islink(file_path):
                            continue
                        size = os.path.getsize(file_path)
                        files_list.append({
                            'name': name,
                            'path': file_path,
                            'size': size
                        })
                    except:
                        pass
        except:
            pass

        # Sort by size descending
        files_list.sort(key=lambda x: x['size'], reverse=True)
        return files_list[:limit]
