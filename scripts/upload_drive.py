from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json
import os

# === Lecture des informations d'identification depuis les secrets ===
SERVICE_ACCOUNT_INFO = json.loads(os.getenv("GOOGLE_DRIVE_CREDENTIALS_JSON"))
print("✅ Clé lue avec succès !")
print("Client email :", SERVICE_ACCOUNT_INFO["client_email"])

SCOPES = ['https://www.googleapis.com/auth/drive.file']  # accès limité
credentials = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO, scopes=SCOPES
)

# === Initialisation du service Google Drive ===
service = build('drive', 'v3', credentials=credentials)

# === Nom du fichier à uploader ===
fichier_local = 'donnees.xlsx'  # ou donnees.csv
nom_sur_drive = 'donnees.xlsx'

# === Définition des métadonnées ===
file_metadata = {
    'name': nom_sur_drive,
    'parents': ['1TfYWl5TjIcklmSAxo_H0a-LMvlYHaSZO']
}


# === Fichier à uploader ===
media = MediaFileUpload(fichier_local, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# === Upload du fichier ===
fichier = service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id'
).execute()

print(f"✅ Fichier uploadé avec succès. ID Google Drive : {fichier.get('id')}")
