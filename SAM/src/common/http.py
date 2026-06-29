import base64
import json


JSON_HEADERS = {
    "Content-Type": "application/json",
}


def json_response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS,
        "body": json.dumps(payload),
    }


def parse_json_body(event):
    body = event.get("body") or "{}"

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        parsed = json.loads(body)
    except (TypeError, ValueError):
        return None, json_response(400, {"error": "Request body must be valid JSON"})

    if not isinstance(parsed, dict):
        return None, json_response(400, {"error": "Request body must be a JSON object"})

    return parsed, None


def encode_next_token(last_evaluated_key):
    if not last_evaluated_key:
        return None

    encoded = json.dumps(last_evaluated_key).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("utf-8")


def decode_next_token(token):
    if not token:
        return None, None

    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        return json.loads(decoded), None
    except (TypeError, ValueError, json.JSONDecodeError):
        return None, json_response(400, {"error": "next_token is invalid"})


def parse_limit(raw_limit, default=25, maximum=100):
    if raw_limit in (None, ""):
        return default, None

    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return None, json_response(400, {"error": "limit must be a positive integer"})

    if limit < 1 or limit > maximum:
        return None, json_response(400, {"error": f"limit must be between 1 and {maximum}"})

    return limit, None
