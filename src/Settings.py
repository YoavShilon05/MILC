import configparser
import os

config = configparser.ConfigParser()
settings_path = os.path.expandvars("%appdata%/MILC/settings.ini")
config.read(settings_path)

home = os.path.expandvars("%appdata%/MILC")

ip = config["SSH"]["IP"]
ssh_username = config["SSH"]["Username"]
ssh_password = config["SSH"]["Password"]

root = os.path.normpath(config["Local"]["Root"])
garbage = config["Remote"]["GarbageDestination"]
username = config["Remote"]["Username"]
localroot = root + f"/{username}"
payload = "assi-payload"

remote = f"~/assi-pkg/{username}"
