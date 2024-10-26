from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import openai
from assist import Assistant
import subprocess
from openai import OpenAI
import vosk
import sounddevice as sd
import queue
import json
import time
import assist
import os
import re
from assist import Assistant

app = Flask(__name__)

# Configure your Twilio credentials
account_sid = "AC37522f855bedd37c5c96bc2e2d4cf5fb"
auth_token = "97f635861d48bb46b18e82835c30052d"
twilio_number = "whatsapp:+14155238886"
client = Client(account_sid, auth_token)

# Inicializar el asistente con tus datos
assistant = Assistant(api_key="sk-6MUmqpO0imVR4lex7CR33-Kn4CWsfvs0kZpalj3EzDT3BlbkFJqPpjnzD7RvjdbEffrIh6L15Bvkymj2CyP3lX1cBfQA", assistant_id="asst_63ynZRFDr1YrSYgpJTXVKWXW", thread_id="thread_oyuWJQph9E1oaIHFrvDT7plu")

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
    return str(response)

if __name__ == "__main__":
    app.run(debug=True)