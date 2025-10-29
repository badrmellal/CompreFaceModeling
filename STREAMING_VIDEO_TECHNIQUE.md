# 📹 Streaming Vidéo - Informations Techniques

## ✅ État Actuel du Streaming

### Configuration Actuelle
Le système utilise **MJPEG (Motion JPEG)** pour le streaming vidéo en direct vers le dashboard.

**Caractéristiques:**
- **Protocole:** HTTP/MJPEG (multipart/x-mixed-replace)
- **Port:** 5001
- **Résolution stream:** 1280x720 (720p)
- **Qualité JPEG:** 60%
- **FPS:** 25 images/seconde
- **Bande passante:** ~4-6 Mbps

### Indépendance du Stream
**IMPORTANT:** Le stream vidéo est **complètement indépendant** de l'intervalle de rafraîchissement du dashboard (30 secondes).

- ✅ **Stream vidéo:** Temps réel continu (25 FPS)
- ✅ **Rafraîchissement dashboard:** Toutes les 30 secondes (statistiques, tableaux)
- ✅ **Reconnaissance faciale:** Full HD (résolution complète)

Le changement de 10s → 30s affecte **uniquement** les requêtes API pour les statistiques, **PAS** le stream vidéo!

## 🔧 Architecture Actuelle

### Pipeline Séparé

```
Caméra Hikvision (8MP)
      ↓
[RTSP Stream]
      ↓
Service Caméra (Python/OpenCV)
      ├─→ [Pipeline 1] Reconnaissance Faciale (Full HD 1920x1080)
      │                    ↓
      │              CompreFace API
      │                    ↓
      │              Base de données
      │
      └─→ [Pipeline 2] Streaming Web (720p optimisé)
                           ↓
                    Serveur MJPEG (port 5001)
                           ↓
                    Dashboard (navigateur)
```

### Avantages de l'Architecture Actuelle

1. **Séparation des préoccupations:**
   - La reconnaissance faciale ne ralentit pas le stream
   - Le stream ne ralentit pas la reconnaissance

2. **Optimisation indépendante:**
   - Reconnaissance: Full HD pour précision maximale
   - Stream: 720p pour fluidité maximale

3. **Simplicité:**
   - Pas de dépendances complexes
   - Compatible tous navigateurs
   - Facile à déboguer

## 🚀 Options d'Amélioration Future

### Option 1: WebSocket Streaming (Recommandé)
**Avantages:**
- Latence réduite (~20-50ms vs 50-100ms MJPEG)
- Bande passante optimisée
- Bidirectionnel (contrôles PTZ possibles)

**Inconvénients:**
- Implémentation plus complexe
- Nécessite JavaScript côté client pour décoder
- Support navigateur à vérifier

**Effort:** 2-3 jours de développement

### Option 2: WebRTC (Avancé)
**Avantages:**
- Latence ultra-faible (<50ms)
- P2P possible
- Standard moderne

**Inconvénients:**
- Très complexe à implémenter
- Nécessite serveur STUN/TURN
- Overhead important pour un seul stream

**Effort:** 1-2 semaines de développement

### Option 3: HLS (HTTP Live Streaming)
**Avantages:**
- Scalable (plusieurs clients)
- Adaptive bitrate possible
- Support mobile excellent

**Inconvénients:**
- Latence élevée (2-10 secondes)
- Nécessite segmentation
- Pas adapté pour surveillance temps réel

**Effort:** 3-5 jours de développement

## 📊 Comparaison des Protocoles

| Protocole | Latence | Bande Pass. | Complexité | Temps Réel | Recommandé |
|-----------|---------|-------------|------------|------------|------------|
| **MJPEG** (actuel) | 50-100ms | Moyen | Faible | ✅ Bon | ✅ Oui |
| WebSocket | 20-50ms | Faible | Moyenne | ✅✅ Excellent | ✅ Future |
| WebRTC | <50ms | Très faible | Élevée | ✅✅ Excellent | ⚠️ Overkill |
| HLS | 2-10s | Faible | Moyenne | ❌ Mauvais | ❌ Non |
| RTSP | N/A | - | - | - | ❌ Pas supporté navigateur |

## ⚠️ RTSP Direct dans Navigateur

**RTSP n'est PAS supporté nativement par les navigateurs web.**

Pour utiliser RTSP, il faut obligatoirement:
1. Un serveur intermédiaire qui convertit RTSP → autre protocole
2. Un plugin navigateur (déprécié/non sécurisé)
3. Une application native (pas web)

**C'est exactement ce que nous faisons déjà:**
```
RTSP (Caméra) → Python/OpenCV → MJPEG (Web)
```

## 💡 Recommandations

### Pour l'instant: Garder MJPEG Optimisé ✅
Le système actuel est **suffisant** pour une surveillance militaire temps réel:
- Latence acceptable (50-100ms)
- Qualité d'image bonne
- Fiabilité prouvée
- Facile à maintenir

### Prochaine étape: WebSocket (Optionnel)
Si vous voulez améliorer encore la latence, implémenter WebSocket:
- Gain de latence: ~50ms → ~30ms
- Réduction bande passante: ~20-30%
- Complexité modérée

## 🔍 Monitoring du Stream

### Vérifier les Performances

**1. Vérifier les logs:**
```bash
docker-compose logs -f camera-service | grep "Stream"
```

Vous devriez voir:
```
Stream configured: 1280x720 @ 25fps, quality=60%
New client connected to MJPEG stream (1280x720 @ 25fps)
```

**2. Vérifier le health check:**
```bash
curl http://localhost:5001/stream/health
```

Réponse:
```json
{
  "status": "ok",
  "streaming": true,
  "frame_count": 12345
}
```

**3. Monitorer la bande passante:**
```bash
# Trafic réseau sur le port 5001
sudo iftop -i eth0 -f "port 5001"
```

## 📝 Conclusion

Le streaming vidéo actuel est **optimisé et performant** pour votre cas d'usage:

✅ **Temps réel:** 25 FPS, latence <100ms
✅ **Qualité:** 720p, suffisant pour surveillance
✅ **Fiabilité:** MJPEG éprouvé et stable
✅ **Indépendant:** Ne ralentit pas la reconnaissance faciale (Full HD)
✅ **Compatible:** Fonctionne sur tous navigateurs

**Aucune action immédiate nécessaire.** Le système fonctionne bien tel quel!

---

**Dernière mise à jour:** 2025-10-29
**Version:** 2.0
**Optimisations appliquées:** Oui (720p @ 60% qualité @ 25 FPS)
