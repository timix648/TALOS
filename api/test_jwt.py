"""
Test JWT authentication with GitHub API
"""
import time
import jwt
import httpx

# Load key
key_data = open('C:/Users/hp/Downloads/Talos/api/talos-private-key.pem', 'rb').read()

# CRITICAL: App ID must be an integer, not a string for some JWT libraries
app_id = 2751497  # Integer, not string!

now = int(time.time())
payload = {
    'iat': now - 60,
    'exp': now + (9 * 60),
    'iss': app_id
}

token = jwt.encode(payload, key_data, algorithm='RS256')

# Decode to see what we're sending
decoded = jwt.decode(token, options={'verify_signature': False})
print('JWT Claims:', decoded)
print()

# Make the actual request
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}

resp = httpx.get('https://api.github.com/app', headers=headers)
print(f'Status: {resp.status_code}')
print(f'Response: {resp.text[:500]}')
