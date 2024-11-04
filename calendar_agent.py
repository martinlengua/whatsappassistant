import msal
import requests
import os

class CalendarAgent:
    def __init__(self, client_id, client_secret, tenant_id, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = ["User.Read", "Calendars.ReadWrite"]
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
    
    def get_auth_url(self):
        """Genera la URL de autorización de Microsoft"""
        return self.msal_app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )

    def acquire_token(self, code):
        """Intercambia el código de autorización por un token de acceso"""
        result = self.msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Error al adquirir el token: {result.get('error')}, {result.get('error_description')}")

    def list_events(self, access_token):
        """Lista los eventos en el calendario del usuario"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://graph.microsoft.com/v1.0/me/calendar/events", headers=headers)
        if response.status_code == 200:
            events = response.json().get("value", [])
            if not events:
                return "No hay eventos próximos."
            events_list = "\n".join([f"Evento: {event['subject']}, Inicio: {event['start']['dateTime']}, Fin: {event['end']['dateTime']}" for event in events])
            return events_list
        else:
            return f"Error al listar eventos: {response.status_code}, {response.text}"

    def create_event(self, access_token, subject, content, start_time, end_time, attendees_emails=[]):
        """Crea un evento en el calendario del usuario"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        event = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": content
            },
            "start": {
                "dateTime": start_time,
                "timeZone": "America/Lima"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "America/Lima"
            },
            "attendees": [
                {"emailAddress": {"address": email, "name": email.split('@')[0]}, "type": "required"}
                for email in attendees_emails
            ]
        }
        
        response = requests.post("https://graph.microsoft.com/v1.0/me/calendar/events", headers=headers, json=event)
        if response.status_code == 201:
            return f"Evento creado exitosamente: {response.json().get('webLink')}"
        else:
            return f"Error al crear evento: {response.status_code}, {response.text}"
