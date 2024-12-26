#Google cloud text to speech API
# Imports the Google Cloud client library
from tkinter.font import names

from google.cloud import texttospeech
# Instantiates a client
client = texttospeech.TextToSpeechClient()

text_example = ("En esta página, se muestra cómo comenzar a usar las bibliotecas cliente de Cloud para la API de Text-to-Speech. "
                "Las bibliotecas cliente facilitan el acceso a las APIs de Google Cloud mediante un lenguaje compatible.")
# Se da un texto y se genera un archivo de audio
synthesis_input = texttospeech.SynthesisInput(text=text_example)

# Se selecciona el idioma y el genero de la voz
# Se puede cambiar el idioma y el genero de la voz
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US", name="es-ES-Standard-F"
)

# Selección del tipo de archivo de audio
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    effects_profile_id=["handset-class-device"],
    speaking_rate=1, #velocidad de la voz
    pitch=0, #tono de voz
)

# Realizar la solicitud de texto a voz en la entrada de texto con los parámetros de voz
# y el tipo de archivo de audio seleccionados
response = client.synthesize_speech(
    input=synthesis_input,
    voice=voice,
    audio_config=audio_config
)

# The response's audio_content is binary.
with open("audio/output.mp3", "wb") as out:
    # Write the response to the output file.
    out.write(response.audio_content)
    print('Audio content written to file "output.mp3"')
