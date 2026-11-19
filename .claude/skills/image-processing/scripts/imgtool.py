#!/usr/bin/env python3
"""Traitement d'images local : Pillow (+ rembg pour le détourage).

Sous-commandes : info, resize, crop, removebg, compress, convert, text, logo, social.
Chaque commande accepte une ou plusieurs images (ou un dossier) et écrit dans outputs/
(sauf -o). Lancer `imgtool.py <commande> -h` pour le détail.
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    sys.exit("Pillow est requis : pip install pillow")

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".avif"}
SOCIAL = {
    "instagram-post": (1080, 1080),
    "instagram-portrait": (1080, 1350),
    "instagram-paysage": (1080, 566),
    "instagram-story": (1080, 1920),
    "reel": (1080, 1920),
    "facebook-post": (1200, 630),
    "facebook-banniere": (1640, 624),     # couverture de page (affichage 820x312 x2)
    "facebook-evenement": (1920, 1005),
    "linkedin-post": (1200, 627),
    "linkedin-banniere": (1584, 396),
    "x-post": (1600, 900),
    "x-banniere": (1500, 500),
    "youtube-miniature": (1280, 720),
    "pinterest": (1000, 1500),
}
POSITIONS = {"haut-gauche", "haut", "haut-droite", "gauche", "centre", "droite",
             "bas-gauche", "bas", "bas-droite", "mosaique"}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def die(msg):
    print(f"ERREUR : {msg}", file=sys.stderr)
    sys.exit(1)


# ---------- I/O ----------
def expand_inputs(items):
    files = []
    for it in items:
        p = Path(it)
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in IMG_EXT)
        elif p.is_file():
            files.append(p)
        else:
            die(f"introuvable : {it}")
    if not files:
        die("aucune image à traiter")
    return files


def open_img(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)  # respecte l'orientation des photos
    return im


def out_path(src, args, tag, ext=None):
    ext = (ext or getattr(args, "format", None) or src.suffix.lstrip(".")).lower()
    ext = "jpg" if ext == "jpeg" else ext
    if args.output and len(args._inputs) == 1 and Path(args.output).suffix:
        p = Path(args.output)
    else:
        d = Path(args.output) if args.output else Path("outputs")
        p = d / f"{src.stem}_{tag}.{ext}"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def save(im, path, quality=90, lossless=False):
    ext = path.suffix.lower()
    kw = {}
    if ext in (".jpg", ".jpeg"):
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        kw = dict(quality=quality, optimize=True, progressive=True)
    elif ext == ".webp":
        kw = dict(quality=quality, method=6, lossless=lossless)
    elif ext == ".png":
        kw = dict(optimize=True)
    elif ext == ".avif":
        kw = dict(quality=quality)
    im.save(path, **kw)
    print(f"{path}  ({im.width}x{im.height}, {path.stat().st_size / 1024:.0f} Ko)")
    return path


# ---------- helpers ----------
def parse_size(s):
    """'1080x1350', '1080x', 'x720', '50%'"""
    s = s.lower().strip()
    if s.endswith("%"):
        return ("pct", float(s[:-1]) / 100)
    if "x" not in s:
        return (int(s), None)
    w, h = s.split("x", 1)
    return (int(w) if w else None, int(h) if h else None)


def parse_ratio(s):
    if ":" in s:
        a, b = s.split(":")
        return float(a) / float(b)
    return float(s)


def anchor_xy(pos, W, H, w, h, margin):
    col = 0 if "gauche" in pos else 2 if "droite" in pos else 1
    row = 0 if pos.startswith("haut") else 2 if pos.startswith("bas") else 1
    x = [margin, (W - w) // 2, W - w - margin][col]
    y = [margin, (H - h) // 2, H - h - margin][row]
    return x, y


def load_font(path, size):
    for cand in ([path] if path else []) + FONT_CANDIDATES:
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


def parse_color(c, opacity):
    from PIL import ImageColor
    rgb = ImageColor.getrgb(c)[:3]
    return rgb + (int(255 * opacity),)


def cover(im, w, h, focus=(0.5, 0.5)):
    return ImageOps.fit(im, (w, h), method=Image.LANCZOS, centering=focus)


def contain(im, w, h, bg):
    im = im.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    if bg == "flou":
        canvas = cover(im.convert("RGB"), w, h)
        from PIL import ImageFilter
        canvas = canvas.filter(ImageFilter.GaussianBlur(max(w, h) // 30))
        canvas = canvas.convert("RGBA")
    elif bg == "transparent":
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    else:
        canvas = Image.new("RGBA", (w, h), parse_color(bg, 1))
    im = im.convert("RGBA")
    canvas.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2))
    return canvas


FOCUS = {"centre": (0.5, 0.5), "haut": (0.5, 0.0), "bas": (0.5, 1.0),
         "gauche": (0.0, 0.5), "droite": (1.0, 0.5)}


# ---------- commandes ----------
def cmd_info(args):
    for f in args._inputs:
        with Image.open(f) as im:
            print(f"{f}: {im.format} {im.width}x{im.height} {im.mode} "
                  f"{f.stat().st_size / 1024:.0f} Ko")


def cmd_resize(args):
    for f in args._inputs:
        im = open_img(f)
        w, h = parse_size(args.size)
        if w == "pct":
            new = (max(1, round(im.width * h)), max(1, round(im.height * h)))
            im = im.resize(new, Image.LANCZOS)
        elif w and h and args.mode == "cover":
            im = cover(im, w, h, FOCUS[args.focus])
        elif w and h and args.mode == "contain":
            im = contain(im, w, h, args.bg)
        elif w and h and args.mode == "stretch":
            im = im.resize((w, h), Image.LANCZOS)
        else:  # fit : garde le ratio, tient dans la boîte
            box = (w or 10**6, h or 10**6)
            if not args.upscale and im.width <= box[0] and im.height <= box[1]:
                pass
            else:
                r = min(box[0] / im.width, box[1] / im.height)
                im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
        save(im, out_path(f, args, f"{im.width}x{im.height}"), args.quality)


def cmd_crop(args):
    for f in args._inputs:
        im = open_img(f)
        if args.box:
            x, y, w, h = map(int, args.box.split(","))
            im = im.crop((x, y, x + w, y + h))
            tag = "crop"
        elif args.ratio:
            r = parse_ratio(args.ratio)
            if im.width / im.height > r:
                w, h = round(im.height * r), im.height
            else:
                w, h = im.width, round(im.width / r)
            im = cover(im, w, h, FOCUS[args.focus])
            tag = "crop-" + args.ratio.replace(":", "x")
        elif args.trim:
            bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
            from PIL import ImageChops
            diff = ImageChops.difference(im.convert("RGB"), bg.convert("RGB"))
            bbox = (im.getchannel("A").getbbox() if im.mode == "RGBA" else None) or diff.getbbox()
            if bbox:
                im = im.crop(bbox)
            tag = "trim"
        else:
            die("indique --box x,y,l,h, --ratio 4:5 ou --trim")
        save(im, out_path(f, args, tag), args.quality)


def cmd_removebg(args):
    try:
        from rembg import remove, new_session
    except ImportError:
        die("rembg n'est pas installé : pip install \"rembg[cpu]\"")
    session = new_session(args.model)
    for f in args._inputs:
        im = open_img(f)
        cut = remove(im, session=session, alpha_matting=args.matting,
                     post_process_mask=True)
        if args.trim:
            bbox = cut.getchannel("A").getbbox()
            if bbox:
                cut = cut.crop(bbox)
        if args.bg:
            canvas = Image.new("RGBA", cut.size, parse_color(args.bg, 1))
            canvas.alpha_composite(cut)
            cut = canvas
        ext = None if args.bg else ("webp" if getattr(args, "format", None) == "webp" else "png")
        save(cut, out_path(f, args, "detoure", ext), args.quality)


def cmd_compress(args):
    for f in args._inputs:
        im = open_img(f)
        if args.max_size:
            im.thumbnail((args.max_size, args.max_size), Image.LANCZOS)
        p = out_path(f, args, "compresse")
        q = args.quality
        save_q = q
        if args.target_kb and p.suffix.lower() in (".jpg", ".jpeg", ".webp", ".avif"):
            lo, hi = 20, q
            best = None
            while lo <= hi:  # recherche dichotomique sur la qualité
                mid = (lo + hi) // 2
                tmp = p.with_suffix(".tmp" + p.suffix)
                _quiet_save(im, tmp, mid)
                if tmp.stat().st_size / 1024 <= args.target_kb:
                    best, lo = mid, mid + 1
                else:
                    hi = mid - 1
                tmp.unlink()
            save_q = best or 20
        elif p.suffix.lower() == ".png" and args.colors:
            im = im.convert("RGBA").quantize(colors=args.colors, method=Image.FASTOCTREE)
        before = f.stat().st_size / 1024
        save(im, p, save_q)
        print(f"   {before:.0f} Ko -> {p.stat().st_size / 1024:.0f} Ko (qualité {save_q})")


def _quiet_save(im, path, q):
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        save(im, path, q)


def cmd_convert(args):
    for f in args._inputs:
        im = open_img(f)
        save(im, out_path(f, args, "converti", args.to), args.quality, args.lossless)


def _overlay(base, layer, pos, margin, rotate=0):
    base = base.convert("RGBA")
    if rotate:
        layer = layer.rotate(rotate, expand=True, resample=Image.BICUBIC)
    over = Image.new("RGBA", base.size, (0, 0, 0, 0))
    if pos == "mosaique":
        sx, sy = layer.width + margin * 2, layer.height + margin * 2
        for row, y in enumerate(range(-layer.height // 2, base.height, sy)):
            off = (sx // 2) * (row % 2)
            for x in range(-layer.width + off, base.width + layer.width, sx):
                over.paste(layer, (x, y), layer)  # paste gère les coordonnées négatives
    else:
        over.alpha_composite(layer, anchor_xy(pos, base.width, base.height, layer.width, layer.height, margin))
    return Image.alpha_composite(base, over)


def cmd_text(args):
    for f in args._inputs:
        im = open_img(f)
        size = args.size or max(12, int(min(im.size) * args.scale))
        font = load_font(args.font, size)
        tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        stroke = args.stroke if args.stroke is not None else max(1, size // 18)
        l, t, r, b = tmp.textbbox((0, 0), args.text, font=font, stroke_width=stroke)
        layer = Image.new("RGBA", (r - l, b - t), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((-l, -t), args.text, font=font, fill=parse_color(args.color, args.opacity),
               stroke_width=stroke, stroke_fill=parse_color(args.stroke_color, args.opacity * 0.6))
        margin = int(min(im.size) * 0.03)
        res = _overlay(im, layer, args.position, margin, args.rotate)
        save(res, out_path(f, args, "texte"), args.quality)


def cmd_logo(args):
    logo_src = Image.open(args.logo).convert("RGBA")
    for f in args._inputs:
        im = open_img(f)
        lw = max(1, int(im.width * args.scale))
        logo = logo_src.resize((lw, max(1, round(logo_src.height * lw / logo_src.width))), Image.LANCZOS)
        if args.opacity < 1:
            a = logo.getchannel("A").point(lambda v: int(v * args.opacity))
            logo.putalpha(a)
        margin = int(min(im.size) * 0.03)
        res = _overlay(im, logo, args.position, margin, args.rotate)
        save(res, out_path(f, args, "logo"), args.quality)


def cmd_social(args):
    targets = list(SOCIAL) if args.preset == ["tous"] else args.preset
    for t in targets:
        if t not in SOCIAL:
            die(f"format inconnu '{t}'. Choix : {', '.join(SOCIAL)}, tous")
    for f in args._inputs:
        im = open_img(f)
        for t in targets:
            w, h = SOCIAL[t]
            res = contain(im, w, h, args.bg) if args.mode == "contain" else cover(im, w, h, FOCUS[args.focus])
            ext = args.format or ("png" if res.mode == "RGBA" and args.bg == "transparent" else "jpg")
            save(res, out_path(f, args, t, ext), args.quality)


# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def p(name, fn, help_):
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("inputs", nargs="+", help="image(s) ou dossier")
        sp.add_argument("-o", "--output", help="fichier (si 1 image) ou dossier de sortie (défaut : outputs/)")
        sp.add_argument("-q", "--quality", type=int, default=90, help="qualité JPG/WebP (1-100)")
        sp.set_defaults(fn=fn)
        return sp

    p("info", cmd_info, "dimensions, format, poids")

    s = p("resize", cmd_resize, "redimensionner")
    s.add_argument("size", help="1080x1350, 1080x (largeur), x720 (hauteur), 50%%")
    s.add_argument("--mode", default="fit", choices=["fit", "cover", "contain", "stretch"],
                   help="fit=dans la boîte, cover=remplit+recadre, contain=bandes, stretch=déforme")
    s.add_argument("--focus", default="centre", choices=list(FOCUS))
    s.add_argument("--bg", default="white", help="fond pour contain : couleur, 'flou' ou 'transparent'")
    s.add_argument("--upscale", action="store_true", help="autorise l'agrandissement en mode fit")
    s.add_argument("--format")

    s = p("crop", cmd_crop, "recadrer")
    s.add_argument("--box", help="x,y,largeur,hauteur")
    s.add_argument("--ratio", help="ex. 1:1, 4:5, 16:9")
    s.add_argument("--focus", default="centre", choices=list(FOCUS))
    s.add_argument("--trim", action="store_true", help="supprime les bords unis/transparents")
    s.add_argument("--format")

    s = p("removebg", cmd_removebg, "détourer (supprimer le fond)")
    s.add_argument("--model", default="u2net",
                   help="u2net (défaut), isnet-general-use (plus précis), u2net_human_seg (personnes), birefnet-general")
    s.add_argument("--matting", action="store_true", help="bords plus fins (cheveux), plus lent")
    s.add_argument("--trim", action="store_true", help="recadre au plus près du sujet")
    s.add_argument("--bg", help="couleur de fond de remplacement (sinon transparent)")
    s.add_argument("--format", choices=["png", "webp", "jpg"])

    s = p("compress", cmd_compress, "alléger le poids")
    s.add_argument("--target-kb", type=int, help="poids visé en Ko (JPG/WebP)")
    s.add_argument("--max-size", type=int, help="plus grand côté max en px")
    s.add_argument("--colors", type=int, help="PNG : réduit la palette (ex. 128)")
    s.add_argument("--format", help="jpg, webp, png… (défaut : identique)")
    s.set_defaults(quality=82)

    s = p("convert", cmd_convert, "convertir PNG/JPG/WebP/AVIF…")
    s.add_argument("--to", required=True, help="png, jpg, webp, avif, gif, tiff")
    s.add_argument("--lossless", action="store_true", help="WebP sans perte")

    s = p("text", cmd_text, "filigrane texte")
    s.add_argument("--text", required=True)
    s.add_argument("--position", default="bas-droite", choices=sorted(POSITIONS))
    s.add_argument("--opacity", type=float, default=0.5)
    s.add_argument("--color", default="white")
    s.add_argument("--stroke-color", default="black")
    s.add_argument("--stroke", type=int, help="épaisseur du contour")
    s.add_argument("--size", type=int, help="taille de police en px")
    s.add_argument("--scale", type=float, default=0.05, help="taille relative au petit côté (défaut 5%%)")
    s.add_argument("--font", help="chemin d'un .ttf/.otf")
    s.add_argument("--rotate", type=float, default=0)
    s.add_argument("--format")

    s = p("logo", cmd_logo, "filigrane logo")
    s.add_argument("--logo", required=True, help="PNG du logo (idéalement transparent)")
    s.add_argument("--position", default="bas-droite", choices=sorted(POSITIONS))
    s.add_argument("--scale", type=float, default=0.15, help="largeur du logo / largeur image")
    s.add_argument("--opacity", type=float, default=0.8)
    s.add_argument("--rotate", type=float, default=0)
    s.add_argument("--format")

    s = p("social", cmd_social, "formats réseaux sociaux")
    s.add_argument("--preset", nargs="+", required=True, help=f"{', '.join(SOCIAL)} ou 'tous'")
    s.add_argument("--mode", default="cover", choices=["cover", "contain"],
                   help="cover=remplit et recadre, contain=image entière + fond")
    s.add_argument("--focus", default="centre", choices=list(FOCUS))
    s.add_argument("--bg", default="flou", help="fond pour contain : couleur, 'flou' ou 'transparent'")
    s.add_argument("--format", help="jpg (défaut), png, webp")

    args = ap.parse_args()
    args._inputs = expand_inputs(args.inputs)
    if not hasattr(args, "output"):
        args.output = None
    args.fn(args)


if __name__ == "__main__":
    main()
