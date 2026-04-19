from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ── Сурет ──────────────────────────────────────────────────────────

def format_keyboard_single() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 PDF",  callback_data="fmt:pdf"),
            InlineKeyboardButton(text="📝 DOCX", callback_data="fmt:docx"),
        ],
        [
            InlineKeyboardButton(text="🖼 JPG",  callback_data="fmt:jpg"),
            InlineKeyboardButton(text="🖼 PNG",  callback_data="fmt:png"),
        ],
        [InlineKeyboardButton(text="🔗 Сілтеме", callback_data="fmt:link")],
        [InlineKeyboardButton(text="❌ Бас тарту", callback_data="fmt:cancel")],
    ])


def format_keyboard_multi() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 PDF",  callback_data="mfmt:pdf"),
            InlineKeyboardButton(text="📝 DOCX", callback_data="mfmt:docx"),
        ],
        [InlineKeyboardButton(text="❌ Бас тарту", callback_data="mfmt:cancel")],
    ])


def done_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Дайын",     callback_data="collect:done"),
        InlineKeyboardButton(text="❌ Бас тарту", callback_data="collect:cancel"),
    ]])


# ── Видео ───────────────────────────────────────────────────────────

def video_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎵 MP3",         callback_data="vfmt:mp3"),
            InlineKeyboardButton(text="🎤 Дауысхат",    callback_data="vfmt:ogg"),
        ],
        [InlineKeyboardButton(text="⭕ Бейнехат",       callback_data="vfmt:vidnote")],
        [InlineKeyboardButton(text="🔗 Сілтеме",        callback_data="vfmt:link")],
        [InlineKeyboardButton(text="❌ Бас тарту",      callback_data="vfmt:cancel")],
    ])


# ── Дауысхат / Аудио ────────────────────────────────────────────────

def voice_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎵 MP3",         callback_data="voice:mp3"),
            InlineKeyboardButton(text="🎤 Дауысхат",    callback_data="voice:ogg"),
        ],
        [InlineKeyboardButton(text="✏️ Тег өңдеу",     callback_data="voice:edit")],
        [InlineKeyboardButton(text="❌ Бас тарту",      callback_data="voice:cancel")],
    ])


# ── Аудио редактор ──────────────────────────────────────────────────

def audio_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Атауы",          callback_data="aedit:title")],
        [InlineKeyboardButton(text="🏷 Орындаушы",      callback_data="aedit:artist")],
        [InlineKeyboardButton(text="🖼 Фон (обложка)",  callback_data="aedit:cover")],
        [InlineKeyboardButton(text="✅ Сақтау",         callback_data="aedit:save")],
        [InlineKeyboardButton(text="❌ Бас тарту",      callback_data="aedit:cancel")],
    ])


# ── Хостинг ─────────────────────────────────────────────────────────

def upload_host_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Catbox", callback_data="host:catbox")],
        [InlineKeyboardButton(text="❌ Бас тарту", callback_data="host:cancel")],
    ])