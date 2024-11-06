from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import openai
from assist import Assistant
import subprocess
#librerias para TTS
#from openai import OpenAI
#import vosk
#import sounddevice as sd
import queue
import json
import time
import assist
import os
import re

app = Flask(__name__)

# Configure your Twilio credentials
account_sid = "AC37522f855bedd37c5c96bc2e2d4cf5fb"
auth_token = "f1c431bfb8b4ff6b2cecbec87c7e4424"
twilio_number = "whatsapp:+51997720677"
client = Client(account_sid, auth_token)

# Inicializar el asistente con tus datos
assistant = Assistant(api_key="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", assistant_id="asst_63ynZRFDr1YrSYgpJTXVKWXW", thread_id="thread_oyuWJQph9E1oaIHFrvDT7plu")

def generate_response(incoming_message):
    """
    Uses OpenAI to generate a response based on the received message.
    """

    respuesta = assistant.ask_question_memory(incoming_message)
    print(respuesta)
    return respuesta;

def send_response(reply, from_number):
    """
    Sends the response back to the sender's WhatsApp number.
    """
    client.messages.create(
        body=reply,
        from_=twilio_number,
        to=from_number
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_message = request.form.get("Body", "")
    from_number = request.form.get("From", "")

    # Generate a response based on the incoming message
    reply = generate_response(incoming_message)

    # Send the response back to the user
    send_response(reply, from_number)

    # Respond with TwiML to keep the conversation active
    response = MessagingResponse()
    response.message(reply)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)