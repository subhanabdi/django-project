from rest_framework_simplejwt.tokens import RefreshToken
from users.models import MyUser
import uuid
from Crypto.Cipher import AES
import base64


def generate_invite_token(email, user_type):
    # Create a temporary user instance with a unique identifier
    temp_user = MyUser(email=email, username=str(uuid.uuid4()))
    refresh = RefreshToken.for_user(temp_user)
    refresh['email'] = email
    refresh['user_type'] = user_type
    return str(refresh.access_token)

def decrypt_password(encrypted_password, secret_key):
    key_bytes = bytes(secret_key, 'utf-8')
    while len(key_bytes) < 32:
        key_bytes += b' '  # Pad key to 32 bytes

    cipher = AES.new(key_bytes, AES.MODE_EAX, nonce=b'0'*16)
    decrypted_password = cipher.decrypt(base64.b64decode(encrypted_password))

    return decrypted_password.decode('utf-8')
