"""
Composant d'Historique Interactif (24 Heures) pour Sodio (Sonic-Audio).
Permet d'inspecter, réécouter (Play/Stop) et retranscrire à la demande les enregistrements audio.
"""
import os
import threading
import tkinter as tk
from tkinter import messagebox
import pyperclip
from transcriber import Transcriber
from history_manager import load_history, play_audio, stop_audio, update_entry_text, BASE_DIR

BG_CARD = '#130C22'
BORDER_COLOR = '#2E1A47'
TEXT_MAIN = '#FFFFFF'
TEXT_MUTED = '#A39BB0'
ACCENT_GOLD = '#FFD700'
ACCENT_VIOLET = '#9D4EDD'
BG_MAIN = '#090511'
BTN_BG = '#241438'

def build_history_tab(parent, cfg=None):
    frame = tk.Frame(parent, bg=BG_MAIN, padx=18, pady=14)

    # En-tête
    header = tk.Frame(frame, bg=BG_MAIN)
    header.pack(fill='x', pady=(0, 10))
    tk.Label(header, text="Historique des Dictées & Audios (24h)",
             font=("Segoe UI", 13, "bold"), fg=TEXT_MAIN, bg=BG_MAIN).pack(side='left')

    btn_refresh = tk.Button(header, text="🔄 Actualiser", font=("Segoe UI", 8, "bold"),
                            bg=BTN_BG, fg=ACCENT_GOLD, activebackground='#351C52',
                            activeforeground='#FFFFFF', relief='flat', padx=8, pady=3,
                            cursor='hand2', command=lambda: refresh_list())
    btn_refresh.pack(side='right')

    # Conteneur scrollable avec Canvas
    canvas_container = tk.Frame(frame, bg=BG_MAIN)
    canvas_container.pack(fill='both', expand=True)

    canvas = tk.Canvas(canvas_container, bg=BG_MAIN, highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=BG_MAIN)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def _on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind("<Configure>", _on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Support de la molette souris
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    status_banner = tk.Label(frame, text="", font=("Segoe UI", 8, "bold"), bg=BG_MAIN, fg=ACCENT_GOLD)
    status_banner.pack(anchor='w', pady=(4, 0))

    def show_msg(msg, color=ACCENT_GOLD):
        status_banner.config(text=msg, fg=color)
        frame.after(4000, lambda: status_banner.config(text=""))

    def retranscribe_action(entry, txt_widget, card_btn_retranscribe):
        audio_rel = entry.get('audio_file')
        if not audio_rel:
            messagebox.showwarning("Audio manquant", "Aucun fichier audio associé à cette dictée.")
            return

        abs_audio_path = os.path.join(BASE_DIR, audio_rel)
        if not os.path.exists(abs_audio_path):
            messagebox.showerror("Fichier introuvable", f"Le fichier audio a expiré ou a été purgé : {audio_rel}")
            return

        card_btn_retranscribe.config(text="⏳ En cours...", state='disabled')
        show_msg("⏳ Retranscription avec Gemini en arrière-plan...", ACCENT_VIOLET)

        def _thread():
            try:
                with open(abs_audio_path, 'rb') as f:
                    wav_bytes = f.read()

                api_key = (cfg.get('api_key') if cfg else '') or ''
                model_name = (cfg.get('model_name') if cfg else '') or 'gemini-flash-lite-latest'

                t = Transcriber(api_key=api_key, model_name=model_name)
                new_text, latency = t.transcribe(wav_bytes, entry.get('duration_seconds', 0.0))

                if new_text:
                    update_entry_text(entry.get('id'), new_text, latency)
                    pyperclip.copy(new_text)

                    def _ui_update():
                        txt_widget.config(state='normal')
                        txt_widget.delete('1.0', 'end')
                        txt_widget.insert('end', new_text)
                        txt_widget.config(state='disabled')
                        card_btn_retranscribe.config(text="🔄 Retranscrire", state='normal')
                        show_msg(f"✅ Retranscrit en {latency:.2f}s et copié dans le presse-papier !")
                    frame.after(0, _ui_update)
                else:
                    def _ui_fail():
                        card_btn_retranscribe.config(text="🔄 Retranscrire", state='normal')
                        show_msg("⚠️ Échec : aucun texte retourné par Gemini.", '#FF5577')
                    frame.after(0, _ui_fail)
            except Exception as ex:
                def _ui_err():
                    card_btn_retranscribe.config(text="🔄 Retranscrire", state='normal')
                    show_msg(f"❌ Erreur: {str(ex)[:50]}", '#FF5577')
                frame.after(0, _ui_err)

        threading.Thread(target=_thread, daemon=True).start()

    def refresh_list():
        stop_audio()
        for w in scroll_frame.winfo_children():
            w.destroy()

        entries = load_history()
        if not entries:
            tk.Label(scroll_frame, text="Aucune dictée enregistrée pour le moment.",
                     font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_MAIN).pack(pady=40)
            return

        for entry in reversed(entries[-20:]):
            c = tk.Frame(scroll_frame, bg=BG_CARD, highlightbackground=BORDER_COLOR,
                         highlightthickness=1, padx=12, pady=10)
            c.pack(fill='x', expand=True, pady=4)

            # Ligne Info Meta
            ts = entry.get('timestamp', '')[:16].replace('T', ' ')
            dur = entry.get('duration_seconds', 0.0)
            lat = entry.get('latency_seconds', 0.0)
            mod = entry.get('model', 'gemini')

            top_meta = tk.Frame(c, bg=BG_CARD)
            top_meta.pack(fill='x', pady=(0, 4))
            tk.Label(top_meta, text=f"🕒 {ts}  •  ⏱️ {dur:.1f}s  •  ⚡ {lat:.2f}s  •  🤖 {mod}",
                     font=("Segoe UI", 8, "bold"), fg=ACCENT_GOLD, bg=BG_CARD).pack(side='left')

            # Zone de Texte
            txt_box = tk.Text(c, bg=BG_MAIN, fg=TEXT_MAIN, font=("Segoe UI", 9),
                              relief='flat', wrap='word', height=2, padx=6, pady=4)
            txt_box.insert('end', entry.get('text', ''))
            txt_box.config(state='disabled')
            txt_box.pack(fill='x', pady=(2, 6))

            # Barre d'actions
            actions = tk.Frame(c, bg=BG_CARD)
            actions.pack(fill='x')

            audio_rel = entry.get('audio_file')
            if audio_rel:
                tk.Button(actions, text="▶️ Écouter", font=("Segoe UI", 8, "bold"),
                          bg=BTN_BG, fg=ACCENT_GOLD, activebackground='#351C52',
                          relief='flat', padx=7, pady=2, cursor='hand2',
                          command=lambda f=audio_rel: play_audio(f)).pack(side='left', padx=(0, 4))

                tk.Button(actions, text="⏹️ Stop", font=("Segoe UI", 8),
                          bg=BTN_BG, fg=TEXT_MUTED, activebackground='#351C52',
                          relief='flat', padx=5, pady=2, cursor='hand2',
                          command=stop_audio).pack(side='left', padx=(0, 6))

                btn_re = tk.Button(actions, text="🔄 Retranscrire", font=("Segoe UI", 8, "bold"),
                                   bg=BTN_BG, fg=ACCENT_VIOLET, activebackground='#351C52',
                                   relief='flat', padx=7, pady=2, cursor='hand2')
                btn_re.config(command=lambda e=entry, tb=txt_box, b=btn_re: retranscribe_action(e, tb, b))
                btn_re.pack(side='left', padx=(0, 6))

            def _copy(text_to_copy=entry.get('text', '')):
                pyperclip.copy(text_to_copy)
                show_msg("📋 Texte copié dans le presse-papier !")

            tk.Button(actions, text="📋 Copier", font=("Segoe UI", 8),
                      bg=BTN_BG, fg=TEXT_MAIN, activebackground='#351C52',
                      relief='flat', padx=6, pady=2, cursor='hand2',
                      command=_copy).pack(side='right')

    refresh_list()
    return frame
