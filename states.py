from aiogram.fsm.state import State, StatesGroup      
                                                      class ConvertState(StatesGroup):                          # Сурет
    waiting_format = State()                              collecting_photos = State()                           waiting_multi_format = State()
                                                          # Видео                                               
waiting_video_format = State()
                  
# Дауысхат / Аудио                        
waiting_voice_format = State()

# Сілтеме — хост таңдау
waiting_upload_host = State()
        
    # Аудио редактор                                      
waiting_audio_edit = State()      # тег / фон таңдау                                                        
waiting_audio_title = State()     # атауы енгізу
waiting_audio_artist = State()    # орындаушы енгізу                                                        
waiting_audio_cover = State()     # фон сурет күту

