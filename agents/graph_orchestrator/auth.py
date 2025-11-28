"""
Módulo de autenticação com Keycloak
Gerencia login, validação de token JWT e cookies seguros
"""

import os
import requests
from functools import wraps
from flask import request, jsonify, redirect, url_for
import jwt
from jwt import PyJWKClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Keycloak
KEYCLOAK_SERVER_URL = f"https://{os.getenv('KEYCLOAK_HOSTNAME')}"
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'ezpocket')
KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'ezpocket-client')
KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET')

# URLs do Keycloak
TOKEN_URL = f"{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
USERINFO_URL = f"{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
JWKS_URL = f"{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
LOGOUT_URL = f"{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout"


def authenticate_user(username: str, password: str) -> dict:
    """
    Autentica usuário no Keycloak e retorna os tokens
    
    Args:
        username: Nome de usuário
        password: Senha
    
    Returns:
        dict com access_token, refresh_token, expires_in, etc.
    
    Raises:
        Exception se autenticação falhar
    """
    try:
        payload = {
            'client_id': KEYCLOAK_CLIENT_ID,
            'client_secret': KEYCLOAK_CLIENT_SECRET,
            'username': username,
            'password': password,
            'grant_type': 'password'
        }
        
        print(f"[AUTH] Tentando autenticar usuário: {username}")
        print(f"[AUTH] URL: {TOKEN_URL}")
        print(f"[AUTH] Client ID: {KEYCLOAK_CLIENT_ID}")
        
        response = requests.post(TOKEN_URL, data=payload, timeout=10)
        
        print(f"[AUTH] Status: {response.status_code}")
        print(f"[AUTH] Response: {response.text[:500]}")
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            error_msg = error_data.get('error_description', 'Credenciais inválidas')
            print(f"[AUTH] Erro: {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTH] Exceção: {str(e)}")
        raise Exception(f"Erro ao conectar com Keycloak: {str(e)}")


def refresh_access_token(refresh_token: str) -> dict:
    """
    Renova o access token usando o refresh token
    
    Args:
        refresh_token: Token de refresh
    
    Returns:
        dict com novo access_token, refresh_token, etc.
    """
    try:
        payload = {
            'client_id': KEYCLOAK_CLIENT_ID,
            'client_secret': KEYCLOAK_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(TOKEN_URL, data=payload, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Token de refresh inválido ou expirado")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao renovar token: {str(e)}")


def verify_token(token: str) -> dict:
    """
    Verifica e decodifica o JWT token do Keycloak
    
    Args:
        token: JWT access token
    
    Returns:
        dict com dados do token decodificado (username, email, roles, etc.)
    
    Raises:
        Exception se token inválido
    """
    try:
        # Buscar chaves públicas do Keycloak
        jwks_client = PyJWKClient(JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decodificar e verificar o token
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="account",
            options={"verify_exp": True}
        )
        
        return decoded
        
    except jwt.ExpiredSignatureError:
        raise Exception("Token expirado")
    except jwt.InvalidTokenError as e:
        raise Exception(f"Token inválido: {str(e)}")
    except Exception as e:
        raise Exception(f"Erro ao verificar token: {str(e)}")


def get_user_info(access_token: str) -> dict:
    """
    Busca informações do usuário usando o access token
    
    Args:
        access_token: JWT access token
    
    Returns:
        dict com informações do usuário (sub, preferred_username, email, etc.)
    """
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        print(f"[AUTH] Buscando user info em: {USERINFO_URL}")
        response = requests.get(USERINFO_URL, headers=headers, timeout=10)
        
        print(f"[AUTH] User info status: {response.status_code}")
        print(f"[AUTH] User info response: {response.text[:200]}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao buscar informações do usuário (status {response.status_code}): {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTH] Exceção ao buscar user info: {str(e)}")
        raise Exception(f"Erro ao conectar com Keycloak: {str(e)}")


def logout_user(refresh_token: str):
    """
    Faz logout do usuário no Keycloak (invalida tokens)
    
    Args:
        refresh_token: Token de refresh para invalidar
    """
    try:
        payload = {
            'client_id': KEYCLOAK_CLIENT_ID,
            'client_secret': KEYCLOAK_CLIENT_SECRET,
            'refresh_token': refresh_token
        }
        
        requests.post(LOGOUT_URL, data=payload, timeout=10)
        # Não verifica resposta porque logout sempre retorna 204
        
    except Exception:
        pass  # Ignora erros de logout


def token_required(f):
    """
    Decorator para proteger rotas que requerem autenticação
    Verifica se há um token JWT válido nos cookies
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 401
        
        try:
            decoded = verify_token(token)
            # Adiciona dados do usuário ao request
            request.user = decoded
            return f(*args, **kwargs)
            
        except Exception as e:
            # Tentar renovar token usando refresh_token
            refresh_token = request.cookies.get('refresh_token')
            if refresh_token:
                try:
                    tokens = refresh_access_token(refresh_token)
                    # Token renovado com sucesso
                    request.user = verify_token(tokens['access_token'])
                    # Nota: você precisará setar os novos cookies na resposta
                    return f(*args, **kwargs)
                except:
                    pass
            
            return jsonify({'error': f'Token inválido: {str(e)}'}), 401
    
    return decorated


def get_username_from_token(token: str) -> str:
    """
    Extrai o username do token JWT
    
    Args:
        token: JWT access token
    
    Returns:
        str com o username
    """
    try:
        decoded = verify_token(token)
        return decoded.get('preferred_username', decoded.get('sub', 'unknown'))
    except:
        return 'unknown'
