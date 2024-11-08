import logging
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
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

def generate_response(incoming_message):
    """
    Uses OpenAI to generate a response based on the received message.
    """
    logging.info(f"Received message: {incoming_message}")
    respuesta = assistant.ask_question_memory(incoming_message)
    logging.info(f"Generated response: {respuesta}")
    return respuesta

def send_response(reply, from_number):
    """
    Sends the response back to the sender's WhatsApp number.
    """
    logging.info(f"Sending response to {from_number}: {reply}")
    client.messages.create(
        body=reply,
        from_=twilio_number,
        to=from_number
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_message = request.form.get("Body", "")
    from_number = request.form.get("From", "")

    # Log incoming message and sender info
    logging.info(f"Incoming message from {from_number}: {incoming_message}")

    # Generate a response based on the incoming message
    reply = generate_response(incoming_message)

    # # Send the response back to the user
    # send_response(reply, from_number)

    # Respond with TwiML to keep the conversation active
    response = MessagingResponse()
    response.message(reply)

    # # Log response sent back to Twilio
    # logging.info(f"Response sent back to Twilio: {reply}")
    
    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
