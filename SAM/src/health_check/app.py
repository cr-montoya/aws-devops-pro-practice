try:
    from common.http import json_response
except ModuleNotFoundError:
    from src.common.http import json_response


def lambda_handler(event, context):
    """Returns a lightweight application health response."""

    return json_response(200, {
        "message": "All systems operational",
    })
