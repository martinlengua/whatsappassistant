import requests

def test_webhook():
    # URL for the locally hosted webhook (adjust port if necessary)
    url = "http://127.0.0.1:5000/webhook"

    # Mock data simulating a Twilio WhatsApp message
    data = {
        "Body": "Hello, this is a test message!",
        "From": "whatsapp:+1234567890"  # Mock sender number
    }

    try:
        # Send POST request to the webhook
        response = requests.post(url, data=data)
        
        # Print response from the webhook
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)

    except requests.exceptions.RequestException as e:
        print("Error sending request:", e)

if __name__ == "__main__":
    test_webhook()