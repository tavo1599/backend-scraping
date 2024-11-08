import firebase_admin
from firebase_admin import credentials, firestore
import os
import base64
import json
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la cadena Base64 desde el archivo .env
firebase_credentials_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")

if firebase_credentials_base64 is None:
    raise ValueError("No se pudo encontrar la variable de entorno FIREBASE_CREDENTIALS_BASE64.")

# Decodificar la cadena Base64 y convertirla a un diccionario JSON
firebase_credentials_json = json.loads(base64.b64decode(firebase_credentials_base64))

# Inicializar Firebase con las credenciales decodificadas
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_json)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def upload_to_firebase(collection_name, data):
    try:
        db.collection(collection_name).add(data)
        return True
    except Exception as e:
        print(f"Error al subir a Firebase: {e}")
        return False