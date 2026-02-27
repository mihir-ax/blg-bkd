import secrets
import string


def generate_api_key() -> str:
    """Generate a secure API key like sk-xxxxxxxxxxxxxxxxxxxxxx"""
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(32))
    return f"sk-{token}"
