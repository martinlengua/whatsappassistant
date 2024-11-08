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

# Inicializar el asistente con los datos desde las variables de entorno
assistant = Assistant(
    api_key=os.getenv("OPENAI_API_KEY"),
    assistant_id=os.getenv("ASSISTANT_ID"),
    thread_id=os.getenv("THREAD_ID")
)

# Crear una cola para manejar los mensajes entrantes
message_queue = queue.Queue()

def generate_response(incoming_message):
    """
    Usa OpenAI para generar una respuesta basada en el mensaje recibido.
    """
    logging.info(f"Received message: {incoming_message}")
    respuesta = assistant.ask_question_memory(incoming_message)
    logging.info(f"Generated response: {respuesta}")
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
            # Esperar hasta que haya un mensaje en la cola o el tiempo de espera se complete
            from_number, incoming_message = message_queue.get(timeout=5)

            # Generar la respuesta para el mensaje inmediatamente
            reply = generate_response(incoming_message)
            
            # Enviar la respuesta de vuelta al usuario
            send_response(reply, from_number)
            
            # Marcar el mensaje como procesado
            message_queue.task_done()

        except queue.Empty:
            # Si la cola está vacía, esperar 5 segundos antes de revisar nuevamente
            logging.info("No hay mensajes en la cola. Esperando 5 segundos...")
            time.sleep(5)

# Crear un hilo separado para procesar la cola de mensajes
threading.Thread(target=process_message_queue, daemon=True).start()

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_message = request.form.get("Body", "")
    from_number = request.form.get("From", "")

    # Log incoming message and sender info
    logging.info(f"Incoming message from {from_number}: {incoming_message}")

    # Añadir el mensaje a la cola para ser procesado
    message_queue.put((from_number, incoming_message))

    # Responder inmediatamente para confirmar recepción a Twilio
    response = MessagingResponse()
    response.message("Tu mensaje ha sido recibido. Procesaremos tu solicitud en breve.")

    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)