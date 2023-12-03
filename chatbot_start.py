import os
import subprocess
import json
import openai
import time
import pyaudio
import wave
import audioop
import sms
import threading
import RPi.GPIO as GPIO
from dotenv import load_dotenv


help_flag = False


def emergency_situation():
    print('비상상황')

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(33, GPIO.OUT)                 # 모터
    GPIO.setup(5, GPIO.OUT)                  # 비상 경광등
    GPIO.output(33, GPIO.HIGH)
    GPIO.output(5, GPIO.LOW)

    time.sleep(30)


def start_alam():
    os.system("mpg123 /home/pi/CodeFair_Partner_ChatBot/sound/start.mp3") 


def start_gpio():
    global button_pin
    button_pin = 32
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def motor_start():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(33, GPIO.OUT)                 # 모터              
    GPIO.output(33, GPIO.LOW)
    time.sleep(30)
    

def motor_stop():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(33, GPIO.OUT)                 # 모터              
    GPIO.output(33, GPIO.HIGH)
    
    time.sleep(30)


def warn_alam():
    for x in range(4):
        os.system('mpg123 /home/pi/CodeFair_Partner_ChatBot/sound/warn.mp3')
        time.sleep(2)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(5, GPIO.OUT)                 # 비상 경광등
    GPIO.output(5, GPIO.LOW)


def ment_rec():             # 카카오i클라우드 'Text to Speech API'의 음성합성 기능을 이용해서 스피커 시작 멘트를 만듬
    voice = """ curl -v \
              -H "x-api-key: 91ce013c97b577b8f4c8d354e675b883" \
              -H "Content-Type: application/xml" \
              -H "X-TTS-Engine: deep" \
              -d '<speak>
                  <voice name="Summer">Protective AI Blender의 청각 안전 장치입니다. 모터작동 준비가 완료되었습니다.</voice>
                  </speak>' \
              https://94a32363-bfe6-4c43-8cd5-0ecb45a376e6.api.kr-central-1.kakaoi.io/ai/text-to-speech/d7504f19ae0e4390b7c790dc2e2d4226 > ./sound/start.mp3 && mpg123 ./sound/start.mp3 """
    os.system(voice)


def mayday_119():                          # Naver SMS API를 이용해서 119에 문자 메시지 신고
    sms.send_sms(119)
    os.system("mpg123 /home/pi/CodeFair_Partner_ChatBot/sound/success.mp3")
    print('119 신고')
    return


def voice_rec():   
    po = pyaudio.PyAudio()                               # 녹음 기능을 위한 pyaudio 초기화
    for index in range(po.get_device_count()):
        desc = po.get_device_info_by_index(index)
        # if desc["name"] == "record":
        print("DEVICE: %s  INDEX:  %s  RATE:  %s " % (desc["name"], index, int(desc["defaultSampleRate"])))

    FORMAT = pyaudio.paInt16
    CHANNELS = 1                                      # 모노 음성
    RATE = 44100                                      # 전송률
    CHUNK = 640                                       # 전송 단위 크기
    RECORD_SECONDS = 7                                # 녹음 시간
    WAVE_OUTPUT_FILENAME = "/home/pi/CodeFair_Partner_ChatBot/sound/question.wav"       # 녹음 생성 오디오 파일

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    sound_volume = 2000

    os.system("mpg123 /home/pi/CodeFair_Partner_ChatBot/sound/rec.mp3")  # 음성 녹음 시작 안내 메시지
    print("---음성 녹음 시작---")

    while True:
        if GPIO.input(32) == GPIO.HIGH:
            break
        data = stream.read(CHUNK)
        rms = audioop.rms(data, 2)
        if rms > sound_volume:                 # 마이크에 기준 볼륨보다 큰 소리가 들어오면 녹음 작동
            frames.append(data)
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            data = stream.read(CHUNK)
            rms = audioop.rms(data, 2)
            if rms < 1500:                     # 큰 소리가 들어오지 않으면 녹음 종료
                break
            else:
                continue

    print("---음성 녹음 완료---")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')        # question.wav 파일 생성
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    time.sleep(0.1)


def mayday_voice_rec():   
    po = pyaudio.PyAudio()                               # 녹음 기능을 위한 pyaudio 초기화
    for index in range(po.get_device_count()):
        desc = po.get_device_info_by_index(index)
        # if desc["name"] == "record":
        print("DEVICE: %s  INDEX:  %s  RATE:  %s " % (desc["name"], index, int(desc["defaultSampleRate"])))

    FORMAT = pyaudio.paInt16
    CHANNELS = 1                                      # 모노 음성
    RATE = 44100                                      # 전송률
    CHUNK = 640                                       # 전송 단위 크기
    RECORD_SECONDS = 7                                # 녹음 시간
    WAVE_OUTPUT_FILENAME = "/home/pi/CodeFair_Partner_ChatBot/sound/question.wav"       # 녹음 생성 오디오 파일

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    sound_volume = 2000

    print("---음성 녹음 시작---")

    while True:
        if GPIO.input(32) == GPIO.LOW:
            break
        data = stream.read(CHUNK)
        rms = audioop.rms(data, 2)
        if rms > sound_volume:                 # 마이크에 기준 볼륨보다 큰 소리가 들어오면 녹음 작동
            frames.append(data)
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            data = stream.read(CHUNK)
            rms = audioop.rms(data, 2)
            if rms < 1500:                     # 큰 소리가 들어오지 않으면 녹음 종료
                break
            else:
                continue

    print("---음성 녹음 완료---")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')        # question.wav 파일 생성
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    time.sleep(0.1)

def mayday_speak():
    global help_flag
    if GPIO.input(button_pin) == GPIO.LOW:
        return
    load_dotenv()
    openai.organization = "org-oMb8n1ArLu6XkrsXxXNg9hQQ"                    # OpenAI API를 사용하기 위한 키값들 초기화
    openai.api_key = os.getenv("OPENAI_API_KEY")                            # .env 파일에 작성한 API 키 가져오기
    openai.Model.list()

    for cmd in [""" curl https://api.openai.com/v1/audio/transcriptions \
                  -H "Authorization: Bearer $OPENAI_API_KEY" \
                  -H "Content-Type: multipart/form-data" \
                  -F file="@/home/pi/CodeFair_Partner_ChatBot/sound/question.wav" \
                  -F model="whisper-1" """]:                                         # OpenAI Speech to text API에 질문 파일인 question.wav 파일 전송 후 결과 값 수신

        words = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()     # 결과 값(음성을 텍스트로 바꾼 값)을 json으로 되돌려 받은 후 질문 문자열만 추출
        json_list = json.loads(words)
        speech_text = json_list["text"]
        print(speech_text)

    if '도와줘' in speech_text or '구해줘' in speech_text or '살려줘' in speech_text:
        threading.Thread(target=emergency_situation).start()
        help_flag = True
        mayday_119()
        threading.Thread(target=warn_alam).start()   


def chat_gpt_speak():
    if GPIO.input(button_pin) == GPIO.HIGH:
        return
    load_dotenv()
    openai.organization = "org-oMb8n1ArLu6XkrsXxXNg9hQQ"                    # OpenAI API를 사용하기 위한 키값들 초기화
    openai.api_key = os.getenv("OPENAI_API_KEY")                            # .env 파일에 작성한 API 키 가져오기
    openai.Model.list()

    for cmd in [""" curl https://api.openai.com/v1/audio/transcriptions \
                  -H "Authorization: Bearer $OPENAI_API_KEY" \
                  -H "Content-Type: multipart/form-data" \
                  -F file="@/home/pi/CodeFair_Partner_ChatBot/sound/question.wav" \
                  -F model="whisper-1" """]:                                         # OpenAI Speech to text API에 질문 파일인 question.wav 파일 전송 후 결과 값 수신

        words = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()     # 결과 값(음성을 텍스트로 바꾼 값)을 json으로 되돌려 받은 후 질문 문자열만 추출
        json_list = json.loads(words)
        speech_text = json_list["text"]
        print(speech_text)

    conversation.append({"role": "user", "content": speech_text})       # 구조 요청이 아닐 경우 ChatGPT에게 질문함
    response = openai.ChatCompletion.create(
        model="gpt-4",                                                  # ChatGPT 버전이 최근 gpt-3-turbo에서 gpt-4로 업그레이드 됨
        messages=conversation
    )

    answer = response.choices[0]["message"]["content"].strip()         # 문자열로 응답을 받음
    print(answer)
    voice = """ curl -v \
                  -H "x-api-key: 91ce013c97b577b8f4c8d354e675b883" \
                  -H "Content-Type: application/xml" \
                  -H "X-TTS-Engine: deep" \
                  -d '<speak>
                      <voice name="Nora">{0}</voice>
                      </speak>' \
                  https://94a32363-bfe6-4c43-8cd5-0ecb45a376e6.api.kr-central-1.kakaoi.io/ai/text-to-speech/d7504f19ae0e4390b7c790dc2e2d4226 > /home/pi/CodeFair_Partner_ChatBot/sound/answer.mp3 && mpg123 /home/pi/CodeFair_Partner_ChatBot/sound/answer.mp3 """.format(answer)
    os.system(voice)   # 응답받은 문자열을 음성파일(answer.mp3)로 바꾸기 위해서 카카오i클라우드 'Text to Speech API'의 음성합성 기능을 이용해서 'answer.mp3' 로 변환해서 수신한 후, 음성 재생함

    conversation.append({"role": "assistant", "content": response['choices'][0]['message']['content']})  # ChatGPT가 답변 후 재질문 받는 기능을 위한 코드


if __name__ == "__main__":
    threading.Thread(target=start_alam).start()     # 스피커 시작 멘트
    time.sleep(8)
    threading.Thread(target=start_gpio).start()
    time.sleep(3)

    conversation = [{"role": "system", "content": "You are a helpful assistant."}]      # ChatGPT system 초기화
    time.sleep(10)
    while True:
        if GPIO.input(button_pin) == GPIO.LOW:
            threading.Thread(target=motor_stop).start()           
            voice_rec()
            chat_gpt_speak()
        else:
            if not help_flag:
                threading.Thread(target=motor_start).start()
            else:
                threading.Thread(target=motor_stop).start()
            mayday_voice_rec()
            mayday_speak()
            
