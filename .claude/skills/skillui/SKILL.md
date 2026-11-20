---
name: skillui
description: Extrait le design system complet (couleurs, typographies, espacements, animations, composants, captures) d'un site web, d'un dépôt git ou d'un dossier local avec la CLI SkillUI, pour ensuite construire une UI fidèle à ce style. À utiliser quand l'utilisateur veut « reproduire le style de tel site », « extraire le design system de… », ou construire une page qui ressemble à un site existant.
---

# SkillUI : extraire un design system

SkillUI (npm `skillui`, source github.com/amaancoderx/npxskillui) est une CLI d'analyse
statique, sans IA ni clé API. Elle génère un dossier contenant `SKILL.md`, `CLAUDE.md`,
les tokens et des captures, que l'on lit ensuite pour construire l'UI.

## Lancer l'extraction

Pas besoin d'installation globale : utiliser `npx`.

```bash
# Site web
npx -y skillui --url https://exemple.com

# Dépôt git ou dossier local
npx -y skillui --repo https://github.com/owner/repo
npx -y skillui --dir ./mon-projet

# Mode ultra (extraction visuelle complète via Playwright, plus lent)
npx -y skillui --url https://exemple.com --mode ultra
```

Autres options : `--out <dossier>`, `--name <nom>`, `--format design-md|skill|both`, `--screens <n>` (ultra). Voir `npx -y skillui --help`.
Le mode ultra a besoin de Playwright ; s'il manque : `npm install playwright && npx playwright install chromium`.

## Utiliser le résultat

1. La sortie est créée dans `<nom>-design/` (ex. `notion-design/`) sous `--out`. Y lire `SKILL.md`, `CLAUDE.md` et `DESIGN.md`,
   puis les fichiers de tokens et les captures d'écran.
2. Construire l'UI demandée en respectant strictement les couleurs, polices, espacements,
   rayons, ombres et animations extraits.
3. S'inspirer du style, sans copier logos, marques ni contenus protégés du site source.
