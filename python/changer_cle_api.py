"""
Module d'interface graphique pour configurer la clé API Google Gemini dans Sodio (Sonic-Audio).
Thème Darkspine Sonic (Violet Électrique & Anneaux d'Or).
"""
import os
import sys
import json
import webbrowser
import threading
import tkinter as tk
from tkinter import messagebox

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')

def load_current_key():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                return data.get('api_key', '')
        except Exception:
            pass
    return ''

def save_api_key(new_key):
    config_data = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                config_data = json.load(f)
        except Exception:
            pass

    config_data['api_key'] = new_key.strip()
    if 'model_name' not in config_data:
        config_data['model_name'] = 'gemini-flash-lite-latest'
    if 'hotkey' not in config_data:
        config_data['hotkey'] = 'f4'

    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

def test_gemini_key(key):
    """Teste rapidement la clé API avec un appel léger."""
    if not key or key.strip() in ['VOTRE_CLE_GEMINI_AI_STUDIO', '']:
        return False, "La clé ne peut pas être vide."
    try:
        from google import genai
        client = genai.Client(api_key=key.strip())
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents='ping'
        )
        if response and response.text:
            return True, "✅ Clé valide ! Connexion à Gemini Flash-Lite réussie."
        return False, "Réponse inattendue de Gemini."
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "400" in err_msg:
            return False, "❌ Clé invalide (vérifiez la clé sur Google AI Studio)."
        elif "PERMISSION_DENIED" in err_msg or "403" in err_msg:
            return False, "❌ Accès refusé (vérifiez vos autorisations)."
        return False, f"❌ Erreur: {err_msg[:80]}"

def show_api_dialog():
    root = tk.Tk()
    root.title("Sodio — Configuration Clé API Gemini")
    root.geometry("520x400")
    root.minsize(500, 380)
    root.configure(bg="#090511")

    # Centrage sur l'écran
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 520) // 2
    y = (root.winfo_screenheight() - 400) // 2
    root.geometry(f"+{x}+{y}")
    root.attributes('-topmost', True)

    current_key = load_current_key()

    header = tk.Frame(root, bg="#0E0919", padx=20, pady=15)
    header.pack(fill="x")

    title_lbl = tk.Label(
        header, text="⚡ Sodio (Sonic-Audio)",
        font=("Segoe UI", 14, "bold"), fg="#FFD700", bg="#0E0919"
    )
    title_lbl.pack(anchor="w")

    subtitle = tk.Label(
        header, text="Configuration de votre clé personnelle Google Gemini",
        font=("Segoe UI", 9), fg="#9D4EDD", bg="#0E0919"
    )
    subtitle.pack(anchor="w", pady=(2, 0))

    body = tk.Frame(root, bg="#090511", padx=20, pady=15)
    body.pack(fill="both", expand=True)

    info_txt = (
        "💡 Votre clé Gemini est stockée localement dans config.json.\n"
        "Elle utilise votre quota gratuit Google AI Studio pour transcrire\n"
        "vos paroles à la vitesse de l'éclair !"
    )
    info_lbl = tk.Label(
        body, text=info_txt, font=("Segoe UI", 9),
        fg="#A39BB0", bg="#090511", justify="left"
    )
    info_lbl.pack(anchor="w", pady=(0, 15))

    key_label = tk.Label(
        body, text="Clé API Google Gemini :",
        font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#090511"
    )
    key_label.pack(anchor="w", pady=(0, 5))

    entry_frame = tk.Frame(body, bg="#090511")
    entry_frame.pack(fill="x", pady=(0, 8))

    key_var = tk.StringVar(value=current_key)
    entry_key = tk.Entry(
        entry_frame, textvariable=key_var, show="*",
        font=("Consolas", 11), bg="#130C22", fg="#FFFFFF",
        insertbackground="#FFD700", relief="flat", highlightthickness=1,
        highlightbackground="#2E1A47", highlightcolor="#9D4EDD"
    )
    entry_key.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

    is_masked = [True]
    def toggle_mask():
        if is_masked[0]:
            entry_key.configure(show="")
            btn_eye.configure(text="🔒")
            is_masked[0] = False
        else:
            entry_key.configure(show="*")
            btn_eye.configure(text="👁️")
            is_masked[0] = True

    btn_eye = tk.Button(
        entry_frame, text="👁️", command=toggle_mask,
        font=("Segoe UI", 10), bg="#241438", fg="#FFFFFF",
        relief="flat", cursor="hand2", width=3, pady=3
    )
    btn_eye.pack(side="right")

    status_lbl = tk.Label(
        body, text="", font=("Segoe UI", 9),
        fg="#A39BB0", bg="#090511", justify="left"
    )
    status_lbl.pack(anchor="w", pady=(0, 10))

    actions_frame = tk.Frame(body, bg="#090511")
    actions_frame.pack(fill="x", pady=(0, 15))

    def on_test():
        key = key_var.get().strip()
        status_lbl.configure(text="⏳ Test de connexion en cours...", fg="#FFD700")
        root.update()

        def _do_test():
            ok, msg = test_gemini_key(key)
            color = "#FFD700" if ok else "#FF5577"
            status_lbl.configure(text=msg, fg=color)

        threading.Thread(target=_do_test, daemon=True).start()

    btn_test = tk.Button(
        actions_frame, text="🧪 Tester la Clé", command=on_test,
        font=("Segoe UI", 9, "bold"), bg="#241438", fg="#FFD700",
        relief="flat", cursor="hand2", padx=12, pady=6
    )
    btn_test.pack(side="left", padx=(0, 8))

    def on_get_key():
        webbrowser.open("https://aistudio.google.com/app/apikey")

    btn_link = tk.Button(
        actions_frame, text="Obtenir une clé gratuite ↗", command=on_get_key,
        font=("Segoe UI", 9), bg="#090511", fg="#9D4EDD",
        relief="flat", cursor="hand2", padx=6, pady=6, bd=0
    )
    btn_link.pack(side="left")

    footer = tk.Frame(root, bg="#0E0919", padx=20, pady=12)
    footer.pack(fill="x", side="bottom")

    def on_save():
        key = key_var.get().strip()
        if not key:
            if not messagebox.askyesno("Sodio", "Voulez-vous enregistrer une clé vide ?"):
                return
        save_api_key(key)
        messagebox.showinfo("Sodio", "✅ Clé API enregistrée avec succès !")
        root.destroy()

    def on_cancel():
        root.destroy()

    btn_cancel = tk.Button(
        footer, text="Annuler", command=on_cancel,
        font=("Segoe UI", 9), bg="#241438", fg="#A39BB0",
        relief="flat", cursor="hand2", padx=14, pady=6
    )
    btn_cancel.pack(side="right", padx=(8, 0))

    btn_save = tk.Button(
        footer, text="💾 Enregistrer", command=on_save,
        font=("Segoe UI", 9, "bold"), bg="#9D4EDD", fg="#FFFFFF",
        activebackground="#FFD700", activeforeground="#000000",
        relief="flat", cursor="hand2", padx=18, pady=6
    )
    btn_save.pack(side="right")

    root.mainloop()

if __name__ == "__main__":
    show_api_dialog()
