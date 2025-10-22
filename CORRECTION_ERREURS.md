# 🔧 Guide de Correction des Erreurs - 1BIP CompreFace

## 🚨 Diagnostic de Vos Erreurs

Vous avez **DEUX problèmes** qui empêchent le système de fonctionner:

### Erreur 1: Échec d'Authentification PostgreSQL ❌
```
FATAL: password authentication failed for user "postgres"
DETAIL: Password does not match for user "postgres"
```

**CAUSE:** La base de données PostgreSQL a été créée avec un ancien mot de passe, mais les services essaient de se connecter avec le nouveau mot de passe que j'ai mis dans `.env`.

### Erreur 2: Architecture Incompatible (ARM64 vs AMD64) ⚠️
```
! The requested image's platform (linux/amd64) does not match
  the detected host platform (linux/arm64/v8)
```

**CAUSE:** Votre M3 Max est ARM64 (Apple Silicon), mais les images Docker CompreFace sont AMD64 (Intel). Docker utilise Rosetta 2 pour l'émulation, ce qui fonctionne mais est BEAUCOUP plus lent.

---

## ✅ SOLUTION COMPLÈTE (Étape par Étape)

### Étape 1: Arrêter et Nettoyer Complètement

```bash
# Aller dans le dossier du projet
cd ~/Desktop/Projects/CompreFaceModeling

# Arrêter TOUS les services
docker-compose down

# SUPPRIMER les volumes de base de données (réinitialisation complète)
docker-compose down -v

# Vérifier que tout est arrêté
docker-compose ps
# (devrait être vide)
```

### Étape 2: Vérifier le Mot de Passe dans .env

```bash
# Afficher le mot de passe configuré
cat .env | grep postgres_password
```

**Vous devriez voir:**
```
postgres_password=Morocco_Airborne_Secure2025!
```

Si c'est différent, éditez le fichier:
```bash
nano .env
# Assurez-vous que la ligne est:
postgres_password=Morocco_Airborne_Secure2025!
# Sauvegarder: Ctrl+O, Enter, Ctrl+X
```

### Étape 3: Mettre à Jour camera_config.env

Le mot de passe dans la configuration caméra **DOIT correspondre** à celui dans `.env`:

```bash
# Éditer la config caméra
nano camera-service/config/camera_config.env

# Trouver la ligne DB_PASSWORD et s'assurer qu'elle est:
DB_PASSWORD=Morocco_Airborne_Secure2025!

# Sauvegarder: Ctrl+O, Enter, Ctrl+X
```

### Étape 4: Redémarrer avec Base de Données Neuve

```bash
# Démarrer tous les services (avec nouvelle base de données vierge)
docker-compose up -d

# IMPORTANT: Attendre 3 MINUTES pour l'initialisation
echo "⏱️  Attente de 3 minutes pour l'initialisation..."
sleep 180

# Vérifier l'état des services
docker-compose ps
```

**Vous devriez voir tous les services "Up":**
```
NAME                     STATUS
compreface-postgres-db   Up
compreface-admin         Up
compreface-api           Up
compreface-core          Up
compreface-ui            Up
1bip-dashboard           Up
1bip-camera-service      Up (ou Restarting si pas de clé API)
```

### Étape 5: Vérifier les Logs de la Base de Données

```bash
# Vérifier qu'il n'y a PLUS d'erreurs d'authentification
docker-compose logs compreface-postgres-db | grep -i "fatal\|error"
```

**Si vous voyez encore des erreurs d'authentification**, la base de données n'a pas été réinitialisée. Retournez à l'Étape 1 et utilisez:

```bash
# Force la suppression des volumes
docker-compose down
docker volume ls | grep compreface
docker volume rm comprefacemodeling_postgres-data
docker volume rm comprefacemodeling_embedding-data

# Puis redémarrer
docker-compose up -d
```

### Étape 6: Accéder à l'Interface CompreFace

```bash
# Ouvrir dans votre navigateur
open http://localhost:8000
```

**Première Connexion:**
1. Cliquez sur **"Sign Up"** (Créer un compte)
2. Email: `admin@1bip.ma`
3. Mot de passe: `VotreMotDePasseSecurise123!`
4. Connectez-vous

---

## 🍎 Optimisation pour M3 Max (ARM64)

### Problème de Performance

Les images Docker CompreFace sont construites pour **Intel/AMD (amd64)**, pas pour **Apple Silicon (arm64)**. Votre M3 Max utilise Rosetta 2 pour les émuler, ce qui est:
- ✅ Fonctionnel (ça marche)
- ❌ LENT (3-5x plus lent)
- ❌ Consomme plus d'énergie

### Solution 1: Activer Rosetta 2 dans Docker Desktop (Rapide)

**Si vous utilisez Docker Desktop:**

1. Ouvrir Docker Desktop
2. Settings (⚙️) → Features in development
3. Cocher **"Use Rosetta for x86/amd64 emulation on Apple Silicon"**
4. Apply & Restart
5. Redémarrer vos services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

Cela améliore les performances d'émulation de ~30%.

### Solution 2: Build Natif ARM64 (Optimal mais Complexe)

CompreFace ne fournit pas d'images ARM64 officielles. Pour de meilleures performances, vous devriez:

1. **Cloner le repo CompreFace original**
2. **Builder les images localement** pour ARM64
3. **Modifier docker-compose.yml** pour utiliser vos images locales

**C'est complexe et nécessite ~30 minutes de build.** Je peux vous guider si nécessaire.

### Solution 3: Attendre les Images ARM64 Officielles

CompreFace travaille sur des images ARM64 natives. En attendant, l'émulation Rosetta 2 fonctionne correctement pour votre usage (300-500 personnes).

---

## 🔍 Vérification que Tout Fonctionne

### Test 1: Base de Données

```bash
# Vérifier la connexion à la base de données
docker-compose exec compreface-postgres-db psql -U postgres -d morocco_1bip_frs -c "\dt"
```

**Devrait afficher une liste de tables** (users, faces, etc.)

### Test 2: API CompreFace

```bash
# Tester l'API CompreFace
curl http://localhost:8000
```

**Devrait retourner du HTML** (page de login)

### Test 3: Dashboard

```bash
# Ouvrir le dashboard
open http://localhost:5000
```

**Devrait afficher le tableau de bord en français** 🇫🇷

### Test 4: Service Caméra

```bash
# Vérifier les logs de la caméra
docker-compose logs 1bip-camera-service
```

**Vous verrez:**
- ❌ Si API key manquante: `API key not configured`
- ✅ Si API key OK mais caméra non configurée: `RTSP connection error`
- ✅ Si tout OK: `Camera service running`

---

## 📝 Checklist de Résolution

Cochez au fur et à mesure:

- [ ] Étape 1: Services arrêtés et volumes supprimés (`docker-compose down -v`)
- [ ] Étape 2: Mot de passe vérifié dans `.env`
- [ ] Étape 3: Mot de passe vérifié dans `camera_config.env`
- [ ] Étape 4: Services redémarrés (`docker-compose up -d`)
- [ ] Étape 5: Attendu 3 minutes
- [ ] Étape 6: Vérifié les logs PostgreSQL (pas d'erreur auth)
- [ ] Étape 7: CompreFace UI accessible (http://localhost:8000)
- [ ] Étape 8: Compte admin créé
- [ ] Étape 9: Dashboard accessible (http://localhost:5000)

---

## 🚨 Si Ça Ne Fonctionne Toujours Pas

### Diagnostic Avancé

```bash
# 1. Vérifier TOUS les logs
docker-compose logs > logs_complets.txt

# 2. Vérifier les volumes Docker
docker volume ls

# 3. Vérifier l'espace disque
df -h

# 4. Vérifier la mémoire disponible
docker stats --no-stream
```

### Réinitialisation TOTALE (Option Nucléaire)

Si rien ne fonctionne, réinitialisation complète:

```bash
# ATTENTION: Ceci supprime TOUT (images, conteneurs, volumes)
docker-compose down -v
docker system prune -a --volumes -f

# Puis recommencer depuis le début
docker-compose up -d
```

---

## 📞 Commandes de Diagnostic Utiles

```bash
# État des services
docker-compose ps

# Logs d'un service spécifique
docker-compose logs [service-name]

# Suivre les logs en temps réel
docker-compose logs -f [service-name]

# Redémarrer un service spécifique
docker-compose restart [service-name]

# Entrer dans un conteneur
docker-compose exec [service-name] /bin/bash

# Vérifier les variables d'environnement d'un service
docker-compose exec [service-name] env | grep -i postgres
```

---

## 🎯 Workflow de Résolution Rapide

**Si vous voyez des erreurs de mot de passe PostgreSQL:**

```bash
# Solution en 4 commandes
docker-compose down -v
docker-compose up -d
sleep 180
open http://localhost:8000
```

**Si le service caméra redémarre en boucle:**

C'est **NORMAL** sans clé API configurée. Vous devez:
1. Créer une application dans CompreFace UI
2. Copier la clé API
3. Mettre à jour `camera_config.env`
4. Redémarrer: `docker-compose restart 1bip-camera-service`

---

## ✅ Résultat Attendu Final

Une fois tout corrigé:

```bash
$ docker-compose ps

NAME                     STATUS
compreface-postgres-db   Up 5 minutes
compreface-admin         Up 5 minutes
compreface-api           Up 5 minutes
compreface-core          Up 5 minutes (healthy)
compreface-ui            Up 5 minutes
1bip-dashboard           Up 5 minutes (healthy)
1bip-camera-service      Up 5 minutes
```

**Accès:**
- 🌐 CompreFace UI: http://localhost:8000 (Fonctionne! ✅)
- 📊 Dashboard 1BIP: http://localhost:5000 (Fonctionne! ✅)
- 📹 Service Caméra: En attente de configuration API

---

## 🇲🇦 1BIP - 1ère Brigade d'Infanterie Parachutiste
### Forces Armées Royales Marocaines - Troupes Aéroportées

**CLASSIFIÉ - USAGE MILITAIRE UNIQUEMENT**

---

*Guide généré avec [Claude Code](https://claude.com/claude-code)*
