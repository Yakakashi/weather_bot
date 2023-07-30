import telebot
import requests
import speech_recognition as sr
import subprocess, os
from telebot import types
from pprint import pprint
from config import weather_api_token


TOKEN = "##########:###################################"

f1 = """/start - я погодный бот
Для просмотра прогноза погоды пропишите название населенного пункта
"""


ffmpeg = r"E:\Programming\ffmpeg-4.0.2-win64-static\ffmpeg-4.0.2-win64-static\bin\ffmpeg.exe"

def convert_to_wav(ffmmpeg_path, input_file):
    output_file = input_file[:-4] + ".wav"
    p = subprocess.Popen(ffmmpeg_path + " -i " + input_file + " -acodec pcm_s16le -ac 1 -ar 16000 " + output_file)
    p.communicate()

def millibars_to_millimetres(press_millibars):
    press_millimeters = press_millibars * 0.75
    if press_millimeters > 760:
        press_millimeters = press_millimeters * 0.985
    return press_millimeters


def kph_to_mps(kph):
    mps = kph / 3.6
    return mps


def winddir(abbr):
    res = ""
    if len(abbr) == 1:
        if abbr == "E":
            res = "Восточный"
        elif abbr == "N":
            res = "Северный"
        elif abbr == "W":
            res = "Западный"
        elif abbr == "S":
            res = "Южный"
    elif len(abbr) == 2:
        if abbr == "SE":
            res = "Юго-Восточный"
        elif abbr == "SW":
            res = "Юго-Западный"
        elif abbr == "NE":
            res = "Северо-Восточный"
        elif abbr == "NW":
            res = "Северо-Западный"
    elif len(abbr) == 3:
        if abbr == "ESE":
            res = "Восточный, Юго-Восточный"
        elif abbr == "ENE":
            res = "Восточный, Северо-Восточный"
        elif abbr == "NNE":
            res = "Северный, Северо-Восточный"
        elif abbr == "SSE":
            res = "Южный, Юго-Восточный"
        elif abbr == "WSW":
            res = "Западный, Юго-Западный"
        elif abbr == "SSW":
            res = "Южный, Юго-Западный"
        elif abbr == "WNW":
            res = "Западный, Северо-Западный"
        elif abbr == "NNW":
            res = "Северный, Северо-Западный"
    return res


def get_icon_by_url(url):
    resp = requests.get(url)
    with open("cond_icon.png", "wb") as out_img:
        out_img.write(resp.content)
    return out_img


def get_weather(city, weather_api_token):
    try:
        responce = requests.get(f"http://api.weatherapi.com/v1/current.json?q={city}&key={weather_api_token}&lang=ru")
        data = responce.json()
        pprint(data)

        localtime = data["location"]["localtime"]
        city = data["location"]["name"]
        condition_text = data["current"]["condition"]["text"]
        condition_icon = data["current"]["condition"]["icon"]
        print(type(condition_icon))
        pref = "http:"
        print(pref + condition_icon)
        icon = get_icon_by_url(pref + condition_icon)
        print(type(icon))
        temp = data["current"]["temp_c"]
        feels_temp = data["current"]["feelslike_c"]
        wind = kph_to_mps(data["current"]["wind_kph"])
        gust = kph_to_mps(data["current"]["gust_kph"])
        wind_dir = winddir(data["current"]["wind_dir"])
        pressure = millibars_to_millimetres(data["current"]["pressure_mb"])
        humidity = data["current"]["humidity"]

        if gust >= wind:
            weather_text = f"******** {localtime} ********\n{city} - {condition_text}\n" \
                           f"Температура: {temp}°С (ощущается, как {feels_temp}°С)\n"f"Ветер: {wind:.2f} м/с с порывами до {gust:.2f} м/с\n" \
                           f"Направление ветра: {wind_dir}\nДавление: {int(pressure)} мм рт.ст\nВлажность воздуха: {humidity}%"
        else:
            weather_text = f"******** {localtime} ********\n{city} - {condition_text}\n" \
                           f"Температура: {temp}°С (ощущается, как {feels_temp}°С)\n"f"Ветер: {wind:.2f} м/с\n" \
                           f"Направление ветра: {wind_dir}\nДавление: {int(pressure)} мм рт.ст\nВлажность воздуха: {humidity}%"

    except Exception:
        weather_text = "Погода в данном месте не отслеживается, либо получены некорректные данные"
    return weather_text

def audio_recognition(file):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(file)
    with audio_file as source_audio:
        res_audio = recognizer.record(source_audio)
    try:
        text = recognizer.recognize_google(res_audio, language="ru-RU")
    except Exception:
        text = "не распознал фразу"
    return text



bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, f1)
    # bot.send_message(message.chat.id, "Введите название нас. пункта: ")


@bot.message_handler(content_types=['text'])
def show_weather(message):
    bot.send_message(message.chat.id, get_weather(message.text.strip(), weather_api_token))
    try:
        bot.send_photo(message.chat.id, open("cond_icon.png", "rb"))

        os.remove("cond_icon.png")
    except FileNotFoundError:
        print("проблема с файлом")


@bot.message_handler(content_types=['voice'])
def show_weather_by_voice(message):
    try:
        voice_info = bot.get_file(message.voice.file_id)
        url = f"https://api.telegram.org/file/bot{TOKEN}/{voice_info.file_path}"
        file = requests.get(url)
        with open ("voice.ogg", "wb") as voice_mess:
            voice_mess.write(file.content)
        convert_to_wav(ffmpeg, "voice.ogg")
        out_text = audio_recognition("voice.wav")
        bot.send_message(message.chat.id, get_weather(out_text.strip(), weather_api_token))
        bot.send_photo(message.chat.id, open("cond_icon.png", "rb"))

        os.remove("voice.wav")
        os.remove("cond_icon.png")
    except FileNotFoundError:
        bot.send_message(message.chat.id, "не распознал фразу")

bot.polling(none_stop=True)