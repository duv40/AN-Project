import os
import json
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# === Reconstitution du credentials.json temporaire ===
creds_str = os.getenv("GOOGLE_DRIVE_CREDENTIALS_JSON")
if not creds_str:
    print("❌ Clé secrète absente.")
    exit(1)

credentials_path = "temp_credentials.json"
with open(credentials_path, "w") as f:
    json.dump(json.loads(creds_str), f)

# === Authentification Google Drive ===
gauth = GoogleAuth()
gauth.LoadClientConfigFile(credentials_path)
gauth.LocalWebserverAuth()  # Pour exécution locale, sinon .CommandLineAuth()

drive = GoogleDrive(gauth)

# === Chemin du fichier à uploader ===
fichier_excel = "donnees.xlsx"

# === Upload du fichier sur Drive ===
fichier = drive.CreateFile({'title': fichier_excel})
fichier.SetContentFile(fichier_excel)
fichier.Upload()

print(f"✅ Fichier '{fichier_excel}' uploadé sur Google Drive avec succès.")
