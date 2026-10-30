"""
Module d'injection de texte pour Phoenix Voice.
Copie le texte transcrit dans le presse-papier et injecte via Ctrl+V instantané.
"""
import time
import pyperclip
import keyboard

def inject_text(text):
    """
    Copie le texte dans le presse-papier et le colle via Ctrl+V
    dans l'application active où se trouve le curseur.
    """
    if not text:
        return False

    try:
        # 1. Copie dans le presse-papier Windows
        pyperclip.copy(text)

        # 2. Micro-pause ultra-courte (10 ms) pour validation presse-papier par l'OS
        time.sleep(0.01)

        # 3. Injection instantanée sans délai artificiel (< 5 ms)
        keyboard.send('ctrl+v')
        return True

    except Exception:
        try:
            import pyautogui
            pyautogui.PAUSE = 0.01  # Élimine la pause de sécurité par défaut de 100 ms
            pyautogui.hotkey('ctrl', 'v')
            return True
        except Exception as e:
            print(f"⚠️ [Injector] Erreur collage: {e}")
            return False
