"""
Composants et onglets pour le Tableau de bord Sodio (Sonic-Audio).
Design Darkspine Sonic (Violet Électrique & Anneaux d'Or) pour Melvin.
"""
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
LEXIQUE_PATH = os.path.join(BASE_DIR, 'config', 'lexique.json')
HISTORY_PATH = os.path.join(BASE_DIR, 'history', 'history.json')

BG_CARD, BORDER_COLOR = '#130C22', '#2E1A47'
TEXT_MAIN, TEXT_MUTED = '#FFFFFF', '#A39BB0'
ACCENT_VIOLET = '#9D4EDD'
ACCENT_VIOLET_HOVER = '#7B2CBF'
ACCENT_GOLD = '#FFD700'
ACCENT_GOLD_HOVER = '#FFB703'

def build_general_tab(parent, cfg, save_fn):
    frame = tk.Frame(parent, bg='#090511', padx=20, pady=15)
    tk.Label(frame, text="Paramètres Généraux & Matériel Audio", font=("Segoe UI", 13, "bold"), fg=TEXT_MAIN, bg='#090511').pack(anchor='w', pady=(0, 10))
    
    # 1. Microphone
    c_mic = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=10)
    c_mic.pack(fill='x', pady=5)
    tk.Label(c_mic, text="🎙️ Microphone d'enregistrement", font=("Segoe UI", 10, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w')
    mics = []
    try:
        for idx, d in enumerate(sd.query_devices()):
            if d.get('max_input_channels', 0) > 0:
                mics.append(f"[{idx}] {d.get('name', f'Micro {idx}')[:32]}")
    except Exception:
        mics = ["[1] Microphone"]
    cur_mic = cfg.get('microphone_index', 1)
    mic_var = tk.StringVar(value=next((m for m in mics if m.startswith(f"[{cur_mic}]")), mics[0] if mics else ""))
    cb_mic = ttk.Combobox(c_mic, textvariable=mic_var, values=mics, state='readonly', width=45)
    cb_mic.pack(anchor='w', pady=(5, 2))
    def on_mic(e=None):
        val = mic_var.get()
        if val.startswith('['):
            cfg['microphone_index'] = int(val.split(']')[0][1:])
            save_fn(cfg)
    cb_mic.bind('<<ComboboxSelected>>', on_mic)

    # 2. Raccourci
    c_hk = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=10)
    c_hk.pack(fill='x', pady=5)
    tk.Label(c_hk, text="⌨️ Raccourci Clavier Global (Sonic Toggle)", font=("Segoe UI", 10, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w')
    hk_var = tk.StringVar(value=cfg.get('hotkey', 'f4').upper())
    cb_hk = ttk.Combobox(c_hk, textvariable=hk_var, values=['F4', 'F6', 'F8', 'F9', 'CTRL+SPACE', 'CTRL+SHIFT+SPACE'], state='readonly', width=20)
    cb_hk.pack(anchor='w', pady=(5, 2))
    def on_hk(e=None):
        cfg['hotkey'] = hk_var.get().lower()
        save_fn(cfg)
    cb_hk.bind('<<ComboboxSelected>>', on_hk)

    # 3. Toggles Retour Sonore et HUD
    c_opts = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=10)
    c_opts.pack(fill='x', pady=5)
    snd_var = tk.BooleanVar(value=cfg.get('audio_feedback', False))
    hud_var = tk.BooleanVar(value=cfg.get('floating_hud', True))
    def on_snd():
        cfg['audio_feedback'] = snd_var.get()
        save_fn(cfg)
    def on_hud():
        cfg['floating_hud'] = hud_var.get()
        save_fn(cfg)
    tk.Checkbutton(c_opts, text="Bip sonore au démarrage et à l'arrêt (Désactivé)", variable=snd_var, command=on_snd,
                   bg=BG_CARD, fg=TEXT_MAIN, selectcolor='#090511', activebackground=BG_CARD, activeforeground=TEXT_MAIN).pack(anchor='w', pady=2)
    tk.Checkbutton(c_opts, text="Mini-Badge visuel discret (🔴 Rouge = Écoute / 🟡 Jaune = Transcription)", variable=hud_var, command=on_hud,
                   bg=BG_CARD, fg=TEXT_MAIN, selectcolor='#090511', activebackground=BG_CARD, activeforeground=TEXT_MAIN).pack(anchor='w', pady=2)
    return frame

def build_keys_tab(parent, cfg, save_fn):
    frame = tk.Frame(parent, bg='#090511', padx=20, pady=15)
    tk.Label(frame, text="Moteurs IA & Clé API Google Gemini", font=("Segoe UI", 13, "bold"), fg=TEXT_MAIN, bg='#090511').pack(anchor='w', pady=(0, 10))
    
    card = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=14, pady=12)
    card.pack(fill='x', pady=5)
    tk.Label(card, text="Clé API Gemini Personnelle (Google AI Studio)", font=("Segoe UI", 10, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w')
    key_var = tk.StringVar(value=cfg.get('api_key', ''))
    entry = tk.Entry(card, textvariable=key_var, show='•', bg='#090511', fg=TEXT_MAIN, insertbackground=ACCENT_GOLD, relief='flat', highlightbackground=BORDER_COLOR, highlightthickness=1, font=("Segoe UI", 10))
    entry.pack(fill='x', pady=(6, 8))
    
    status_lbl = tk.Label(card, text="", font=("Segoe UI", 9), bg=BG_CARD)
    status_lbl.pack(anchor='w', pady=(0, 6))
    row_btn = tk.Frame(card, bg=BG_CARD)
    row_btn.pack(fill='x')
    
    def toggle_show():
        is_hidden = entry.cget('show') == '•'
        entry.config(show='' if is_hidden else '•')
        btn_show.config(text="Masquer" if is_hidden else "Afficher")
    btn_show = tk.Button(row_btn, text="Masquer" if entry.cget('show') == '' else "Afficher", command=toggle_show, bg='#241438', fg=TEXT_MAIN, relief='flat', padx=8, pady=3, font=("Segoe UI", 9))
    btn_show.pack(side='left', padx=(0, 8))

    def test_key():
        status_lbl.config(text="⏳ Test de connexion en cours...", fg=TEXT_MUTED)
        frame.update_idletasks()
        try:
            from google import genai
            client = genai.Client(api_key=key_var.get().strip())
            r = client.models.generate_content(model='gemini-flash-lite-latest', contents='ping')
            if r and r.text:
                status_lbl.config(text="✅ Connexion réussie à Google Gemini !", fg=ACCENT_GOLD)
                cfg['api_key'] = key_var.get().strip()
                save_fn(cfg)
        except Exception as ex:
            status_lbl.config(text=f"❌ Erreur: {str(ex)[:60]}", fg='#FF5577')
    
    btn_test = tk.Button(row_btn, text="⚡ Tester la connexion", command=test_key, bg=ACCENT_VIOLET, fg='#FFFFFF', activebackground=ACCENT_GOLD, activeforeground='#000000', relief='flat', padx=12, pady=3, font=("Segoe UI", 9, "bold"))
    btn_test.pack(side='left')

    # Modèle IA
    c_m = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=14, pady=10)
    c_m.pack(fill='x', pady=8)
    tk.Label(c_m, text="Moteur IA par défaut (Transcription)", font=("Segoe UI", 10, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w')
    models_list = [
        'gemini-flash-lite-latest',
        'gemini-3.5-flash-lite',
        'gemini-3-flash-preview'
    ]
    model_notes = {
        'gemini-flash-lite-latest': "⚡ Recommandé : Production stable mondiale & latence < 1s",
        'gemini-3.5-flash-lite': "🚀 Vitesse max : N°1 Artificial Analysis (224 tok/s)",
        'gemini-3-flash-preview': "🔬 Expérimental : Dernière génération Gemini 3"
    }
    cur_mod = cfg.get('model_name', 'gemini-flash-lite-latest')
    mod_var = tk.StringVar(value=cur_mod if cur_mod in models_list else models_list[0])
    cb_mod = ttk.Combobox(c_m, textvariable=mod_var, values=models_list, state='readonly', width=32)
    cb_mod.pack(anchor='w', pady=(5, 3))
    note_lbl = tk.Label(c_m, text=model_notes.get(mod_var.get(), ""), font=("Segoe UI", 8), fg=ACCENT_VIOLET, bg=BG_CARD)
    note_lbl.pack(anchor='w')
    def on_mod(e=None):
        cfg['model_name'] = mod_var.get()
        note_lbl.config(text=model_notes.get(mod_var.get(), ""))
        save_fn(cfg)
    cb_mod.bind('<<ComboboxSelected>>', on_mod)
    return frame

def build_lexique_tab(parent):
    frame = tk.Frame(parent, bg='#090511', padx=20, pady=15)
    tk.Label(frame, text="Lexique Personnel de Melvin — Sodio", font=("Segoe UI", 13, "bold"), fg=TEXT_MAIN, bg='#090511').pack(anchor='w', pady=(0, 2))
    tk.Label(frame, text="Mots magiques, noms de projets et termes reconnus à la perfection.", font=("Segoe UI", 9), fg=TEXT_MUTED, bg='#090511').pack(anchor='w', pady=(0, 8))

    card = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=10)
    card.pack(fill='both', expand=True)
    lb_frame = tk.Frame(card, bg=BG_CARD)
    lb_frame.pack(fill='both', expand=True, pady=(0, 6))
    sb = tk.Scrollbar(lb_frame)
    sb.pack(side='right', fill='y')
    listbox = tk.Listbox(lb_frame, bg='#090511', fg=TEXT_MAIN, selectbackground=ACCENT_VIOLET, relief='flat', yscrollcommand=sb.set, font=("Segoe UI", 10), height=7)
    listbox.pack(side='left', fill='both', expand=True)
    sb.config(command=listbox.yview)

    def load_words():
        listbox.delete(0, 'end')
        if os.path.exists(LEXIQUE_PATH):
            try:
                with open(LEXIQUE_PATH, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    mots = data.get('mots_cles_perso', []) or data.get('mots_cles_phoenix', [])
                    for w in sorted(mots):
                        listbox.insert('end', f"  {w}")
            except Exception: pass
    load_words()

    row_add = tk.Frame(card, bg=BG_CARD)
    row_add.pack(fill='x', pady=4)
    new_w = tk.StringVar()
    tk.Entry(row_add, textvariable=new_w, bg='#090511', fg=TEXT_MAIN, insertbackground=ACCENT_GOLD, relief='flat', highlightbackground=BORDER_COLOR, highlightthickness=1, font=("Segoe UI", 9), width=24).pack(side='left', padx=(0, 6))

    def add_word():
        w = new_w.get().strip()
        if w and os.path.exists(LEXIQUE_PATH):
            try:
                with open(LEXIQUE_PATH, 'r', encoding='utf-8-sig') as f: data = json.load(f)
                key = 'mots_cles_perso' if 'mots_cles_perso' in data else 'mots_cles_phoenix'
                mots = data.get(key, [])
                if w not in mots:
                    mots.append(w)
                    data[key] = mots
                    with open(LEXIQUE_PATH, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
                    new_w.set("")
                    load_words()
            except Exception as e: messagebox.showerror("Erreur", str(e))
    tk.Button(row_add, text="➕ Ajouter", command=add_word, bg=ACCENT_GOLD, fg='#000000', relief='flat', padx=10, font=("Segoe UI", 9, "bold")).pack(side='left')

    def del_word():
        sel = listbox.curselection()
        if sel and os.path.exists(LEXIQUE_PATH):
            w = listbox.get(sel[0]).strip()
            try:
                with open(LEXIQUE_PATH, 'r', encoding='utf-8-sig') as f: data = json.load(f)
                key = 'mots_cles_perso' if 'mots_cles_perso' in data else 'mots_cles_phoenix'
                data[key] = [x for x in data.get(key, []) if x != w]
                with open(LEXIQUE_PATH, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
                load_words()
            except Exception: pass
    tk.Button(card, text="🗑️ Supprimer le terme sélectionné", command=del_word, bg='#241438', fg='#FF7B90', relief='flat', padx=8, pady=3, font=("Segoe UI", 9)).pack(anchor='w', pady=(4, 0))
    return frame

def build_history_tab(parent, cfg=None):
    import gui_history
    return gui_history.build_history_tab(parent, cfg)

def build_legal_tab(parent):
    frame = tk.Frame(parent, bg='#090511', padx=20, pady=15)
    tk.Label(frame, text="Souveraineté & Données Privées — Sodio", font=("Segoe UI", 13, "bold"), fg=TEXT_MAIN, bg='#090511').pack(anchor='w', pady=(0, 6))
    card = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=14, pady=12)
    card.pack(fill='both', expand=True)

    legal_txt = (
        "🛡️ SOUVERAINETÉ & CONFIDENTIALITÉ ABSOLUE POUR MELVIN\n\n"
        "• Traitement In-Memory : Vos flux vocaux transitent exclusivement dans la RAM de votre PC.\n"
        "• Zéro Stockage Externe : Aucun audio n'est conservé sur des serveurs tiers.\n"
        "• Connexion Sécurisée Directe : Communication directe et chiffrée avec Google AI Studio.\n"
        "• Maîtrise Totale : Votre clé API personnelle, votre historique local et vos propres règles.\n"
    )
    t = tk.Text(card, bg='#090511', fg='#CBD5E1', font=("Segoe UI", 9), relief='flat', wrap='word', height=8)
    t.insert('end', legal_txt)
    t.config(state='disabled')
    t.pack(fill='both', expand=True, pady=(0, 8))
    tk.Label(card, text="✨ 100% Souverain, Personnel & Gratuit sur quota Gemini", font=("Segoe UI", 9, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w')
    return frame
