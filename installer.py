import shutil
import winreg
import os.path
from urllib.request import urlretrieve
from inspect import cleandoc

home = os.path.expandvars("%appdata%/MILC")

def get_input(inp):
    return input(f"{inp}? > ")

def get_valid_input(inp, check, message):
    while check(output := get_input(inp)):
        print(message)
    return output

def create_send(path, title, arg):
    with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILC")) as key:
        winreg.SetValue(key, "", winreg.REG_SZ, title)
        winreg.SetValueEx(key, "Icon", None, winreg.REG_EXPAND_SZ, rf"%appdata%\MILC\MILC.ico")
    with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILC\command")) as key:
        winreg.SetValueEx(key, "", None, winreg.REG_EXPAND_SZ, rf'"{home}\MILC.exe" "send" "{arg}"')

def create_send_to(path):
    with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo")) as key:
        winreg.SetValueEx(key, "MUIVerb", None, winreg.REG_SZ, "Send to")
        winreg.SetValueEx(key, "subcommands", None, winreg.REG_SZ, "")

def create_item(path, title, arg):
    # winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILC")
    create_send(path, title, arg)
    # winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo")
    create_send_to(path)

if __name__ == "__main__":
    print("""
    
    /$$      /$$ /$$$$$$ /$$        /$$$$$$ 
    | $$$    /$$$|_  $$_/| $$       /$$__  $$
    | $$$$  /$$$$  | $$  | $$      | $$  \__/
    | $$ $$/$$ $$  | $$  | $$      | $$      
    | $$  $$$| $$  | $$  | $$      | $$      
    | $$\  $ | $$  | $$  | $$      | $$    $$
    | $$ \/  | $$ /$$$$$$| $$$$$$$$|  $$$$$$/
    |__/     |__/|______/|________/ \______/
            Mothers I'd Like to Calm
    
            
    """)

    print("Downloading MILC...")

    if os.path.isdir(home):
        shutil.rmtree(home)
    os.mkdir(home)

    urlretrieve("https://github.com/YoavShilon05/MILC/releases/latest/download/MILC.exe", f"{home}/MILC.exe")
    urlretrieve("https://raw.githubusercontent.com/YoavShilon05/MILC/main/MILC.ico", f"{home}/MILC.ico")

    print("\nCreating settings...")

    def root_valid(o: str) -> bool:
        return not os.path.isdir(os.path.dirname(o.lstrip('\\/')))

    root = get_valid_input("Root directory", root_valid, "Invalid path").replace('/', '\\').rstrip('\\')
    if not os.path.isdir(root):
        os.mkdir(root)
    name = get_valid_input("Your name", lambda o: ' ' in o, "Spaces in names unsupported")
    ip = get_input("SSH IP")
    ssh_name = get_input("SSH Username")
    ssh_password = get_input("SSH Password")

    with open(f"{home}/settings.ini", 'w') as f:
        f.write(cleandoc(f"""
        [Local]
        Root={root}
        [Remote]
        Username={name}
        GarbageDestination=
        [SSH]
        IP={ip}
        Username={ssh_name}
        Password={ssh_password}
        """))

    print("\nCreating context menu items...")
    create_item("*", "Send file", "%1")
    create_item("Directory", "Send folder", "%1")
    create_item("Directory\\Background", "Send folder", "%w")

    print("\nAdding MILC to startup...")
    os.system(r'schtasks /create /sc ONLOGON /tn MILC /tr "%appdata%\MILC\MILC.exe tray" /rl HIGHEST /f')

    print("\nInitializing MILC...")
    os.system(f"{home}\\MILC init")
    os.system(f"{home}\\MILC update-users")

    print("\n\nDone! Launching MILC...")
    os.system("schtasks /run /tn MILC")
