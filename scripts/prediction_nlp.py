import pandas as pd
import spacy
import numpy as np
import joblib
import os
import shutil
import sys
from datetime import datetime

# === Initialisation ===
racine = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
chemin_donnees = os.path.join(racine, 'donnees.csv')
backup_dir = os.path.join(racine, 'backups')
os.makedirs(backup_dir, exist_ok=True)

# === Vérification des fichiers modèles ===
fichiers_modeles = {
    'vectoriseur': os.path.join(racine, 'models', 'le_vectoriseur.joblib'),
    'model_activite': os.path.join(racine, 'models', 'model_activite.joblib'),
    'model_domaine': os.path.join(racine, 'models', 'model_domaine.joblib')
}

for nom, fichier in fichiers_modeles.items():
    if not os.path.exists(fichier):
        print(f"❌ Le fichier '{fichier}' est introuvable. Abandon.")
        sys.exit(1)

# === Chargement des modèles ===
vectoriseur = joblib.load(fichiers_modeles['vectoriseur'])
model_activite = joblib.load(fichiers_modeles['model_activite'])
model_domaine = joblib.load(fichiers_modeles['model_domaine'])

# === Chargement NLP spaCy ===
try:
    nlp = spacy.load("fr_core_news_md")
except OSError:
    print("❌ Le modèle spaCy 'fr_core_news_md' est introuvable.")
    print("👉 Exécute : python -m spacy download fr_core_news_md")
    sys.exit(1)

# === Chargement du fichier de données ===
try:
    data = pd.read_csv(chemin_donnees)
except FileNotFoundError:
    print("❌ Le fichier 'donnees.csv' est introuvable.")
    sys.exit(1)

# === Prétraitement de base ===
for col in ['transcription', 'titre', 'description', 'type_activite', 'domaine']:
    data[col] = data[col].fillna('').astype(str)

# === Sélection des lignes à compléter ===
liste_a_remplir = data[(data['type_activite'] == '') | (data['domaine'] == '')]

if liste_a_remplir.empty:
    print("✅ Aucune ligne à mettre à jour. Fichier déjà complet.")
    sys.exit(0)

# === Construction du corpus texte ===
working_list = pd.DataFrame({
    'video_id': liste_a_remplir.video_id,
    'texte': liste_a_remplir.titre + ' ' + liste_a_remplir.description + ' ' + liste_a_remplir.transcription,
    'type_activite': liste_a_remplir.type_activite,
    'domaine': liste_a_remplir.domaine
})

# === Nettoyage du texte ===
docs = [nlp(t) for t in working_list['texte']]
tokens_list = []

for doc in docs:
    tokens = [tk.lemma_.lower() for tk in doc if not tk.is_stop and not tk.is_punct and tk.lemma_.strip()]
    tokens_list.append(tokens)

working_list["texte_nettoye"] = [' '.join(tokens) for tokens in tokens_list]

# === Prédictions ===
X = vectoriseur.transform(working_list["texte_nettoye"])
working_list["type_activite"] = model_activite.predict(X)
working_list["domaine"] = model_domaine.predict(X)

# === Mise à jour des données ===
index_cibles = liste_a_remplir.index
data.loc[index_cibles, "type_activite"] = working_list["type_activite"].values
data.loc[index_cibles, "domaine"] = working_list["domaine"].values

# === Sauvegarde (avec backup) ===
if os.path.exists(chemin_donnees):
    backup_path = os.path.join(backup_dir, f"donnees_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    shutil.copy(chemin_donnees, backup_path)
    print(f"🗂️ Backup effectué : {backup_path}")

data.to_csv(chemin_donnees, index=False)
data.to_excel(chemin_donnees, index=False)

print(f"✅ {len(working_list)} lignes mises à jour avec succès.")
