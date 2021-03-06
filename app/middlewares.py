from flask import Response, request, abort, g
from flask_restplus import abort
from app.utils import msg
from app.routes_need_login_config import routes
from werkzeug.security import generate_password_hash
import jwt
from app import cache
import config



def verify_route():
    """
    Verify if the route is in a list of routes that need have the authorization header
    """
    for route in routes:
        if route[0] == str(request.url_rule) and request.method in route[1] and 'Authorization' not in request.headers:
            abort(403, 'Authorization header missing')


# TODO: Implementar a validação dos modelos de entrada

def verify_token():
    """
    Verify if the token is valid, not expired and not blacklisted
    """
    if 'Authorization' in request.headers:
        if request.headers['Authorization'] in cache.blacklisted_tokens:
            abort(403, 'Error: invalid token')
        try:
            payload = jwt.decode(request.headers['Authorization'], config.SECRET_KEY)
            g.current_user = payload['id_user']
        except jwt.ExpiredSignatureError:
            abort(403, 'Error: token expired')
        except jwt.DecodeError:
            abort(403, 'Error: invalid token')


def encrypt_password():
    """
    Verify if the route is for password reset or user create, then encrypts the password.
    """
    if request.json is None or not 'password' in request.json:
        return
    if str(request.url_rule) == '/auth/user/' and request.method == 'POST' \
    or str(request.url_rule) == '/auth/user/resetpassword/' and request.method == 'PUT':
        request.json['password'] = generate_password_hash(request.json['password'])

def set_cors_header(response):
    """
    Set the headers needed to cross origin access.
    
    :param response: flask.Response
    :return: flask.Response
    """
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, api_key, Authorization, x-requested-with, Total-Count, Total-Pages, Error-Message'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Max-Age'] = '1800'
    return response