import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.auth.transport.requests
from googleapiclient.errors import HttpError

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
    if creds.expired and creds.refresh_token:
        creds.refresh(google.auth.transport.requests.Request())
else:
    flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
    creds = flow.run_local_server(port=0)
    print("💡 Nouveau TOKEN_JSON généré :")
    print(creds.to_json())

# === Initialisation du service Google Drive ===
service = build('drive', 'v3', credentials=creds)

# === Préparation du fichier local ===
racine = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
fichier_local = os.path.join(racine, 'donnees.xlsx')
nom_fichier = 'donnees.xlsx'
dossier_id = '1TfYWl5TjIcklmSAxo_H0a-LMvlYHaSZO'

try:
    # === Recherche du fichier existant ===
    query = f"name='{nom_fichier}' and '{dossier_id}' in parents and trashed=false"
    result = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    fichiers = result.get('files', [])

    media = MediaFileUpload(
        fichier_local,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    if fichiers:
        # 🔁 Mettre à jour le premier fichier trouvé
        file_id = fichiers[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"✅ Fichier existant mis à jour. ID : {file_id}")
    else:
        # ➕ Créer un nouveau fichier
        file_metadata = {
            'name': nom_fichier,
            'parents': [dossier_id]
        }
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"✅ Nouveau fichier uploadé. ID : {file.get('id')}")

except HttpError as error:
    print(f"❌ Erreur Google Drive : {error}")
