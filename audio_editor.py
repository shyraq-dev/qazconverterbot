"""                                                   audio_editor.py — MP3 тег өңдеу және обложка қою (mutagen).                                                 Барлық операция disk-тегі уақытша файл арқылы жасалады.
"""                                                   from __future__ import annotations                    import os                                             import tempfile
from datetime import timedelta                                                                              
# ── Утилиталар ─────────────────────────────────────────────────────                                       
def _write_tmp(data: bytes, suffix: str = ".mp3") -> str:                                                       fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:                            f.write(data)                                     return path
                                                                                                            def _read(path: str) -> bytes:
    with open(path, "rb") as f:                               return f.read()                                                                                     
def _rm(*paths: str):                                     for p in paths:                                           try:
            os.remove(p)                                      except OSError:                                           pass                                                                                            
def _fmt_dur(sec: float) -> str:                          from datetime import timedelta                        td = timedelta(seconds=int(sec))
    h, rem = divmod(td.seconds, 3600)                     m, s = divmod(rem, 60)                                if td.days or h:                                          return f"{td.days * 24 + h}:{m:02d}:{s:02d}"      return f"{m}:{s:02d}"
                                                                                                            def _fmt_size(n: int) -> str:
    if n < 1024:       return f"{n} B"                    if n < 1024 ** 2:  return f"{n / 1024:.1f} KB"        return f"{n / 1024 ** 2:.2f} MB"
                                                                                                            def _ensure_tags(path: str):                              """
    Файлда ID3 header жоқ болса — жасайды және дискке жазады.                                                   mutagen-да add_tags() тек объектке қосады, save() керек.                                                    """                                                   from mutagen.id3 import ID3, ID3NoHeaderError         from mutagen.mp3 import MP3                           try:
        ID3(path)  # бар болса — жарайды                  except ID3NoHeaderError:                                  audio = MP3(path)
        audio.add_tags()                                      audio.save(path)   # ← міне бұл жетіспеп тұрған жол                                                                                                       
# ── Мета оқу ───────────────────────────────────────────────────────                                       
def get_audio_info(data: bytes) -> dict:                  from mutagen.mp3 import MP3                           from mutagen.id3 import ID3, ID3NoHeaderError                                                               path = _write_tmp(data)
    try:                                                      audio = MP3(path)                                     duration = audio.info.length
                                                              try:                                                      tags = ID3(path)                                      title  = str(tags.get("TIT2", "—"))                   artist = str(tags.get("TPE1", "—"))
        except ID3NoHeaderError:                                  title = artist = "—"                      
        return {                                                  "title":    title,                                    "artist":   artist,                                   "size":     _fmt_size(len(data)),                     "duration": _fmt_dur(duration),
        }                                                 finally:                                                  _rm(path)
                                                                                                            # ── Барлық өзгерістерді бір рет қолдану ───────────────────────────
                                                      def apply_edits(data: bytes, edits: dict) -> tuple[bytes, bytes | None]:
    """                                                   edits = {"title": str|None, "artist": str|None, "cover": bytes|None}                                    
    Қайтарады: (жаңартылған_mp3_bytes, cover_bytes | None)                                                      cover_bytes — Telegram answer_audio(thumbnail=...) үшін бөлек.                                                                                                    Алгоритм:
      1. Байтты уақытша файлға жаз                          2. ID3 header жоқ болса — жасап, файлға сақта (_ensure_tags)
      3. ID3 объектін оқы — барлық тегтерді жаз             4. tags.save(path) — барлығы бір рет жазылады         5. Файлды оқып, bytes қайтар                        """
    from mutagen.id3 import ID3, TIT2, TPE1, APIC                                                               path = _write_tmp(data)
    try:                                                      _ensure_tags(path)          # ID3 header кепілдігі                                                          tags = ID3(path)            # бар тегтермен жүктеу
                                                              if edits.get("title") is not None:                        tags["TIT2"] = TIT2(encoding=3, text=edits["title"])                                                                                                          if edits.get("artist") is not None:
            tags["TPE1"] = TPE1(encoding=3, text=edits["artist"])                                           
        cover: bytes | None = edits.get("cover")              if cover is not None:                                     tags["APIC"] = APIC(
                encoding=3,                                           mime="image/jpeg",                                    type=3,        # Front cover
                desc="Cover",                                         data=cover,                                       )                                         
        tags.save(path, v2_version=3)   # бір рет, барлығы бірге                                            
        result = _read(path)                                  return result, cover                          
    finally:                                                  _rm(path)