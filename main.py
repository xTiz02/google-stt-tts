import queue
import re
import sys
import wave

import vertexai
from google.cloud import speech
from google.cloud import texttospeech
import pyaudio
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool, ToolConfig,
)


project_id = ""

vertexai.init(project=project_id, location="us-central1")
model = GenerativeModel(
        # model_name="gemini-1.0-pro-001",
        model_name="gemini-1.5-pro-001",
        # system_instruction="""
        #
        #     """
        # generation_config=GenerationConfig(temperature=0),
        # tools=[wikipedia_tool],
    )
chat = model.start_chat()
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self: object, rate: int =RATE , chunk: int=CHUNK) -> None:
        """The audio -- and generator -- is guaranteed to be on the main thread."""
        self._rate = rate
        self._chunk = chunk
        self.pause = False
        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self: object) -> object:
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(
        self: object,
        type: object,
        value: object,
        traceback: object,
    ) -> None:
        """Closes the stream, regardless of whether the connection was lost or not."""
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self: object,
        in_data: object,
        frame_count: int,
        time_info: object,
        status_flags: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
            in_data: The audio data as a bytes object
            frame_count: The number of frames captured
            time_info: The time information
            status_flags: The status flags

        Returns:
            The audio data as a bytes object
        """
        if not self.pause:
            self._buff.put(in_data)
        return None, pyaudio.paContinue

    def pause_stream(self):
        """Pausar la captura del micrófono."""
        self.pause = True

    def resume_stream(self):
        """Reanudar la captura del micrófono."""
        self.pause = False

    def generator(self: object) -> object:
        """Generates audio chunks from the stream of audio data in chunks.

        Args:
            self: The MicrophoneStream object

        Returns:
            A generator that outputs audio chunks.
        """
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def synthesize_and_play(prompt: str, config_request,client):
    """Handles the synthesis and playback for a single input."""
    #Llamar a la ai:
    res = chat.send_message(prompt)
    print("Respuesta de la IA: "+str(res.text))
    # Generador de solicitudes
    def request_generator(text):
        yield config_request
        # palabras = prompt.split(" ")
        # Dividir las palabras en bloques de 5
        # bloques = [palabras[i:i + 5] for i in range(0, len(palabras), 5)]
        # oraciones = [" ".join(bloque).capitalize() + "." for bloque in bloques]
        # for oracion in oraciones:
        yield texttospeech.StreamingSynthesizeRequest(
            input=texttospeech.StreamingSynthesisInput(text=text)
        )

    # Llamada a la API de streaming
    streaming_responses = client.streaming_synthesize(request_generator(res.text))

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
        print("Finalizando stream de voz")



def listen_print_loop(responses: object, config_request_tts, client_tts,mic_stream)->str:
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.

    Args:
        responses: List of server responses

    Returns:
        The transcribed text.
    """
    num_chars_printed = 0
    transcript = ""
    for response in responses:
        print("Respuesta del stream stt: "+str(response))
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        #print(result)
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            print("Se está escribiendo..")
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)
            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(cerrar voz|salir voz)\b", transcript, re.I):
                print("Saliendo..")
                break
            num_chars_printed = 0
            try:
                # Pausa la grabación antes de sintetizar y reproducir
                mic_stream.pause_stream()
                synthesize_and_play(transcript, config_request_tts, client_tts)
            except Exception as e:
                print(f"Error reproduciendo audio: {e}")
            finally:
                # Reanuda la grabación después de reproducir el audio
                mic_stream.resume_stream()



def main() -> None:
    """Transcribe Text to audio file."""
    client_tts = texttospeech.TextToSpeechClient()

    streaming_config_tts = texttospeech.StreamingSynthesizeConfig(
        voice=texttospeech.VoiceSelectionParams(
            name="es-US-Journey-F", language_code="es-US"
        ),
    )
    # Configuración inicial de la solicitud
    config_request_tts = texttospeech.StreamingSynthesizeRequest(
        streaming_config=streaming_config_tts,

    )
    """Transcribe speech from audio file."""
    client_stt = speech.SpeechClient()
    config_stt = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
        alternative_language_codes=["es-US"],
        #audio_channel_count=2,
        enable_automatic_punctuation=True,
        #enable_separate_recognition_per_channel=True,
        #enable_word_time_offsets=True,
        #model="default",
    )
    streaming_config_stt = speech.StreamingRecognitionConfig(
        config=config_stt, interim_results=True
    )


    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        print("Listening..")
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client_stt.streaming_recognize(streaming_config_stt, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses, config_request_tts, client_tts,stream)


if __name__ == "__main__":
    main()