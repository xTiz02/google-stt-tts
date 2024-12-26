import wave

from google.cloud import speech



def run_quickstart() -> speech.RecognizeResponse:
    # Instantiates a client
    client = speech.SpeechClient()

    # The name of the audio file to transcribe
    file = "audio/gen3.wav"
    with wave.open(file, "rb") as audio_file: # rb = read binary
        data = audio_file.readframes(audio_file.getnframes())
        framerate = audio_file.getframerate()
        channels = audio_file.getnchannels()
    print("Audio file loaded")

    audio = speech.RecognitionAudio(content=data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, # LINEAR16 = 16-bit signed little-endian samples
        sample_rate_hertz=framerate, #Miara la conf del audio de entrada(microfono)
        #enable_automatic_punctuation=True,
        language_code="en-US", # El idioma del audio
        #model="default" # El modelo de lenguaje a usar
    )
    print("Config:"+str(config))

    # Detecta el idioma del audio
    response = client.recognize(config=config, audio=audio)
    print("Audio file recognized")
    print(response)
    for result in response.results:
        #print(f"Result: {result}")
        print(f"Transcript: {result.alternatives[0].transcript}")

if __name__ == "__main__":
    run_quickstart()
# model: latest_long, latest_short, telephony o telephony_short

#Asincrono
# def transcribe_file(audio_file: str) -> speech.RecognizeResponse:
#     """Transcribe the given audio file asynchronously.
#     Args:
#         audio_file (str): Path to the local audio file to be transcribed.
#     """
#     client = speech.SpeechClient()
#
#     with open(audio_file, "rb") as file:
#         audio_content = file.read()
#
#     # Note that transcription is limited to a 60 seconds local audio file.
#     # Use a GCS file for audio longer than 1 minute.
#     audio = speech.RecognitionAudio(content=audio_content)
#
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=16000,
#         language_code="en-US",
#     )
#
#
#     operation = client.long_running_recognize(config=config, audio=audio)
#
#     print("Waiting for operation to complete...")
#     response = operation.result(timeout=90)
#
#     # Each result is for a consecutive portion of the audio. Iterate through
#     # them to get the transcripts for the entire audio file.
#     for result in response.results:
#         # The first alternative is the most likely one for this portion.
#         print(f"Transcript: {result.alternatives[0].transcript}")
#         print(f"Confidence: {result.alternatives[0].confidence}")
#
#     return response