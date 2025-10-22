# 🪂 Guide d'Installation 1BIP - Système de Reconnaissance Faciale
## 1ère Brigade d'Infanterie Parachutiste - Forces Armées Royales Marocaines

---

## ⚠️ IMPORTANT - À Propos des Erreurs 401/500 au Premier Démarrage

### Pourquoi ces erreurs se produisent-elles?

Les erreurs **401 Unauthorized** et **500 Internal Server Error** que vous voyez au premier démarrage sont **NORMALES** et attendues. Voici pourquoi:

1. **CompreFace a besoin de temps pour initialiser** - La base de données PostgreSQL doit créer les tables et charger les modèles d'IA
2. **Les services démarrent dans un ordre spécifique** - Certains services dépendent d'autres qui ne sont pas encore prêts
3. **C'est un processus de première installation** - Cela ne se produira qu'une seule fois

### Solution: Patience et Ordre Correct

**Attendez 2-3 minutes** après `docker-compose up -d` avant d'accéder à l'interface.

---

## 📋 Installation Complète Étape par Étape

### Étape 1: Démarrer Tous les Services

```bash
cd /path/to/CompreFaceModeling

# Démarrer tous les services
docker-compose up -d

# Attendez que tous les services soient prêts (IMPORTANT!)
echo "Attente de l'initialisation des services... Veuillez patienter 3 minutes"
sleep 180

# Vérifier que tous les services sont en cours d'exécution
docker-compose ps
```

**Vous devriez voir:**
- `compreface-postgres-db` - Running
- `compreface-admin` - Running
- `compreface-api` - Running
- `compreface-core` - Running
- `compreface-ui` - Running
- `1bip-camera-service` - Running (optionnel si caméra configurée)
- `1bip-dashboard` - Running

### Étape 2: Vérifier les Logs (Résoudre les Problèmes)

Si vous avez toujours des erreurs après 3 minutes:

```bash
# Vérifier les logs de chaque service
docker-compose logs compreface-admin
docker-compose logs compreface-api
docker-compose logs compreface-core
docker-compose logs compreface-postgres-db

# Si vous voyez "waiting for PostgreSQL to start" - c'est normal, attendez encore
# Si vous voyez "database migration complete" - c'est bon!
```

### Étape 3: Accéder à l'Interface CompreFace

```bash
# Ouvrir dans votre navigateur
open http://localhost:8000
```

**Page de connexion:** Vous verrez la page de connexion de CompreFace

**PREMIÈRE FOIS - Créer un compte administrateur:**

1. Cliquez sur **"Sign Up"** (Créer un compte)
2. Remplissez:
   - **Email:** admin@1bip.ma (ou votre email)
   - **Mot de passe:** ChoisissezUnMotDePasseSecurise123!
   - **Confirmation:** ChoisissezUnMotDePasseSecurise123!
3. Cliquez sur **"Sign Up"**
4. Connectez-vous avec vos identifiants

---

## 🔑 Configuration de la Clé API (CRITIQUE - 100% Hors Ligne!)

### ❗ CLARIFICATION IMPORTANTE SUR LA CLÉ API

**La clé API CompreFace n'est PAS d'internet!**

- ✅ La clé API est **générée par VOTRE propre instance CompreFace** sur votre serveur
- ✅ **100% hors ligne** - Aucune connexion internet nécessaire
- ✅ C'est juste une clé de sécurité entre vos propres services
- ✅ Tout fonctionne sur **votre réseau local uniquement**

### Comment Obtenir Votre Clé API (Sur Votre Serveur)

#### Option 1: Interface Web CompreFace (Recommandée)

1. **Connectez-vous à CompreFace** - http://localhost:8000

2. **Créer une Application de Reconnaissance:**
   - Allez dans **"Applications"**
   - Cliquez **"Add New Application"**
   - Nom: `1BIP Base Principale` (ou le nom de votre unité)
   - Cliquez **"Create"**

3. **Activer le Service de Reconnaissance Faciale:**
   - Dans votre application, cliquez sur **"Services"**
   - Trouvez **"Recognition"**
   - Cliquez **"Enable"** ou **"Configure"**

4. **Copier la Clé API:**
   - Vous verrez **"API Key"** affiché
   - Cliquez sur l'icône 📋 pour copier
   - **EXEMPLE:** `00000000-0000-0000-0000-000000000001`

5. **Enregistrer la Clé API dans votre Configuration:**

```bash
# Éditer le fichier de configuration de la caméra
nano camera-service/config/camera_config.env

# Remplacer la ligne:
COMPREFACE_API_KEY=your_api_key_here_from_compreface_ui

# Par votre vraie clé API:
COMPREFACE_API_KEY=00000000-0000-0000-0000-000000000001

# Sauvegarder: Ctrl+O, Enter, Ctrl+X
```

6. **Redémarrer le Service Caméra:**

```bash
docker-compose restart 1bip-camera-service
```

---

## 👥 Organisation du Personnel par Unité et Département

### Structure Recommandée

CompreFace vous permet d'organiser le personnel de manière hiérarchique:

```
1BIP (1ère Brigade d'Infanterie Parachutiste)
│
├── Application 1: "1BIP - Compagnie Alpha"
│   ├── Personne: CPT. Ahmed Mansouri
│   ├── Personne: LT. Mohammed Benani
│   ├── Personne: SGT. Youssef Khalil
│   └── ... (300-500 personnes)
│
├── Application 2: "1BIP - Compagnie Bravo"
│   ├── Personne: CPT. Hassan Ziani
│   ├── Personne: LT. Omar Tazi
│   └── ... (300-500 personnes)
│
├── Application 3: "1BIP - Compagnie Charlie"
│   └── ... (300-500 personnes)
│
├── Application 4: "1BIP - État-Major"
│   ├── Personne: COL. Rachid Alami (Commandant)
│   ├── Personne: MAJ. Karim Benjelloun
│   └── ...
│
└── Application 5: "1BIP - Services de Soutien"
    └── ...
```

### Méthode 1: Une Application par Unité/Département

**Avantages:**
- ✅ Organisation claire
- ✅ Clés API séparées par unité
- ✅ Contrôle d'accès granulaire
- ✅ Rapports et statistiques par unité

**Comment Créer:**

1. **Pour Chaque Unité/Département:**
   ```
   Nom Application: "1BIP - Compagnie Alpha"
   Description: "Compagnie Alpha - Zone Opérationnelle Nord"
   ```

2. **Activer le Service de Reconnaissance** pour chaque application

3. **Ajouter le Personnel à l'Application:**
   - Cliquez sur l'application
   - Cliquez **"Subjects"** (Personnes)
   - Cliquez **"Add Subject"**
   - Nom: `CPT_Ahmed_Mansouri` (Format: GRADE_Prenom_Nom)
   - Téléchargez **3-5 photos** de la personne (différents angles)

### Méthode 2: Utiliser les Metadata pour Organiser

**Une application avec métadonnées:**

```
Application: "1BIP - Personnel de la Brigade"

Personne 1:
- Nom: CPT_Ahmed_Mansouri
- Métadonnées: {
    "unite": "Compagnie Alpha",
    "grade": "Capitaine",
    "matricule": "1BIP-2024-001",
    "fonction": "Commandant de Compagnie"
  }

Personne 2:
- Nom: LT_Mohammed_Benani
- Métadonnées: {
    "unite": "Compagnie Alpha",
    "grade": "Lieutenant",
    "matricule": "1BIP-2024-002",
    "fonction": "Chef de Section"
  }
```

**Avantages:**
- ✅ Gestion centralisée
- ✅ Recherche et filtrage faciles
- ✅ Rapports flexibles
- ✅ Une seule clé API

---

## 📹 Configuration de la Caméra Hikvision

### Étape 1: Trouver l'URL RTSP de votre Caméra

**Format RTSP Hikvision:**
```
rtsp://username:password@IP_ADDRESS:554/Streaming/Channels/101
```

**Exemple concret:**
```
rtsp://admin:Morocco2025@192.168.1.100:554/Streaming/Channels/101
```

**Paramètres:**
- `username`: Nom d'utilisateur de la caméra (généralement `admin`)
- `password`: Mot de passe de votre caméra Hikvision
- `IP_ADDRESS`: Adresse IP de la caméra sur votre réseau local (ex: 192.168.1.100)
- `554`: Port RTSP (standard)
- `/Streaming/Channels/101`: Canal principal (haute résolution 8MP)
  - `/Streaming/Channels/102`: Canal secondaire (résolution inférieure)

### Étape 2: Tester la Connexion RTSP

```bash
# Installer VLC si pas déjà installé
# Sur macOS:
brew install vlc

# Tester le stream RTSP
vlc rtsp://admin:VotreMotDePasse@192.168.1.100:554/Streaming/Channels/101
```

Si vous voyez la vidéo dans VLC, votre URL RTSP est correcte!

### Étape 3: Configurer le Service Caméra

```bash
# Éditer la configuration
nano camera-service/config/camera_config.env
```

**Paramètres CRITIQUES à modifier:**

```bash
# URL de Votre Caméra Hikvision
CAMERA_RTSP_URL=rtsp://admin:VotreMotDePasse@192.168.1.100:554/Streaming/Channels/101

# Nom et Localisation
CAMERA_NAME=1BIP Portail Principal
CAMERA_LOCATION=1BIP Base - Point de Contrôle Alpha

# Clé API (copiée depuis CompreFace UI - ÉTAPE CRITIQUE!)
COMPREFACE_API_KEY=00000000-0000-0000-0000-000000000001

# Performance pour M3 Max (ajuster selon votre matériel)
FRAME_SKIP=2              # Traiter 1 image sur 2 (augmenter pour CPU plus lent)
FRAME_WIDTH=2560          # 4K pour M3 Max (réduire à 1920 pour matériel moins puissant)
FRAME_HEIGHT=1440
MAX_FACES_PER_FRAME=20    # Détection multi-visages

# Sécurité - Seuil de Similarité (plus élevé = plus strict)
SIMILARITY_THRESHOLD=0.88 # 88% recommandé pour usage militaire
                          # 0.85 = moins strict (plus de faux positifs)
                          # 0.90 = très strict (peut rejeter vrais positifs)
```

### Étape 4: Redémarrer les Services

```bash
# Redémarrer le service caméra
docker-compose restart 1bip-camera-service

# Vérifier les logs
docker-compose logs -f 1bip-camera-service
```

**Vous devriez voir:**
```
✅ Connected to RTSP stream: rtsp://admin:****@192.168.1.100:554/Streaming/Channels/101
✅ Frame size: 2560x1440
✅ CompreFace API connection successful
🎥 Camera service running...
```

---

## 📊 Accéder au Tableau de Bord

```bash
# Ouvrir le tableau de bord
open http://localhost:5000
```

**Vous verrez:**
- 🪖 Accès Total Aujourd'hui
- ✅ Personnel Autorisé
- 🚨 Alertes de Sécurité
- 🪂 Parachutistes Actifs
- 📹 Caméras de Surveillance

**Fonctionnalités:**
- 🔴 Moniteur en Direct (actualisation auto toutes les 10 secondes)
- 📋 Suivi du Personnel (arrivées/départs)
- 🚨 Alertes d'Accès Non Autorisé
- 📹 État des Caméras
- 📊 Rapports d'Opérations (export CSV)

---

## 🔧 Flux de Travail Complet

### Workflow Quotidien

```
1. MATIN - Démarrage du Système
   └─> docker-compose up -d
   └─> Attendre 2-3 minutes
   └─> Vérifier dashboard: http://localhost:5000

2. AJOUT DE NOUVEAU PERSONNEL
   └─> Accéder à CompreFace UI: http://localhost:8000
   └─> Choisir l'application (unité/département)
   └─> Ajouter une personne ("Subject")
   └─> Télécharger 3-5 photos (face, profil gauche, profil droit)
   └─> La personne est maintenant dans la base de données

3. RECONNAISSANCE EN TEMPS RÉEL
   └─> La caméra détecte automatiquement les visages
   └─> Compare avec la base de données locale
   └─> Si reconnu → Accès autorisé (enregistré dans les logs)
   └─> Si non reconnu → Alerte d'intrusion (notification)

4. SURVEILLANCE ET RAPPORTS
   └─> Dashboard en direct: http://localhost:5000
   └─> Voir tous les accès du jour
   └─> Filtrer les alertes
   └─> Exporter les rapports CSV

5. FIN DE JOURNÉE
   └─> Les données sont sauvegardées automatiquement
   └─> Option: docker-compose down (si vous voulez arrêter)
```

---

## ✅ Checklist de Vérification

- [ ] Docker et Docker Compose installés
- [ ] CompreFace démarré et accessible (http://localhost:8000)
- [ ] Compte administrateur créé
- [ ] Application de reconnaissance créée
- [ ] Clé API copiée et configurée dans `camera_config.env`
- [ ] URL RTSP de la caméra testée avec VLC
- [ ] Service caméra démarré et connecté
- [ ] Dashboard accessible (http://localhost:5000)
- [ ] Au moins 1 personne test ajoutée avec photos
- [ ] Test de reconnaissance effectué avec succès

---

## 🚨 Dépannage - Problèmes Courants

### Problème 1: Erreur 401/500 sur la Page de Connexion

**Cause:** Services pas encore complètement initialisés

**Solution:**
```bash
# Attendez 3-5 minutes
sleep 300

# Vérifier l'état de la base de données
docker-compose logs compreface-postgres-db | grep "ready"

# Si vous voyez "database system is ready to accept connections" - c'est bon!

# Redémarrer si nécessaire
docker-compose restart
```

### Problème 2: Service Caméra Ne Se Connecte Pas

**Cause:** Clé API manquante ou incorrecte

**Solution:**
```bash
# 1. Vérifier que la clé API est dans la config
cat camera-service/config/camera_config.env | grep COMPREFACE_API_KEY

# 2. Si vous voyez "your_api_key_here" - vous devez la remplacer!
# 3. Retournez à l'étape "Configuration de la Clé API" ci-dessus
# 4. Copiez la vraie clé depuis CompreFace UI
# 5. Redémarrez le service
docker-compose restart 1bip-camera-service
```

### Problème 3: Caméra RTSP Ne Se Connecte Pas

**Diagnostic:**
```bash
# Vérifier les logs de la caméra
docker-compose logs 1bip-camera-service

# Tester manuellement avec VLC
vlc rtsp://admin:password@IP:554/Streaming/Channels/101
```

**Solutions:**
- ✅ Vérifiez l'adresse IP de la caméra (ping 192.168.1.100)
- ✅ Vérifiez le mot de passe de la caméra
- ✅ Vérifiez que le port 554 est ouvert
- ✅ Essayez le canal 102 au lieu de 101
- ✅ Vérifiez que RTSP est activé dans les paramètres de la caméra

### Problème 4: Détection Trop de Faux Positifs

**Cause:** Seuil de similarité trop bas

**Solution:**
```bash
# Éditer la config
nano camera-service/config/camera_config.env

# Augmenter le seuil
SIMILARITY_THRESHOLD=0.90  # Au lieu de 0.85

# Redémarrer
docker-compose restart 1bip-camera-service
```

### Problème 5: Performance Lente sur M3 Max

**Solution:**
```bash
# Vérifier que MPS GPU est utilisé
docker-compose logs compreface-core | grep "MPS"

# Si pas de MPS, voir le guide M3_MAX_GPU_GUIDE.md
cat M3_MAX_GPU_GUIDE.md

# Ajuster les paramètres de performance dans .env
nano .env

# Augmenter:
compreface_api_java_options=-Xmx12g  # Si vous avez 64GB RAM
uwsgi_processes=6                     # Plus de workers
```

---

## 🔐 Sécurité - Recommandations

### 1. Changer le Mot de Passe de la Base de Données

```bash
# Éditer .env AVANT le premier démarrage
nano .env

# Changer:
postgres_password=VotreMotDePasseTresSecurise2025!
```

### 2. Réseau Isolé (Air-Gapped)

Ce système peut fonctionner **complètement hors ligne**:

- ✅ Aucune connexion internet nécessaire
- ✅ Toutes les communications sont locales
- ✅ Aucune donnée ne quitte votre serveur
- ✅ Peut être déployé sur réseau isolé militaire

### 3. Sauvegardes

```bash
# Sauvegarder la base de données
docker-compose exec compreface-postgres-db pg_dump -U postgres morocco_1bip_frs > backup_$(date +%Y%m%d).sql

# Sauvegarder les images et configurations
tar -czf backup_1bip_$(date +%Y%m%d).tar.gz camera-service/ dashboard-service/ .env docker-compose.yml
```

---

## 📞 Support

Pour des questions ou problèmes:

1. **Vérifier les logs:** `docker-compose logs [service-name]`
2. **Consulter la documentation CompreFace:** https://github.com/exadel-inc/CompreFace
3. **Fichiers de référence:**
   - `QUICK_START.md` - Guide de démarrage rapide
   - `M3_MAX_GPU_GUIDE.md` - Guide d'optimisation M3 Max
   - `OFFLINE_OPERATION_GUIDE.md` - Guide opération hors ligne

---

## 🇲🇦 1BIP - 1ère Brigade d'Infanterie Parachutiste
### Forces Armées Royales Marocaines - Troupes Aéroportées
### اللواء الأول للمشاة المحمولة جواً

**CLASSIFIÉ - USAGE MILITAIRE UNIQUEMENT**

---

*Guide généré avec [Claude Code](https://claude.com/claude-code)*
