import vertexai
import requests
from google.cloud.aiplatform_v1 import FunctionCallingConfig
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool, ToolConfig,
)
from vertexai.preview.generative_models import ChatSession

project_id = "my-"

vertexai.init(project=project_id, location="us-central1")
get_current_weather_func = FunctionDeclaration(
        name="get_weather",
        description="Obtener información sobre el clima en una ubicación",
        parameters={
            "type": "object",
            "properties": {"ubicacion": {"type": "string", "description": "La ubicación de la que se obtendrá la información del clima."
                                                                          "Puede ser el nombre de una ciudad, pais o estado"
                                                                          "Por ejemplo: Lima, Peru"}},
            "required": ["ubicacion"],
        },
    )
get_info_func = FunctionDeclaration(
    name="get_info",
    description="Obtener información sobre Piero",
    parameters={
        "type": "object",
        "properties": {"nombre": {"type": "string", "description": "Nombre de la persona"}},
        "required": ["nombre"],
    },
)

def generate_text(prompt: str):
    model = GenerativeModel(
        # model_name="gemini-1.0-pro-001",
        model_name="gemini-1.5-pro-001",
        # system_instruction=["Responde en formato json",]
        # generation_config=GenerationConfig(temperature=0),
        # tools=[wikipedia_tool],
    )
    res = model.generate_content(prompt)
    return res

def generate_text_schema(prompt: str):
    model = GenerativeModel(
        # model_name="gemini-1.0-pro-001",
        model_name="gemini-1.5-pro-001",
        # system_instruction=["Responde en formato json",]
        # generation_config=GenerationConfig(temperature=0),
        # tools=[wikipedia_tool],
    )
    response_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "recipe_name": {
                    "type": "string",
                },
            },
            "required": ["recipe_name"],
        },
    }
    res = model.generate_content(
        prompt,
        generation_config=GenerationConfig(
            response_mime_type="application/json", response_schema=response_schema
        ),
    )
    return res

def get_current_weather(args)->dict:
    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key":".................",
        "q":args.get("ubicacion"),
    }
    try:
        response = requests.get(url, timeout=8,params=params) #timeout en segundos
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        return {"error": "No se pudo obtener el clima de la ubicación"}

def get_info_by_name(args)->dict:
    return {
        "description": "Piero es un estudiante de la UTP y tiene 22 años"
    }

#Solo llama a una función de varias que se pueden llamar
def generate_simple_text_with_function1(prompt: str):
    model = GenerativeModel(
        model_name="gemini-1.5-flash-001",
        # system_instruction="""
        #         """
    )
    user_prompt_content = Content(
        role="user",
        parts=[
            Part.from_text(prompt),
        ],
    )
    fun_tool = Tool(
        function_declarations=[get_current_weather_func,get_info_func],
    )
    #Retorna la json con la descripcion de lo que se uso
    # res = model.generate_content(
    #     prompt,
    #     generation_config=GenerationConfig(temperature=0),
    #     tools=[weather_tool],
    # )
    res = model.generate_content(
        user_prompt_content,
        generation_config=GenerationConfig(temperature=0),
        tools=[fun_tool],
    )
    print(res)

    function_handlers = {
        "get_weather": get_current_weather,
        "get_info": get_info_by_name,
    }
    for function_call in res.candidates[0].function_calls:
        print(function_call)
        function_name = function_call.name
        args = {key: value for key, value in function_call.args.items()}

        if function_name in function_handlers:

            api_response = function_handlers[function_name](args)
            print("response: {}".format(api_response))

            res = model.generate_content(
                [
                    user_prompt_content,  # User prompt(con o sin/Con Flash/Pro no se muestra la presentacion)
                    res.candidates[0].content,  # Function call response
                    Content(
                        parts=[
                            Part.from_function_response(
                                name=function_call.name,
                                response={"content": api_response},
                            ),
                        ],
                    ),
                ],
                tools=[fun_tool],
            )

            # Get the model response and print it
            print(res.text)

def generate_simple_text_with_function2(prompt:str):
    fun_tool = Tool(
        function_declarations=[get_current_weather_func, get_info_func],
    )

    model = GenerativeModel(
        model_name="gemini-1.5-flash-001",
        # system_instruction="""
        #
        #     """,
        generation_config=GenerationConfig(temperature=0),
        tools=[fun_tool],
    )
    chat = model.start_chat()

    res = chat.send_message(prompt)
    print(res)
    inicio = ""
    for part in res.candidates[0].content.parts:
         if part._raw_part._pb.WhichOneof("data") == "text":
             print(part.text)  # Imprime el texto de las partes con contenido "text"
             inicio += part.text
    function_handlers = {
        "get_weather": get_current_weather,
        "get_info": get_info_by_name,
    }
    for function_call in res.candidates[0].function_calls:
        print(function_call)
        function_name = function_call.name
        args = {key: value for key, value in function_call.args.items()}

        if function_name in function_handlers:
            api_response = function_handlers[function_name](args)
            print("response: {}".format(api_response))

            res = chat.send_message(
                Part.from_function_response(
                    name=function_name,
                    response={
                        "content": api_response,
                    },
                ),
            )

            # Get the model response and print it
            print(inicio+res.text)
            #print(res.text)


def generate_multiple_text_with_function1(prompt:str):
    model = GenerativeModel(
        model_name="gemini-1.5-flash-001",
        system_instruction = """
                   
                    # """,
    )
    user_prompt_content = Content(
        role="user",
        parts=[
            Part.from_text(prompt),
        ],
    )
    fun_tool = Tool(
        function_declarations=[get_current_weather_func, get_info_func],
    )
    # Retorna la json con la descripcion de lo que se uso
    # res = model.generate_content(
    #     prompt,
    #     generation_config=GenerationConfig(temperature=0),
    #     tools=[weather_tool],
    # )
    res = model.generate_content(
        user_prompt_content,
        generation_config=GenerationConfig(temperature=0),
        tools=[fun_tool],
    )
    print(res)

    function_handlers = {
        "get_weather": get_current_weather,
        "get_info": get_info_by_name,
    }
    # for part in res.candidates[0].content.parts:
    #     if part._raw_part._pb.WhichOneof("data") == "text":
    #         print(part.text)  # Imprime el texto de las partes con contenido "text"
    parts = []
    function_calls = res.candidates[0].function_calls
    if(function_calls):
        for function_call in res.candidates[0].function_calls:
            print(function_call)
            function_name = function_call.name
            args = {key: value for key, value in function_call.args.items()}

            if function_name in function_handlers:
                api_response = function_handlers[function_name](args)
                print("response: {}".format(api_response))
                parts.append(
                    Part.from_function_response(
                        name=function_call.name,
                        response={"content": api_response},
                    )
                )

        res = model.generate_content(
            [
                user_prompt_content,  # User prompt
                res.candidates[0].content,  # Function call response
                Content(
                    parts=parts
                ),
            ],
            tools=[fun_tool],
        )
        print(res.text)
    else:
        print(res.text)

def generate_parallel_text_with_function1(session:ChatSession ,prompt:str):
    fun_tool = Tool(
        function_declarations=[get_current_weather_func, get_info_func],
    )
    model = GenerativeModel(
        model_name="gemini-1.5-pro-001",
        generation_config=GenerationConfig(temperature=0),
        system_instruction="""
                Eres un asistente virtual que te ayudará a obtener información sobre el clima.
                """,
        tools=[fun_tool],
    )


    # Start a chat session
    if session is None:
        chat_session = model.start_chat()
    else:
        chat_session = session

    res = chat_session.send_message(
        prompt,
    )
    print("Primera respuesta")
    print(res)
    #print(res.text)
    function_calls = res.candidates[0].function_calls
    function_handlers = {
        "get_weather": get_current_weather,
        "get_info": get_info_by_name,
    }


    # if function_calls:
    #     msg = []
    #     parts = []
    #     for part in res.candidates[0].content.parts:
    #         #Si el contenido es una funcion
    #         if part._raw_part._pb.WhichOneof("data") == "function_call":
    #             function_name = part.function_call.name
    #             print("Se llamo: "+function_name)
    #             args = {key: value for key, value in part.function_call.args.items()}
    #             #Si la funcion  que se llamo esta en la lista de funciones
    #             if function_name in function_handlers:
    #                 api_response = function_handlers[function_name](args)
    #                 print("response: {}".format(api_response))
    #                 parts.append(
    #                     Part.from_function_response(
    #                         name=function_name,
    #                         response={"content": api_response},
    #                     )
    #                 )
    #         #Si el contenido de la parte es texto
    #         if part._raw_part._pb.WhichOneof("data") == "text":
    #             # print(part.text)  # Imprime el texto de las partes con contenido "text"
    #             # parts.append(
    #             #     Part.from_text(part.text),
    #             #)
    #             msg.append(part.text)



        # Return the API response to Gemini
        # tool_config = ToolConfig(
        #      function_calling_config = ToolConfig.FunctionCallingConfig(
        #             mode=ToolConfig.FunctionCallingConfig.Mode.NONE
        #      ),
        # )
    if function_calls:
        parts = []
        for function_call in res.candidates[0].function_calls:
            print(function_call)
            function_name = function_call.name
            args = {key: value for key, value in function_call.args.items()}

            if function_name in function_handlers:
                api_response = function_handlers[function_name](args)
                print("response: {}".format(api_response))
                parts.append(
                    Part.from_function_response(
                        name=function_call.name,
                        response={"content": api_response},
                    )
                )
        responses = chat_session.send_message(
            parts,
            stream=True,
           # tools=[fun_tool],
        )
        text_response = []
        for chunk in responses:
            text_response.append(chunk.text)
            #Imprimir sin saltos de linea
            print(chunk.text, end="")
        #print("".join(text_response))
        # responses = chat_session.send_message(
        #     parts,
        #     stream=True
        # )
        # print(responses)
        # text_response = []
        # for chunk in responses:
        #     text_response.append(chunk.text)
        # print("".join(text_response))
        #print(response.text) #Esto solo funciona cuando la respuesta es un solo part con un texto
        # for part in response.candidates[0].content.parts:
        #     if part._raw_part._pb.WhichOneof("data") == "text":
        #         print(part.text)  # Imprime el texto de las partes con contenido "text"
    else:
        print(res.text)





#gemini-1.5-flash-001 consume mucho
#gemini-1.5-pro-001 consume mucho
#gemini-1.0-pro-001 solo texto consume poco


#Solo una pregunta God
#print(generate_simple_text_with_function1("Presentate y despues dime el clima en Lima Peru"))
#Solo una pregunta con sesion God
#print(generate_simple_text_with_function2("Presentate, cuentame un chiste y despues dime el clima detallado en Lima Peru, al final despidete"))
#Varias preguntas(no paralelas) meh
#print(generate_multiple_text_with_function1("Dime quien es Piero Rodriguez Diaz y busca el clima en Lima Peru"))
fun_tool = Tool(
        function_declarations=[get_current_weather_func, get_info_func],
    )
global_model = GenerativeModel(
        model_name="gemini-1.5-flash-001",
        system_instruction = """
                    Eres un asistente virtual que te ayudará a obtener información completa y detallada sobre el clima.
                    """,
        generation_config=GenerationConfig(temperature=0),
        tools=[fun_tool],
    )
global_session = global_model.start_chat()
print(generate_parallel_text_with_function1(global_session,"cual es el clima en Paris?"))
#print(generate_parallel_text_with_function1(global_session,"Que te pregunte anteriormente ? "))





# def generate_text_with_function(prompt: str):
#     get_current_weather_func = FunctionDeclaration(
#         name="get_weather",
#         description="Obtiene el clima actual de una ubicación",
#         parameters={
#             "type": "object",
#             "properties": {"ubicacion": {"type": "string", "description": "Nombre de la ubicación"}},
#             "required": ["ubicacion"],
#         },
#     )
#     weather_tool = Tool(
#         function_declarations=[get_current_weather_func, ],
#     )
#     model = GenerativeModel(
#         # model_name="gemini-1.0-pro-001",
#         model_name="gemini-1.5-pro-001",
#         # system_instruction=["Responde en formato json",]
#         generation_config=GenerationConfig(temperature=0),
#         tools=[weather_tool],
#     )
#     chat = model.start_chat()
#     # user_prompt_content = Content(
#     #     role="user",
#     #     parts=[
#     #         Part.from_text(prompt),
#     #     ],
#     # )
#
#     # Retorna la json con la descripcion de lo que se uso
#     # res = model.generate_content(
#     #     prompt,
#     #     generation_config=GenerationConfig(temperature=0),
#     #     tools=[weather_tool],
#     # )
#     res = chat.send_message(
#         prompt,
#         # generation_config=GenerationConfig(temperature=0),
#         # tools=[weather_tool],
#     )
#     print(res)
#     # Se verifica si la respuesta contiene la llamada a la función get_weather
#     # parts = []
#     for function_call in res.candidates[0].function_calls:
#
#         print("Se llamo a: " + function_call.name)
#         if function_call.name == "get_weather":
#             ubicacion = function_call.args["ubicacion"]  # Extraer la ubicación
#             weather = get_current_weather(ubicacion)
#             #
#         else:
#             error = {
#                 "error": "Error en la Api, no se pudo obtener el clima de la ubicación",
#             }
#         res = model.generate_content(
#             [
#                 prompt,  # User prompt
#                 res.candidates[0].content,
#                 Content(
#                     parts=[
#                         Part.from_function_response(
#                             name=function_call.name,
#                             response={
#                                 "content": weather,
#                             },
#                         )
#                     ],
#                 ),
#             ],
#             tools=[weather_tool],
#         )
#         # Esto es para que la respuesta contenga la llamada a la función get_weather y se pueda obtener el clima
#
#     return res



"""
from vertexai.generative_models import GenerativeModel, ChatSession

# TODO(developer): Update and un-comment below lines
# project_id = "PROJECT_ID"
# location = "us-central1"
vertexai.init(project=project_id, location=location)


# TODO developer - override these parameters as needed:
parameters = {
    "temperature": temperature,  # Temperature controls the degree of randomness in token selection.
    "max_output_tokens": 64,  # Token limit determines the maximum amount of text output.
}


model = GenerativeModel(model_name="gemini-1.0-pro-002")
chat = model.start_chat()

def get_chat_response(chat: ChatSession, prompt: str) -> str:
    text_response = []
    responses = chat.send_message(prompt, stream=True)
    for chunk in responses:
        text_response.append(chunk.text)
    return "".join(text_response)

prompt = "Hello."
print(get_chat_response(chat, prompt))

prompt = "What are all the colors in a rainbow?"
print(get_chat_response(chat, prompt))

prompt = "Why does it appear when it rains?"
print(get_chat_response(chat, prompt))
"""

"""
#https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output
response_schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "to_discard": {"type": "INTEGER"},
            "subcategory": {"type": "STRING"},
            "safe_handling": {"type": "INTEGER"},
            "item_category": {
                "type": "STRING",
                "enum": [
                    "clothing",
                    "winter apparel",
                    "specialized apparel",
                    "furniture",
                    "decor",
                    "tableware",
                    "cookware",
                    "toys",
                ],
            },
            "for_resale": {"type": "INTEGER"},
            "condition": {
                "type": "STRING",
                "enum": [
                    "new in package",
                    "like new",
                    "gently used",
                    "used",
                    "damaged",
                    "soiled",
                ],
            },
        },
    },
}
"""

"""
#Multimodal
from vertexai.generative_models import GenerativeModel, Part

# TODO(developer): Update project_id and location
vertexai.init(project=PROJECT_ID, location="us-central1")

# Load images from Cloud Storage URI
image_file1 = Part.from_uri(
    "gs://cloud-samples-data/vertex-ai/llm/prompts/landmark1.png",
    mime_type="image/png",
)
image_file2 = Part.from_uri(
    "gs://cloud-samples-data/vertex-ai/llm/prompts/landmark2.png",
    mime_type="image/png",
)
image_file3 = Part.from_uri(
    "gs://cloud-samples-data/vertex-ai/llm/prompts/landmark3.png",
    mime_type="image/png",
)

model = GenerativeModel("gemini-1.5-flash-001")
response = model.generate_content(
    [
        image_file1,
        "city: Rome, Landmark: the Colosseum",
        image_file2,
        "city: Beijing, Landmark: Forbidden City",
        image_file3,
    ]
)
print(response.text)





from vertexai.generative_models import GenerativeModel, Part

# TODO(developer): Update and un-comment below lines
# project_id = "PROJECT_ID"

vertexai.init(project=project_id, location="us-central1")

model = GenerativeModel(model_name="gemini-1.5-flash-001")

prompt = "
Provide a description of the video.
The description should also contain anything important which people say in the video.
"

video_file_uri = "gs://cloud-samples-data/generative-ai/video/pixel8.mp4"
video_file = Part.from_uri(video_file_uri, mime_type="video/mp4")

contents = [video_file, prompt]

response = model.generate_content(contents)
print(response.text)





from vertexai.generative_models import GenerativeModel, Part

# TODO(developer): Update and un-comment below lines
# project_id = "PROJECT_ID"

vertexai.init(project=project_id, location="us-central1")

model = GenerativeModel("gemini-1.5-flash-001")

prompt = ""
You are a very professional document summarization specialist.
Please summarize the given document.
""

pdf_file_uri = "gs://cloud-samples-data/generative-ai/pdf/2403.05530.pdf"
pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
contents = [pdf_file, prompt]

response = model.generate_content(contents)
print(response.text)
"""


#Filtros de seguridad para que no obtener respuestas no deseadas
# https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/configure-safety-filters

#Entrenar la ia https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning?hl=es-419#python