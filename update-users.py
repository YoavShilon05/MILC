import winreg
from main import ssh

def add(path, u, arg = '%1'):
    with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo\shell\SendTo{u}")) as key:
        winreg.SetValue(key, "", winreg.REG_SZ, f"Send to {u}")
        winreg.SetValueEx(key, "Icon", None, winreg.REG_EXPAND_SZ, rf"%appdata%\MILC\MILC.ico")
    with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo\shell\SendTo{u}\command")) as key:
        winreg.SetValueEx(key, "", None, winreg.REG_EXPAND_SZ, f'%appdata%\MILC\MILC.exe "sendto" "{arg}" "{u}"')

_, stdout, _ = ssh.exec_command("ls ~/assi-pkg/")
for u in stdout.read().split(b'\n'):
    u = u.decode()
    if u == '': continue
    add("*", u)
    add("Directory", u)
    add("Directory\\Background", u, '%w')

