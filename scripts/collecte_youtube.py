from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    VideoUnplayable
)
import csv
from datetime import datetime
import isodate
import pandas as pd
import numpy as np
import os
import shutil

API_KEY = os.getenv("YOUTUBE_API_KEY")
if API_KEY is None:
    print("Erreur : Clé API manquante.")
    exit(1)


backup_dir = "../backups"
os.makedirs(backup_dir, exist_ok=True)


liste_playlist = [
    'PLh6ucOK4zNVuRoPgB7Cfw5dwN_SHtRjQa',
    'PLh6ucOK4zNVvz3uvBo1zyfW8qc95elDlA',
    'PLh6ucOK4zNVvjZGVDMhJGlEKDCP1vRvM2',
    'PLh6ucOK4zNVvse87q8YO6lscujMr7_1xv'
]

nom_fichier = [
    'f1.csv',
    'f2.csv',
    'f3.csv',
    'f4.csv'
]

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

    # Transcription
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr'])
        transcription = " ".join([line['text'] for line in transcript])
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, VideoUnplayable):
        transcription = ''
    except Exception:
        transcription = ''


    # Format date
    pub_date_iso = snippet['publishedAt']
    pub_date = datetime.strptime(pub_date_iso[:10], '%Y-%m-%d')
    jour_semaine = pub_date.strftime('%A')  # ex : Monday
    date_str = pub_date.strftime('%d/%m/%Y')

    # Durée ISO -> secondes
    duree_seconds = int(isodate.parse_duration(content['duration']).total_seconds())

    # Données numériques
    vues = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    commentaires = int(stats.get('commentCount', 0))

    # Ratios
    ratio_likes_vues = round((likes / vues) * 100, 2) if vues > 0 else 0
    ratio_commentaires_vues = round((commentaires / vues) * 100, 2) if vues > 0 else 0

    # Performance globale simple (pondération personnalisable)
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
        'type_activite': '',  # à compléter manuellement ou via NLP
        'domaine': ''         # idem
    }

def main():
    i = 0
    for playlist in liste_playlist:
        video_ids = get_video_ids(playlist)
        fieldnames = ['url_video', 'video_id', 'titre', 'description', 'transcription',
                    'date_publication', 'jour_semaine', 'vues', 'likes', 'commentaires', 'duree',
                    'ratio_likes_vues', 'ratio_commentaires_vues', 'performance_globale',
                    'type_activite', 'domaine']

        with open(nom_fichier[i], 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for vid in video_ids:
                data = get_video_details(vid)
                if data:  # ← on saute les None
                    writer.writerow(data)

        i = i + 1

if __name__ == '__main__':
    main()


    f1 = pd.read_csv('f1.csv')
    f2 = pd.read_csv('f2.csv')
    f3 = pd.read_csv('f3.csv')
    f4 = pd.read_csv('f4.csv')

    try:
        data = pd.read_csv('../donnees.csv', encoding='utf-8')
    except FileNotFoundError:
        data = pd.DataFrame()

    fusion = pd.concat([f1,f2,f3,f4]).reset_index(drop=True)
    fusion = fusion.drop(fusion.loc[fusion.video_id.duplicated() == True].index).reset_index(drop=True)

    maListe = [
        'TH MATIN',
        'FEMMES LEADERS',
        'QUE DIT LA LOI',
        'FOCUS SANTE',
        'LEXIQUE PARLEMENTAIRE',
        "PARLEMEN'TERRE",
        'ENTRE PARLEMENTAIRES',
        'JOURNAL',
        'JT',
        'REVUE DE PRESSE',
        'DYSFONCTON ERECTILE',
        "PARL'HEBDO"
    ]

    for emission in maListe:
        fusion = fusion.drop(fusion.loc[fusion.titre.str.contains(emission,case=False,na=False)].index).reset_index(drop=True)

    fusion.transcription = fusion.transcription.astype(str)
    fusion.date_publication = pd.to_datetime(fusion.date_publication, format='%d/%m%Y')
    fusion.type_activite = fusion.type_activite.astype(str)
    fusion.domaine = fusion.domaine.astype(str)

    traduction_jour = {
        "Monday" : "Lundi",
        "Tuesday" : "Mardi",
        "Wednesday" : "Mercredi",
        "Thursday" : "Jeudi",
        "Friday" : "Vendredi",
        "Saturday" : "Samedi",
        "Sunday" : "Dimanche"
    }

    fusion.jour_semaine = fusion.jour_semaine.map(traduction_jour)


    
    a_ajouter = fusion[~fusion.video_id.isin(data.video_id)]

    if os.path.exists("../donnees.csv"):
        backup_path = os.path.join(
            backup_dir,
            f"donnees_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        shutil.copy("../donnees.csv", backup_path)
        print(f"-->Fichier existant sauvegardé dans {backup_path}")

    data = pd.concat([data,a_ajouter]).reset_index(drop=True)
    data.to_csv('../donnees.csv', index=False)


print(f"-->{len(a_ajouter)} nouvelles vidéos ajoutées à donnees.csv")
