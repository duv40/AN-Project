import pandas as pd
import spacy
import numpy as np
import joblib
import os
import shutil
from datetime import datetime
import sys
backup_dir = "../backups"
os.makedirs(backup_dir, exist_ok=True)


# Vérifie que les fichiers de modèles existent
fichiers_modeles = {
    'vectoriseur': '../models/le_vectoriseur.joblib',
    'model_activite': '../models/model_activite.joblib',
    'model_domaine': '../models/model_domaine.joblib'
}

for nom, fichier in fichiers_modeles.items():
    if not os.path.exists(fichier):
        print(f"-->Le fichier '{fichier}' est introuvable. Impossible de continuer.")
        sys.exit(1)

# Chargement des modèles
vectoriseur = joblib.load(fichiers_modeles['vectoriseur'])
model_activite = joblib.load(fichiers_modeles['model_activite'])
model_domaine = joblib.load(fichiers_modeles['model_domaine'])

# Chargement du modèle NLP
try:
    nlp = spacy.load("fr_core_news_md")
except:
    print("-->Le modèle spaCy 'fr_core_news_md' est introuvable. Fais `python -m spacy download fr_core_news_md`")
    sys.exit(1)

# Chargement du fichier de données
try:
    data = pd.read_csv('../donnees.csv')
except FileNotFoundError:
    print("-->Le fichier 'donnees.csv' est introuvable.")
    sys.exit(1)

data["transcription"] = data["transcription"].fillna('').astype(str)
data["titre"] = data["titre"].fillna('').astype(str)
data["description"] = data["description"].fillna('').astype(str)
data["type_activite"] = data["type_activite"].fillna('').astype(str)
data["domaine"] = data["domaine"].fillna('').astype(str)

liste_a_remplir = data.loc[(data.type_activite == '') | (data.domaine == ''), :]

dico = {
    "video_id" : liste_a_remplir.video_id,
    "texte" : liste_a_remplir.titre + ' ' + liste_a_remplir.description + ' ' + liste_a_remplir.transcription,
    "type_activite" : liste_a_remplir.type_activite,
    "domaine" : liste_a_remplir.domaine
}

working_list = pd.DataFrame(dico)


liste = []

for text in working_list.texte:
    liste.append(nlp(text))

liste_tokens = []

for tt in liste:
    tok_lem = [tk.lemma_ for tk in tt if not tk.is_punct and not tk.is_stop]
    liste_tokens.append(tok_lem)

for i in range(len(liste_tokens)):
    liste_tokens[i] = [t.lower() for t in liste_tokens[i] if t.strip() != '' and t.lower() != 'nan']

working_list["texte_nettoye"] = [' '.join(x) for x in liste_tokens]


if not working_list.empty:
    X = vectoriseur.transform(working_list["texte_nettoye"])
    working_list["type_activite"] = model_activite.predict(X)
    working_list["domaine"] = model_domaine.predict(X)

    # Mise à jour des lignes d'origine
    index_cibles = liste_a_remplir.index
    data.loc[index_cibles, "type_activite"] = working_list["type_activite"].values
    data.loc[index_cibles, "domaine"] = working_list["domaine"].values

    if os.path.exists("../donnees.csv"):
        backup_path = os.path.join(
            backup_dir,
            f"donnees_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        shutil.copy("../donnees.csv", backup_path)
        print(f"-->Fichier existant sauvegardé dans {backup_path}")

    # Sauvegarde finale
    data.to_csv("../donnees.csv", index=False)
    print(f"-->{len(working_list)} lignes mises à jour.")
else:
    print("-->Aucune ligne à mettre à jour.")