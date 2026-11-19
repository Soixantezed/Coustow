# Visuels culinaires : prompts IA et retouche

## Formule de prompt (en anglais : meilleurs résultats)
```
[Sujet précis + ingrédients visibles], [présentation / contenant], [décor & surface],
[lumière], [angle & cadrage], [ambiance & palette], [espace réservé au texte],
professional food photography, appetizing, high detail,
no text, no letters, no logo, no watermark
```

## Briques prêtes à l'emploi
**Lumière**
- warm side window light, soft shadows : naturel, bistrot, brunch
- dramatic low-key lighting, dark moody background : gastro, burger premium, cocktail
- bright airy daylight, white background : healthy, pâtisserie, boulangerie
- golden hour sunlight, terrace : terrasse, apéro, été
- neon reflections, night street : street food, asiatique, bar

**Angle**
- 45-degree angle : burger, pizza à la part, assiette dressée (angle naturel, le plus vendeur)
- eye-level, front view : burger, sandwich, cocktail, pile de pancakes (montre la hauteur)
- top-down flat lay : pizza entière, bowls, table de partage, brunch, plateau de sushi
- extreme close-up, macro : texture (fromage qui file, sauce qui coule, croûte)

**Effets d'appétit** (en ajouter 1 ou 2, pas plus)
steam rising · melted cheese stretching · sauce dripping · crispy golden crust · glistening ·
fresh herbs sprinkled · water droplets on glass (boisson fraîche) · flaky layers · sesame seeds

**Décor et surface**
rustic wooden table · dark slate · white marble · linen napkin · kraft paper (street) ·
terracotta plate · cast iron skillet · wooden pizza peel · ceramic handmade plate

**Espace texte** (indispensable pour l'affiche)
- `subject in upper half, empty dark space in lower third` : template bandeau-bas
- `subject in lower half, clean empty background above` : template titre-haut
- `subject centered with generous negative space around` : templates minimal et story
- `subject on the right side, empty space on the left` : format paysage, titre à gauche

## Exemples
**Burger street**
```
A double smash burger with melted cheddar dripping, caramelized onions, toasted brioche bun,
on kraft paper with crispy fries, dark moody background, dramatic side lighting,
eye-level close-up, subject in upper half with empty dark space in lower third,
professional food photography, appetizing, high detail, no text, no letters, no logo, no watermark
```
→ `--format portrait`, puis poster `--template bandeau-bas --style street`

**Pizza napolitaine**
```
Neapolitan margherita pizza with leopard-spotted puffy crust, fresh basil, glistening mozzarella,
on a wooden peel, wood-fired oven glowing softly in the blurred background, warm light,
45-degree angle, subject in lower half with clean dark space above,
professional food photography, no text, no letters, no logo, no watermark
```

**Assiette gastro**
```
Elegant plated dish: seared scallops on cauliflower purée, hazelnut butter, micro herbs,
on a matte black handmade ceramic plate, dark slate surface, low-key lighting, shallow depth of field,
45-degree angle, generous negative space, fine dining editorial photography, no text, no logo
```

**Brunch**
```
Stack of fluffy pancakes with maple syrup pouring, fresh berries, latte art coffee beside,
white marble table, bright airy morning window light, top-down 30-degree angle,
subject centered with space above, lifestyle food photography, no text, no logo
```

## Améliorer une vraie photo du client (toujours préférable)
`imagegen.py edit photo.jpg "<consigne>"`. Formule : **ce qui change** + **ce qui reste identique**.
- « Make the lighting warmer and more appetizing, add soft shallow depth of field to the background, keep the dish exactly identical (same ingredients, same plate, same portion size) »
- « Replace the background with a dark slate surface and moody lighting, keep the burger exactly as it is »
- « Remove the clutter on the table (phone, napkins), keep the plate unchanged »
- « Extend the image upward with matching background to leave space for a title »

Ou en local, sans IA :
- `imgtool.py removebg photo.jpg --trim` pour détourer le plat ;
- puis le poser sur un fond généré : `imagegen.py generate "dark slate texture background, empty, top-down…"`.

## Garde-fous
- Le visuel doit **correspondre au produit réel** : pas de portion gonflée ni d'ingrédient absent de la recette. Sinon, ajoute « Photo non contractuelle » et préviens l'utilisateur. Une promesse non tenue fait des avis négatifs.
- Ne génère pas de marque tierce (logo Coca-Cola…), de personne réelle identifiable ou de style d'un photographe nommé.
- Rejette une image qui a des mains déformées, des couverts fondus, du texte parasite ou un aliment « plastique ».
