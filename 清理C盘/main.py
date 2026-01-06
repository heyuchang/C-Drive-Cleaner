import sys
import os
import ctypes
import tkinter as tk
from ui import CleanerApp

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    # Get absolute path of the script to avoid "File not found" in new process
    script_path = os.path.abspath(sys.argv[0])
    
    # Quote arguments to handle spaces in paths
    args = [f'"{script_path}"'] + [f'"{arg}"' for arg in sys.argv[1:]]
    args_str = " ".join(args)
    
    # Explicitly set the working directory to the script's directory
    cwd = os.path.dirname(script_path)
    
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args_str, cwd, 1)

def main():
    if not is_admin():
        # Re-run the program with admin rights
        try:
            run_as_admin()
        except Exception as e:
            print(f"Failed to elevate: {e}")
            input("Press Enter to exit...")
        sys.exit()

    
    try:
        root = tk.Tk()
        app = CleanerApp(root)
        
        # Center the window
        window_width = 600
        window_height = 450
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[Error] 程序发生错误: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
