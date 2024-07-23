from rest_framework_simplejwt.tokens import RefreshToken
from users.models import MyUser
import uuid

def generate_invite_token(email):
    # Create a temporary user instance with a unique identifier
    temp_user = MyUser(email=email, username=str(uuid.uuid4()))
    refresh = RefreshToken.for_user(temp_user)
    return str(refresh.access_token)
