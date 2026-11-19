---
name: image-processing
description: Traitement d'images local, sans IA générative ni clé API, avec Python (Pillow, rembg) et ImageMagick. Sert à redimensionner, recadrer, détourer (supprimer le fond), compresser, convertir (PNG/JPG/WebP/AVIF), ajouter un texte ou un logo en filigrane, et décliner une image aux formats des réseaux sociaux (post et story Instagram, bannière Facebook, LinkedIn, X, YouTube…). À utiliser dès que l'utilisateur veut modifier techniquement une image ou un dossier d'images. Pour créer une image ou la modifier par IA à partir d'une consigne, utiliser image-generation.
---

# Image processing (local)

Outil principal : `~/.claude/skills/image-processing/scripts/imgtool.py`
(dans les exemples ci-dessous, `T` désigne ce chemin).

- Chaque commande accepte **une ou plusieurs images, ou un dossier** (traitement par lot).
- Les résultats vont dans `outputs/`, sous le nom `<nom-source>_<opération>.<ext>`. Change la destination avec `-o` : un fichier si une seule image, sinon un dossier.
- L'orientation EXIF des photos est respectée. Le passage en JPG remplit la transparence en blanc.
- Le script affiche le chemin, les dimensions et le poids de chaque fichier. Montre ensuite le résultat à l'utilisateur, par exemple avec l'outil Read.

## Dépendances

- Pillow : obligatoire.
- rembg : uniquement pour le détourage. Installation : `pip install "rembg[cpu]"`. Au premier usage, il télécharge un modèle d'environ 170 Mo dans `~/.u2net`.
- ImageMagick : facultatif, pour les cas avancés (voir plus bas). Commande `magick` en v7 ou `convert` en v6.

Si un module manque, installe-le avec pip, puis relance la commande.

## Recettes

| Besoin | Commande |
|---|---|
| Infos (taille, format, poids) | `python3 T info photo.jpg` |
| Redimensionner, ratio conservé | `python3 T resize photo.jpg 1920x` (largeur), `x1080` (hauteur), `1200x1200` (dans la boîte), `50%` |
| Taille exacte, recadrée | `python3 T resize photo.jpg 1080x1350 --mode cover --focus haut` |
| Taille exacte, image entière + fond | `python3 T resize logo.png 1200x630 --mode contain --bg "#0B1F3A"` (`--bg flou` ou `transparent` possibles) |
| Recadrer à un ratio | `python3 T crop photo.jpg --ratio 4:5 --focus centre` |
| Recadrer une zone | `python3 T crop photo.jpg --box 100,50,800,600` (x,y,largeur,hauteur) |
| Rogner les bords unis | `python3 T crop produit.png --trim` |
| Détourer | `python3 T removebg produit.jpg --trim` → PNG transparent |
| Détourer une personne / des cheveux | `python3 T removebg portrait.jpg --model u2net_human_seg --matting` (ou `--model isnet-general-use`) |
| Détourer + fond uni | `python3 T removebg produit.jpg --bg white` |
| Compresser | `python3 T compress photo.jpg -q 80 --max-size 2000` |
| Viser un poids | `python3 T compress photo.jpg --target-kb 200 --format webp` |
| Alléger un PNG | `python3 T compress image.png --colors 128` |
| Convertir | `python3 T convert dossier/ --to webp -q 85` (`--lossless` pour du WebP sans perte) |
| Filigrane texte | `python3 T text photo.jpg --text "© Coustow 2026" --position bas-droite --opacity 0.6` |
| Filigrane en mosaïque | `python3 T text photo.jpg --text "APERÇU" --position mosaique --rotate 30 --opacity 0.25` |
| Logo en filigrane | `python3 T logo photo.jpg --logo logo.png --position bas-droite --scale 0.15 --opacity 0.8` |
| Formats réseaux sociaux | `python3 T social visuel.jpg --preset instagram-post instagram-story facebook-banniere` |
| Tous les formats d'un coup | `python3 T social visuel.jpg --preset tous` |

Options du filigrane :
- Positions : `haut-gauche`, `haut`, `haut-droite`, `gauche`, `centre`, `droite`, `bas-gauche`, `bas`, `bas-droite`, `mosaique`.
- Taille du texte : `--size` (en px) ou `--scale` (part du petit côté, 5 % par défaut).
- Autres réglages : `--color`, `--font chemin.ttf`.

Pour enchaîner plusieurs opérations, donne la sortie d'une étape en entrée de la suivante. Exemple :
`removebg` → `social --mode contain --bg "#F5F0E8"` → `logo`.

## Formats réseaux sociaux (`social --preset`)

| Preset | Taille (px) |
|---|---|
| instagram-post | 1080×1080 |
| instagram-portrait | 1080×1350 (4:5, le plus visible dans le fil) |
| instagram-paysage | 1080×566 |
| instagram-story / reel | 1080×1920 |
| facebook-post | 1200×630 |
| facebook-banniere | 1640×624 (couverture de page) |
| facebook-evenement | 1920×1005 |
| linkedin-post / linkedin-banniere | 1200×627 / 1584×396 |
| x-post / x-banniere | 1600×900 / 1500×500 |
| youtube-miniature | 1280×720 |
| pinterest | 1000×1500 |

Modes :
- `--mode cover` (défaut) remplit le cadre et recadre l'image. Règle le cadrage avec `--focus haut|bas|gauche|droite|centre`.
- `--mode contain` garde toute l'image, avec un fond `--bg flou` (défaut), une couleur ou `transparent`.

Pour une story, garde le texte et les éléments importants hors des 250 px du haut et du bas : l'interface d'Instagram les recouvre.

## ImageMagick : cas avancés

Sur cette machine, ImageMagick est en v6 : utilise `convert` et `mogrify`. En v7, remplace par `magick`.

```bash
convert in.jpg -resize 1080x1080^ -gravity center -extent 1080x1080 out.jpg          # cover
mogrify -path outputs -resize 1600x -quality 82 -format webp *.jpg                    # lot -> WebP
convert in.jpg -strip -interlace Plane -quality 80 out.jpg                            # supprime les métadonnées
convert in.png -fuzz 10% -transparent white out.png                                   # fond blanc uni -> transparent (simple)
convert in.jpg \( logo.png -resize 200x \) -gravity southeast -geometry +30+30 -composite out.jpg
convert *.png -delay 50 -loop 0 anim.gif                                              # GIF animé
convert in.jpg -modulate 105,120 -sharpen 0x1 out.jpg                                 # +luminosité, +saturation, netteté
montage img*.jpg -tile 3x -geometry 400x400+4+4 planche.jpg                           # planche contact
```

## Bonnes pratiques

- Ne remplace jamais l'original. Écris toujours dans `outputs/` ou dans un fichier `-o` différent.
- Choix du format :
  - Web : WebP, qualité 80 à 85.
  - Photo à imprimer ou à envoyer : JPG, qualité 90.
  - Transparence ou logo : PNG.
- Pour un détourage parfait des cheveux ou d'objets transparents, rembg a ses limites. Propose alors une retouche IA avec image-generation (`edit` + « supprime le fond »).
