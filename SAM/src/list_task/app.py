import boto3
import os

try:
    from common.http import decode_next_token, encode_next_token, json_response, parse_limit
except ModuleNotFoundError:
    from src.common.http import decode_next_token, encode_next_token, json_response, parse_limit


def get_table():
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(os.environ.get('TABLE_NAME', 'Tasks-${Stage}'))


def lambda_handler(event, context):
    """
    Lists tasks from DynamoDB with bounded pagination.

    Returns:
        200: A page of tasks and a next_token when more results exist.
    """
    query_params = event.get('queryStringParameters') or {}
    limit, error_response = parse_limit(query_params.get('limit'))
    if error_response:
        return error_response

    exclusive_start_key, error_response = decode_next_token(query_params.get('next_token'))
    if error_response:
        return error_response

    scan_args = {'Limit': limit}
    if exclusive_start_key:
        scan_args['ExclusiveStartKey'] = exclusive_start_key

    response = get_table().scan(**scan_args)
    items = response.get('Items', [])
    next_token = encode_next_token(response.get('LastEvaluatedKey'))

    return json_response(200, {
        'items': items,
        'next_token': next_token
    })
