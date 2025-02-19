import json
import logging

import requests
from flask import request, redirect

from env_vars import SLACK_CLIENT_ID, SLACK_REDIRECT_URI, SLACK_CLIENT_SECRET
from flask import jsonify, Blueprint

from persistance.db_utils import get_account_for_user_email
from route_handlers.slack_route_handler import handle_oauth_callback, handle_event_callback

slack_blueprint = Blueprint('slack_router', __name__)

logger = logging.getLogger(__name__)


@slack_blueprint.route('/install', methods=['GET'])
def install():
    # Redirect users to Slack's OAuth URL
    user_email = request.args.get('user_email', None)
    state = json.dumps({'user_email': user_email})
    return redirect(
        f'https://slack.com/oauth/v2/authorize?client_id={SLACK_CLIENT_ID}&scope=app_mentions:read,channels:history,channels:read,chat:write,commands,groups:history,groups:read,mpim:read,files:write&user_scope=&redirect_uri={SLACK_REDIRECT_URI}&state={state}')


@slack_blueprint.route('/oauth_redirect', methods=['GET'])
def oauth_redirect():
    # Extract the authorization code from the request
    code = request.args.get('code')
    state = request.args.get('state')
    state = json.loads(state)
    accounts = get_account_for_user_email(state['user_email'])
    if not accounts:
        logger.error(
            f"Error while fetching bot OAuth token with error: No account found for user_email: {state['user_email']}")
        return jsonify(
            {'success': False, 'message': 'Alert Summary Bot Installation failed: Kenobi Account not found'})
    if not code:
        logger.error(f"Error while fetching bot OAuth token with error: No code found")
        return jsonify({'success': False, 'message': 'Alert Summary Bot Installation failed with error: No code found'})
    # Exchange the authorization code for an OAuth token
    response = requests.post('https://slack.com/api/oauth.v2.access', {
        'client_id': SLACK_CLIENT_ID,
        'client_secret': SLACK_CLIENT_SECRET,
        'code': code,
        'redirect_uri': SLACK_REDIRECT_URI
    })

    # Parse the response
    data = response.json()
    account_id = accounts[0].account_id
    # Extract the OAuth token
    if 'ok' in data:
        response = handle_oauth_callback(account_id, data)
        if response:
            return jsonify({'success': True, 'message': 'Alert Summary Bot Installation successful'})
        else:
            return jsonify({'success': False, 'message': 'Alert Summary Bot Installation failed'})
    else:
        logger.error(f"Error while fetching bot OAuth token with response: {data}")
        return jsonify({'success': False, 'message': 'Alert Summary Bot Installation failed', 'data': data})


@slack_blueprint.route('/events', methods=['POST'])
def handle_slack_events():
    request_data = request.data.decode('utf-8')
    if request_data:
        data = json.loads(request_data)
        if data['type'] == 'url_verification':
            return jsonify({'challenge': data['challenge']})
        elif data['type'] == 'event_callback':
            response = handle_event_callback(data)
            if response:
                return jsonify({'success': True, 'message': 'Alert Summary Bot Event Handling Successful'})
            else:
                return jsonify({'success': False, 'message': 'Alert Summary Bot Event Handling failed'})
        else:
            logger.error(f"Error while fetching bot OAuth token with response: {data}")
            return jsonify({'success': False, 'message': 'Alert Summary Bot Event Handling failed'})
    return jsonify({'success': False, 'message': 'Alert Summary Bot Event Handling failed'})

