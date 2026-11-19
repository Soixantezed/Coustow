# Design : règles et contrôle qualité

## Lisibilité selon le support
| Support | Distance de lecture | Titre | Corps de texte |
|---|---|---|---|
| Affiche A3/A2 en vitrine | 3 à 5 m | ≥ 8 % de la hauteur | ≥ 2,5 % |
| A4 en vitrine ou au mur | 2 à 3 m | ≥ 6 % | ≥ 2 % |
| Flyer A5/DL, chevalet de table | 40 cm | ≥ 5 % | ≥ 1,8 % (8 pt minimum à l'impression) |
| Écran TV en salle | 3 à 6 m | énorme, 5 à 7 mots au maximum, contraste maximal | |
| Post / story (sur téléphone) | 30 cm, scroll rapide | lisible en vignette ; tester à 25 % de la taille | |

## Hiérarchie (ordre de lecture voulu)
1. Visuel du produit
2. Titre
3. Prix ou offre
4. CTA
5. Infos pratiques et logo

Si l'œil part ailleurs (logo trop gros, badge trop flashy, fond chargé), corrige.

## Couleurs
- Contraste texte/fond d'au moins **4,5:1** (WCAG AA). Sur une photo, garde le dégradé (`--overlay` 0.7 à 0.9) ou utilise `split` ou `cadre`.
- **1 couleur d'accent**, réservée au prix, au badge et au CTA. L'œil apprend où trouver l'action.
- Si le client a une charte, passe `--accent` / `--panel` / `--text`. Sinon, prends la palette du style.
- Pour reprendre une couleur de la photo : `python3 -c "from PIL import Image; im=Image.open('x.png').convert('RGB').resize((1,1)); print('#%02x%02x%02x'%im.getpixel((0,0)))"`. Assombris-la ensuite pour `--panel`.

## Impression
- 300 dpi au format final. Le visuel source doit être assez grand : une image IA de 1024 à 1536 px suffit pour un A5, juste pour un A4 et faible pour un A3. Pour l'A3 et plus, demande la meilleure qualité, ou préviens que la photo sera un peu douce (le texte vectoriel reste net).
- `--bleed 3` : 3 mm de fonds perdus, demandés par la plupart des imprimeurs en ligne. Le texte reste à au moins 5 mm du bord de coupe : la marge de `poster.py` le garantit.
- Le PDF est en RVB. La plupart des imprimeurs en ligne convertissent en CMJN. Préviens que les couleurs très vives (jaune fluo, rouge pur) seront un peu ternes à l'impression.

## Checklist avant livraison
- [ ] Un seul message clair. Le test des 3 secondes est réussi (quoi, combien, où et quand).
- [ ] Le visuel est appétissant, net, sans artefact IA, et fidèle au produit.
- [ ] Le titre est lisible à la distance prévue, avec un bon contraste et rien de coupé.
- [ ] Le prix est exact, au format français « 12,90 € » (virgule, espace avant €).
- [ ] Orthographe, accents, majuscules, horaires et numéro de téléphone sont vérifiés : relis tous les textes.
- [ ] Le CTA est présent et concret.
- [ ] Logo, adresse et réseaux sont présents (sauf en story, si c'est épuré).
- [ ] Les mentions légales sont là si nécessaire (alcool, photo non contractuelle, conditions de l'offre).
- [ ] Les déclinaisons sont cohérentes (même accroche, même style).
- [ ] Le PDF imprimeur avec fonds perdus est fourni si c'est pour l'impression.
