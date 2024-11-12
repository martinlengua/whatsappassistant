import logging
import time
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
import threading
import queue
from dotenv import load_dotenv
from assist import Assistant

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carga las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configura tus credenciales usando variables de entorno
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")
client = Client(account_sid, auth_token)

# Diccionario para almacenar los asistentes y contextos por número de teléfono
user_assistants = {}
user_threads = {}
message_queue = queue.Queue()

# Inicializar el asistente con datos y un `thread_id` único para cada usuario
def get_assistant_for_user(user_id):
    """
    Obtiene o crea un asistente para un usuario si no existe, asignando un `thread_id` único.
    """
    if user_id not in user_assistants:
        # Genera un `thread_id` único usando el número de teléfono del usuario o similar
        unique_thread_id = f"thread_{user_id}"

        # Crear un nuevo asistente y guardar el `thread_id`
        assistant = Assistant(
            api_key=os.getenv("OPENAI_API_KEY"),
            assistant_id=os.getenv("ASSISTANT_ID"),
            thread_id=unique_thread_id
        )
        
        user_assistants[user_id] = assistant
        user_threads[user_id] = unique_thread_id
    return user_assistants[user_id]

def generate_response(incoming_message, user_id):
    """
    Genera una respuesta con OpenAI usando el `thread_id` del usuario para mantener el contexto.
    """
    logging.info(f"Received message from {user_id}: {incoming_message}")

    assistant = get_assistant_for_user(user_id)
    thread_id = user_threads[user_id]

    # Usar `thread_id` específico del usuario para mantener su contexto
    respuesta = assistant.ask_question_memory(incoming_message)

    logging.info(f"Generated response for {user_id}: {respuesta}")
    return respuesta

def send_response(reply, from_number):
    """
    Envía la respuesta de vuelta al número de WhatsApp del remitente.
    """
    logging.info(f"Sending response to {from_number}: {reply}")
    client.messages.create(
        body=reply,
        from_=twilio_number,
        to=from_number
    )

def process_message_queue():
    """
    Procesa los mensajes en la cola, esperando 5 segundos solo si la cola está vacía.
    """
    while True:
        try:
            from_number, incoming_message = message_queue.get(timeout=5)
            reply = generate_response(incoming_message, from_number)
            send_response(reply, from_number)
            message_queue.task_done()
        except queue.Empty:
            logging.info("No hay mensajes en la cola. Esperando 5 segundos...")
            time.sleep(5)

# Crear un hilo separado para procesar la cola de mensajes
threading.Thread(target=process_message_queue, daemon=True).start()

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_message = request.form.get("Body", "")
    from_number = request.form.get("From", "")

    logging.info(f"Incoming message from {from_number}: {incoming_message}")
    message_queue.put((from_number, incoming_message))
    response = MessagingResponse()
    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
