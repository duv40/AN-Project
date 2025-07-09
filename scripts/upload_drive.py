import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.auth.transport.requests

# === Variables d'environnement ===
creds_json = os.getenv("GOOGLE_DRIVE_CREDENTIALS_JSON")
token_json = os.getenv("TOKEN_JSON")

if not creds_json:
    raise ValueError("❌ GOOGLE_DRIVE_CREDENTIALS_JSON est manquant")

creds_dict = json.loads(creds_json)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# === Récupération ou création des credentials ===
if token_json:
    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    # Rafraîchir si besoin
    if creds.expired and creds.refresh_token:
        creds.refresh(google.auth.transport.requests.Request())
else:
    flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
    creds = flow.run_local_server(port=0)
    print("💡 Nouveau TOKEN_JSON généré :")
    print(creds.to_json())  # À copier et sauvegarder toi-même dans les variables

# === Initialisation du service Google Drive ===
service = build('drive', 'v3', credentials=creds)

# === Métadonnées pour le fichier à uploader ===
file_metadata = {
    'name': 'donnees.xlsx',
    'parents': ['1TfYWl5TjIcklmSAxo_H0a-LMvlYHaSZO']  # Remplace par l'ID de ton dossier
}

# === Préparation du fichier local ===
racine = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
fichier_local = os.path.join(racine, 'donnees.xlsx')

media = MediaFileUpload(
    fichier_local,
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# === Upload vers Drive ===
file = service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id'
).execute()

print(f"✅ Fichier uploadé avec succès. ID : {file.get('id')}")
