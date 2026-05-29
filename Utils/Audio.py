# File responsible to hold a class which trasnaltes text into speech

from Utils.Singleton import Singleton
import asyncio
import edge_tts
from Utils.Exception import UnsupportedLanguage
from config import OUTPUT_FOLDER
import os

# Voice configurations
VOICE_CONFIGS = {
    'en': "en-US-JennyNeural",
    'hi': "hi-IN-SwaraNeural",
    'es': "es-MX-JorgeNeural",
    'fr': "fr-FR-HenriNeural",
    'de': "de-DE-KillianNeural",
    'ja': "ja-JP-KeitaNeural",
    'ko': "ko-KR-SunHiNeural",
    'zh': "zh-CN-XiaoxiaoNeural",
    'it': "it-IT-DiegoNeural",
    'pt': "pt-BR-AntonioNeural",
    'ru': "ru-RU-DmitryNeural",
    'nl': "nl-NL-MaartenNeural",
    'tr': "tr-TR-AhmetNeural",
    'pl': "pl-PL-MarekNeural",
    'id': "id-ID-ArdiNeural",
    'th': "th-TH-NiwatNeural",
    'vi': "vi-VN-HoaiMyNeural"
}

LANGUAGE_MAP = {
    'en': "English",
    'hi': "Hindi",
    'es': "Spanish",
    'fr': "French",
    'de': "German",
    'ja': "Japanese",
    'ko': "Korean",
    'zh': "Chinese (Mandarin)",
    'it': "Italian",
    'pt': "Portuguese (Brazilian)",
    'ru': "Russian",
    'nl': "Dutch",
    'tr': "Turkish",
    'pl': "Polish",
    'id': "Indonesian",
    'th': "Thai",
    'vi': "Vietnamese"
}

@Singleton
class Audio:
    def __init__(self):
        pass
           
    def tts(self,TEXT,LANG,OUTPUT_FILE): # LANG - en,hi,es....
        if(TEXT.strip() == ""):
            return True
        
        voice = VOICE_CONFIGS.get(LANG)
        if voice is None:
            raise UnsupportedLanguage(f"[Audio.py:] {LANG} is not supported.")
        
        OUTPUT_FILE = os.path.join(OUTPUT_FOLDER,OUTPUT_FILE)
        
        communicate = edge_tts.Communicate(TEXT, voice)
        asyncio.run(communicate.save(OUTPUT_FILE))
        return True