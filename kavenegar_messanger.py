from kavenegar import KavenegarAPI, APIException, HTTPException
import requests
import logging
import environ


# ==========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = environ.Env()
env.read_env()


def message_sender(phone_number, message, retries=2):
    api_key = env.str("KAVENEGAR_API_KEY", default=None)
    sender_number = env.str("KAVENEGAR_SENDER", default=None)

    print(f"DEBUG: API Key: {api_key}") 
    print(f"DEBUG: Sender: {sender_number}")  
    print(f"DEBUG: Phone: {phone_number}") 

    if not api_key or not sender_number:
        logger.error("Missing Kavenegar API key or sender number in environment.")
        return None

    params = {
        "sender": sender_number,
        "receptor": phone_number,
        "message": f"{message}"
    }

    print(f"DEBUG: Params: {params}")  

    for attempt in range(1, retries + 1):
        try:
            print(f"DEBUG: Attempt {attempt}") 
            api = KavenegarAPI(api_key)
            response = api.sms_send(params)
            
            print(f"DEBUG: Response: {response}")  

            status = response.get("return", {}).get("status")
            message_id = response.get("entries", [{}])[0].get("messageid")

            logger.info(f"SMS sent to {phone_number}. Status: {status}, Message ID: {message_id}, Message: {message}")
            return response

        except (APIException, HTTPException) as error:
            print(f"DEBUG: Kavenegar error: {error}")  
            logger.warning(f"Attempt {attempt} failed to send SMS: {error}", exc_info=True)
        except Exception as error:
            print(f"DEBUG: Unexpected error: {error}")  
            logger.warning(f"Attempt {attempt} failed with unexpected error: {error}", exc_info=True)

    logger.error(f"All {retries} attempts to send SMS to {phone_number} failed.")
    return None


# ==========================================================

# Example of Kavenegar's response

"""{
  "return": {
    "status": 200,
    "message": "Message sent successfully"
  },
  "entries": [
    {
      "messageid": "123456789",
      "status": 1,
      "statustext": "Sent",
      "sender": "10004346",
      "receptor": "09123456789",
      "date": 1630000000
    }
  ]
}
"""