import os

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


def quickstart_v2() -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file.
    Args:
        audio_file (str): Path to the local audio file to be transcribed.
    Returns:
        cloud_speech.RecognizeResponse: The response from the recognize request, containing
        the transcription results
    """
    # Reads a file as bytes
    audio_file = "audio/ges.wav"
    with open(audio_file, "rb") as audio_file:
        audio_content = audio_file.read()

    # Instantiates a client
    client = SpeechClient()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["es-US"],
        model="long",
        features=cloud_speech.RecognitionFeatures(
            # Enable automatic punctuation
            enable_automatic_punctuation=True,
        ),
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/my-a/locations/global/recognizers/_",
        config=config,
        content=audio_content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)
    print(response)
    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")

    return response

if __name__ == "__main__":
    quickstart_v2()


#Nota: Solo puedes usar la función de idiomas alternativos con los modelos long, short y telephony. Para