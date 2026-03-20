import http.client
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone_number: str, otp_code: str) -> bool:
    """Send OTP code via SMS.ir bulk API.

    Returns True on success, False on failure.
    """
    api_key = getattr(settings, "SMS_IR_API_KEY", "")
    line_number = getattr(settings, "SMS_IR_LINE_NUMBER", 300000000000)

    if not api_key:
        logger.error("SMS_IR_API_KEY is not configured.")
        return False

    message_text = f"کد تایید شما: {otp_code}"

    payload = json.dumps({
        "lineNumber": line_number,
        "messageText": message_text,
        "mobiles": [phone_number],
        "sendDateTime": None,
    })

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    try:
        conn = http.client.HTTPSConnection("api.sms.ir")
        conn.request("POST", "/v1/send/bulk", payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        conn.close()

        response = json.loads(data)
        status_code = response.get("status")

        if res.status == 200 and status_code == 1:
            logger.info("SMS sent successfully to %s", phone_number)
            return True

        logger.warning(
            "SMS.ir returned unexpected response: HTTP %s, body: %s",
            res.status,
            data,
        )
        return False

    except Exception:
        logger.exception("Failed to send SMS to %s", phone_number)
        return False
