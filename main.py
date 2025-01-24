import os
import speech_recognition as sr
import pyttsx3
import webbrowser
from youtube_search import YoutubeSearch  # Corrected import for YouTube search
import requests
from google.cloud import texttospeech  # Google Cloud Text-to-Speech
from google.cloud import dialogflow_v2 as dialogflow  # Dialogflow API
import pygame
import uuid  # For generating unique session IDs
import re  # To validate mathematical expressions
import sys  # To exit the program
import datetime
import pyjokes  # For jokes
import psutil  # For system status
import wikipedia  # For Wikipedia search
from pycaw.pycaw import AudioUtilities  # For system volume control

# Set the path for the Google Cloud service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\krish\Downloads\canvas-rampart-448807-h9-2b2f89fb0d1b.json"

# Initialize Pygame mixer and speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    # Initialize the Text-to-Speech client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code and the voice gender
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Set the audio file format
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request
    response = client.synthesize_speech(
        request={"input": synthesis_input, "voice": voice, "audio_config": audio_config}
    )

    # Save the response audio to a file
    with open("temp.mp3", "wb") as out:
        out.write(response.audio_content)

    # Initialize Pygame mixer
    pygame.mixer.init()

    # Load and play the MP3 file
    pygame.mixer.music.load('temp.mp3')
    pygame.mixer.music.play()

    # Wait until the sound is finished
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.unload()
    os.remove("temp.mp3")  # Remove the temporary file

def change_speech_volume(command):
    volume = engine.getProperty('volume')  # Get the current volume (0.0 to 1.0)
    
    if "increase volume" in command.lower():
        new_volume = min(volume + 0.1, 1.0)  # Increase volume by 0.1, but max is 1.0
        engine.setProperty('volume', new_volume)
        speak("Increasing volume.")
        
    elif "decrease volume" in command.lower():
        new_volume = max(volume - 0.1, 0.0)  # Decrease volume by 0.1, but min is 0.0
        engine.setProperty('volume', new_volume)
        speak("Decreasing volume.")

def change_system_volume(command):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        AudioUtilities.IID_IAudioEndpointVolume, 1, None)
    volume = interface.QueryInterface(AudioUtilities.IAudioEndpointVolume)
    
    current_volume = volume.GetMasterVolumeLevelScalar()  # Volume is between 0.0 and 1.0

    if "increase volume" in command.lower():
        new_volume = min(current_volume + 0.1, 1.0)  # Increase volume
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        speak("Increasing system volume.")
        
    elif "decrease volume" in command.lower():
        new_volume = max(current_volume - 0.1, 0.0)  # Decrease volume
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        speak("Decreasing system volume.")

def aiProcess(command):
    try:
        project_id = "canvas-rampart-448807"  # Replace with your Dialogflow project ID
        session_id = str(uuid.uuid4())  # Generate a unique session ID for each request
        language_code = "en"

        # Initialize Dialogflow client
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(project_id, session_id)

        text_input = dialogflow.TextInput(text=command, language_code=language_code)
        query_input = dialogflow.QueryInput(text_input)

        # Send the request to Dialogflow
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})

        # Return Dialogflow's response
        return response.query_result.fulfillment_text
    except Exception as e:
        print(f"Dialogflow error: {e}")
        return "I'm sorry, I couldn't process that request."

def search_and_play_song(song_name):
    # Search the song on YouTube using youtube-search-python
    results = YoutubeSearch(song_name, max_results=1).to_dict()  # Get the top search result
    if results:
        video_url = f"https://www.youtube.com{results[0]['url_suffix']}"
        webbrowser.open(video_url)  # Open the video URL in the browser
        speak(f"Playing {song_name} on YouTube")
    else:
        speak("Sorry, I couldn't find the song on YouTube.")

def solve_math_problem(command):
    try:
        # Removing any unwanted characters to avoid issues
        command = command.replace("minus", "-").replace("plus", "+").replace("times", "*").replace("divided", "/")
        
        # Validate that the command only contains valid characters for math (numbers, operators)
        if re.match(r'^[\d+\-*/.() ]+$', command):  # Only allow digits and operators
            result = str(eval(command))  # Use eval to evaluate the expression
            return f"The result is {result}"
        else:
            return "Sorry, I couldn't understand the math problem."
    except Exception as e:
        return "Sorry, there was an error solving that math problem."

def get_weather(city):
    try:
        api_key = "YOUR_OPENWEATHER_API_KEY"  # Replace with your OpenWeather API key
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        response = requests.get(url)
        data = response.json()

        if data["cod"] == "404":
            return "City not found."
        
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"] - 273.15  # Convert from Kelvin to Celsius
        return f"The weather in {city} is {weather} with a temperature of {temp:.2f}°C."
    except Exception as e:
        return "Sorry, I couldn't fetch the weather information."

def get_system_status():
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        battery = psutil.sensors_battery().percent
        return f"CPU Usage: {cpu}%, Memory Usage: {memory}%, Battery: {battery}%"
    except Exception as e:
        return "Sorry, I couldn't get the system status."

def tell_joke():
    joke = pyjokes.get_joke()
    return joke

def get_date_time():
    now = datetime.datetime.now()
    return f"Today's date is {now.strftime('%A, %B %d, %Y')}, and the time is {now.strftime('%I:%M %p')}."

def search_wikipedia(query):
    try:
        # Search Wikipedia and fetch the summary
        result = wikipedia.summary(query, sentences=2)  # Limit to 2 sentences
        return result
    except wikipedia.exceptions.DisambiguationError as e:
        # In case of ambiguity, return a message suggesting clarification
        return f"Your query was too broad. Here are some suggestions: {e.options}"
    except wikipedia.exceptions.HTTPTimeoutError:
        return "There was an issue reaching Wikipedia. Please try again later."
    except wikipedia.exceptions.RedirectError:
        return "It seems like the page has moved. Try another query."
    except wikipedia.exceptions.PageError:
        return "I couldn't find anything related to that topic on Wikipedia."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def processCommand(c):
    # Handle volume commands
    if "increase volume" in c.lower():
        change_speech_volume(c)
        change_system_volume(c)
        
    elif "decrease volume" in c.lower():
        change_speech_volume(c)
        change_system_volume(c)
    
    # Handle commands related to time
    elif "what is the time" in c.lower() or "what's the time" in c.lower():
        time = get_date_time()
        speak(f"The time is {time}")
    
    # Handle commands related to weather
    elif "what's the weather" in c.lower() or "what is the weather" in c.lower():
        city = c.lower().split("weather", 1)[1].strip()
        weather_info = get_weather(city)
        speak(weather_info)

    # Handle commands related to opening websites
    elif "open google" in c.lower():
        webbrowser.open("https://google.com")
    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
    elif "open instagram" in c.lower():
        webbrowser.open("https://instagram.com")
    elif "play" in c.lower():
        song = c.lower().split("play", 1)[1].strip()  # Extract song name after "play"
        search_and_play_song(song)  # Search and play the song
    elif "tell me a joke" in c.lower():
        joke = tell_joke()
        speak(joke)
    elif "what is system status" in c.lower():
        status = get_system_status()
        speak(status)
    elif "wikipedia" in c.lower():
        query = c.lower().split("wikipedia", 1)[1].strip()
        wikipedia_info = search_wikipedia(query)
        speak(wikipedia_info)
    # Handle math commands (addition, subtraction, multiplication, etc.)
    elif any(operator in c for operator in ["+", "-", "*", "/", "%", "(", ")"]):  # Check if math operator is in command
        result = solve_math_problem(c)
        speak(result)  # Speak the result of the math problem
    elif "shut down" in c.lower():
        speak("Shutting down...")
        sys.exit()  # Exit the program
    else:
        # Let Dialogflow handle the request
        output = aiProcess(c)
        speak(output)  # Speak the response

def listen_for_wake_word():
    """ Continuously listens for the wake word 'Jarvis' to activate the assistant. """
    while True:
        try:
            with sr.Microphone() as source:
                print("Listening for 'Jarvis'...")
                audio = recognizer.listen(source)
            word = recognizer.recognize_google(audio)
            if "jarvis" in word.lower():
                speak("Yes?")
                # Once 'Jarvis' is detected, start listening for the command
                with sr.Microphone() as source:
                    print("Listening for command...")
                    audio = recognizer.listen(source)
                    command = recognizer.recognize_google(audio)
                    processCommand(command)
        except sr.UnknownValueError:
            print("I didn't catch that. Please repeat.")
        except sr.RequestError as e:
            print(f"Speech Recognition error: {e}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    listen_for_wake_word()
