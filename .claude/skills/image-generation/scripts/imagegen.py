#!/usr/bin/env python3
"""Génère / modifie des images via OpenAI (gpt-image) ou Google Gemini.

Exemples :
  imagegen.py generate "un chat astronaute" --format portrait --name chat
  imagegen.py edit photo.jpg "change le fond en plage" --name photo-plage
  imagegen.py edit photo.jpg logo.png "ajoute ce logo en bas à droite"
"""
import argparse
import base64
import datetime as dt
import mimetypes
import os
import re
import sys
import unicodedata
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("Le module 'requests' est requis : pip install requests")

FORMATS = {
    # nom: (taille OpenAI, ratio Gemini)
    "carre": ("1024x1024", "1:1"),
    "portrait": ("1024x1536", "3:4"),
    "paysage": ("1536x1024", "4:3"),
}
ALIASES = {"square": "carre", "carré": "carre", "landscape": "paysage"}
OPENAI_URL = "https://api.openai.com/v1/images"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT = 300


def die(msg, code=1):
    print(f"ERREUR : {msg}", file=sys.stderr)
    sys.exit(code)


def norm_format(fmt):
    if fmt is None:
        return None
    f = ALIASES.get(fmt.lower(), fmt.lower())
    if f not in FORMATS:
        die(f"format inconnu '{fmt}' (choix : carre, portrait, paysage)")
    return f


def guess_format(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        return "carre"
    r = w / h
    return "paysage" if r > 1.15 else "portrait" if r < 0.87 else "carre"


def slugify(text, maxlen=40):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return (t[:maxlen].rstrip("-")) or "image"


def save_images(blobs, action, name, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    paths = []
    for i, (data, ext) in enumerate(blobs, 1):
        suffix = f"_{i}" if len(blobs) > 1 else ""
        p = out / f"{stamp}_{action}_{name}{suffix}.{ext}"
        n = 2
        while p.exists():
            p = out / f"{stamp}_{action}_{name}{suffix}-{n}.{ext}"
            n += 1
        p.write_bytes(data)
        paths.append(p)
    return paths


def check_response(r, provider):
    if r.ok:
        return r.json()
    try:
        err = r.json().get("error", {})
        msg = err.get("message") if isinstance(err, dict) else str(err)
    except Exception:
        msg = r.text[:500]
    die(f"{provider} a répondu {r.status_code} : {msg}")


# ---------------- OpenAI ----------------
def openai_key():
    k = os.environ.get("OPENAI_API_KEY")
    if not k:
        die("OPENAI_API_KEY n'est pas définie.")
    return k


def openai_model(args):
    return args.model or os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")


def openai_blobs(js, output_format):
    ext = "jpg" if output_format == "jpeg" else output_format
    blobs = []
    for d in js.get("data", []):
        if d.get("b64_json"):
            blobs.append((base64.b64decode(d["b64_json"]), ext))
        elif d.get("url"):
            blobs.append((requests.get(d["url"], timeout=TIMEOUT).content, ext))
    if not blobs:
        die("OpenAI n'a renvoyé aucune image.")
    return blobs


def openai_generate(args, fmt):
    payload = {
        "model": openai_model(args),
        "prompt": args.prompt,
        "size": FORMATS[fmt][0],
        "n": args.n,
    }
    if not payload["model"].startswith("dall-e"):
        payload["quality"] = args.quality
        payload["output_format"] = args.output_format
        if args.background:
            payload["background"] = args.background
    else:  # dall-e-3 etc.
        payload["response_format"] = "b64_json"
    r = requests.post(f"{OPENAI_URL}/generations", json=payload, timeout=TIMEOUT,
                      headers={"Authorization": f"Bearer {openai_key()}"})
    return openai_blobs(check_response(r, "OpenAI"), args.output_format)


def openai_edit(args, fmt):
    model = openai_model(args)
    data = {"model": model, "prompt": args.prompt, "size": FORMATS[fmt][0], "n": str(args.n)}
    if not model.startswith("dall-e"):
        data["quality"] = args.quality
        data["output_format"] = args.output_format
        if args.background:
            data["background"] = args.background
    files, handles = [], []
    try:
        for img in args.images:
            fh = open(img, "rb")
            handles.append(fh)
            mime = mimetypes.guess_type(img)[0] or "image/png"
            files.append(("image[]", (Path(img).name, fh, mime)))
        if args.mask:
            fh = open(args.mask, "rb")
            handles.append(fh)
            files.append(("mask", (Path(args.mask).name, fh, "image/png")))
        r = requests.post(f"{OPENAI_URL}/edits", data=data, files=files, timeout=TIMEOUT,
                          headers={"Authorization": f"Bearer {openai_key()}"})
    finally:
        for fh in handles:
            fh.close()
    return openai_blobs(check_response(r, "OpenAI"), args.output_format)


# ---------------- Gemini ----------------
def gemini_key():
    k = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not k:
        die("GEMINI_API_KEY (ou GOOGLE_API_KEY) n'est pas définie.")
    return k


def gemini_call(args, fmt, images=()):
    model = args.model or os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    parts = [{"text": args.prompt}]
    for img in images:
        mime = mimetypes.guess_type(img)[0] or "image/png"
        parts.append({"inline_data": {"mime_type": mime,
                                      "data": base64.b64encode(Path(img).read_bytes()).decode()}})
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"],
                             "imageConfig": {"aspectRatio": FORMATS[fmt][1]}},
    }
    blobs = []
    for _ in range(args.n):
        r = requests.post(GEMINI_URL.format(model=model), json=body, timeout=TIMEOUT,
                          headers={"x-goog-api-key": gemini_key()})
        js = check_response(r, "Gemini")
        texts = []
        for cand in js.get("candidates", []):
            for p in cand.get("content", {}).get("parts", []):
                inline = p.get("inlineData") or p.get("inline_data")
                if inline:
                    ext = (mimetypes.guess_extension(inline.get("mimeType", "image/png")) or ".png")[1:]
                    blobs.append((base64.b64decode(inline["data"]), "jpg" if ext == "jpe" else ext))
                elif p.get("text"):
                    texts.append(p["text"])
        if texts:
            print("Gemini : " + " ".join(texts).strip(), file=sys.stderr)
    if not blobs:
        die("Gemini n'a renvoyé aucune image (demande peut-être refusée).")
    return blobs


# ---------------- CLI ----------------
def pick_provider(args):
    if args.provider:
        return args.provider
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    die("aucune clé API trouvée : définis OPENAI_API_KEY (ou GEMINI_API_KEY).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--format", "-f", help="carre | portrait | paysage")
        p.add_argument("--provider", choices=["openai", "gemini"])
        p.add_argument("--model")
        p.add_argument("--quality", default="auto", choices=["low", "medium", "high", "auto"])
        p.add_argument("--n", type=int, default=1, help="nombre d'images")
        p.add_argument("--background", choices=["transparent", "opaque", "auto"])
        p.add_argument("--output-format", default="png", choices=["png", "jpeg", "webp"])
        p.add_argument("--name", help="nom court pour le fichier")
        p.add_argument("--out-dir", default="outputs")

    g = sub.add_parser("generate", help="texte -> image")
    g.add_argument("prompt")
    common(g)

    e = sub.add_parser("edit", help="image(s) + consigne -> image")
    e.add_argument("items", nargs="+", metavar="IMAGE... PROMPT",
                   help="une ou plusieurs images puis la consigne (en dernier)")
    e.add_argument("--mask", help="PNG de masque (OpenAI) : zones transparentes = à modifier")
    common(e)

    args = ap.parse_args()
    if args.cmd == "edit":
        if len(args.items) < 2:
            die("edit attend au moins une image puis une consigne.")
        args.images, args.prompt = args.items[:-1], args.items[-1]
        for img in args.images + ([args.mask] if args.mask else []):
            if not Path(img).is_file():
                die(f"fichier introuvable : {img}")
        fmt = norm_format(args.format) or guess_format(args.images[0])
    else:
        fmt = norm_format(args.format) or "carre"

    provider = pick_provider(args)
    if args.n < 1:
        die("--n doit être >= 1")

    print(f"[{provider}] {args.cmd} - format {fmt}...", file=sys.stderr)
    if provider == "openai":
        blobs = openai_generate(args, fmt) if args.cmd == "generate" else openai_edit(args, fmt)
    else:
        blobs = gemini_call(args, fmt, args.images if args.cmd == "edit" else ())

    name = slugify(args.name) if args.name else slugify(args.prompt)
    for p in save_images(blobs, args.cmd, name, args.out_dir):
        print(p)


if __name__ == "__main__":
    main()
