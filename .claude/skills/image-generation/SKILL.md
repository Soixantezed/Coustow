---
name: image-generation
description: Génère des images à partir d'un texte et modifie des images existantes avec une consigne, via l'API OpenAI (gpt-image) ou Google Gemini. À utiliser quand l'utilisateur demande de créer, dessiner, générer une image, une illustration, un visuel, un logo, ou de modifier une image avec l'IA (« change le fond », « ajoute un logo », « mets-le en style aquarelle »…). Les résultats sont enregistrés dans outputs/. Pour du traitement local sans IA (redimensionner, détourer, compresser, filigrane, formats réseaux sociaux), utiliser plutôt le skill image-processing.
---

# Image generation (OpenAI / Gemini)

Tout passe par un seul script : `~/.claude/skills/image-generation/scripts/imagegen.py`
(Python 3 + `requests`, aucune autre dépendance).

## Clés API

- **OpenAI** (fournisseur par défaut) : variable `OPENAI_API_KEY`.
- **Gemini** (optionnel) : variable `GEMINI_API_KEY` (ou `GOOGLE_API_KEY`), avec `--provider gemini`.
- Le script choisit OpenAI si sa clé existe, sinon Gemini. Si aucune clé n'est définie, il s'arrête avec un message clair :
  dis à l'utilisateur quelle variable définir. Ne demande jamais de coller la clé dans le chat.
- Modèles par défaut : `gpt-image-2` (OpenAI ; `gpt-image-1` a été retiré) et `gemini-2.5-flash-image` (Gemini).
  Change-les avec `--model`, ou avec les variables `OPENAI_IMAGE_MODEL` / `GEMINI_IMAGE_MODEL`.

## Générer une image à partir d'un texte

```bash
python3 ~/.claude/skills/image-generation/scripts/imagegen.py generate \
  "Une tasse de café fumante sur une table en bois, lumière du matin, photo réaliste" \
  --format paysage --name cafe-matin
```

Options :
- `--format` : `carre` (défaut), `portrait` ou `paysage`. Les formes anglaises `square`, `portrait` et `landscape` marchent aussi.
  - OpenAI : 1024x1024, 1024x1536 ou 1536x1024.
  - Gemini : ratio 1:1, 3:4 ou 4:3.
- `--quality` : `low`, `medium`, `high` ou `auto` (OpenAI uniquement, `auto` par défaut).
- `--n 3` : plusieurs variantes (OpenAI uniquement).
- `--background transparent` : fond transparent en PNG (OpenAI uniquement).
- `--provider openai|gemini`, `--model ...`
- `--name` : nom court du fichier (sinon déduit du prompt). `--out-dir` : `outputs` par défaut.

## Modifier une image existante

```bash
python3 ~/.claude/skills/image-generation/scripts/imagegen.py edit photo.jpg \
  "Remplace le fond par une plage au coucher du soleil, garde la personne identique" \
  --name photo-plage
```

- Pour ajouter un logo, passe plusieurs images. La première est l'image à modifier, les suivantes servent de références :
  `edit photo.jpg logo.png "Ajoute ce logo en bas à droite du t-shirt"`
- `--mask masque.png` (OpenAI) : PNG de la même taille que l'image. Les zones transparentes sont celles à modifier.
- `--format` : même valeurs que pour `generate`. Par défaut, le script prend le format le plus proche de l'image source.

## Sorties

- Les fichiers sont enregistrés dans `outputs/`, par rapport au dossier courant (créé si besoin).
- Nom des fichiers : `AAAAMMJJ-HHMMSS_<action>_<nom-court>[_N].png`, par exemple `20261119-143205_generate_cafe-matin.png`.
- Le script affiche le chemin de chaque fichier créé. Montre le résultat à l'utilisateur, par exemple en lisant l'image avec l'outil Read.

## Conseils pour les prompts

- Décris le sujet, le style (photo, illustration, 3D, aquarelle…), la lumière, le cadrage et les couleurs.
- Pour une modification, dis ce qui doit **changer** et ce qui doit **rester identique** (visage, texte, produit…).
- Pour un texte dans l'image, mets-le entre guillemets dans le prompt.
- Après la génération, le skill **image-processing** peut adapter le résultat : recadrage Instagram, compression, WebP, filigrane, etc.

## Erreurs fréquentes

- `401` : clé invalide. `429` : quota ou limite de débit atteint, attends un peu ou vérifie la facturation.
- `400` avec `moderation` / `safety` : la demande a été refusée par le filtre de contenu. Reformule-la.
- Les modèles `gpt-image` peuvent demander une organisation vérifiée sur platform.openai.com.
