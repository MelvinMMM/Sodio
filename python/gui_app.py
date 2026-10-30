"""
Application Tableau de Bord Principal (Dashboard V2) - Sodio (Sonic-Audio).
Thème Darkspine Sonic (Violet Améthyste & Anneaux d'Or) pour Melvin.
"""
import os
import sys
import json
import time
import subprocess
import ctypes
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
os.chdir(BASE_DIR)

if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
ICON_PATH = os.path.join(BASE_DIR, 'assets', 'icon.png')
PID_FILE = os.path.join(BASE_DIR, 'sodio.pid')

import gui_tabs

# Palette Sodio — Darkspine Sonic (Violet & Gold)
C_BG_SIDEBAR = '#0E0919'
C_BG_MAIN = '#090511'
C_ACCENT = '#9D4EDD'          # Violet Électrique Sonic
C_ACCENT_HOVER = '#7B2CBF'    # Violet Royal Profond
C_GOLD = '#FFD700'            # Anneau d'Or (World Ring)
C_GOLD_HOVER = '#FFB703'      # Ambre Doré
C_BTN_ACTIVE = '#1C1230'
C_BORDER = '#2E1A47'
C_TEXT_ACTIVE = '#FFFFFF'
C_TEXT_INACTIVE = '#A39BB0'

class SodioDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sodio (Sonic-Audio) — Micro-agent de Dictée Vocale")
        self.root.geometry("890x600")
        self.root.minsize(840, 550)
        self.root.configure(bg=C_BG_MAIN)

        # Centrage sur l'écran
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - 890) // 2)
        y = max(0, (sh - 600) // 2)
        self.root.geometry(f"890x600+{x}+{y}")

        # Gestion de la fermeture de fenêtre via [X]
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)

        # Icône de fenêtre
        self.brand_icon = None
        if os.path.exists(ICON_PATH):
            try:
                img = Image.open(ICON_PATH)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(False, self.icon_photo)
            except Exception:
                pass

        self.cfg = self.load_config()
        self.current_tab = None
        self.nav_buttons = {}

        self.setup_ui()
        self.select_tab("general")
        self.start_engine_status_monitor()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self, new_cfg):
        self.cfg = new_cfg
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde config: {e}")

    def is_engine_running(self):
        """Vérifie instantanément si le moteur d'écoute en tâche de fond tourne."""
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    content = f.read().strip()
                if content.isdigit():
                    pid = int(content)
                    PROCESS_QUERY_INFORMATION = 0x0400
                    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
                    if handle != 0:
                        ctypes.windll.kernel32.CloseHandle(handle)
                        return True
            except Exception:
                pass
        return False

    def setup_ui(self):
        # 1. Sidebar gauche
        self.sidebar = tk.Frame(self.root, bg=C_BG_SIDEBAR, width=240)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Header Sidebar avec logo officiel assets/icon.png
        brand_frame = tk.Frame(self.sidebar, bg=C_BG_SIDEBAR, pady=16, padx=14)
        brand_frame.pack(fill='x')

        brand_row = tk.Frame(brand_frame, bg=C_BG_SIDEBAR)
        brand_row.pack(anchor='w')

        if os.path.exists(ICON_PATH):
            try:
                raw_icon = Image.open(ICON_PATH).convert('RGBA')
                resized_icon = raw_icon.resize((32, 32), Image.Resampling.LANCZOS)
                self.brand_icon = ImageTk.PhotoImage(resized_icon)
                tk.Label(brand_row, image=self.brand_icon, bg=C_BG_SIDEBAR).pack(side='left', padx=(0, 8))
            except Exception:
                pass

        tk.Label(brand_row, text="Sodio", font=("Segoe UI", 13, "bold"),
                 fg=C_GOLD, bg=C_BG_SIDEBAR).pack(side='left')
        tk.Label(brand_frame, text="Sonic-Audio • Melvin Edition", font=("Segoe UI", 8, "italic"),
                 fg=C_ACCENT, bg=C_BG_SIDEBAR).pack(anchor='w', pady=(3, 0))

        # Séparateur subtil
        tk.Frame(self.sidebar, bg=C_BORDER, height=1).pack(fill='x', padx=14, pady=(0, 10))

        # Boutons Navigation
        tabs_def = [
            ("general", "⚙️  Général & Audio"),
            ("keys", "🔑  Moteurs IA & Clés"),
            ("lexique", "📖  Lexique Perso"),
            ("history", "📜  Historique (24H)"),
            ("legal", "🛡️  Confidentialité"),
        ]

        nav_container = tk.Frame(self.sidebar, bg=C_BG_SIDEBAR)
        nav_container.pack(fill='both', expand=True, padx=8)

        for tab_id, label in tabs_def:
            btn = tk.Button(
                nav_container, text=label, font=("Segoe UI", 9, "bold"),
                anchor='w', padx=12, pady=9, relief='flat', bd=0, cursor='hand2',
                bg=C_BG_SIDEBAR, fg=C_TEXT_INACTIVE, activebackground=C_BTN_ACTIVE,
                activeforeground=C_TEXT_ACTIVE,
                command=lambda tid=tab_id: self.select_tab(tid)
            )
            btn.pack(fill='x', pady=2)
            self.nav_buttons[tab_id] = btn

        # --- SECTION HERO : BOUTON ARRIÈRE-PLAN ---
        action_box = tk.Frame(self.sidebar, bg='#140C24', highlightbackground=C_BORDER, highlightthickness=1, padx=10, pady=10)
        action_box.pack(fill='x', padx=10, pady=(10, 5))

        self.btn_bg = tk.Button(
            action_box,
            text="🚀 Faire tourner en arrière-plan",
            font=("Segoe UI", 9, "bold"),
            bg='#7B2CBF', fg='#FFD700',
            activebackground='#9D4EDD', activeforeground='#FFFFFF',
            relief='flat', bd=0, cursor='hand2', padx=8, pady=8,
            command=self.run_in_background
        )
        self.btn_bg.pack(fill='x')

        tk.Label(
            action_box,
            text="Ferme cette interface et garde Sodio actif\ndans les icônes cachées (près de l'horloge).",
            font=("Segoe UI", 7), fg=C_TEXT_INACTIVE, bg='#140C24', justify='center'
        ).pack(fill='x', pady=(6, 0))

        # Footer Sidebar
        footer_frame = tk.Frame(self.sidebar, bg=C_BG_SIDEBAR, padx=12, pady=10)
        footer_frame.pack(fill='x', side='bottom')
        tk.Frame(self.sidebar, bg=C_BORDER, height=1).pack(fill='x', padx=14, side='bottom')

        # Indicateur Dynamique de Statut du Moteur
        self.status_engine_label = tk.Label(
            footer_frame, text="⚡ Vérification...", font=("Segoe UI", 8, "bold"),
            fg=C_GOLD, bg=C_BG_SIDEBAR
        )
        self.status_engine_label.pack(anchor='w', pady=(0, 6))

        # Bouton Arrêter Complètement
        btn_stop = tk.Button(
            footer_frame, text="🛑 Arrêter complètement Sodio", font=("Segoe UI", 8, "bold"),
            anchor='center', padx=8, pady=5, relief='flat', bd=0, cursor='hand2',
            bg='#23121F', fg='#FF7B90', activebackground='#351A2C',
            activeforeground='#FFA1B0', command=self.stop_all
        )
        btn_stop.pack(fill='x', pady=(0, 6))

        tk.Label(footer_frame, text="Créé pour Melvin", font=("Segoe UI", 7, "italic"),
                 fg=C_TEXT_INACTIVE, bg=C_BG_SIDEBAR).pack(anchor='w')

        # 2. Zone de Contenu droite
        self.content_area = tk.Frame(self.root, bg=C_BG_MAIN)
        self.content_area.pack(side='right', fill='both', expand=True)

    def start_engine_status_monitor(self):
        """Met à jour l'indicateur de statut du moteur toutes les 2 secondes."""
        def _check():
            if self.is_engine_running():
                hk = self.cfg.get('hotkey', 'f4').upper()
                self.status_engine_label.config(
                    text=f"🟢 Moteur Actif [{hk}]", fg=C_GOLD
                )
                self.btn_bg.config(text="🚀 Minimiser en arrière-plan")
            else:
                self.status_engine_label.config(
                    text="⏸️ Moteur en attente", fg=C_TEXT_INACTIVE
                )
                self.btn_bg.config(text="🚀 Démarrer en arrière-plan")

            if self.root.winfo_exists():
                self.root.after(2000, _check)

        _check()

    def run_in_background(self):
        """Active le moteur en tâche de fond et ferme le tableau de bord."""
        if not self.is_engine_running():
            vbs_path = os.path.join(BASE_DIR, 'lancer_silencieux.vbs')
            if os.path.exists(vbs_path):
                subprocess.Popen(['wscript.exe', vbs_path], cwd=BASE_DIR, shell=True)
            else:
                run_script = os.path.join(PYTHON_DIR, 'run.py')
                subprocess.Popen(['pythonw.exe', run_script], cwd=BASE_DIR, shell=True)
            time.sleep(0.4)

        hk = self.cfg.get('hotkey', 'f4').upper()
        messagebox.showinfo(
            "Sodio (Sonic-Audio)",
            f"✨ Sodio roule désormais en arrière-plan !\n\n"
            f"• Raccourci actif : Appuyez sur [{hk}] n'importe où pour dicter.\n"
            f"• Icône : Retrouvez Sodio dans les icônes cachées Windows (près de l'horloge) "
            f"pour rouvrir ce tableau de bord à tout moment."
        )
        self.root.destroy()

    def on_close_window(self):
        """Comportement quand l'utilisateur clique sur la croix [X] de la fenêtre."""
        # Si le moteur tourne, fermer la fenêtre le laisse tourner en arrière-plan !
        self.root.destroy()

    def stop_all(self):
        """Arrête le moteur d'arrière-plan et ferme l'interface."""
        if messagebox.askyesno("Sodio", "Voulez-vous vraiment arrêter complètement Sodio et couper la dictée vocale ?"):
            stop_script = os.path.join(BASE_DIR, 'arreter_sodio.bat')
            if os.path.exists(stop_script):
                subprocess.Popen(['cmd.exe', '/c', stop_script], cwd=BASE_DIR, shell=True)
            self.root.destroy()
            sys.exit(0)

    def select_tab(self, tab_id):
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(bg=C_BTN_ACTIVE, fg=C_GOLD)
            else:
                btn.configure(bg=C_BG_SIDEBAR, fg=C_TEXT_INACTIVE)

        for widget in self.content_area.winfo_children():
            widget.destroy()

        self.cfg = self.load_config()
        if tab_id == "general":
            view = gui_tabs.build_general_tab(self.content_area, self.cfg, self.save_config)
        elif tab_id == "keys":
            view = gui_tabs.build_keys_tab(self.content_area, self.cfg, self.save_config)
        elif tab_id == "lexique":
            view = gui_tabs.build_lexique_tab(self.content_area)
        elif tab_id == "history":
            view = gui_tabs.build_history_tab(self.content_area, self.cfg)
        elif tab_id == "legal":
            view = gui_tabs.build_legal_tab(self.content_area)
        else:
            return

        view.pack(fill='both', expand=True)

def open_dashboard():
    root = tk.Tk()
    app = SodioDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    open_dashboard()
