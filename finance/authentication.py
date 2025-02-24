from firebase_admin import auth as firebase_auth, exceptions as firebase_exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Retrieve the Authorization header from the request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None  # Return None for unauthenticated requests

        # Extract the Firebase ID token from the header
        id_token = auth_header.split(' ')[1]

        try:
            # Verify the Firebase ID token using Firebase Admin SDK
            decoded_token = firebase_auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email')

            # Get or create a user in Django associated with this Firebase UID
            user, created = User.objects.get_or_create(username=uid, defaults={'email': email})

            # Return the user instance and None for authentication
            return (user, None)
        except firebase_exceptions.InvalidIdTokenError:
            raise AuthenticationFailed('Invalid Firebase token')
        except firebase_exceptions.ExpiredIdTokenError:
            raise AuthenticationFailed('Firebase token has expired')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
