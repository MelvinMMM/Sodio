"""
Module HUD Flottant (Mini-Badge discret) pour Sodio (Sonic-Audio).
Affiche un retour visuel ultra-lisible et direct :
- 🔴 Enregistrement actif : Rouge (#FF3B30)
- 🟡 Transcription en cours : Jaune (#FFD700)
Utilise WS_EX_NOACTIVATE sous Windows pour ne JAMAIS voler le focus du curseur.
"""
import sys
import queue
import threading
import tkinter as tk
import ctypes

class FloatingHUD:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self._cmd_queue = queue.Queue()
        self._root = None
        self._label = None
        self._dot_label = None
        self._thread = None
        self._is_running = False

        if self.enabled:
            self._thread = threading.Thread(target=self._run_ui, daemon=True)
            self._thread.start()

    def _apply_no_activate(self, hwnd):
        """Applique les flags Windows pour empêcher le vol de focus."""
        if sys.platform == 'win32':
            try:
                user32 = ctypes.windll.user32
                GWL_EXSTYLE = -20
                WS_EX_NOACTIVATE = 0x08000000
                WS_EX_TOOLWINDOW = 0x00000080
                WS_EX_TOPMOST = 0x00000008
                parent = user32.GetParent(hwnd) or hwnd
                style = user32.GetWindowLongW(parent, GWL_EXSTYLE)
                user32.SetWindowLongW(parent, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST)
            except Exception:
                pass

    def _run_ui(self):
        """Boucle Tkinter exécutée dans un thread d'arrière-plan."""
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes('-topmost', True)
        self._root.attributes('-alpha', 0.95)
        self._root.configure(bg='#090511')

        # Micro-cadre carré minimaliste avec bordure réactive
        self._container = tk.Frame(self._root, bg='#130C22', highlightbackground='#FF3B30', highlightthickness=2)
        self._container.pack(fill='both', expand=True)

        # Indicateur lumineux unique (Point Rouge / Point Jaune)
        self._dot_label = tk.Label(self._container, text="●", font=("Segoe UI", 15), fg="#FF3B30", bg='#130C22')
        self._dot_label.pack(expand=True)

        # Position compacte 36x36 centrée en bas de l'écran
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        w, h = 36, 36
        x = (sw - w) // 2
        y = sh - 110
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        self._apply_no_activate(self._root.winfo_id())
        self._root.withdraw()

        self._is_running = True
        self._root.after(40, self._check_queue)
        try:
            self._root.mainloop()
        except Exception:
            pass

    def _check_queue(self):
        """Dépile les actions envoyées depuis le thread principal."""
        try:
            while not self._cmd_queue.empty():
                cmd, args = self._cmd_queue.get_nowait()
                if cmd == 'show_recording':
                    # 🔴 Point ROUGE : Enregistrement micro actif
                    self._container.config(highlightbackground='#FF3B30')
                    self._dot_label.config(text="●", fg="#FF3B30")
                    self._root.deiconify()
                elif cmd == 'show_processing':
                    # 🟡 Point JAUNE : Transcription IA en cours
                    self._container.config(highlightbackground='#FFD700')
                    self._dot_label.config(text="●", fg="#FFD700")
                    self._root.deiconify()
                elif cmd == 'hide':
                    self._root.withdraw()
        except Exception:
            pass

        if self._is_running and self._root:
            self._root.after(50, self._check_queue)

    def show_recording(self):
        """Active l'état d'enregistrement (Rouge)."""
        if self.enabled:
            self._cmd_queue.put(('show_recording', None))

    def show_processing(self):
        """Active l'état de traitement IA (Jaune)."""
        if self.enabled:
            self._cmd_queue.put(('show_processing', None))

    def hide(self):
        """Masque le badge."""
        if self.enabled:
            self._cmd_queue.put(('hide', None))
