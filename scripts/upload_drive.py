import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === Lecture des identifiants depuis les variables d'environnement ===
creds_json = os.getenv("GOOGLE_OAUTH_CREDENTIALS_JSON")
creds_dict = json.loads(creds_json)

# === Scopes d'accès au Drive ===
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# === Authentification OAuth (en local uniquement) ===
flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
creds = flow.run_local_server(port=0)  # ⚠️ Ne fonctionne pas sur GitHub Actions

# === Initialisation du service Drive ===
service = build('drive', 'v3', credentials=creds)

# === Métadonnées du fichier à envoyer ===
file_metadata = {
    'name': 'donnees.xlsx'
}

# === Chemin du fichier local à uploader ===
racine = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
fichier_local = os.path.join(racine, 'donnees.xlsx')

media = MediaFileUpload(
    fichier_local,
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# === Upload du fichier ===
file = service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id'
).execute()

print(f"✅ Fichier uploadé avec succès. ID : {file.get('id')}")
