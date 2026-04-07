"""
handlers.py

Режимдер:
  1. Жалғыз сурет → waiting_format → файл
  2. Альбом → collecting_photos → ✅ Дайын → waiting_multi_format → файл
  3. Бірнеше альбом қатарынан → жинақталады →  ✅ Дайын → файл
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from states import ConvertState
from keyboards import format_keyboard_single, format_keyboard_multi, done_keyboard
from converter import convert_single, convert_multi, FORMAT_LABELS

router = Router()
logger = logging.getLogger(__name__)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif", "image/tiff"}

# media_group_id → asyncio.Task
_album_tasks: dict[str, asyncio.Task] = {}


# ══════════════════════════════════════════════
# Утилиталар
# ══════════════════════════════════════════════

def _default_filename() -> str:
    return "document_" + datetime.now().strftime("%Y%m%d_%H%M%S")


async def _download_photo(bot: Bot, photo) -> bytes:
    f = await bot.get_file(photo.file_id)
    buf = await bot.download_file(f.file_path)
    return buf.read()


async def _download_doc(bot: Bot, doc) -> bytes:
    f = await bot.get_file(doc.file_id)
    buf = await bot.download_file(f.file_path)
    return buf.read()


async def _send_result(message: Message, data: bytes, filename: str, fmt: str, count: int = 1):
    label = FORMAT_LABELS.get(fmt, fmt.upper())
    pages = f"{count} бет · " if count > 1 else ""
    await message.answer_document(
        BufferedInputFile(data, filename=filename),
        caption=f"✅ <b>{label}</b> дайын!\n<i>{pages}Сурет → Файл. Тез. Дәл.</i>",
        parse_mode="HTML",
    )


async def _update_counter(bot: Bot, chat_id: int, msg_id: int | None, count: int, message: Message) -> int:
    """Ескі санауышты жойып, жаңасын чаттың ТӨМЕНІНЕ жібереді."""
    text = f"📎 <b>{count}</b> сурет жиналды. Жалғастырыңыз немесе ✅ Дайынды басыңыз."
    if msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    sent = await message.answer(text, reply_markup=done_keyboard(), parse_mode="HTML")
    return sent.message_id


async def _add_to_collection(state: FSMContext, bot: Bot, message: Message, new_photos: list[bytes]):
    """Суреттерді collecting_photos-қа қосады. State жоқ болса жаңа сессия бастайды."""
    current = await state.get_state()
    sd = await state.get_data()

    if current == ConvertState.collecting_photos:
        existing: list[bytes] = sd.get("photos", [])
        existing.extend(new_photos)
        counter_msg_id: int | None = sd.get("counter_msg_id")
        await state.update_data(photos=existing)
    else:
        existing = list(new_photos)
        counter_msg_id = None
        await state.set_state(ConvertState.collecting_photos)
        await state.update_data(photos=existing, counter_msg_id=None)

    new_mid = await _update_counter(bot, message.chat.id, counter_msg_id, len(existing), message)
    await state.update_data(counter_msg_id=new_mid)


# ══════════════════════════════════════════════
# /start  /help
# ══════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Сәлем! Мен <b>QazConverter</b> — суретті тез файлға айналдыратын бот.\n\n"
        "📌 <b>Қолдану:</b>\n"
        "• Бір сурет жібер → формат таңда → файл ал\n"
        "• Альбом жібер → суреттер жинақталады → ✅ Дайын\n"
        "• Бірнеше альбомды қатарынан жібере бер — бәрі жинақталады\n\n"
        "<i>Сурет → Файл. Тез. Дәл.</i>",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>QazConverter көмегі</b>\n\n"
        "📥 <b>Кіріс форматтары:</b> JPG, PNG, WebP, BMP, GIF, TIFF\n\n"
        "📤 <b>Шығыс форматтары:</b>\n"
        "• <b>PDF</b> — A4, әр сурет жеке бет\n"
        "• <b>DOCX</b> — Word, әр сурет жеке бет\n"
        "• <b>JPG / PNG</b> — тек жалғыз сурет үшін\n\n"
        "📎 <b>Режимдер:</b>\n"
        "• Жалғыз сурет → 4 формат қолжетімді\n"
        "• Альбом → суреттер жинақталады → ✅ Дайын\n\n"
        "🏷 Файл аты автоматты түрде қойылады.",
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════
# Барлық F.photo — БІР handler
# ══════════════════════════════════════════════

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, state: FSMContext):
    media_group_id = message.media_group_id

    if media_group_id:
        # ── Альбом: буферге қосып, flush task бастаймыз ──
        data = await _download_photo(bot, message.photo[-1])

        sd = await state.get_data()
        album_buf: dict = sd.get("_album_buf", {})
        bucket: list = album_buf.get(media_group_id, [])
        bucket.append((data, message.message_id))
        album_buf[media_group_id] = bucket
        await state.update_data(_album_buf=album_buf)

        old_task = _album_tasks.pop(media_group_id, None)
        if old_task:
            old_task.cancel()

        async def flush_album(mgid: str, msg: Message, st: FSMContext, bt: Bot):
            await asyncio.sleep(1.5)
            _album_tasks.pop(mgid, None)

            sd2 = await st.get_data()
            album_buf2: dict = sd2.get("_album_buf", {})
            bucket2: list = album_buf2.pop(mgid, [])
            await st.update_data(_album_buf=album_buf2)

            new_photos = [d for d, _ in sorted(bucket2, key=lambda x: x[1])]
            if not new_photos:
                return

            await _add_to_collection(st, bt, msg, new_photos)

        _album_tasks[media_group_id] = asyncio.create_task(
            flush_album(media_group_id, message, state, bot)
        )

    else:
        # ── Жалғыз сурет ──
        current = await state.get_state()
        data = await _download_photo(bot, message.photo[-1])

        if current == ConvertState.collecting_photos:
            # Collecting режимінде болса — жинаққа қосамыз
            await _add_to_collection(state, bot, message, [data])
        else:
            await state.update_data(image_bytes=data)
            await state.set_state(ConvertState.waiting_format)
            await message.answer(
                "✅ Сурет қабылданды! Қандай форматқа түрлендірейін?",
                reply_markup=format_keyboard_single(),
            )


# ══════════════════════════════════════════════
# Document handler
# ══════════════════════════════════════════════

@router.message(F.document)
async def handle_document(message: Message, bot: Bot, state: FSMContext):
    doc = message.document
    if doc.mime_type not in ALLOWED_MIME:
        await message.answer("❌ Тек сурет файлдарын жіберіңіз (JPG, PNG, WebP, BMP, GIF, TIFF).")
        return

    data = await _download_doc(bot, doc)
    current = await state.get_state()

    if current == ConvertState.collecting_photos:
        await _add_to_collection(state, bot, message, [data])
    else:
        await state.update_data(image_bytes=data)
        await state.set_state(ConvertState.waiting_format)
        await message.answer(
            "✅ Сурет қабылданды! Қандай форматқа түрлендірейін?",
            reply_markup=format_keyboard_single(),
        )


# ══════════════════════════════════════════════
# Collecting → Done / Cancel
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.collecting_photos, F.data.startswith("collect:"))
async def collecting_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        await callback.answer()
        return

    sd = await state.get_data()
    photos: list[bytes] = sd.get("photos", [])

    if not photos:
        await callback.answer("⚠️ Әлі сурет жіберілмеді!", show_alert=True)
        return

    await state.set_state(ConvertState.waiting_multi_format)
    await callback.message.edit_text(
        f"✅ <b>{len(photos)}</b> сурет қабылданды!\nҚандай форматқа түрлендірейін?",
        reply_markup=format_keyboard_multi(),
        parse_mode="HTML",
    )
    await callback.answer()


# ══════════════════════════════════════════════
# Жалғыз сурет → формат callback
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_format, F.data.startswith("fmt:"))
async def single_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split(":")[1]

    if fmt == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды. Жаңа сурет жіберуіңізге болады.")
        await callback.answer()
        return

    # Telegram 10с timeout-тан бұрын жауап береміз
    await callback.answer()
    await callback.message.edit_text("⏳ Түрлендірілуде...")
    sd = await state.get_data()

    try:
        result, fname = convert_single(sd["image_bytes"], fmt, _default_filename())
        await _send_result(callback.message, result, fname, fmt)
        await callback.message.delete()
    except Exception as exc:
        logger.exception("single convert error: %s", exc)
        await callback.message.edit_text("❌ Қате пайда болды. Басқа сурет жіберіп көріңіз.")

    await state.clear()


# ══════════════════════════════════════════════
# Көп сурет → формат callback
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_multi_format, F.data.startswith("mfmt:"))
async def multi_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split(":")[1]

    if fmt == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        await callback.answer()
        return

    # Telegram 10с timeout-тан бұрын жауап береміз
    await callback.answer()
    await callback.message.edit_text("⏳ Түрлендірілуде...")
    sd = await state.get_data()
    photos: list[bytes] = sd["photos"]

    try:
        result, fname = convert_multi(photos, fmt, _default_filename())
        await _send_result(callback.message, result, fname, fmt, count=len(photos))
        await callback.message.delete()
    except Exception as exc:
        logger.exception("multi convert error: %s", exc)
        await callback.message.edit_text("❌ Қате пайда болды.")

    await state.clear()


# ══════════════════════════════════════════════
# Fallback
# ══════════════════════════════════════════════

@router.message()
async def unknown_message(message: Message, state: FSMContext):
    current = await state.get_state()
    if current == ConvertState.collecting_photos:
        await message.answer("📸 Альбом жіберіңіз немесе ✅ Дайын басыңыз.", reply_markup=done_keyboard())
    elif current in (ConvertState.waiting_format, ConvertState.waiting_multi_format):
        await message.answer("⬆️ Жоғарыдағы мәзірден форматты таңдаңыз.")
    else:
        await message.answer(
            "📸 Маған сурет жіберіңіз — мен оны файлға айналдырамын!\n"
            "/help — толық ақпарат"
        )
