import pyttsx3
import speech_recognition as sr
import pyaudio
import wave
import threading
import mysql.connector

class VoiceEmailSystem:

    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voices', self.voices[0])
        self.engine.setProperty('rate', 130)
        self.engine.setProperty('volume',10.0)

        self.recognizer = sr.Recognizer()

        # Connect to the MySQL database
        self.conn = mysql.connector.connect(
            host='localhost',  # Replace with your MySQL host
            user='root',  # Replace with your MySQL username
            password='Sam@9818',  # Replace with your MySQL password
            database='mail_db',
            port='3306'  # Replace with your MySQL database name
        )
        self.cursor = self.conn.cursor()

    def speak(self, message):
        self.engine.say(message)
        self.engine.runAndWait()

    def recognize_speech(self):
        with sr.Microphone() as source:
            self.recognizer.pause_threshold = 0.5
            self.recognizer.energy_threshold = 300
            print("Listening...")
            audio = self.recognizer.listen(source)

            try:
                print("Recognizing...")
                query = self.recognizer.recognize_google(audio, language='en-in').lower().replace(" ", "").replace(
                    "attherate", "@")
                print(query)
                return query
            except sr.UnknownValueError:
                self.speak("Sorry, I couldn't understand. Please try again.")
                return None

    def record_and_save_audio(self, duration, output_filename, prompt_message):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        audio = pyaudio.PyAudio()

        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=1024)

        print(f"{prompt_message} ({duration} seconds)")

        frames = []
        is_recording = True

        def stop_recording():
            nonlocal is_recording
            is_recording = False

        stop_thread = threading.Timer(duration, stop_recording)
        stop_thread.start()

        while is_recording:
            data = stream.read(1024)
            frames.append(data)

        stop_thread.cancel()
        print("Finished recording.")

        stream.stop_stream()
        stream.close()
        audio.terminate()

        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

        print(f"Audio saved as {output_filename}")

    def capture_user_data(self):
        email_id = None
        while email_id is None:
            self.speak("Please say your email ID.")
            email_id = self.recognize_speech()
            print(email_id)

            # Confirm the email ID by spelling it out
            self.speak(f"Did you say {email_id}? Please say 'yes' or 'no' to confirm.")
            confirmation = self.recognize_speech()

            while confirmation not in ["yes", "no"]:
                self.speak("Please say 'yes' or 'no' to confirm your email ID.")
                confirmation = self.recognize_speech()


            if confirmation == "no":
                email_id = None  # Reset email_id if the user didn't confirm
            elif confirmation == "yes":
                break

        password = None
        while password is None:
            self.speak("Please say your email password.")
            password = self.recognize_speech()
            print(password)
            # Confirm the email password by spelling it out
            self.speak(f"Did you say {password}? Please say 'ok' or 'no' to confirm.")
            confirmation = self.recognize_speech()

            while confirmation not in ["ok", "no"]:
                self.speak("Please say 'ok' or 'no' to confirm your email password.")
                confirmation = self.recognize_speech()

            if confirmation == "no":
                password = None  # Reset email_id if the user didn't confirm
            elif confirmation == "ok":
                break

            # You can add a similar confirmation step for the password if needed

        audio_sections = []
        for i in range(3):
            output_filename = f"audio_{i + 1}.wav"

            if i == 0:
                prompt_message = "Please say 'HI GMAIL, THIS IS MY RECORDING'"
                self.speak(prompt_message)
            elif i == 1:
                prompt_message = "Please say 'this email system is voice-based'"
                self.speak(prompt_message)
            else:
                prompt_message = "Please say 'I am signing in this system'"
                self.speak(prompt_message)

            self.record_and_save_audio(5, output_filename, prompt_message)
            audio_sections.append(output_filename)

        return email_id, password, audio_sections

    def store_user_data_in_db(self, email_id, password, audio_sections):
        insert_query = "INSERT INTO user_data (email_id, password, audio_section_1, audio_section_2, audio_section_3) VALUES (%s, %s, %s, %s, %s)"
        cursor = self.conn.cursor()
        try:
            # Insert user data into the MySQL database using the modified query
            cursor.execute(insert_query, (email_id, password, audio_sections[0], audio_sections[1], audio_sections[2]))
            self.conn.commit()
            print("Data saved to the database.")

        except mysql.connector.Error as e:
            print("Database error:", e)

        finally:
            # Close the cursor and database connection
            cursor.close()
            self.conn.close()

    def close_database_connection(self):
        self.conn.close()


if __name__ == "__main__":
    email_system = VoiceEmailSystem()
    email_id, password, audio_sections = email_system.capture_user_data()
    email_system.store_user_data_in_db(email_id, password, audio_sections)
    email_system.close_database_connection()
