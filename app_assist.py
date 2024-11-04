from flask import Flask, request, redirect, session, url_for
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from calendar_agent import CalendarAgent
from assist import Assistant

# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializar el asistente con tus datos
assistant = Assistant(api_key="sk-56aCXbxoKJISheRAbhByS8NQwypKygNH6E9gtt3UjkT3BlbkFJC9ebpcTzARCTl-tS_zbCUA2UVzH5MOIM3Ue_jLP04A", assistant_id="asst_63ynZRFDr1YrSYgpJTXVKWXW", thread_id="thread_oyuWJQph9E1oaIHFrvDT7plu")

# Configuración de Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")
client = Client(account_sid, auth_token)

# Configuración de la aplicación registrada en Azure
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = "http://localhost:5000/redirect"  # Cambiar esto a tu dominio en producción

# Instanciar el agente de calendario
calendar_agent = CalendarAgent(CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI)

# Endpoint para autenticación con Microsoft
@app.route("/auth")
def auth():
    auth_url = calendar_agent.get_auth_url()
    return redirect(auth_url)

# Endpoint de redirección después de autenticarse con Microsoft
@app.route("/redirect")
def redirect_login():
    code = request.args.get('code')
    if not code:
        return "Error: no se recibió el código de autorización", 400

    try:
        token = calendar_agent.acquire_token(code)
        session['access_token'] = token
        return "Autenticación exitosa. Puedes proceder a realizar solicitudes usando el token."
    except Exception as e:
        return str(e), 400

# Webhook para recibir mensajes de WhatsApp
@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_message = request.form.get("Body", "").strip().lower()
    from_number = request.form.get("From", "")

    # Iniciar una respuesta de Twilio
    response = MessagingResponse()

    # Lógica para diferentes comandos
    if incoming_message == "listar eventos":
        token = session.get('access_token')
        if token:
            events_list = calendar_agent.list_events(token)
            response.message(events_list)
        else:
            response.message("Por favor, autentícate primero visitando: /auth")

    elif incoming_message.startswith("crear evento"):
        # Extract the details from the message (example format: "crear evento subject, content, start_time, end_time, attendee1, attendee2")
        try:
            _, subject, content, start_time, end_time, *attendees = incoming_message.split(',')
            token = session.get('access_token')
            if token:
                create_status = calendar_agent.create_event(token, subject.strip(), content.strip(), start_time.strip(), end_time.strip(), [attendee.strip() for attendee in attendees])
                response.message(create_status)
            else:
                response.message("Por favor, autentícate primero visitando: /auth")
        except ValueError:
            response.message("Por favor, proporciona los detalles en el formato: 'crear evento asunto, contenido, inicio, fin, email1, email2...'")

    else:
        response.message("Hola! Puedes usar los siguientes comandos:\n- 'listar eventos': Para listar tus próximos eventos.\n- 'crear evento asunto, contenido, inicio, fin, email1, email2...': Para crear un nuevo evento.")

    return str(response)

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(debug=True, port=5000)
