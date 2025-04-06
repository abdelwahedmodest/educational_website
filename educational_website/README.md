# Educational Website Project

Un site web éducatif basé sur le contenu de ma chaîne YouTube, offrant différentes catégories : programmation, divertissement, e-commerce, etc.

## Fonctionnalités

- Classification automatique du contenu YouTube
- Système de catégorisation flexible (programmation, e-commerce, divertissement)
- Intégration de passerelles de paiement multiples (y compris Cash on Delivery)
- Interface utilisateur responsive
- Gestion d'abonnements et de contenus premium

## Installation

1. Cloner le dépôt
```bash
git clone https://github.com/abdelwahedmodest/educational_website.git
cd educational_website
============================================
utils/youtube_api.py

Ce code Python, situé dans le fichier `utils/youtube_api.py`, fait partie d’une application Django. Il permet d’interagir avec l’API de YouTube pour récupérer des vidéos d’une chaîne, les analyser, les classer automatiquement dans des catégories, les enregistrer dans une base de données, et mettre à jour leurs statistiques (vues et likes). Voici une description détaillée de son fonctionnement :

---

### 1. **Fonction `determine_category(title, description)`**
Cette fonction prend en entrée le **titre** et la **description** d'une vidéo YouTube, et détermine à quelle catégorie elle appartient (parmi "Programming", "E-commerce", "Entertainment", ou "Uncategorized") en se basant sur des **mots-clés**.

- Les mots-clés sont définis pour chaque catégorie.
- Le titre et la description sont analysés en minuscules pour faciliter la comparaison.
- On compte le nombre d’occurrences des mots-clés dans le texte.
- La catégorie ayant le plus de correspondances est choisie. Si aucune ne ressort clairement, la vidéo est placée dans une catégorie par défaut : “Uncategorized”.
- Si la catégorie n’existe pas en base de données, elle est créée grâce à `Category.objects.get_or_create()`.

---

### 2. **Fonction `fetch_channel_videos(channel_id)`**
Cette fonction utilise l’**API YouTube** pour extraire toutes les vidéos d'une chaîne à partir de son **ID**, puis elle les stocke dans la base de données de l'application.

#### Étapes :
1. **Connexion à l’API YouTube** via une clé stockée dans les paramètres Django.
2. **Récupération du playlist ID** correspondant aux vidéos publiées par la chaîne (`uploads`).
3. **Parcours de chaque vidéo** dans cette playlist, avec pagination (`nextPageToken`).
4. Pour chaque vidéo :
   - Récupération de détails (titre, description, miniatures, date de publication, durée, statistiques).
   - Conversion de la durée depuis le format ISO 8601 (`PT...`) vers un objet `timedelta`.
   - Appel à `determine_category()` pour classer la vidéo.
   - Enregistrement ou mise à jour de la vidéo dans la base via `Video.objects.update_or_create()`.
5. La fonction retourne le **nombre total de vidéos traitées**.

---

### 3. **Fonction `update_video_statistics(days=7)`**
Cette fonction met à jour les **statistiques de vues et de likes** des vidéos qui ont été publiées récemment (par défaut dans les 7 derniers jours).

#### Étapes :
1. Sélectionne les vidéos publiées dans les X derniers jours.
2. Découpe la liste en **batches de 50 vidéos** (limite imposée par l’API YouTube).
3. Récupère les statistiques actualisées pour chaque vidéo.
4. Met à jour les objets `Video` correspondants dans la base de données.
5. Retourne le **nombre total de vidéos mises à jour**.

---

### En résumé

Ce fichier automatise l’ingestion et la gestion de contenu vidéo à partir d’une chaîne YouTube. Il permet :

- de **classer automatiquement** les vidéos en catégories pertinentes,
- de **stocker et organiser** les vidéos dans la base de données,
- de **mettre à jour les statistiques** pour garder les données à jour,
- et de **gérer les erreurs API** (via `try/except` avec `HttpError`).

C’est un outil utile pour tout projet web souhaitant intégrer du contenu YouTube de façon structurée et intelligente.