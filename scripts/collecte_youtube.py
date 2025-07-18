from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, VideoUnplayable
)
import csv
from datetime import datetime
import isodate
import pandas as pd
import numpy as np
import os
import shutil
import sys

# === Détection dynamique du dossier racine ===
racine = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# === Vérification API KEY ===
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    print("❌ Erreur : Clé API YOUTUBE_API_KEY manquante.")
    sys.exit(1)

# === Dossier de sauvegarde ===
backup_dir = os.path.join(racine, "backups")
os.makedirs(backup_dir, exist_ok=True)

# === Playlists ciblées ===
liste_playlist = [
    'PLh6ucOK4zNVuRoPgB7Cfw5dwN_SHtRjQa',
    'PLh6ucOK4zNVvz3uvBo1zyfW8qc95elDlA',
    'PLh6ucOK4zNVvjZGVDMhJGlEKDCP1vRvM2',
    'PLh6ucOK4zNVvse87q8YO6lscujMr7_1xv'
]

nom_fichier = ['f1.csv', 'f2.csv', 'f3.csv', 'f4.csv']

youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_video_ids(playlist_id):
    video_ids = []
    next_page_token = None
    while True:
        response = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return video_ids

def get_video_details(video_id):
    response = youtube.videos().list(
        part='snippet,statistics,contentDetails',
        id=video_id
    ).execute()
    if not response['items']:
        return None

    item = response['items'][0]
    snippet = item['snippet']
    stats = item.get('statistics', {})
    content = item['contentDetails']

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr'])
        transcription = " ".join([line['text'] for line in transcript])
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, VideoUnplayable, Exception):
        transcription = ''

    pub_date_iso = snippet['publishedAt']
    pub_date = datetime.strptime(pub_date_iso[:10], '%Y-%m-%d')
    jour_semaine = pub_date.strftime('%A')
    date_str = pub_date.strftime('%d/%m/%Y')

    duree_seconds = int(isodate.parse_duration(content['duration']).total_seconds())

    vues = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    commentaires = int(stats.get('commentCount', 0))

    ratio_likes_vues = round((likes / vues) * 100, 2) if vues > 0 else 0
    ratio_commentaires_vues = round((commentaires / vues) * 100, 2) if vues > 0 else 0
    performance_globale = round((0.5 * ratio_likes_vues + 0.5 * ratio_commentaires_vues), 2)

    return {
        'url_video': f"https://www.youtube.com/watch?v={video_id}",
        'video_id': video_id,
        'titre': snippet['title'],
        'description': snippet.get('description', ''),
        'transcription': transcription,
        'date_publication': date_str,
        'jour_semaine': jour_semaine,
        'vues': vues,
        'likes': likes,
        'commentaires': commentaires,
        'duree': duree_seconds,
        'ratio_likes_vues': ratio_likes_vues,
        'ratio_commentaires_vues': ratio_commentaires_vues,
        'performance_globale': performance_globale,
        'type_activite': '',
        'domaine': ''
    }

def main():
    chemin_donnees = os.path.join(racine, 'donnees.csv')
    try:
        data_existante = pd.read_csv(chemin_donnees, encoding='utf-8')
        ids_existants = set(data_existante['video_id'])
    except FileNotFoundError:
        data_existante = pd.DataFrame()
        ids_existants = set()

    for i, playlist in enumerate(liste_playlist):
        all_video_ids = get_video_ids(playlist)
        video_ids = [vid for vid in all_video_ids if vid not in ids_existants]
        print(f"🎯 Playlist {i+1} : {len(video_ids)} nouvelles vidéos à analyser")

        fieldnames = [
            'url_video', 'video_id', 'titre', 'description', 'transcription',
            'date_publication', 'jour_semaine', 'vues', 'likes', 'commentaires', 'duree',
            'ratio_likes_vues', 'ratio_commentaires_vues', 'performance_globale',
            'type_activite', 'domaine'
        ]

        with open(os.path.join(racine, nom_fichier[i]), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for vid in video_ids:
                data = get_video_details(vid)
                if data:
                    writer.writerow(data)

    f_dataframes = [pd.read_csv(os.path.join(racine, f)) for f in nom_fichier]
    fusion = pd.concat(f_dataframes).drop_duplicates(subset='video_id').reset_index(drop=True)

    maListe = [
        'TH MATIN', 'FEMMES LEADERS', 'QUE DIT LA LOI', 'FOCUS SANTE',
        'LEXIQUE PARLEMENTAIRE', "PARLEMEN'TERRE", 'ENTRE PARLEMENTAIRES',
        'JOURNAL', 'JT', 'REVUE DE PRESSE', 'DYSFONCTON ERECTILE', "PARL'HEBDO"
    ]
    for emission in maListe:
        fusion = fusion[~fusion.titre.str.contains(emission, case=False, na=False)]

    fusion.transcription = fusion.transcription.astype(str)
    fusion.date_publication = pd.to_datetime(fusion.date_publication, format='%d/%m/%Y')
    fusion.type_activite = fusion.type_activite.astype(str)
    fusion.domaine = fusion.domaine.astype(str)

    traduction_jour = {
        "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
        "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"
    }
    fusion.jour_semaine = fusion.jour_semaine.map(traduction_jour)

    a_ajouter = fusion[~fusion.video_id.isin(data_existante.video_id)]

    # 🔁 Mise à jour des stats pour vidéos existantes
    colonnes_dynamiques = [
        'vues', 'likes', 'commentaires',
        'ratio_likes_vues', 'ratio_commentaires_vues',
        'performance_globale'
    ]
    fusion_indexed = fusion.set_index('video_id')
    data_existante_indexed = data_existante.set_index('video_id')
    data_existante_indexed.update(fusion_indexed[colonnes_dynamiques])
    data_existante = data_existante_indexed.reset_index()
    fusion = fusion_indexed.reset_index()

    if os.path.exists(chemin_donnees):
        backup_path = os.path.join(backup_dir, f"donnees_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        shutil.copy(chemin_donnees, backup_path)
        print(f"🗂️ Fichier existant sauvegardé dans {backup_path}")

    donnees_finales = pd.concat([data_existante, a_ajouter]).drop_duplicates(subset='video_id').reset_index(drop=True)
    donnees_finales.to_csv(chemin_donnees, index=False)
    print(f"✅ {len(a_ajouter)} nouvelles vidéos ajoutées à donnees.csv")

if __name__ == '__main__':
    main()
