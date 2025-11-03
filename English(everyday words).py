#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vokabeltrainer: lädt 'vokabeln = {englisch: [deutsch, ...], ...}' aus URL oder Datei,
fragt gemischt EN->DE und DE->EN, ignoriert Groß-/Kleinschreibung, vergibt Punkte und Note.
Nach jeder Runde geht es zurück zum Anfang; Eingabe '0' beendet.

Aufruf:
  python3 vokabeltrainer.py                # lädt Standard-URL
  python3 vokabeltrainer.py vokabeln.txt   # lädt lokale Datei

Kompatibel mit Python 3.8+ inkl. 3.14.
"""

from __future__ import annotations
import os
import re
import sys
import ssl
import random
from typing import Dict, List, Tuple, Set
from urllib.request import urlopen, Request
from urllib.error import URLError

DEFAULT_URL = "https://raw.githubusercontent.com/theguy16/python-lernprogramme/refs/heads/main/vokabeln.txt"

# ---------- Laden ----------

def _urlopen_with_cert(url: str):
    # Nutzt certifi, wenn verfügbar, sonst Standards.
    try:
        import certifi  # type: ignore
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
    headers = {"User-Agent": "vokabeltrainer/1.0"}
    return urlopen(Request(url, headers=headers), context=ctx, timeout=20)

def _read_text_from_src(src: str) -> str:
    if src.startswith(("http://", "https://")):
        try:
            with _urlopen_with_cert(src) as f:
                return f.read().decode("utf-8")
        except Exception as e:
            # macOS-Standard-Python benötigt ggf. Zertifikate
            raise RuntimeError(
                "Download fehlgeschlagen. Falls macOS: /Applications/Python 3.14/Install Certificates.command ausführen oder lokale Datei verwenden."
            ) from e
    # Datei
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    with open(src, "r", encoding="utf-8") as f:
        return f.read()

def load_vocab(src: str) -> Dict[str, List[str]]:
    """
    Erwartet Python-Quelltext, der eine Variable 'vokabeln' setzt.
    Werte dürfen String oder Liste von Strings sein.
    """
    text = _read_text_from_src(src)
    ns: Dict[str, object] = {}
    exec(text, {}, ns)
    if "vokabeln" not in ns or not isinstance(ns["vokabeln"], dict):
        raise ValueError("Quelle enthält kein 'vokabeln'-Dict")
    raw: dict = ns["vokabeln"]

    # Normalisieren: nur {str: List[str]}
    cleaned: Dict[str, List[str]] = {}
    for en, de_vals in raw.items():
        if not isinstance(en, str):
            continue
        if isinstance(de_vals, str):
            vals = [de_vals]
        elif isinstance(de_vals, (list, tuple)):
            vals = [x for x in de_vals if isinstance(x, str)]
        else:
            continue
        vals = [v for v in (s.strip() for s in vals) if v]
        if not vals:
            continue
        cleaned[en.strip()] = vals
    if not cleaned:
        raise ValueError("Die Liste enthält keine nutzbaren Einträge")
    return cleaned

# ---------- Logik ----------

_PUNCT_STRIP = str.maketrans({c: "" for c in "\"'`´‘’‚“”„"})

def norm(s: str) -> str:
    # Ignoriert Groß-/Kleinschreibung, führenden/trailing Leerraum und einfache Anführungszeichen
    s = s.strip().casefold().translate(_PUNCT_STRIP)
    s = re.sub(r"\s+", " ", s)
    return s

def build_reverse(vok: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """
    Mappe deutsch->Menge englischer Übersetzungen.
    Wenn ein deutsches Wort mehrfach vorkommt, werden alle EN-Varianten akzeptiert.
    """
    rev: Dict[str, Set[str]] = {}
    for en, de_list in vok.items():
        for de in de_list:
            rev.setdefault(norm(de), set()).add(en)
    return rev

def grade_from_percent(pct: float) -> int:
    # Deutsche Notenskala
    if pct >= 95: return 1
    if pct >= 80: return 2
    if pct >= 65: return 3
    if pct >= 50: return 4
    if pct >= 30: return 5
    return 6

def ask(
    vok: Dict[str, List[str]],
    rev: Dict[str, Set[str]],
    mode: int,
    n_questions: int,
) -> Tuple[int, int]:
    """
    mode: 1 EN->DE, 2 DE->EN, 3 gemischt
    n_questions: Anzahl Fragen, mit Zurücklegen wenn größer als Items
    """
    en_items = list(vok.items())
    total = 0
    correct = 0

    def q_en_to_de(en: str, de_list: List[str]) -> bool:
        user = input(f"{en}  -> deutsch: ")
        if not user.strip():
            print(f"falsch | richtig: {', '.join(de_list)}")
            return False
        if norm(user) in {norm(x) for x in de_list}:
            print("richtig")
            return True
        print(f"falsch | richtig: {', '.join(de_list)}")
        return False

    def q_de_to_en(en: str, de_list: List[str]) -> bool:
        de = random.choice(de_list)
        user = input(f"{de}  -> englisch: ")
        if not user.strip():
            valid = sorted(rev.get(norm(de), {en}))
            print(f"falsch | richtig: {', '.join(valid)}")
            return False
        if norm(user) in {norm(x) for x in rev.get(norm(de), {en})}:
            print("richtig")
            return True
        valid = sorted(rev.get(norm(de), {en}))
        print(f"falsch | richtig: {', '.join(valid)}")
        return False

    for _ in range(n_questions):
        en, de_list = random.choice(en_items)
        direction = (
            1 if mode == 1 else
            2 if mode == 2 else
            (1 if random.random() < 0.5 else 2)
        )
        total += 1
        ok = q_en_to_de(en, de_list) if direction == 1 else q_de_to_en(en, de_list)
        if ok:
            correct += 1

    return correct, total

# ---------- UI ----------

def read_int(prompt: str, default: int, valid: Set[int] | None = None) -> int:
    s = input(prompt).strip()
    if not s:
        return default
    try:
        v = int(s)
    except ValueError:
        return default
    if valid is not None and v not in valid:
        return default
    return max(0, v)

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    try:
        vok = load_vocab(src)
    except Exception as e:
        # Fallback: lokale "vokabeln.txt", wenn vorhanden
        local = "vokabeln.txt"
        if src.startswith(("http://", "https://")) and os.path.exists(local):
            try:
                vok = load_vocab(local)
                print("Online-Quelle fehlgeschlagen, lokale Datei geladen.")
            except Exception:
                raise
        else:
            raise

    rev = build_reverse(vok)
    print(f"{len(vok)} Einträge geladen.\n")

    while True:
        print("Modus: 1=Englisch→Deutsch, 2=Deutsch→Englisch, 3=Gemischt")
        mode = read_int("Wähle Modus (1/2/3, 0=Ende): ", default=3, valid={0, 1, 2, 3})
        if mode == 0:
            print("Beendet.")
            return

        n = read_int("Anzahl Fragen (leer=20, 0=Ende): ", default=20)
        if n == 0:
            print("Beendet.")
            return

        correct, total = ask(vok, rev, mode, n)

        pct = (correct / total * 100.0) if total else 0.0
        note = grade_from_percent(pct)
        print("\nErgebnis:")
        print(f"richtig: {correct}/{total} ({pct:.1f} %)")
        print(f"Note: {note}\n")
        # Danach automatisch zurück zum Anfang der Schleife

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBeendet.")
