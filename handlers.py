"""
handlers.py — барлық handler-лер бір Router-де.

Мүмкіндіктер:
  🖼  Сурет  → PDF / DOCX / JPG / PNG / 🔗 Сілтеме
  🖼  Альбом → PDF / DOCX (жинақталып)
  🎬  Видео  → 🎵 MP3 / 🎤 Дауысхат / ⭕ Бейнехат / 🔗 Сілтеме
  🎤  Дауысхат → 🎵 MP3 / 🎤 OGG / ✏️ Тег өңдеу
  🎵  Аудио  → 🎤 Дауысхат / 🎵 MP3 / ✏️ Тег өңдеу
  ✏️  Аудио редактор: атауы / орындаушы / фон (обложка)
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
from keyboards import (
    format_keyboard_single, format_keyboard_multi, done_keyboard,
    video_format_keyboard, voice_format_keyboard,
    audio_edit_keyboard, upload_host_keyboard,
)
from converter import convert_single, convert_multi, FORMAT_LABELS
from media_converter import video_to_mp3, video_to_ogg, video_to_note, audio_to_mp3, audio_to_ogg
from uploader import upload
from audio_editor import get_audio_info, apply_edits

router = Router()
logger = logging.getLogger(__name__)

IMAGE_MIME = {"image/jpeg","image/png","image/webp","image/bmp","image/gif","image/tiff"}
VIDEO_MIME = {"video/mp4","video/mpeg","video/quicktime","video/x-msvideo","video/webm","video/x-matroska"}
AUDIO_MIME = {"audio/mpeg","audio/mp3","audio/ogg","audio/wav","audio/x-wav","audio/aac","audio/flac"}

_album_tasks: dict[str, asyncio.Task] = {}


# ══════════════════════════════════════════════
# Утилиталар
# ══════════════════════════════════════════════

def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _default_filename() -> str:
    return "document_" + _ts()

async def _dl(bot: Bot, file_id: str) -> bytes:
    f = await bot.get_file(file_id)
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
    text = f"📎 <b>{count}</b> сурет жиналды. Жалғастырыңыз немесе ✅ Дайынды басыңыз."
    if msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    sent = await message.answer(text, reply_markup=done_keyboard(), parse_mode="HTML")
    return sent.message_id

async def _add_to_collection(state: FSMContext, bot: Bot, message: Message, new_photos: list[bytes]):
    current = await state.get_state()
    sd = await state.get_data()
    if current == ConvertState.collecting_photos:
        existing: list[bytes] = sd.get("photos", [])
        existing.extend(new_photos)
        counter_msg_id = sd.get("counter_msg_id")
        await state.update_data(photos=existing)
    else:
        existing = list(new_photos)
        counter_msg_id = None
        await state.set_state(ConvertState.collecting_photos)
        await state.update_data(photos=existing, counter_msg_id=None)
    new_mid = await _update_counter(bot, message.chat.id, counter_msg_id, len(existing), message)
    await state.update_data(counter_msg_id=new_mid)

def _audio_info_text(info: dict) -> str:
    return (
        f"🏷 <b>Атауы:</b> {info['title']}\n"
        f"🏷 <b>Орындаушы:</b> {info['artist']}\n"
        f"📂 <b>Өлшемі:</b> {info['size']}\n"
        f"⏰ <b>Ұзақтығы:</b> {info['duration']}\n\n"
        "Не өзгертесің?"
    )


# ══════════════════════════════════════════════
# /start  /help
# ══════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Сәлем! Мен <b>QazConverter</b>.\n\n"
        "📌 <b>Не түрлендіре аламын:</b>\n"
        "🖼 Сурет → PDF, DOCX, JPG, PNG, 🔗 Сілтеме\n"
        "🎬 Видео → 🎵 MP3, 🎤 Дауысхат, ⭕ Бейнехат, 🔗 Сілтеме\n"
        "🎤 Дауысхат ↔ 🎵 Аудио | ✏️ Тег өңдеу\n\n"
        "Файлды жіберсең — мен қалғанын жасаймын!\n"
        "<i>Сурет → Файл. Тез. Дәл.</i>",
        parse_mode="HTML",
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>QazConverter көмегі</b>\n\n"
        "🖼 <b>Сурет:</b> JPG PNG WebP BMP GIF TIFF\n"
        "  → PDF · DOCX · JPG · PNG · 🔗 Сілтеме\n\n"
        "🎬 <b>Видео:</b> MP4 MOV AVI MKV WebM\n"
        "  → 🎵 MP3 · 🎤 Дауысхат · ⭕ Бейнехат · 🔗 Сілтеме\n\n"
        "🎤 <b>Дауысхат / 🎵 Аудио:</b>\n"
        "  → 🎵 MP3 · 🎤 Дауысхат · ✏️ Тег өңдеу\n\n"
        "✏️ <b>Аудио редактор:</b>\n"
        "  🏷 Атауы · 🏷 Орындаушы · 🖼 Фон (обложка)\n\n"
        "📎 Альбом жіберсең — суреттер жинақталады → PDF/DOCX",
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════
# СУРЕТ
# ══════════════════════════════════════════════

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, state: FSMContext):
    media_group_id = message.media_group_id
    if media_group_id:
        data = await _dl(bot, message.photo[-1].file_id)
        sd = await state.get_data()
        album_buf: dict = sd.get("_album_buf", {})
        bucket: list = album_buf.get(media_group_id, [])
        bucket.append((data, message.message_id))
        album_buf[media_group_id] = bucket
        await state.update_data(_album_buf=album_buf)
        old = _album_tasks.pop(media_group_id, None)
        if old: old.cancel()

        async def flush(mgid: str, msg: Message, st: FSMContext, bt: Bot):
            await asyncio.sleep(1.5)
            _album_tasks.pop(mgid, None)
            sd2 = await st.get_data()
            buf2: dict = sd2.get("_album_buf", {})
            bkt2 = buf2.pop(mgid, [])
            await st.update_data(_album_buf=buf2)
            photos = [d for d, _ in sorted(bkt2, key=lambda x: x[1])]
            if photos:
                await _add_to_collection(st, bt, msg, photos)

        _album_tasks[media_group_id] = asyncio.create_task(flush(media_group_id, message, state, bot))
    else:
        current = await state.get_state()
        data = await _dl(bot, message.photo[-1].file_id)
        if current == ConvertState.collecting_photos:
            # Альбом жинауда — Telegram сығымдайды, lossless PNG сақтаймыз
            from PIL import Image as _PilImage
            import io as _io
            img = _PilImage.open(_io.BytesIO(data))
            buf = _io.BytesIO()
            img.save(buf, format="PNG")
            data = buf.getvalue()
            await _add_to_collection(state, bot, message, [data])
        elif current == ConvertState.waiting_audio_cover:
            # Аудио обложка үшін жіберілген сурет
            await _apply_cover(state, bot, message, data)
        else:
            # Жалғыз сурет — lossless PNG-ге конвертациялап сақтаймыз
            # Telegram F.photo-да JPEG артефакттары болады, PNG арқылы сапа сақталады
            from PIL import Image as _PilImage
            import io as _io
            img = _PilImage.open(_io.BytesIO(data))
            buf = _io.BytesIO()
            img.save(buf, format="PNG")
            data = buf.getvalue()
            await state.update_data(image_bytes=data, upload_mime="image/png")
            await state.set_state(ConvertState.waiting_format)
            await message.answer("✅ Сурет қабылданды! Формат таңда:", reply_markup=format_keyboard_single())


# ══════════════════════════════════════════════
# DOCUMENT
# ══════════════════════════════════════════════

@router.message(F.document)
async def handle_document(message: Message, bot: Bot, state: FSMContext):
    doc = message.document
    mime = doc.mime_type or ""
    data = await _dl(bot, doc.file_id)
    current = await state.get_state()

    if current == ConvertState.waiting_audio_cover and mime in IMAGE_MIME:
        await _apply_cover(state, bot, message, data)
        return

    if mime in IMAGE_MIME:
        if current == ConvertState.collecting_photos:
            await _add_to_collection(state, bot, message, [data])
        else:
            await state.update_data(image_bytes=data, upload_mime=mime)
            await state.set_state(ConvertState.waiting_format)
            await message.answer("✅ Сурет қабылданды! Формат таңда:", reply_markup=format_keyboard_single())
    elif mime in VIDEO_MIME:
        fname = doc.file_name or f"video_{_ts()}.mp4"
        await state.update_data(media_bytes=data, media_filename=fname, upload_mime=mime)
        await state.set_state(ConvertState.waiting_video_format)
        await message.answer("✅ Видео қабылданды! Не жасайын?", reply_markup=video_format_keyboard())
    elif mime in AUDIO_MIME:
        ext = "." + (doc.file_name or "audio.mp3").rsplit(".", 1)[-1]
        await state.update_data(media_bytes=data, media_ext=ext)
        await state.set_state(ConvertState.waiting_voice_format)
        await message.answer("✅ Аудио қабылданды! Формат таңда:", reply_markup=voice_format_keyboard())
    else:
        await message.answer("❌ Бұл файл түрін қолдамаймын.\nСурет, видео немесе аудио жіберіңіз.")


# ══════════════════════════════════════════════
# ВИДЕО / ДАУЫСХАТ / АУДИО
# ══════════════════════════════════════════════

@router.message(F.video)
async def handle_video(message: Message, bot: Bot, state: FSMContext):
    data = await _dl(bot, message.video.file_id)
    fname = message.video.file_name or f"video_{_ts()}.mp4"
    await state.update_data(media_bytes=data, media_filename=fname, upload_mime="video/mp4")
    await state.set_state(ConvertState.waiting_video_format)
    await message.answer("✅ Видео қабылданды! Не жасайын?", reply_markup=video_format_keyboard())

@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot, state: FSMContext):
    data = await _dl(bot, message.voice.file_id)
    await state.update_data(media_bytes=data, media_ext=".ogg")
    await state.set_state(ConvertState.waiting_voice_format)
    await message.answer("✅ Дауысхат қабылданды! Формат таңда:", reply_markup=voice_format_keyboard())

@router.message(F.audio)
async def handle_audio(message: Message, bot: Bot, state: FSMContext):
    data = await _dl(bot, message.audio.file_id)
    ext = "." + (message.audio.file_name or "audio.mp3").rsplit(".", 1)[-1]
    await state.update_data(media_bytes=data, media_ext=ext)
    await state.set_state(ConvertState.waiting_voice_format)
    await message.answer("✅ Аудио қабылданды! Формат таңда:", reply_markup=voice_format_keyboard())


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
        reply_markup=format_keyboard_multi(), parse_mode="HTML",
    )
    await callback.answer()


# ══════════════════════════════════════════════
# Жалғыз сурет → формат
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_format, F.data.startswith("fmt:"))
async def single_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split(":")[1]
    if fmt == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        await callback.answer()
        return
    await callback.answer()
    if fmt == "link":
        await state.set_state(ConvertState.waiting_upload_host)
        await callback.message.edit_text("🔗 Қай хостингке жүктейін?", reply_markup=upload_host_keyboard())
        return
    await callback.message.edit_text("⏳ Түрлендірілуде...")
    sd = await state.get_data()
    try:
        result, fname = convert_single(sd["image_bytes"], fmt, _default_filename())
        await _send_result(callback.message, result, fname, fmt)
        await callback.message.delete()
    except Exception as exc:
        logger.exception("single convert: %s", exc)
        await callback.message.edit_text("❌ Қате пайда болды.")
    await state.clear()


# ══════════════════════════════════════════════
# Көп сурет → формат
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_multi_format, F.data.startswith("mfmt:"))
async def multi_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split(":")[1]
    if fmt == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text("⏳ Түрлендірілуде...")
    sd = await state.get_data()
    photos: list[bytes] = sd["photos"]
    try:
        result, fname = convert_multi(photos, fmt, _default_filename())
        await _send_result(callback.message, result, fname, fmt, count=len(photos))
        await callback.message.delete()
    except Exception as exc:
        logger.exception("multi convert: %s", exc)
        await callback.message.edit_text("❌ Қате пайда болды.")
    await state.clear()


# ══════════════════════════════════════════════
# Видео → формат
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_video_format, F.data.startswith("vfmt:"))
async def video_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split(":")[1]
    if fmt == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        await callback.answer()
        return
    await callback.answer()
    if fmt == "link":
        await state.set_state(ConvertState.waiting_upload_host)
        await callback.message.edit_text("🔗 Қай хостингке жүктейін?", reply_markup=upload_host_keyboard())
        return

    await callback.message.edit_text("⏳ Өңделуде...")
    sd = await state.get_data()
    data: bytes = sd["media_bytes"]
    try:
        if fmt == "mp3":
            result = video_to_mp3(data)
            await callback.message.answer_audio(
                BufferedInputFile(result, filename=f"audio_{_ts()}.mp3"),
                caption="✅ <b>MP3</b> дайын!", parse_mode="HTML",
            )
        elif fmt == "ogg":
            result = video_to_ogg(data)
            await callback.message.answer_voice(
                BufferedInputFile(result, filename=f"voice_{_ts()}.ogg"),
                caption="✅ <b>Дауысхат</b> дайын!", parse_mode="HTML",
            )
        elif fmt == "vidnote":
            result = video_to_note(data)
            await callback.message.answer_video_note(
                BufferedInputFile(result, filename=f"note_{_ts()}.mp4"),
            )
        await callback.message.delete()
    except Exception as exc:
        logger.exception("video convert: %s", exc)
        await callback.message.edit_text("❌ Қате пайда болды. ffmpeg орнатылған ба?")
    await state.clear()


# ══════════════════════════════════════════════
# Дауысхат / Аудио → формат
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_voice_format, F.data.startswith("voice:"))
async def voice_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split(":")[1]
    if fmt == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        await callback.answer()
        return
    await callback.answer()

    sd = await state.get_data()
    data: bytes = sd["media_bytes"]
    ext: str = sd.get("media_ext", ".ogg")

    if fmt == "edit":
        # Аудио редакторға өту — тек MP3 қолдайды
        if ext != ".mp3":
            await callback.message.edit_text("⏳ MP3-ке түрлендірілуде...")
            try:
                data = audio_to_mp3(data, src_suffix=ext)
                ext = ".mp3"
            except Exception as exc:
                logger.exception("to mp3: %s", exc)
                await callback.message.edit_text("❌ MP3-ке түрлендіру қатесі.")
                await state.clear()
                return

        info = get_audio_info(data)
        await state.update_data(media_bytes=data, media_ext=".mp3", audio_edits={})
        await state.set_state(ConvertState.waiting_audio_edit)
        await callback.message.edit_text(_audio_info_text(info), reply_markup=audio_edit_keyboard(), parse_mode="HTML")
        return

    await callback.message.edit_text("⏳ Түрлендірілуде...")
    try:
        if fmt == "mp3":
            result = audio_to_mp3(data, src_suffix=ext)
            await callback.message.answer_audio(
                BufferedInputFile(result, filename=f"audio_{_ts()}.mp3"),
                caption="✅ <b>MP3</b> дайын!", parse_mode="HTML",
            )
        elif fmt == "ogg":
            result = audio_to_ogg(data, src_suffix=ext)
            await callback.message.answer_voice(
                BufferedInputFile(result, filename=f"voice_{_ts()}.ogg"),
                caption="✅ <b>Дауысхат</b> дайын!", parse_mode="HTML",
            )
        await callback.message.delete()
    except Exception as exc:
        logger.exception("voice convert: %s", exc)
        await callback.message.edit_text("❌ Қате пайда болды.")
    await state.clear()


# ══════════════════════════════════════════════
# Аудио редактор
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_audio_edit, F.data.startswith("aedit:"))
async def audio_edit_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    await callback.answer()

    if action == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        return

    if action == "title":
        await state.set_state(ConvertState.waiting_audio_title)
        await callback.message.edit_text("✏️ Жаңа <b>атауын</b> жаз:", parse_mode="HTML")
        return

    if action == "artist":
        await state.set_state(ConvertState.waiting_audio_artist)
        await callback.message.edit_text("✏️ Жаңа <b>орындаушы атын</b> жаз:", parse_mode="HTML")
        return

    if action == "cover":
        await state.set_state(ConvertState.waiting_audio_cover)
        await callback.message.edit_text("🖼 Фон ретінде пайдаланылатын <b>суретті</b> жібер:", parse_mode="HTML")
        return

    if action == "save":
        await callback.message.edit_text("⏳ Сақталуда...")
        sd = await state.get_data()
        data: bytes = sd["media_bytes"]
        edits: dict = sd.get("audio_edits", {})
        try:
            # Барлық өзгерістер бір рет, бір файл арқылы қолданылады
            result, cover = apply_edits(data, edits)
            info = get_audio_info(result)
            fname = f"audio_{_ts()}.mp3"
            caption = (
                f"✅ <b>Аудио сақталды!</b>\n\n"
                f"🏷 <b>Атауы:</b> {info['title']}\n"
                f"🏷 <b>Орындаушы:</b> {info['artist']}\n"
                f"📂 <b>Өлшемі:</b> {info['size']}\n"
                f"⏰ <b>Ұзақтығы:</b> {info['duration']}"
            )
            import tempfile, os as _os
            audio_file = BufferedInputFile(result, filename=fname)

            # performer / title — answer_audio параметрлері арқылы беру
            # (mutagen тегтеріне қосымша, Telegram да оқиды)
            send_kwargs = dict(
                caption=caption,
                parse_mode="HTML",
                performer=edits.get("artist") or info["artist"],
                title=edits.get("title") or info["title"],
            )

            if cover:
                # BufferedInputFile кейде thumbnail қабылдамайды —
                # FSInputFile (уақытша disk файлы) арқылы беру сенімдірек
                from aiogram.types import FSInputFile
                fd, tmp_cover = tempfile.mkstemp(suffix=".jpg")
                try:
                    with _os.fdopen(fd, "wb") as tf:
                        tf.write(cover)
                    send_kwargs["thumbnail"] = FSInputFile(tmp_cover, filename="cover.jpg")
                    await callback.message.answer_audio(audio_file, **send_kwargs)
                finally:
                    try: _os.remove(tmp_cover)
                    except OSError: pass
            else:
                await callback.message.answer_audio(audio_file, **send_kwargs)
            await callback.message.delete()
        except Exception as exc:
            logger.exception("audio save: %s", exc)
            await callback.message.edit_text("❌ Сақтау кезінде қате болды.")
        await state.clear()


@router.message(ConvertState.waiting_audio_title)
async def audio_title_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    edits: dict = dict(sd.get("audio_edits", {}))  # көшірме — мутация қаупін болдырмау
    edits["title"] = message.text.strip()
    await state.update_data(audio_edits=edits)
    await state.set_state(ConvertState.waiting_audio_edit)
    info = get_audio_info(sd["media_bytes"])
    info["title"] = edits["title"]
    if edits.get("artist"):
        info["artist"] = edits["artist"]
    await message.answer(_audio_info_text(info), reply_markup=audio_edit_keyboard(), parse_mode="HTML")


@router.message(ConvertState.waiting_audio_artist)
async def audio_artist_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    edits: dict = dict(sd.get("audio_edits", {}))  # көшірме
    edits["artist"] = message.text.strip()
    await state.update_data(audio_edits=edits)
    await state.set_state(ConvertState.waiting_audio_edit)
    info = get_audio_info(sd["media_bytes"])
    if edits.get("title"):
        info["title"] = edits["title"]
    info["artist"] = edits["artist"]
    await message.answer(_audio_info_text(info), reply_markup=audio_edit_keyboard(), parse_mode="HTML")


def _prepare_cover(raw: bytes) -> bytes:
    """
    Telegram thumbnail шектеулері:
      - JPEG форматы
      - max 200 кБ
      - max 320×320 px
    Pillow арқылы resize + compress жасаймыз.
    """
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(raw))
    img = img.convert("RGB")

    # 320×320-ға сыйдыру (aspect ratio сақтай отырып)
    img.thumbnail((320, 320), Image.LANCZOS)

    # 200 кБ-тан аз болғанша quality азайту
    for quality in (95, 85, 75, 60, 45):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        if buf.tell() <= 200 * 1024:
            return buf.getvalue()

    # Соңғы шара — ең кіші quality
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=30)
    return buf.getvalue()


async def _apply_cover(state: FSMContext, bot: Bot, message: Message, cover_data: bytes):
    """Фон суретін дайындап, state-ке сақтап, редакторға қайтарады."""
    sd = await state.get_data()
    edits: dict = dict(sd.get("audio_edits", {}))

    # Telegram thumbnail талаптарына сай етіп дайындау
    edits["cover"] = _prepare_cover(cover_data)

    await state.update_data(audio_edits=edits)
    await state.set_state(ConvertState.waiting_audio_edit)
    info = get_audio_info(sd["media_bytes"])
    if edits.get("title"):
        info["title"] = edits["title"]
    if edits.get("artist"):
        info["artist"] = edits["artist"]
    await message.answer(
        "✅ Фон сурет сақталды!\n\n" + _audio_info_text(info),
        reply_markup=audio_edit_keyboard(), parse_mode="HTML",
    )


# ══════════════════════════════════════════════
# Сілтеме → хост таңдау
# ══════════════════════════════════════════════

@router.callback_query(ConvertState.waiting_upload_host, F.data.startswith("host:"))
async def host_selected(callback: CallbackQuery, state: FSMContext):
    host = callback.data.split(":")[1]
    if host == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Бас тартылды.")
        await callback.answer()
        return
    await callback.answer()
    host_name = "Catbox" if host == "catbox" else "Imgur"
    await callback.message.edit_text(f"⏳ {host_name}-ке жүктелуде...")
    sd = await state.get_data()
    data: bytes = sd.get("image_bytes") or sd.get("media_bytes")
    mime: str = sd.get("upload_mime", "image/jpeg")
    filename: str = sd.get("media_filename") or (
        f"image_{_ts()}.jpg" if sd.get("image_bytes") else f"file_{_ts()}"
    )
    try:
        link = await upload(data, filename, host=host, mime_type=mime)
        await callback.message.edit_text(
            f"✅ <b>{host_name}</b> сілтемесі дайын!\n\n🔗 <a href='{link}'>{link}</a>",
            parse_mode="HTML", disable_web_page_preview=False,
        )
    except Exception as exc:
        logger.exception("upload: %s", exc)
        await callback.message.edit_text("❌ Жүктеу кезінде қате болды.")
    await state.clear()


# ══════════════════════════════════════════════
# Fallback
# ══════════════════════════════════════════════

@router.message()
async def unknown_message(message: Message, state: FSMContext):
    current = await state.get_state()
    if current == ConvertState.collecting_photos:
        await message.answer("📸 Альбом жіберіңіз немесе ✅ Дайын басыңыз.", reply_markup=done_keyboard())
    elif current == ConvertState.waiting_audio_cover:
        await message.answer("🖼 Фон ретінде сурет жіберіңіз.")
    elif current in (ConvertState.waiting_audio_title, ConvertState.waiting_audio_artist):
        await message.answer("✏️ Мәтін жазыңыз.")
    elif current in (
        ConvertState.waiting_format, ConvertState.waiting_multi_format,
        ConvertState.waiting_video_format, ConvertState.waiting_voice_format,
        ConvertState.waiting_upload_host, ConvertState.waiting_audio_edit,
    ):
        await message.answer("⬆️ Жоғарыдағы мәзірден таңдаңыз.")
    else:
        await message.answer(
            "📎 Маған сурет, видео, дауысхат немесе аудио жіберіңіз!\n"
            "/help — толық ақпарат"
        )