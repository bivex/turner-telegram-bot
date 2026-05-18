import json
import os
import logging

_TRANSLATIONS = {}
_DB_OVERRIDES = {}

SUPPORTED_LANGUAGES = {
    'ru': '🇷🇺 Русский',
    'en': '🇬🇧 English',
    'uk': '🇺🇦 Українська',
}
DEFAULT_LANG = 'ru'

def _load_translations():
    global _TRANSLATIONS
    locales_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locales')
    for lang in SUPPORTED_LANGUAGES:
        path = os.path.join(locales_dir, f'{lang}.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _TRANSLATIONS[lang] = json.load(f)
            logging.info(f"Loaded {len(_TRANSLATIONS[lang])} keys for '{lang}'")
        except FileNotFoundError:
            logging.warning(f"Translation file not found: {path}")
            _TRANSLATIONS[lang] = {}

_load_translations()

def refresh_db_overrides():
    global _DB_OVERRIDES
    try:
        import database
        _DB_OVERRIDES = database.get_bot_config()
    except Exception as e:
        logging.warning(f"Failed to load DB overrides: {e}")
        _DB_OVERRIDES = {}

def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    if key in _DB_OVERRIDES and _DB_OVERRIDES[key]:
        text = _DB_OVERRIDES[key]
    else:
        text = _TRANSLATIONS.get(lang, {}).get(key)
        if text is None:
            text = _TRANSLATIONS.get(DEFAULT_LANG, {}).get(key)
        if text is None:
            return f"[NO_TEXT: {key}]"
    if kwargs:
        try:
            text = text.format_map(kwargs)
        except (KeyError, IndexError):
            pass
    return text
