import os, sys
from tkinter import *
from random import randint
#from NetworkNode import NetWorkNode

class GUIHelper:
    def __init__(self, gui):
        self.gui = gui

    def generate_handler(self, func, *args):
        def handler(event=None):
            func(*args)
        return handler

    def generate_main_text(self, text, parent=None):
        if not parent:
            parent = self.gui.root
        txt_var = StringVar(parent)
        txt_var.set(text)
        lbl = Label(parent, textvariable=txt_var, bg=self.gui.bg, anchor=W)
        lbl.grid(row=0, column=0, sticky=W, pady=20,padx=20)
        return txt_var


class GUI:
    def __init__(self, program):
        self.master = program
        self.root = Tk()
        self.sizes = [530, 200]
        self.bg = 'white'
        self.helper = GUIHelper(self)

    def initial(self):
        self.root.geometry(str(self.sizes[0])+'x'+str(self.sizes[1]))
        self.root.configure(bg=self.bg)
        self.root.title("File Sync Helper")
        self.helper.generate_main_text("Welcome!")
        
        #share_folder_btn = Button(self.root,
         #                         text='Add a folder to LAN synchronization',
          #                        width=50)
        #share_folder_btn.grid(row=1, columnspan=3, padx=30, pady=5)
        #share_folder_btn.bind('<Button-1>',
        #                      self.helper.generate_handler(self.share_folder))

        see_files_btn = Button(self.root,
                               text='See synchronized files state',
                               width=50)
        see_files_btn.grid(row=2, columnspan=3, padx=30, pady=5)
        see_files_btn.bind('<Button-1>',
                              self.helper.generate_handler(self.see_files))

        start_folder_btn = Button(self.root,
                                  text='Join existing folder synchronization',
                                  width=50)
        start_folder_btn.grid(row=3, columnspan=3, padx=30, pady=5)
        start_folder_btn.bind('<Button-1>',
                              self.helper.generate_handler(self.start_folder))

    def share_folder(self):
        cur_window = Toplevel(self.root, bg=self.bg)
        main_txt = self.helper.generate_main_text("Enter folder path to share it:",
                                           cur_window)
        
        folder_path = StringVar(cur_window)
        folder_path.set("Absolute path of folder")
        path_txt = Entry(cur_window, textvariable=folder_path, width=30,
                         bg='light grey')
        path_txt.grid(row=1, column=0, columnspan=2, sticky=W, pady=20, padx=20)

        submit_btn = Button(cur_window, text='Submit')
        submit_btn.grid(row=1, column=2, sticky=E, pady=20, padx=20)
        def submit_handler():
            if path_txt.get()!="Absolute path of folder":
                main_txt.set("Added. Type  new one?")
            else:
                main_txt.set("Error")
        submit_btn.bind('<Button-1>',
                    self.helper.generate_handler(submit_handler))
        '''
        abrir toplevel ou reconfigurar a janela principal para mostrar prompt de caminho da pasta
        verificar se o caminho existe, e dar erro se não existir
        verificar se já existe pasta sincronizada com o mesmo nome e dar erro se existir
        criar nova pasta no diretorio de pastas compartilhadas com o nome original
        copiar arquivos da pasta original para essa nova pasta (talvez precise dar um lock nelas)
        confirmar o sucesso da transferencia para o usuário
        '''

    def see_files(self):
        cur_window = Toplevel(self.root, bg=self.bg)
        main_txt = self.helper.generate_main_text("Choose sync folder:",
                                           cur_window)
        refresh_btn = Button(cur_window, text='Refresh', anchor=E)
        refresh_btn.grid(row=0, column=2, pady=20, padx=20, sticky=E)
        cur_widgets = []
        
        def get_folder_data():
            return self.master.get_synched_folders()
            
        def refresh():
            nonlocal cur_widgets
            for w in cur_widgets:
                w.destroy()
            cur_widgets = []
            folderdata = get_folder_data()
            cur_window.geometry(str(self.sizes[0])+'x'+
                           str(self.sizes[1]+20+35*(len(folderdata)-3)))
            
            for i, folder in enumerate(folderdata):
                folder_btn = Button(cur_window, text=folder, width=50)
                folder_btn.grid(row=i+1, columnspan=3, padx=30, pady=5)
                folder_btn.bind('<Button-1>',
                         self.helper.generate_handler(self.show_folder, folder))
                cur_widgets.append(folder_btn)
                
        refresh_btn.bind('<Button-1>',
                         self.helper.generate_handler(refresh))
        refresh()
        '''
        abrir guia menu, tabela ou combo-box para escolher a pasta para visualizar os arquivos
        serão mostradas só as pastas com sincronização aceita
        após escolhida a pasta, haverá uma nova guia onde
            o usuário verá metadata dos arquivos da pasta
        refresh automatico a cada 5 segundos talvez
        '''

    def show_folder(self, folder):
        cur_window = Toplevel(self.root, bg=self.bg)
        main_txt = self.helper.generate_main_text(folder+"'s files:",
                                           cur_window)
        refresh_btn = Button(cur_window, text='Refresh', anchor=E)
        refresh_btn.grid(row=0, column=2, pady=20, padx=20, sticky=E)
        cur_labels = []
        def get_metadata():
            return self.master.get_files_metadata(folder)

            
        def refresh_handler():
            nonlocal cur_labels
            for w in cur_labels:
                w.destroy()
            cur_labels = []
            metadata = get_metadata()
            for i, file in enumerate(metadata):
                file_lbl = Label(cur_window,
                                 text="  ||  ".join(metadata[i]), anchor=W)
                file_lbl.grid(row=i+1, columnspan=3, padx=30, pady=5, sticky=W)
                cur_labels.append(file_lbl)
            cur_window.geometry(str(self.sizes[0])+'x'+
                                str(self.sizes[1]+20+30*(len(metadata)-3)))

        refresh_btn.bind('<Button-1>',
                         self.helper.generate_handler(refresh_handler))
        refresh_handler()
        
    def start_folder(self):
        cur_window = Toplevel(self.root, bg=self.bg)
        main_txt = self.helper.generate_main_text("Select folders for synchronization:",
                                           cur_window)
        refresh_btn = Button(cur_window, text='Refresh', anchor=E)
        refresh_btn.grid(row=0, column=2, pady=20, padx=20, sticky=E)
        cur_widgets = []
        state = {}
        real_status = {}

        save_btn = Button(cur_window, text='Save Changes', anchor=E)
        save_btn.grid(row=0, column=4, pady=20, padx=20, sticky=E)

        def updt_status(x, v):
            self.master.set_status(x, v)
            
        def save_handler():
            for k in state:
                updt_status(k, state[k].get())

        save_btn.bind('<Button-1>',
                      self.helper.generate_handler(save_handler))
        
        def get_folder_data():
            return self.master.get_all_folders()

        def get_status(a):
            return self.master.get_folder_status(a)
            
        def refresh():
            nonlocal cur_widgets
            for w in cur_widgets:
                w.destroy()
            cur_widgets = []
            folderdata = get_folder_data()
            status = get_status(folderdata)
            cur_window.geometry(str(self.sizes[0])+'x'+
                           str(self.sizes[1]+20+35*(len(folderdata)-3)))

            for i in range(len(folderdata)):
                folder = folderdata[i]
                folder_lbl = Label(cur_window, text=folder, width=50)
                folder_lbl.grid(row=i+1, columnspan=3, padx=30, pady=5)
                cur_widgets.append(folder_lbl)
                
                check_var = IntVar(cur_window)
                folder_check = Checkbutton(cur_window, variable=check_var,
                                           onvalue=1, offvalue=0)
                folder_check.grid(row=i+1, column=4, padx=30, pady=5)
                if status[folder]:
                    folder_check.select()
                cur_widgets.append(folder_check)
                state[folder] = check_var
                
        refresh_btn.bind('<Button-1>',
                         self.helper.generate_handler(refresh))
        refresh()
        '''
        abrir guia de seleção de todas as pastas na rede e mostrar o status de
            sincronização ou não
        permitir escolher uma pasta para alterar o status de sincronização:
            alterar a permissão do NetworkNode de copiar ou não as mudanças da pasta
        
        '''

class Program:
    def __init__(self):
        self.basedir = os.getcwd()
        self.folders_dir = os.path.join(self.basedir, 'Sync Folders')
        self.zips_dir = os.path.join(self.basedir, '.zips')
        self.folders = [os.path.splitext(file)[0] for file in os.listdir(self.zips_dir)]
        self.folder_status = {a: int(a in os.listdir(self.folders_dir)) for a in self.folders}
        self.gui = GUI(self)
        self.gui.initial()
        mainloop()

    def add_folder(self):
        self.folders.append('Folder '+str(len(self.folders)+1))
        self.folder_status[self.folders[-1]] = 0

    def get_synched_folders(self):
        a = []
        for i in self.folders:
            if self.folder_status[i]:
                a.append(i)
        self.add_folder()
        return a

    def get_all_folders(self):
        return self.folders.copy()

    def get_folder_status(self, folder):
        return self.folder_status.copy()

    def get_files_metadata(self, folder):
        #TODO
        a = []
        for i in range(16):
            a.append(['Random File', '00:00:00', '0/0/0000',
                    str(randint(100000000, 999999999))])
        return a

    def set_status(self, folder, new_status):
        #TODO
        if new_status == self.folder_status[folder]:
            return
        self.folder_status[folder] = new_status
        if new_status:
            pass
            #Adicionar a pasta na sincronização
        else:
            pass
            #Retirar a pasta da sincronização
        
        

if __name__=="__main__":
    print(os.getcwd())
    a = Program()
