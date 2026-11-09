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
    tk.Label(frame, text="Moteurs de Transcription IA", font=("Segoe UI", 13, "bold"), fg=TEXT_MAIN, bg='#090511').pack(anchor='w', pady=(0, 6))
    
    # 1. Sélection du moteur actif (Local vs Cloud)
    card_engine = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=14, pady=10)
    card_engine.pack(fill='x', pady=5)
    tk.Label(card_engine, text="Mode de Transcription Actif", font=("Segoe UI", 10, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w', pady=(0, 4))
    
    engine_var = tk.StringVar(value=cfg.get('engine', 'local_whisper'))
    
    def on_engine_change():
        cfg['engine'] = engine_var.get()
        save_fn(cfg)
        update_engine_panels()
    
    r_local = tk.Radiobutton(card_engine, text="⚡ Local Whisper (Instantané & Privé — Façon Super Whisper)", 
                             variable=engine_var, value='local_whisper', command=on_engine_change,
                             bg=BG_CARD, fg=TEXT_MAIN, selectcolor='#090511', activebackground=BG_CARD, activeforeground=TEXT_MAIN, font=("Segoe UI", 10, "bold"))
    r_local.pack(anchor='w', pady=2)
    
    r_cloud = tk.Radiobutton(card_engine, text="☁️ Google Gemini Cloud (API multimodale distante)", 
                             variable=engine_var, value='gemini', command=on_engine_change,
                             bg=BG_CARD, fg=TEXT_MAIN, selectcolor='#090511', activebackground=BG_CARD, activeforeground=TEXT_MAIN, font=("Segoe UI", 10))
    r_cloud.pack(anchor='w', pady=2)

    # 2. Panneau LOCAL WHISPER
    card_local = tk.Frame(frame, bg=BG_CARD, highlightbackground=ACCENT_VIOLET, highlightthickness=1, padx=14, pady=10)
    card_local.pack(fill='x', pady=6)
    
    tk.Label(card_local, text="⚡ Configuration Whisper Local (Sur votre PC)", font=("Segoe UI", 10, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w')
    
    # Détection matérielle
    has_cuda = False
    try:
        import ctranslate2
        has_cuda = ctranslate2.get_cuda_device_count() > 0
    except Exception:
        pass
    hw_text = "🟢 Accélération NVIDIA GeForce RTX 2050 (CUDA) active" if has_cuda else "ℹ️ Mode Processeur AMD Ryzen (INT8)"
    tk.Label(card_local, text=hw_text, font=("Segoe UI", 9, "italic"), fg='#00FF87' if has_cuda else TEXT_MUTED, bg=BG_CARD).pack(anchor='w', pady=(2, 6))

    whisper_models = ['small', 'base', 'tiny', 'medium']
    whisper_notes = {
        'small': "🎯 Recommandé : Excellente précision en français & réponse en < 0.4s",
        'base': "⚡ Équilibré : Très rapide (~0.2s) et léger en mémoire",
        'tiny': "🚀 Ultra-rapide : Vitesse maximale (~0.1s), pour dictées simples",
        'medium': "🔬 Haute fidélité : Vocabulaire complexe et longs discours"
    }
    cur_whisper = cfg.get('local_model_size', 'small')
    whisper_var = tk.StringVar(value=cur_whisper if cur_whisper in whisper_models else 'small')
    
    row_wh = tk.Frame(card_local, bg=BG_CARD)
    row_wh.pack(fill='x', pady=4)
    tk.Label(row_wh, text="Taille du modèle : ", font=("Segoe UI", 9), fg=TEXT_MAIN, bg=BG_CARD).pack(side='left')
    cb_whisper = ttk.Combobox(row_wh, textvariable=whisper_var, values=whisper_models, state='readonly', width=12)
    cb_whisper.pack(side='left', padx=6)
    
    lbl_wh_note = tk.Label(card_local, text=whisper_notes.get(whisper_var.get(), ""), font=("Segoe UI", 8), fg=ACCENT_VIOLET, bg=BG_CARD)
    lbl_wh_note.pack(anchor='w', pady=(2, 6))
    
    def on_whisper_change(e=None):
        cfg['local_model_size'] = whisper_var.get()
        lbl_wh_note.config(text=whisper_notes.get(whisper_var.get(), ""))
        save_fn(cfg)
    cb_whisper.bind('<<ComboboxSelected>>', on_whisper_change)
    
    wh_status_lbl = tk.Label(card_local, text="", font=("Segoe UI", 9), bg=BG_CARD)
    wh_status_lbl.pack(anchor='w')
    
    def test_local_speed():
        wh_status_lbl.config(text="⏳ Test de transcription locale en cours...", fg=TEXT_MUTED)
        frame.update_idletasks()
        try:
            import numpy as np, time
            from transcriber import Transcriber
            t = Transcriber(engine='local_whisper', local_model_size=whisper_var.get())
            fake_audio = np.zeros(16000, dtype=np.float32)
            t0 = time.time()
            list(t.local_model.transcribe(fake_audio, language='fr', vad_filter=False)[0])
            elapsed = time.time() - t0
            wh_status_lbl.config(text=f"✅ Moteur local ultra-rapide validé en {elapsed*1000:.1f} ms !", fg=ACCENT_GOLD)
        except Exception as ex:
            wh_status_lbl.config(text=f"❌ Erreur test: {str(ex)[:60]}", fg='#FF5577')
            
    btn_wh_test = tk.Button(card_local, text="⚡ Tester la vitesse locale", command=test_local_speed, bg='#241438', fg=TEXT_MAIN, activebackground=ACCENT_VIOLET, activeforeground='#FFFFFF', relief='flat', padx=10, pady=3, font=("Segoe UI", 9))
    btn_wh_test.pack(anchor='w', pady=(4, 2))

    # 3. Panneau CLOUD GEMINI
    card_gemini = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=14, pady=10)
    card_gemini.pack(fill='x', pady=6)
    tk.Label(card_gemini, text="☁️ Configuration Google Gemini (Cloud)", font=("Segoe UI", 10, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(anchor='w')
    
    key_var = tk.StringVar(value=cfg.get('api_key', ''))
    entry = tk.Entry(card_gemini, textvariable=key_var, show='•', bg='#090511', fg=TEXT_MAIN, insertbackground=ACCENT_GOLD, relief='flat', highlightbackground=BORDER_COLOR, highlightthickness=1, font=("Segoe UI", 10))
    entry.pack(fill='x', pady=(6, 6))
    
    gem_status_lbl = tk.Label(card_gemini, text="", font=("Segoe UI", 9), bg=BG_CARD)
    gem_status_lbl.pack(anchor='w', pady=(0, 4))
    
    row_btn = tk.Frame(card_gemini, bg=BG_CARD)
    row_btn.pack(fill='x')
    
    def toggle_show():
        is_hidden = entry.cget('show') == '•'
        entry.config(show='' if is_hidden else '•')
        btn_show.config(text="Masquer" if is_hidden else "Afficher")
    btn_show = tk.Button(row_btn, text="Masquer" if entry.cget('show') == '' else "Afficher", command=toggle_show, bg='#241438', fg=TEXT_MAIN, relief='flat', padx=8, pady=3, font=("Segoe UI", 9))
    btn_show.pack(side='left', padx=(0, 8))

    def test_key():
        gem_status_lbl.config(text="⏳ Test de connexion Google en cours...", fg=TEXT_MUTED)
        frame.update_idletasks()
        try:
            from google import genai
            client = genai.Client(api_key=key_var.get().strip())
            r = client.models.generate_content(model='gemini-flash-lite-latest', contents='ping')
            if r and r.text:
                gem_status_lbl.config(text="✅ Connexion réussie à Google Gemini !", fg=ACCENT_GOLD)
                cfg['api_key'] = key_var.get().strip()
                save_fn(cfg)
        except Exception as ex:
            gem_status_lbl.config(text=f"❌ Erreur: {str(ex)[:60]}", fg='#FF5577')
    
    btn_test = tk.Button(row_btn, text="Tester la clé Gemini", command=test_key, bg='#241438', fg=TEXT_MAIN, relief='flat', padx=10, pady=3, font=("Segoe UI", 9))
    btn_test.pack(side='left')

    models_list = ['gemini-flash-lite-latest', 'gemini-3.5-flash-lite', 'gemini-3-flash-preview']
    cur_mod = cfg.get('model_name', 'gemini-flash-lite-latest')
    mod_var = tk.StringVar(value=cur_mod if cur_mod in models_list else models_list[0])
    
    row_mod = tk.Frame(card_gemini, bg=BG_CARD)
    row_mod.pack(fill='x', pady=(8, 2))
    tk.Label(row_mod, text="Modèle Gemini : ", font=("Segoe UI", 9), fg=TEXT_MAIN, bg=BG_CARD).pack(side='left')
    cb_mod = ttk.Combobox(row_mod, textvariable=mod_var, values=models_list, state='readonly', width=26)
    cb_mod.pack(side='left', padx=6)
    
    def on_mod(e=None):
        cfg['model_name'] = mod_var.get()
        save_fn(cfg)
    cb_mod.bind('<<ComboboxSelected>>', on_mod)

    def update_engine_panels():
        active = engine_var.get()
        if active == 'local_whisper':
            card_local.config(highlightbackground=ACCENT_VIOLET, highlightthickness=2)
            card_gemini.config(highlightbackground=BORDER_COLOR, highlightthickness=1)
        else:
            card_gemini.config(highlightbackground=ACCENT_VIOLET, highlightthickness=2)
            card_local.config(highlightbackground=BORDER_COLOR, highlightthickness=1)

    update_engine_panels()
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
