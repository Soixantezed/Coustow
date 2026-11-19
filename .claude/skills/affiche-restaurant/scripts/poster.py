#!/usr/bin/env python3
"""Mise en page d'affiches / visuels publicitaires de restaurant.

Le visuel (photo ou image IA SANS texte) sert de fond ; le script pose la typographie
(vraies polices, accents parfaits), le prix, le badge, le logo, le CTA et les mentions,
puis exporte en PNG (+ PDF imprimeur avec fonds perdus).

Exemple :
  poster.py --bg burger.png --format a4 --template bandeau-bas --style street \
    --kicker "Nouveau" --title "Le Smash Double" --subtitle "Double steak, cheddar affiné, oignons confits" \
    --price "12,90 €" --price-label "menu" --cta "Commandez sur place ou en click & collect" \
    --footer "12 rue des Lilas, Lyon · 04 00 00 00 00" --logo logo.png --pdf --bleed 3
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

FONTS = Path(__file__).resolve().parent.parent / "fonts"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MM_PER_IN = 25.4

# ---------------------------------------------------------------- formats
PRINT_MM = {  # largeur x hauteur en mm (portrait)
    "a6": (105, 148), "a5": (148, 210), "a4": (210, 297), "a3": (297, 420),
    "a2": (420, 594), "a1": (594, 841), "dl": (99, 210),          # flyer DL
    "carre-21": (210, 210), "40x60": (400, 600), "chevalet-a5": (148, 210),
}
SCREEN_PX = {
    "instagram-post": (1080, 1080), "instagram-portrait": (1080, 1350),
    "story": (1080, 1920), "facebook-post": (1200, 630), "facebook-banniere": (1640, 624),
    "ecran-tv": (1920, 1080), "ecran-vertical": (1080, 1920), "google-business": (1200, 900),
    "uber-eats": (2880, 2304), "deliveroo": (1920, 1080),
}

# ---------------------------------------------------------------- styles
# title/body : (fichier, variation éventuelle) ; couleurs : panel, texte, accent, texte-sur-accent
STYLES = {
    "bistrot":   dict(title=("DMSerifDisplay-Regular.ttf", None), script=("DMSerifDisplay-Italic.ttf", None),
                      body="Poppins-Regular.ttf", upper=False,
                      panel="#1E2A24", text="#F6EFE3", accent="#C8553D", on_accent="#FFFFFF"),
    "gastro":    dict(title=("PlayfairDisplay-VF.ttf", b"SemiBold"), script=("PlayfairDisplay-Italic-VF.ttf", b"Regular"),
                      body="Poppins-Light.ttf", upper=False,
                      panel="#0E0E0E", text="#F2EDE4", accent="#B89B5E", on_accent="#0E0E0E"),
    "street":    dict(title=("Anton-Regular.ttf", None), script=("BebasNeue-Regular.ttf", None),
                      body="Poppins-Medium.ttf", upper=True,
                      panel="#111111", text="#FFFFFF", accent="#FFC300", on_accent="#111111"),
    "pizzeria":  dict(title=("BebasNeue-Regular.ttf", None), script=("Lobster-Regular.ttf", None),
                      body="Poppins-Regular.ttf", upper=True,
                      panel="#FBF6EE", text="#1F1F1F", accent="#C8102E", on_accent="#FFFFFF"),
    "cafe":      dict(title=("AbrilFatface-Regular.ttf", None), script=("Pacifico-Regular.ttf", None),
                      body="Poppins-Regular.ttf", upper=False,
                      panel="#F3E9DC", text="#3B2A20", accent="#8C5A3C", on_accent="#FFFFFF"),
    "fun":       dict(title=("Lobster-Regular.ttf", None), script=("Pacifico-Regular.ttf", None),
                      body="Poppins-SemiBold.ttf", upper=False,
                      panel="#FFF4E0", text="#2B1B17", accent="#E63946", on_accent="#FFFFFF"),
    "healthy":   dict(title=("DMSerifDisplay-Regular.ttf", None), script=("Pacifico-Regular.ttf", None),
                      body="Poppins-Regular.ttf", upper=False,
                      panel="#F1F5E9", text="#1F3A2B", accent="#6BA368", on_accent="#FFFFFF"),
    "asiatique": dict(title=("BebasNeue-Regular.ttf", None), script=("DMSerifDisplay-Italic.ttf", None),
                      body="Poppins-Regular.ttf", upper=True,
                      panel="#151515", text="#FFFFFF", accent="#D7263D", on_accent="#FFFFFF"),
}
TEMPLATES = ["bandeau-bas", "titre-haut", "split", "cadre", "minimal"]


def die(msg):
    print(f"ERREUR : {msg}", file=sys.stderr)
    sys.exit(1)


def luminance(c):
    r, g, b = (v / 255 for v in ImageColor.getrgb(c)[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def rgba(c, a=255):
    return ImageColor.getrgb(c)[:3] + (a,)


def font(spec, size):
    name, var = spec if isinstance(spec, tuple) else (spec, None)
    try:
        f = ImageFont.truetype(str(FONTS / name), size)
        if var:
            f.set_variation_by_name(var)
        return f
    except Exception:
        return ImageFont.truetype(FALLBACK, size)


# ---------------------------------------------------------------- texte
def wrap(draw, text, f, max_w, tracking=0):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            test = (cur + " " + w).strip()
            if text_w(draw, test, f, tracking) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_w(draw, s, f, tracking=0):
    l, _, r, _ = draw.textbbox((0, 0), s, font=f)
    return r - l + tracking * max(0, len(s) - 1)


def fit(draw, text, spec, max_w, max_h, start, minimum, leading=1.08, max_lines=None):
    """Plus grande taille de police pour que le texte tienne dans max_w x max_h."""
    size = start
    while size >= minimum:
        f = font(spec, size)
        lines = wrap(draw, text, f, max_w)
        h = block_h(draw, lines, f, leading)
        if (h <= max_h and all(text_w(draw, ln, f) <= max_w for ln in lines)
                and (max_lines is None or len(lines) <= max_lines)):
            return f, lines
        size = int(size * 0.94) - 1
    f = font(spec, minimum)
    return f, wrap(draw, text, f, max_w)


def line_h(f, leading):
    asc, desc = f.getmetrics()
    return int((asc + desc) * leading)


def block_h(draw, lines, f, leading):
    return line_h(f, leading) * len(lines)


def draw_lines(canvas, lines, f, x, y, w, color, align="left", leading=1.08, shadow=0):
    d = ImageDraw.Draw(canvas)
    lh = line_h(f, leading)
    if shadow:
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        for i, ln in enumerate(lines):
            lx = _ax(d, ln, f, x, w, align)
            sd.text((lx, y + i * lh + shadow // 2), ln, font=f, fill=(0, 0, 0, 150))
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow)))
    for i, ln in enumerate(lines):
        d.text((_ax(d, ln, f, x, w, align), y + i * lh), ln, font=f, fill=color)
    return y + lh * len(lines)


def _ax(d, s, f, x, w, align):
    tw = text_w(d, s, f)
    return x if align == "left" else x + (w - tw) // 2 if align == "center" else x + w - tw


# ---------------------------------------------------------------- éléments
def gradient(size, top_alpha, bottom_alpha, color="#000000"):
    w, h = size
    g = Image.new("L", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        t = t * t * (3 - 2 * t)  # smoothstep
        g.putpixel((0, y), int(top_alpha + (bottom_alpha - top_alpha) * t))
    layer = Image.new("RGBA", (w, h), rgba(color))
    layer.putalpha(g.resize((w, h)))
    return layer


def price_badge(canvas, cx, cy, r, price, label, st, title_spec):
    d = ImageDraw.Draw(canvas)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(st["accent"]))
    d.ellipse((cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9),
              outline=rgba(st["on_accent"], 140), width=max(2, r // 40))
    col = rgba(st["on_accent"])
    inner = int(r * 1.45)
    if label:
        fl, ll = fit(d, label.upper(), st["body"], inner, r * 0.3, int(r * 0.24), 10, max_lines=1)
        fp, lp = fit(d, price, title_spec, inner, r * 0.75, int(r * 0.7), 12, max_lines=1)
        hl, hp = block_h(d, ll, fl, 1.0), block_h(d, lp, fp, 1.0)
        y = cy - (hl + hp) // 2
        y = draw_lines(canvas, ll, fl, cx - inner // 2, y, inner, col, "center", 1.0)
        draw_lines(canvas, lp, fp, cx - inner // 2, y, inner, col, "center", 1.0)
    else:
        fp, lp = fit(d, price, title_spec, inner, r * 0.9, int(r * 0.8), 12, max_lines=2)
        y = cy - block_h(d, lp, fp, 1.0) // 2
        draw_lines(canvas, lp, fp, cx - inner // 2, y, inner, col, "center", 1.0)


def pill(canvas, x, y, text, st, size, align="left", invert=False):
    d = ImageDraw.Draw(canvas)
    f = font(st["body"].replace("Regular", "SemiBold").replace("Light", "SemiBold"), size)
    tw = text_w(d, text, f)
    padx, pady = int(size * 0.7), int(size * 0.35)
    asc, desc = f.getmetrics()
    w, h = tw + 2 * padx, asc + desc + 2 * pady
    if align == "right":
        x -= w
    elif align == "center":
        x -= w // 2
    bg, fg = (st["text"], st["panel"]) if invert else (st["accent"], st["on_accent"])
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=rgba(bg))
    d.text((x + padx, y + pady), text, font=f, fill=rgba(fg))
    return h


def place_logo(canvas, path, x, y, max_w, max_h, align="left"):
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((max_w, max_h), Image.LANCZOS)
    if align == "center":
        x -= logo.width // 2
    elif align == "right":
        x -= logo.width
    canvas.alpha_composite(logo, (int(x), int(y)))
    return logo.height


def cover(im, w, h, focus):
    return ImageOps.fit(im.convert("RGBA"), (w, h), Image.LANCZOS, centering=focus)


# ---------------------------------------------------------------- composition
def compose(a, W, H, safe):
    st = dict(STYLES[a.style])
    for k in ("accent", "panel", "text"):
        if getattr(a, k):
            st[k] = getattr(a, k)
    if a.on_accent:
        st["on_accent"] = a.on_accent
    T = st["title"]
    up = (lambda s: s.upper()) if st["upper"] else (lambda s: s)
    focus = {"centre": (.5, .5), "haut": (.5, 0), "bas": (.5, 1), "gauche": (0, .5), "droite": (1, .5)}[a.focus]

    bg_img = Image.open(a.bg) if a.bg else None
    canvas = Image.new("RGBA", (W, H), rgba(st["panel"]))
    m = safe + int(min(W, H) * 0.06)        # marge intérieure
    mv = m + a.vsafe                        # marge verticale (zones d'interface des stories)
    cw = W - 2 * m                          # largeur utile
    U = min(W, H)                           # unité de base
    d = ImageDraw.Draw(canvas)
    txt = rgba(st["text"])
    shadow = int(U * 0.006)
    tpl = a.template

    # --- fond & zone de texte
    if tpl == "split":
        ih = int(H * a.split)
        if bg_img:
            canvas.alpha_composite(cover(bg_img, W, ih, focus), (0, 0))
        zone = (m, ih + int(U * 0.05), cw, H - ih - int(U * 0.05) - m)
        shadow = 0
    elif tpl == "cadre":
        pad = m
        ih = int(H * a.split)
        if bg_img:
            ph = cover(bg_img, W - 2 * pad, ih - pad, focus)
            mask = Image.new("L", ph.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, *ph.size), radius=int(U * 0.03), fill=255)
            canvas.paste(ph, (pad, pad), mask)
        zone = (m, ih + int(U * 0.04), cw, H - ih - int(U * 0.04) - m)
        shadow = 0
    else:
        if bg_img:
            canvas.alpha_composite(cover(bg_img, W, H, focus))
        o = int(255 * a.overlay)
        if tpl == "bandeau-bas":
            gh = int(H * 0.6)
            canvas.alpha_composite(gradient((W, gh), 0, o, st["panel"] if a.overlay_color == "panel" else "#000"), (0, H - gh))
            zone = (m, int(H * 0.52), cw, H - int(H * 0.52) - mv)
        elif tpl == "titre-haut":
            gh = int(H * 0.55)
            canvas.alpha_composite(gradient((W, gh), o, 0, st["panel"] if a.overlay_color == "panel" else "#000"))
            zone = (m, mv, cw, int(H * 0.42) - mv)
            if a.footer or a.cta or a.logo:   # 2e dégradé en bas pour CTA / logo / pied
                bh = int(H * 0.3)
                canvas.alpha_composite(gradient((W, bh), 0, int(o * 0.85)), (0, H - bh))
        else:  # minimal
            canvas.alpha_composite(Image.new("RGBA", (W, H), rgba(st["panel"] if a.overlay_color == "panel" else "#000", int(o * 0.75))))
            zone = (m, int(H * 0.22), cw, int(H * 0.56))
        if a.overlay_color == "panel" and luminance(st["panel"]) > 0.5:
            shadow = 0
        elif a.overlay_color == "noir" and luminance(st["text"]) < 0.5 and not a.text:
            st["text"] = "#FFFFFF"   # texte clair sur dégradé noir
        txt = rgba(st["text"])

    align = a.align or ("left" if tpl == "bandeau-bas" else "center")
    zx, zy, zw, zh = zone

    # --- logo
    logo_h = 0
    if a.logo:
        lw, lh = int(W * a.logo_scale), int(U * 0.14)
        if tpl in ("bandeau-bas", "minimal", "split", "cadre"):
            lx, la = (W // 2, "center") if tpl in ("minimal",) else (m, "left")
            if tpl in ("split", "cadre"):
                lx, la = W - m - int(U * 0.01), "right"
            place_logo(canvas, a.logo, lx, mv + (int(U * 0.01) if tpl == "cadre" else 0), lw, lh, la)
        else:  # titre-haut : logo en bas, aligné sur sa hauteur réelle
            with Image.open(a.logo) as lg:
                real_h = min(lh, round(lg.height * min(lw / lg.width, lh / lg.height)))
            bottom = H - mv - (int(U * 0.07) if a.footer else 0)
            place_logo(canvas, a.logo, W // 2, bottom - real_h, lw, lh, "center")
            logo_h = real_h + int(U * 0.03)

    # --- badge (NOUVEAU, -20 %, Fait maison…)
    if a.badge:
        bx, by = (m, mv) if not (a.logo and tpl in ("bandeau-bas", "split")) else (m, mv + int(U * 0.16))
        if tpl == "cadre":
            bx, by = m + int(U * 0.03), mv + int(U * 0.03)
        pill(canvas, bx, by, a.badge.upper(), st, int(U * 0.032))

    # --- prix (pastille)
    if a.price:
        r = int(U * a.price_size)
        if tpl == "bandeau-bas":
            cx, cy = W - m - r, int(H * 0.40)
        elif tpl == "titre-haut":
            cx, cy = W - m - r, H - mv - r - (int(U * 0.12) if a.footer or a.cta else 0) - logo_h
        elif tpl in ("split", "cadre"):
            ih = int(H * a.split)
            cx, cy = W - m - r, ih - r // 2 - (0 if tpl == "split" else m // 2)
        else:
            cx, cy = W // 2, int(H * 0.80) - (int(U * 0.06) if a.cta else 0)
        price_badge(canvas, cx, cy, r, a.price, a.price_label, st, T)

    # --- bloc texte : surtitre / titre / sous-titre / détails / CTA
    reserve_bottom = 0
    if a.footer:
        reserve_bottom += int(U * 0.06)
    if a.cta and tpl in ("bandeau-bas", "split", "cadre"):
        reserve_bottom += int(U * 0.09)
    if tpl == "titre-haut":
        reserve_bottom = 0
    avail = zh - reserve_bottom
    y = zy
    kick_size = int(U * 0.045)
    if a.kicker:
        fk = font(st["script"], kick_size)
        kl = wrap(d, a.kicker, fk, zw)
        y = draw_lines(canvas, kl, fk, zx, y, zw, rgba(st["accent"]), align, 1.0, shadow) + int(U * 0.005)
    sub_h = int(avail * 0.24) if a.subtitle else 0
    det_h = int(avail * 0.24) if a.details else 0
    title_h = max(int(U * 0.08), zy + avail - y - sub_h - det_h)
    ft, tl = fit(d, up(a.title), T, zw if not (a.price and tpl == "bandeau-bas") else int(zw * 0.98),
                 title_h, int(U * a.title_size), int(U * 0.045), leading=0.98, max_lines=3)
    y = draw_lines(canvas, tl, ft, zx, y, zw, txt, align, 0.98, shadow)
    if a.subtitle:
        y += int(U * 0.015)
        fs, sl = fit(d, a.subtitle, st["body"], zw, sub_h, int(U * 0.042), int(U * 0.026), 1.25, max_lines=3)
        y = draw_lines(canvas, sl, fs, zx, y, zw, rgba(st["text"], 235), align, 1.25, shadow)
    if a.details:
        y += int(U * 0.02)
        fd, dl = fit(d, a.details, st["body"].replace("Light", "Medium").replace("Regular", "Medium"),
                     zw, det_h, int(U * 0.042), int(U * 0.028), 1.3)
        y = draw_lines(canvas, dl, fd, zx, y, zw, rgba(st["accent"] if tpl in ("split", "cadre") else st["text"]), align, 1.3, shadow)

    # --- CTA
    if a.cta:
        size = int(U * 0.03)
        cy = H - mv - (int(U * 0.06) if a.footer else 0) - int(size * 2.2)
        if tpl == "titre-haut":
            cy = H - mv - int(size * 2.2) - (int(U * 0.06) if a.footer else 0)
            cy -= logo_h
        cx = {"left": zx, "center": W // 2, "right": zx + zw}[align]
        pill(canvas, cx, cy, a.cta, st, size, align)

    # --- pied de page (adresse, tel, mentions)
    if a.footer:
        ff = font(st["body"], int(U * 0.022))
        fl = wrap(d, a.footer, ff, cw)
        fh = block_h(d, fl, ff, 1.2)
        fc = rgba("#FFFFFF" if tpl == "titre-haut" else st["text"], 210)
        draw_lines(canvas, fl, ff, m, H - mv - fh + int(U * 0.01), cw, fc, "center", 1.2, shadow // 2)

    if a.legal:  # mentions obligatoires, petit, tout en bas
        fz = font(st["body"], max(9, int(U * 0.015)))
        ll = wrap(d, a.legal, fz, cw)
        draw_lines(canvas, ll, fz, m, H - safe - int(U * 0.012) - block_h(d, ll, fz, 1.1), cw,
                   rgba(st["text"], 190), "center", 1.1)
    return canvas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bg", help="image de fond (photo du plat, visuel IA sans texte)")
    ap.add_argument("--format", default="a4", help=f"{', '.join(list(PRINT_MM) + list(SCREEN_PX))} ; suffixe -paysage possible ; ou LxH en px")
    ap.add_argument("--dpi", type=int, default=300, help="résolution pour les formats print (300 imprimeur, 150 brouillon)")
    ap.add_argument("--bleed", type=float, default=0, help="fonds perdus en mm (3 mm standard imprimeur)")
    ap.add_argument("--template", default="bandeau-bas", choices=TEMPLATES)
    ap.add_argument("--style", default="bistrot", choices=list(STYLES))
    ap.add_argument("--kicker", help="surtitre (Nouveau, Ce week-end, Menu du midi…)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle")
    ap.add_argument("--details", help="dates, horaires, contenu du menu (\\n pour aller à la ligne)")
    ap.add_argument("--price")
    ap.add_argument("--price-label", help="petit texte au-dessus du prix : menu, seulement, dès…")
    ap.add_argument("--badge", help="pastille : NOUVEAU, -20 %, FAIT MAISON…")
    ap.add_argument("--cta", help="appel à l'action")
    ap.add_argument("--footer", help="adresse · téléphone · site / réseaux")
    ap.add_argument("--legal", help="mentions obligatoires (alcool, photo non contractuelle…)")
    ap.add_argument("--logo")
    ap.add_argument("--logo-scale", type=float, default=0.28, help="largeur max du logo / largeur")
    ap.add_argument("--accent"); ap.add_argument("--panel"); ap.add_argument("--text"); ap.add_argument("--on-accent")
    ap.add_argument("--align", choices=["left", "center", "right"])
    ap.add_argument("--focus", default="centre", choices=["centre", "haut", "bas", "gauche", "droite"])
    ap.add_argument("--overlay", type=float, default=0.85, help="opacité max du dégradé de lisibilité (0-1)")
    ap.add_argument("--overlay-color", default="noir", choices=["noir", "panel"])
    ap.add_argument("--split", type=float, default=0.6, help="part de la hauteur occupée par la photo (split/cadre)")
    ap.add_argument("--title-size", type=float, default=0.16, help="taille max du titre (fraction du petit côté)")
    ap.add_argument("--price-size", type=float, default=0.11, help="rayon de la pastille prix (fraction)")
    ap.add_argument("--pdf", action="store_true", help="exporte aussi un PDF (print)")
    ap.add_argument("--jpg", action="store_true", help="exporte aussi un JPG")
    ap.add_argument("-o", "--output", help="chemin de sortie .png (défaut outputs/affiche_<titre>_<format>.png)")
    ap.add_argument("--vsafe", type=int, help="marge verticale supplémentaire en px (auto pour story)")
    a = ap.parse_args()

    fmt = a.format.lower()
    land = fmt.endswith("-paysage")
    base = fmt[:-8] if land else fmt
    safe = 0
    dpi = None
    if base in PRINT_MM:
        dpi = a.dpi
        wmm, hmm = PRINT_MM[base]
        if land:
            wmm, hmm = hmm, wmm
        bleed_px = round(a.bleed / MM_PER_IN * dpi)
        W = round(wmm / MM_PER_IN * dpi) + 2 * bleed_px
        H = round(hmm / MM_PER_IN * dpi) + 2 * bleed_px
        safe = bleed_px
    elif base in SCREEN_PX:
        W, H = SCREEN_PX[base]
        if base == "story" and a.vsafe is None:
            a.vsafe = int(H * 0.09)   # ~170 px : hors barre de profil et zone de réponse
        if land:
            W, H = H, W
    elif "x" in base:
        W, H = map(int, base.split("x"))
    else:
        die(f"format inconnu : {a.format}")
    a.vsafe = a.vsafe or 0
    if a.bg and not Path(a.bg).is_file():
        die(f"image introuvable : {a.bg}")
    if a.logo and not Path(a.logo).is_file():
        die(f"logo introuvable : {a.logo}")
    a.details = a.details.replace("\\n", "\n") if a.details else None

    img = compose(a, W, H, safe).convert("RGB")
    if a.output:
        out = Path(a.output)
    else:
        import re, unicodedata
        slug = unicodedata.normalize("NFKD", a.title).encode("ascii", "ignore").decode()
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug).strip("-").lower()[:40] or "affiche"
        out = Path("outputs") / f"affiche_{slug}_{fmt}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, dpi=(dpi, dpi) if dpi else None, optimize=True)
    print(f"{out}  ({W}x{H}px{f', {dpi} dpi' if dpi else ''}{f', fonds perdus {a.bleed} mm' if a.bleed else ''})")
    if a.jpg:
        p = out.with_suffix(".jpg"); img.save(p, quality=92, dpi=(dpi, dpi) if dpi else None); print(p)
    if a.pdf:
        p = out.with_suffix(".pdf"); img.save(p, resolution=dpi or 150); print(p)


if __name__ == "__main__":
    main()
