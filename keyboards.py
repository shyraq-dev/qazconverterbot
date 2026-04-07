from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def format_keyboard_single() -> InlineKeyboardMarkup:
    """Бір сурет үшін — барлық форматтар."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 PDF",  callback_data="fmt:pdf"),
            InlineKeyboardButton(text="📝 DOCX", callback_data="fmt:docx"),
        ],
        [
            InlineKeyboardButton(text="🖼 JPG",  callback_data="fmt:jpg"),
            InlineKeyboardButton(text="🖼 PNG",  callback_data="fmt:png"),
        ],
        [
            InlineKeyboardButton(text="❌ Бас тарту", callback_data="fmt:cancel"),
        ],
    ])


def format_keyboard_multi() -> InlineKeyboardMarkup:
    """Көп сурет үшін — тек PDF / DOCX."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 PDF",  callback_data="mfmt:pdf"),
            InlineKeyboardButton(text="📝 DOCX", callback_data="mfmt:docx"),
        ],
        [
            InlineKeyboardButton(text="❌ Бас тарту", callback_data="mfmt:cancel"),
        ],
    ])


def done_keyboard() -> InlineKeyboardMarkup:
    """Суреттерді жинау кезіндегі Done / Бас тарту."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Дайын",       callback_data="collect:done"),
            InlineKeyboardButton(text="❌ Бас тарту",   callback_data="collect:cancel"),
        ],
    ])
