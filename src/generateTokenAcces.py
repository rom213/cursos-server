from google.oauth2 import service_account
import google.auth.transport.requests
import threading

# Token inicial (puede ser un token de prueba o vacío)
access_token = "ya29.c.c0ASRK0GYZJ2jJUrUi1oIUBVH7Z_cDHJsQNB0M_WGETPhcC8IvsQcqgeHWhaFXmf8EuXafWHl-_8s_wEy6D4hgwo7qQmoxTBuTNjww1ChZGup-2a2EfwECMIgPsHDuGq2y4af9xvYUyGFmivQXyexeClH-Itm7Ko-tnN7RMfEc8QIbnrWGVk8N7s1-lR-CUahLHxRgOQw3fx2SlJ14DycesOOP1w8VPT-dPnzPqrMGAZDHRZ2tw4bCV5VaTT8uNnLnnLkDlPuI7m55URHS9-24FQJzFK3SNuNfqrZvpmSjdFlxOA-UaHNNs0xxBZWKyKzx61dTq6oi08QJv_tT2rWjhD_06J1Aeh3bTmgCsTtuprhWImyCQGU-0UvmE385AxJz20nucjVJIZ0b8JmfpWjxnz6h6r5qfa6-gmuSoSxxRMfcXQZz5Fv4hhctVpu4Sfcezr669s6r6rOWq9w9Qpy6lgz6tXpz7eb_cFSeJon8xfZbQxQ48eWQ6bue0zi0lw4zWFWaJY99w365UUt33fJOFigidVvUB3UU_Yu1iqUJcFIk_OiqWSFgQ8uW0Ry1xjUS0yZB6MWQ7r500YVoOIn06_Vjyt0u6VdZ9ywo81RIs32mjbnRc3BkWsgkM859Un8gxQmxzQtvcWo9n-6beqXyFizZSIOgvv_QS5zanf53b3Z7U3t5_nziplxd5mbZ20JO0_Z9qQuUn_z40cc5gZoUSrWVdexwOzdMcXhxneXwt_OkosFM8nZvi6qY9hVwysZOvoeOeUY8bgju3Rb6fyIqVMYQpSWSRuUp6mm9OOqtUwnsFUYndSruMRpM5q-ajs2Oh6hn0nlBIxSQcszz7t9vb4X14zS8iQkVj57gYJ311bccnkYqJdliweUfQ0gcd8Xdj8R4_t84fbqZjs1WBgYyIkxQqxX_jU6QW96mWR1z5Jjz7x9dq7Z_0fi_Z9lbUg6Zuv48j4vtMWuy9jnIhJoqR65tclcIl9eOJ-5oW6gSO7jsQV3j-42Spng"
token_lock = threading.Lock()

def generate_token():
    global access_token  # Asegurar que estamos modificando la variable global
    credentials = service_account.Credentials.from_service_account_file(
        'src/credentials.json',
        scopes=['https://www.googleapis.com/auth/admin.directory.group']
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)    
    

    access_token = credentials.token
    
    return access_token

def get_access_token():
    """Obtiene el token actual o genera uno nuevo si es necesario"""
    global access_token
    with token_lock:
        if not access_token:
            access_token = generate_token()
        return access_token