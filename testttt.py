import jwt
import requests

# Use your full access token here
token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ0Q2xkQjEwdV9PMDJvdURpZnE0U052U3ZfUmhlVXlZUTctQzVMd2Nhd2V3In0.eyJleHAiOjE3NDA0MDI2MTAsImlhdCI6MTc0MDQwMjMxMCwianRpIjoiNmRhYjE3NjAtYTg1NS00M2QzLTgwMjUtMmQ4MTUwMDUzODg2IiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL3JlYWxtcy9tb2JpbGUtYXBwIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjhjNjg3YjkxLTIwMjYtNGJlOS05Mjk2LTM1YjlkMTI1NjM2MCIsInR5cCI6IkJlYXJlciIsImF6cCI6Im1vYmlsZS1jbGllbnQiLCJzZXNzaW9uX3N0YXRlIjoiYjFmNWI3ZDgtNjI2Zi00YWEyLWE1NzItNmFhZDZmYmEzZWY4IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwODEiLCIqIiwiLyoiLCJleHA6Ly8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLW1vYmlsZS1hcHAiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwic2lkIjoiYjFmNWI3ZDgtNjI2Zi00YWEyLWE1NzItNmFhZDZmYmEzZWY4IiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJkYXlhbmUifQ.D7Fnd4ih9y5mk9br8YMhADiAvRLTMiZd_S7aExxuwE7aHj6tT0xb2sVTGcyjks6aagmdnJz_Qtx09kWwFfapn26aR6XPqIY3k1U7hYmjc6zuD74dZQpSqTw5Jx7mjVOYcgQcuMW1vMWGFV4qCGctHKS8zhFbCh2Ij3YCCne_SquCX-exgzxaYZ4yT_3FtEu5MToUiBVMsh381zPeE5kEXod3Igd85R6ajTeFTvJ9MaVdwVRrIomk7wTSbib7MxpbmWLfdU1JG6fKTyJgWGIGglRyNvQ0VwOnfbakZJ3zLJj6sDIeanM4yAuT9mLKMXa6ZWr8kx67h5hEI6KqmdN7sA"

# Fetch the public key from Keycloak
key_url = "http://keycloak_server:8080/realms/mobile-app/protocol/openid-connect/certs"
key_response = requests.get(key_url, timeout=5)
key_response.raise_for_status()
jwks = key_response.json()

if "keys" in jwks:
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwks["keys"][0])
    print("Using Public Key:", public_key)

    # Try to decode the token with public key
    try:
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Disable audience check temporarily
        )
        print("✅ Decoded Token:", decoded_token)
    except jwt.ExpiredSignatureError:
        print("❌ Token has expired.")
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid Token: {e}")