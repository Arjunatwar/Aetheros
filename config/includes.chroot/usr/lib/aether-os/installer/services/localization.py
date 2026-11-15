#!/usr/bin/env python3
"""
AETHER OS Installer — Localization Service
Multi-language translation table and locale selection.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

AVAILABLE_LANGUAGES: List[Tuple[str, str]] = [
    ("en_US", "English (United States)"),
    ("en_GB", "English (United Kingdom)"),
    ("es_ES", "Español (Spanish)"),
    ("fr_FR", "Français (French)"),
    ("de_DE", "Deutsch (German)"),
    ("hi_IN", "हिन्दी (Hindi)"),
    ("ja_JP", "日本語 (Japanese)"),
]

# Basic translation dictionary for installer UI strings
STRINGS: Dict[str, Dict[str, str]] = {
    "welcome_title": {
        "en_US": "Welcome to AETHER OS",
        "en_GB": "Welcome to AETHER OS",
        "es_ES": "Bienvenido a AETHER OS",
        "fr_FR": "Bienvenue sur AETHER OS",
        "de_DE": "Willkommen bei AETHER OS",
        "hi_IN": "AETHER OS में आपका स्वागत है",
        "ja_JP": "AETHER OS へようこそ",
    },
    "tagline": {
        "en_US": "One System. Every Workflow.",
        "en_GB": "One System. Every Workflow.",
        "es_ES": "Un sistema. Todos los flujos de trabajo.",
        "fr_FR": "Un seul système. Tous vos flux de travail.",
        "de_DE": "Ein System. Jeder Arbeitsablauf.",
        "hi_IN": "एक ऑपरेटिंग सिस्टम। हर वर्कफ़्लो।",
        "ja_JP": "ひとつのシステム。すべてのワークフロー。",
    },
    "start_installation": {
        "en_US": "Start Installation",
        "en_GB": "Start Installation",
        "es_ES": "Comenzar Instalación",
        "fr_FR": "Démarrer l'installation",
        "de_DE": "Installation starten",
        "hi_IN": "इंस्टॉलेशन शुरू करें",
        "ja_JP": "インストールを開始",
    },
    "next": {
        "en_US": "Next",
        "en_GB": "Next",
        "es_ES": "Siguiente",
        "fr_FR": "Suivant",
        "de_DE": "Weiter",
        "hi_IN": "आगे बढ़ें",
        "ja_JP": "次へ",
    },
    "back": {
        "en_US": "Back",
        "en_GB": "Back",
        "es_ES": "Atrás",
        "fr_FR": "Retour",
        "de_DE": "Zurück",
        "hi_IN": "पीछे जाएं",
        "ja_JP": "戻る",
    },
    "restart_now": {
        "en_US": "Restart Now",
        "en_GB": "Restart Now",
        "es_ES": "Reiniciar Ahora",
        "fr_FR": "Redémarrer maintenant",
        "de_DE": "Jetzt neu starten",
        "hi_IN": "अभी रीस्टार्ट करें",
        "ja_JP": "今すぐ再起動",
    },
}

_current_locale = "en_US"


def set_locale(locale_code: str) -> None:
    """Sets active locale code."""
    global _current_locale
    if any(code == locale_code for code, _ in AVAILABLE_LANGUAGES):
        _current_locale = locale_code
    else:
        _current_locale = "en_US"


def get_locale() -> str:
    """Returns active locale code."""
    return _current_locale


def translate(key: str, default: str = "") -> str:
    """Translates key to current locale or returns default/key."""
    translations = STRINGS.get(key)
    if translations:
        return translations.get(_current_locale, translations.get("en_US", default or key))
    return default or key


def _(key: str) -> str:
    """Shorthand translation helper."""
    return translate(key)
