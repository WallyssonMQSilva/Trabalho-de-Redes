import subprocess
import platform
import zipfile
import shutil
import ctypes
import hashlib
import socket
import os
import sys
import time
import copy
import json
import threading
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from NetworkNode import NetworkNode
from interface import GUI
from tkinter import *

#variaveis

updatedStatus = False
basedir = os.getcwd()
source_folder =os.path.join(basedir, 'SyncFolder') # folders
dest_folder = os.path.join(basedir, '.zips')  # zips
G_folder_status = {}

# funcoes

def run_node(param1):
    n = NetworkNode(param1)


def ping_ip(ip):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', ip]

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        if "nreachable" in output or "timed out" in output or "inac" in output:
            return (ip, False)
        return (ip, True)
    except subprocess.CalledProcessError as e:
        return (ip, False)
    except Exception as e:
        print(f"An error occurred: {e}")
        return (ip, False)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def zip_folder(folder_path, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                zipf.write(file_path, arcname)
    print(f"Zipped {folder_path} to {zip_filename}")

def unzip_file(zip_filename, dest_folder):
    base_name = os.path.basename(zip_filename)
    filename, extension = os.path.splitext(base_name)

    # print(filename)
    # print(G_folder_status[filename])

    if G_folder_status[filename] == 0:
        return
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        zipf.extractall(dest_folder)
    print(f"Unzipped {zip_filename} to {dest_folder}")

def get_mod_time(path):
    return os.path.getmtime(path)

def zip_folders(source_folder, dest_folder, folder_mod_times):
    current_folders = set()
    for folder_name in os.listdir(source_folder):
        if G_folder_status[folder_name] == 0:
            continue
        folder_path = os.path.join(source_folder, folder_name)
        if os.path.isdir(folder_path):
            current_folders.add(folder_name)
            zip_filename = os.path.join(dest_folder, f"{folder_name}.zip")
            mod_time = get_mod_time(folder_path)
            if folder_name not in folder_mod_times or folder_mod_times[folder_name] < mod_time:
                zip_folder(folder_path, zip_filename)
                folder_mod_times[folder_name] = mod_time

    existing_zip_files = set(os.listdir(dest_folder))
    for folder_name in folder_mod_times.keys():
        zip_filename = f"{folder_name}.zip"
        if folder_name not in current_folders and zip_filename in existing_zip_files:
            pass
            # zip_path = os.path.join(dest_folder, zip_filename)
            # os.remove(zip_path)
            # print(f"Deleted {zip_path}")

    for folder_name in list(folder_mod_times.keys()):
        if folder_name not in current_folders:
            del folder_mod_times[folder_name]

def unzip_files(dest_folder, source_folder, zip_mod_times):
    current_zip_files = set()
    global updatedStatus
    if updatedStatus:
        for zip_filename in os.listdir(dest_folder):
            if zip_filename.endswith('.zip'):
                zip_path = os.path.join(dest_folder, zip_filename)
                current_zip_files.add(zip_filename)
                folder_name = zip_filename[:-4]
                folder_path = os.path.join(source_folder, folder_name)
                unzip_file(zip_path, folder_path)
                updatedStatus = False

    for zip_filename in os.listdir(dest_folder):
        if zip_filename.endswith('.zip'):
            zip_path = os.path.join(dest_folder, zip_filename)
            current_zip_files.add(zip_filename)
            folder_name = zip_filename[:-4]
            folder_path = os.path.join(source_folder, folder_name)
            mod_time = get_mod_time(zip_path)
            if zip_filename not in zip_mod_times or zip_mod_times[zip_filename] < mod_time:
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)  # Remove the existing folder
                unzip_file(zip_path, folder_path)
                zip_mod_times[zip_filename] = mod_time

    # for zip_filename in list(zip_mod_times.keys()):
    #     if zip_filename not in current_zip_files:
    #         folder_name = zip_filename[:-4]
    #         folder_path = os.path.join(source_folder, folder_name)
    #         if os.path.exists(folder_path):
    #             shutil.rmtree(folder_path)
    #             print(f"Deleted folder {folder_path} corresponding to removed zip file")
    #         del zip_mod_times[zip_filename]

def get_directory_state(directory):
    state = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            state[filepath] = os.path.getmtime(filepath)
    return state

def zip_unzip_check(source_folder, dest_folder, check_interval=2):
    os.makedirs(dest_folder, exist_ok=True)

    folder_mod_times = {}
    zip_mod_times = {}
    last_dest_state = {}
    last_src_state = {}
    dest_update_db = False
    src_update_db = False


    while True:
        try:
            global updatedStatus
            if updatedStatus:
                print("dif state DEST folder")
                unzip_files(dest_folder, source_folder, zip_mod_times)
                last_dest_state = get_directory_state(dest_folder)
                src_update_db = True
            elif last_dest_state == get_directory_state(dest_folder):
                print("same state DEST folder")
            elif dest_update_db == True:
                last_dest_state = get_directory_state(dest_folder)
                dest_update_db = False
                print("same state DEST folder")
            else:
                print("dif state DEST folder")
                unzip_files(dest_folder, source_folder, zip_mod_times)
                last_dest_state = get_directory_state(dest_folder)
                src_update_db = True
        except:
            pass

        time.sleep(check_interval)

        try:
            if last_src_state == get_directory_state(source_folder):
                print("same state SRC folder")
            elif src_update_db == True:
                last_src_state = get_directory_state(source_folder)
                src_update_db = False
                print("same state SRC folder")
            else:
                print("dif state SRC folder")
                zip_folders(source_folder, dest_folder, folder_mod_times)
                last_src_state = get_directory_state(source_folder)
                dest_update_db = True
        except:
            pass

        time.sleep(check_interval)


# ips check
def ip_check():
    print("testando IPs da rede")
    base_ip = "192.168."
    reachable_ips = []
    num_threads = 50

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_ip = {executor.submit(ping_ip, f"{base_ip}{i}.{j}"): (i, j) for i in range(1) for j in range(256)}

        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                result_ip, is_reachable = future.result()
                if is_reachable:
                    print(f"{result_ip} alcancavel")
                    reachable_ips.append(result_ip)

            except Exception as e:
                print(f"erro para {ip}: {e}")

        print(f"IPs alcancaveis: {reachable_ips}")

class Program:
    def __init__(self):
        self.basedir = os.getcwd()
        self.folders_dir = source_folder
        self.zips_dir = dest_folder
        self.folders = [os.path.splitext(file)[0] for file in os.listdir(self.zips_dir)]
        self.folder_status = {a: int(a in os.listdir(self.folders_dir)) for a in self.folders}

        global G_folder_status
        G_folder_status= self.folder_status

        self.gui = GUI(self)
        self.gui.initial()
        mainloop()


    def add_folder(self):
        self.folders.append('Folder ' + str(len(self.folders) + 1))
        self.folder_status[self.folders[-1]] = 0

    def get_synched_folders(self):
        a = []
        for i in self.folders:
            if self.folder_status[i]:
                a.append(i)
        return a

    def get_all_folders(self):
        return self.folders.copy()

    def get_folder_status(self, folder):
        return self.folder_status.copy()

    def get_files_metadata(self, folder):
        folder_path = basedir + os.sep + "SyncFolder" + os.sep + folder
        a = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat_info = os.stat(file_path)
                    last_modified = datetime.datetime.fromtimestamp(stat_info.st_mtime)
                    creation_time = datetime.datetime.fromtimestamp(stat_info.st_ctime)

                    with open(file_path, 'rb') as f:
                        data = f.read()
                        sha1_hash = hashlib.sha1(data).hexdigest()

                    a.append([str(file), str(last_modified), str(creation_time), str(sha1_hash)])
                except OSError as e:
                    print(f"erro: {e}")


        return a

    def set_status(self, folder, new_status):
        print(G_folder_status)
        if new_status == self.folder_status[folder]:
            return
        self.folder_status[folder] = new_status
        global updatedStatus
        updatedStatus = True

if __name__=='__main__':
    # admin check
    if is_admin():
        print("running as administrator")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit(0)
    #ip_check()
    # zip e unzip
    zip_thread = threading.Thread(target=zip_unzip_check, args=(source_folder,dest_folder))
    zip_thread.daemon = True  # Optional: allows the thread to exit when the main program exits
    zip_thread.start()
    a = Program()
    print('here')

    input()
    node_thread.join()
