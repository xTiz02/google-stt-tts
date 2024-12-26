import itertools
import pyaudio
from google.cloud import texttospeech

def run_streaming_tts_quickstart(user_input: str):
    """Synthesizes and plays speech from a stream of input text."""
    client = texttospeech.TextToSpeechClient()

    streaming_config = texttospeech.StreamingSynthesizeConfig(
        voice=texttospeech.VoiceSelectionParams(
            name="en-US-Journey-F", language_code="en-US"
        ),
    )

    def synthesize_and_play(prompt: str = user_input):
        """Handles the synthesis and playback for a single input."""
        # Configuración inicial de la solicitud
        config_request = texttospeech.StreamingSynthesizeRequest(
            streaming_config=streaming_config,
        )

        # Generador de solicitudes
        def request_generator():
            yield config_request
            yield texttospeech.StreamingSynthesizeRequest(
                input=texttospeech.StreamingSynthesisInput(text=prompt)
            )

        # Llamada a la API de streaming
        streaming_responses = client.streaming_synthesize(request_generator())

        p = pyaudio.PyAudio()

        # Open a stream
        stream = p.open(format=pyaudio.paInt16,  # Assuming 16-bit audio. Adjust if needed.
                        channels=1,  # Assuming mono audio. Adjust if needed.
                        rate=24000,
                        output=True)

        try:
            for idx, response in enumerate(streaming_responses):
                audio_content = response.audio_content  # Datos de audio
                print(f"Fragmento {idx + 1} - Tamaño de audio en bytes: {len(audio_content)}")
                if audio_content:
                    # Play the audio chunk
                    stream.write(audio_content)
        except Exception as e:
            print(f"Error procesando audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    while True:
        # user_input = input("Escribe una frase para que sea hablada (o 'salir' para terminar): ")
        # if user_input.lower() == "salir":
        #     print("Saliendo del programa.")
        #     break
        synthesize_and_play(user_input)
        #terminar
        break

if __name__ == "__main__":
    run_streaming_tts_quickstart("Hola, soy una prueba de texto a voz en tiempo real. ")
