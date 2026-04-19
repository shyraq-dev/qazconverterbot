# QazConverter Bot 🤖

Telegram боты — сурет, видео, аудио және дауысхатты тез түрлендіретін көмекші.

---

## ⚡ Мүмкіндіктер

### 🖼 Сурет
| Кіріс | Шығыс |
|---|---|
| JPG, PNG, WebP, BMP, GIF, TIFF | PDF (A4) |
| | DOCX (Word) |
| | JPG |
| | PNG |
| | 🔗 Catbox сілтемесі |

> Бірнеше суретті альбоммен жіберсең — бәрі **жинақталып** бір PDF/DOCX-қа айналады.

---

### 🎬 Видео
| Кіріс | Шығыс |
|---|---|
| MP4, MOV, AVI, MKV, WebM | 🎵 MP3 (аудио файл) |
| | 🎤 OGG (дауысхат) |
| | ⭕ Бейнехат (кружок, max 60с) |
| | 🔗 Catbox сілтемесі |

---

### 🎤 Дауысхат / 🎵 Аудио
| Кіріс | Шығыс |
|---|---|
| OGG дауысхат | 🎵 MP3 |
| MP3, WAV, AAC, FLAC | 🎤 OGG дауысхат |

---

### ✏️ Аудио редактор (MP3)
- 🏷 **Атауы** — музыка атын өзгерту
- 🏷 **Орындаушы** — орындаушы атын өзгерту
- 🖼 **Фон (обложка)** — альбом суретін орнату
- Барлық өзгерістер **бір рет, бір файлға** жазылады

---

## 📁 Файлдар құрылымы

```
qazconverter_bot/
├── main.py            # Іске қосу нүктесі
├── config.py          # .env оқу (pydantic-settings)
├── handlers.py        # Барлық handler-лер (Router)
├── converter.py       # Сурет түрлендіру (Pillow)
├── media_converter.py # Видео/Аудио түрлендіру (moviepy)
├── audio_editor.py    # MP3 тег өңдеу (mutagen)
├── uploader.py        # Catbox жүктеу (aiohttp)
├── keyboards.py       # Inline пернетақталар
├── states.py          # FSM күйлері
├── requirements.txt
├── .env               # Токен (git-ке жүктемеңіз!)
└── .env.example
```

---

## 🛠 Орнату

### 1. Талаптар
- Python 3.11+
- ffmpeg (видео/аудио түрлендіру үшін)

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# Termux
pkg install ffmpeg

# macOS
brew install ffmpeg
```

### 2. Тәуелділіктерді орнату

```bash
pip install -r requirements.txt
```

### 3. Токен алу

[@BotFather](https://t.me/BotFather) → `/newbot` → токенді көшір

### 4. `.env` файлын жасау

```bash
cp .env.example .env
```

`.env` ішіне токенді қой:

```
BOT_TOKEN=1234567890:AAF...
```

### 5. Іске қосу

```bash
python main.py
```

---

## 🖥 Сервер (VPS) — systemd

`/etc/systemd/system/qazconverter.service` файлын жасау:

```ini
[Unit]
Description=QazConverter Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/qazconverter_bot
EnvironmentFile=/home/ubuntu/qazconverter_bot/.env
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable qazconverter
sudo systemctl start qazconverter
sudo systemctl status qazconverter
```

---

## 📱 Termux (Android)

```bash
pkg update && pkg install python ffmpeg
pip install -r requirements.txt
python main.py
```

Фонда іске қосу:

```bash
nohup python main.py &
```

---

## 📦 Тәуелділіктер

| Кітапхана | Нұсқа | Мақсаты |
|---|---|---|
| aiogram | 3.25.0+ | Telegram Bot Framework |
| Pillow | 10.0.4 | Сурет өңдеу |
| reportlab | 4.2.5 | PDF жасау |
| python-docx | 1.1.2 | DOCX жасау |
| moviepy | 2.1.1 | Видео/Аудио түрлендіру |
| mutagen | 1.47.0 | MP3 тег өңдеу |
| aiohttp | 3.11.11 | Catbox жүктеу |
| pydantic-settings | 2.7.0 | .env оқу |

---

## 🔧 FSM күйлері

```
waiting_format        — жалғыз сурет, формат күту
collecting_photos     — альбом жинау
waiting_multi_format  — көп сурет, формат күту
waiting_video_format  — видео, формат күту
waiting_voice_format  — аудио/дауысхат, формат күту
waiting_upload_host   — сілтеме, хост күту
waiting_audio_edit    — аудио редактор мәзірі
waiting_audio_title   — атауы енгізу күту
waiting_audio_artist  — орындаушы енгізу күту
waiting_audio_cover   — фон сурет күту
```

---

*QazConverter — Сурет → Файл. Тез. Дәл.*
