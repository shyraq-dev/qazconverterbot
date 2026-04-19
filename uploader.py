"""
uploader.py — Catbox және Imgur-ға файл жүктеу.       Catbox: барлық файл түрі, тіркеусіз, ұзақ сақталады.  Imgur:  тек сурет (JPG/PNG/GIF/WebP), multipart/form-data арқылы.
"""                                                   from __future__ import annotations                    import aiohttp                                        
IMGUR_CLIENT_ID = "546c25a59c58ad7"                   IMGUR_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}                                         
                                                      async def upload_catbox(data: bytes, filename: str) -> str:                                                     url = "https://catbox.moe/user/api.php"
    form = aiohttp.FormData()                             form.add_field("reqtype", "fileupload")               form.add_field("userhash", "")                        form.add_field("fileToUpload", data, filename=filename)                                                     async with aiohttp.ClientSession() as session:            async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            resp.raise_for_status()                               link = (await resp.text()).strip()                    if not link.startswith("https://"):                       raise ValueError(f"Catbox қате жауап: {link}")
            return link

                                                      async def upload_imgur(data: bytes, filename: str, mime: str = "image/jpeg") -> str:
    """                                                   Imgur anonymous upload — multipart/form-data арқылы.                                                        Base64 емес, тікелей файл жіберу.                     """
    url = "https://api.imgur.com/3/image"                 headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
                                                          form = aiohttp.FormData()                             form.add_field(
        "image", data,                                        filename=filename,                                    content_type=mime,
    )                                                     form.add_field("type", "file")                                                                              async with aiohttp.ClientSession() as session:            async with session.post(                                  url, data=form, headers=headers,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:                                                result = await resp.json()                            if not result.get("success"):                             raise ValueError(f"Imgur қате: {result.get('data', {}).get('error', result)}")                          return result["data"]["link"]

                                                      async def upload(data: bytes, filename: str, host: str, mime_type: str = "image/jpeg") -> str:                  """host: 'catbox' | 'imgur'. Imgur видеоны қабылдамайды — Catbox-қа бағыттайды."""                          if host == "imgur":
        if mime_type not in IMGUR_MIME:
            return await upload_catbox(data, filename)        return await upload_imgur(data, filename, mime=mime_type)
    return await upload_catbox(data, filename)