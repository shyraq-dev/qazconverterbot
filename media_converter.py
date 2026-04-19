"""                                                   media_converter.py — Видео/Аудио/Дауысхат түрлендіру.   video_to_mp3()     Видео → MP3
  video_to_ogg()     Видео → OGG/Opus дауысхат          video_to_note()    Видео → Telegram video note (кружок, 640x640, max 60с)
  audio_to_mp3()     OGG/WAV/... → MP3                  audio_to_ogg()     MP3/WAV/... → OGG/Opus дауысхат  """
from __future__ import annotations                    import io, os, tempfile                               
                                                      def _tmp(data: bytes, suffix: str) -> str:                f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)                                                f.write(data); f.close()                              return f.name
                                                                                                            def _cleanup(*paths: str):
    for p in paths:                                           try: os.remove(p)
        except OSError: pass                                                                                
def _read(path: str) -> bytes:                            with open(path, "rb") as f:
        return f.read()


# ── Видео → аудио ──────────────────────────────────────────────────

def video_to_mp3(data: bytes) -> bytes:
    from moviepy import VideoFileClip
    src = _tmp(data, ".mp4"); dst = src.replace(".mp4", ".mp3")
    try:
        clip = VideoFileClip(src)
        clip.audio.write_audiofile(dst, logger=None)
        clip.close()
        return _read(dst)
    finally:
        _cleanup(src, dst)


def video_to_ogg(data: bytes) -> bytes:
    from moviepy import VideoFileClip                     src = _tmp(data, ".mp4"); dst = src.replace(".mp4", ".ogg")
    try:
        clip = VideoFileClip(src)
        clip.audio.write_audiofile(
            dst, codec="libopus",
            ffmpeg_params=["-ac", "1", "-ar", "48000"],                                                                 logger=None,                                      )                                                     clip.close()
        return _read(dst)                                 finally:                                                  _cleanup(src, dst)
                                                                                                            # ── Видео → бейнехат (кружок) ──────────────────────────────────────                                                                                             def video_to_note(data: bytes, max_seconds: int = 60) -> bytes:                                                 """                                                   Видео → Telegram video note (⭕ кружок).              Талаптар: 640×640, дөңгелек crop, max 60с, mp4/h264.                                                        """                                                   from moviepy import VideoFileClip
                                                          src = _tmp(data, ".mp4")                              dst = src.replace(".mp4", "_note.mp4")
    try:                                                      clip = VideoFileClip(src)                     
        # Ұзақтығын қысқарту                                  if clip.duration > max_seconds:
            clip = clip.subclipped(0, max_seconds)    
        # Квадрат crop (орта)                                 w, h = clip.size                                      side = min(w, h)                                      x1 = (w - side) // 2
        y1 = (h - side) // 2                                  clip = clip.cropped(x1=x1, y1=y1, x2=x1 + side, y2=y1 + side)                                       
        # 640×640-ға resize                                   clip = clip.resized((640, 640))                                                                             clip.write_videofile(
            dst,                                                  codec="libx264",                                      audio_codec="aac",                                    fps=min(clip.fps or 30, 30),
            preset="fast",                                        ffmpeg_params=["-pix_fmt", "yuv420p"],                logger=None,                                      )
        clip.close()                                          return _read(dst)                                 finally:                                                  _cleanup(src, dst)
                                                                                                            # ── Аудио ↔ форматтар ──────────────────────────────────────────────
                                                      def audio_to_ogg(data: bytes, src_suffix: str = ".mp3") -> bytes:                                               from moviepy import AudioFileClip
    src = _tmp(data, src_suffix); dst = src.replace(src_suffix, ".ogg")                                         try:                                                      clip = AudioFileClip(src)
        clip.write_audiofile(                                     dst, codec="libopus",                                 ffmpeg_params=["-ac", "1", "-ar", "48000"],
            logger=None,                                      )                                                     clip.close()                                          return _read(dst)
    finally:                                                  _cleanup(src, dst)                                                                                  
def audio_to_mp3(data: bytes, src_suffix: str = ".ogg") -> bytes:                                               from moviepy import AudioFileClip                     src = _tmp(data, src_suffix); dst = src.replace(src_suffix, ".mp3")                                         try:                                                      clip = AudioFileClip(src)                             clip.write_audiofile(dst, logger=None)
        clip.close()                                          return _read(dst)                                 finally:                                                  _cleanup(src, dst)