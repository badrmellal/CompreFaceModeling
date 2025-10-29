# 🪂 Structure Organisationnelle 1BIP - Configuration Système

## 📋 Vue d'Ensemble

Ce document décrit la structure organisationnelle de la **1ère Brigade d'Infanterie Parachutiste (1BIP)** telle qu'implémentée dans le système de reconnaissance faciale.

## 🏢 Bataillons et Unités

Le système utilise la structure militaire réelle de la 1BIP avec les bataillons suivants:

### Bataillons d'Infanterie Parachutiste
1. **1BCAS** - 1er Bataillon de Commandement et d'Appui au Service
2. **10BPAG** - 10ème Bataillon Parachutiste d'Assaut Génie
3. **11BPAG** - 11ème Bataillon Parachutiste d'Assaut Génie
4. **12BPAG** - 12ème Bataillon Parachutiste d'Assaut Génie
5. **13BIP** - 13ème Bataillon d'Infanterie Parachutiste
6. **14BIP** - 14ème Bataillon d'Infanterie Parachutiste
7. **15BIP** - 15ème Bataillon d'Infanterie Parachutiste

### Unités Spéciales
8. **CITAP** - Centre d'Instruction des Troupes Aéroportées
9. **VISITORS** - Visiteurs

## 📁 Compagnies et Sections (Sous-Départements)

Les compagnies et sections sont saisies **manuellement** pour chaque bataillon selon son organisation interne.

### Exemples de Sous-Départements:

**Pour les bataillons d'infanterie (13BIP, 14BIP, 15BIP):**
- Compagnie 1
- Compagnie 2
- Compagnie 3
- Compagnie 4
- Section Commandement
- Section Appui
- Section Transmissions

**Pour les bataillons d'assaut génie (10BPAG, 11BPAG, 12BPAG):**
- Compagnie Génie
- Section Déminage
- Section Pontage
- Section Travaux

**Pour 1BCAS:**
- Section État-Major
- Section Logistique
- Section Santé
- Section Transmissions
- Section Administration

**Pour CITAP:**
- Section Formation Basique
- Section Formation Avancée
- Section Instructeurs
- Section Entraînement

**Pour VISITORS:**
- (Laisser vide ou indiquer l'organisation d'origine)

## 🔧 Implémentation Technique

### Backend (API)
**Fichier:** `dashboard-service/src/app.py`

```python
departments = [
    '1BCAS',    # 1er Bataillon de Commandement et d'Appui au Service
    '10BPAG',   # 10ème Bataillon Parachutiste d'Assaut Génie
    '11BPAG',   # 11ème Bataillon Parachutiste d'Assaut Génie
    '12BPAG',   # 12ème Bataillon Parachutiste d'Assaut Génie
    '13BIP',    # 13ème Bataillon d'Infanterie Parachutiste
    '14BIP',    # 14ème Bataillon d'Infanterie Parachutiste
    '15BIP',    # 15ème Bataillon d'Infanterie Parachutiste
    'CITAP',    # Centre d'Instruction des Troupes Aéroportées
    'VISITORS'  # Visiteurs
]
```

### Frontend (HTML)
**Fichier:** `dashboard-service/src/templates/dashboard.html`

**Formulaire d'ajout de personnel:**
- Bataillon/Unité: Dropdown avec les 9 bataillons
- Compagnie/Section: Input text (saisie manuelle)

**Filtres de la galerie:**
- Bataillon/Unité: Dropdown dynamique (depuis base de données)
- Compagnie/Section: Dropdown dynamique (depuis base de données)

### JavaScript
**Fichier:** `dashboard-service/src/static/js/dashboard.js`

- **Pas de cascade automatique** pour les sous-départements
- Départements hardcodés dans le HTML
- Sous-départements saisis manuellement

## 📊 Utilisation

### Ajouter un Nouveau Personnel

1. **Accéder à l'onglet:** "👥 Gestion du Personnel"
2. **Remplir le formulaire:**
   - Nom Complet: Ex. "Capitaine Ahmed Bennani"
   - Grade/Rang: Ex. "Capitaine"
   - **Bataillon/Unité:** Sélectionner dans la liste (obligatoire)
   - **Compagnie/Section:** Saisir manuellement (ex: "Compagnie 1")
   - Photos: Minimum 3 photos du visage
3. **Cliquer sur:** "✅ Ajouter Personnel"

### Filtrer dans la Galerie Photos

1. **Accéder à l'onglet:** "📸 Galerie Photos"
2. **Utiliser les filtres:**
   - Nom: Recherche par nom
   - **Bataillon/Unité:** Filtrer par bataillon
   - **Compagnie/Section:** Filtrer par compagnie
   - Statut: Autorisé / Non Autorisé

## 🔍 Recherche et Filtrage

Les filtres dans la galerie sont **dynamiques** et se remplissent automatiquement avec les valeurs réelles présentes dans la base de données:

- **Bataillons:** Affiche uniquement les bataillons qui ont du personnel enregistré
- **Compagnies:** Affiche uniquement les compagnies qui ont du personnel enregistré

## 📝 Conventions de Nommage

### Bataillons
- Format: `[NUMERO][TYPE]`
- Exemples: `1BCAS`, `13BIP`, `10BPAG`
- **Toujours en MAJUSCULES**

### Compagnies/Sections
- Format libre (saisie manuelle)
- Exemples recommandés:
  - "Compagnie 1", "Compagnie 2", etc.
  - "Section Commandement"
  - "Section Transmissions"
  - "Section Appui"

### Grades
- Format: Grade complet
- Exemples: "Capitaine", "Lieutenant", "Adjudant-Chef", "Sergent"

## 🗄️ Stockage des Données

Les informations sont stockées dans:

1. **CompreFace** (Reconnaissance faciale)
   - Subject name = Nom du personnel
   - Metadata = JSON avec département, sous-département, grade

2. **PostgreSQL** (Logs d'accès)
   - Table: `access_logs`
   - Colonnes: `department`, `sub_department`, `subject_name`, etc.

## ⚠️ Notes Importantes

1. **Bataillons fixes:** La liste des bataillons est fixe (9 unités)
2. **Compagnies flexibles:** Les compagnies sont saisies manuellement
3. **Pas de cascade:** Pas de liste prédéfinie de compagnies par bataillon
4. **Filtres dynamiques:** Les filtres montrent uniquement les valeurs existantes

## 🔄 Modification de la Structure

Si vous devez ajouter/modifier des bataillons:

1. **Backend:** Éditer `dashboard-service/src/app.py` → fonction `get_department_config()`
2. **Frontend:** Éditer `dashboard-service/src/templates/dashboard.html` → section formulaire
3. **Rebuild:** `docker-compose up -d --build dashboard-service`

## 📞 Support

Pour toute question sur la structure organisationnelle ou l'utilisation du système, contactez l'administrateur système de la 1BIP.

---

**Dernière mise à jour:** 2025-10-29
**Version système:** 2.0
**Classification:** USAGE MILITAIRE - 1BIP FAR
