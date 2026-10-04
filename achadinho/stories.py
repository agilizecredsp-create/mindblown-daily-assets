# Kit de Stories do dia (04/10): 3 imagens 1080x1920 no visual "limpo" (fundo de estudio pastel por categoria, produto recortado,
# preco em destaque) com espaco livre embaixo pra Leydiane colar a figurinha de LINK do Instagram (a API nao coloca link no Story).
# Env ITENS = JSON [{img, titulo, preco, precoDe, cat}] ; saida: story_1.png ... story_N.png
import io, json, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
FD = os.path.expanduser("~/.fonts/")
def fonte(peso, tam):
    try: return ImageFont.truetype(FD + "Poppins-%s.ttf" % peso, tam)
    except Exception: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", tam)
ESCURO, CINZA, LARANJA = (30, 30, 34), (110, 110, 118), (238, 77, 45)
PAL = {
    "casa": ((247, 241, 232), (232, 219, 200)), "moveis": ((247, 241, 232), (232, 219, 200)), "cama": ((247, 241, 232), (232, 219, 200)),
    "mercado": ((247, 241, 232), (232, 219, 200)), "ferramentas": ((240, 238, 234), (218, 214, 206)),
    "beleza": ((251, 236, 238), (240, 210, 217)), "perfumaria": ((251, 236, 238), (240, 210, 217)), "pet": ((232, 246, 240), (202, 232, 220)),
    "familia": ((233, 242, 253), (208, 225, 246)), "brinquedos": ((233, 242, 253), (208, 225, 246)), "presentes": ((252, 238, 242), (238, 214, 226)),
    "moda": ((241, 236, 250), (221, 210, 240)), "masculino": ((236, 240, 244), (212, 220, 230)), "tech": ((236, 240, 244), (212, 220, 230)),
    "viral": ((252, 242, 228), (244, 222, 196)), "fitness": ((252, 238, 228), (244, 214, 196)),
}

try:
    from rembg import remove, new_session
    SESS = new_session("isnet-general-use")
except Exception:
    SESS = None

def baixa(url):
    for _ in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGBA")
        except Exception as e:
            print("imagem falhou:", e, file=sys.stderr)
    return None

def texto(txt, fnt, cor, bg=None, pad=(30, 14), risco=False):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    x0, y0, x1, y1 = d0.textbbox((0, 0), txt, font=fnt)
    im = Image.new("RGBA", (x1 - x0 + 2 * pad[0], y1 - y0 + 2 * pad[1]), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if bg: d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=bg)
    d.text((pad[0] - x0, pad[1] - y0), txt, font=fnt, fill=cor)
    if risco: d.line((pad[0], im.height // 2 + 2, im.width - pad[0], im.height // 2 + 2), fill=cor, width=4)
    return im

def quebra(txt, fnt, larg):  # quebra o titulo em ate 2 linhas
    pal, linhas, atual = txt.split(), [], ""
    for p in pal:
        t = (atual + " " + p).strip()
        if ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(t, font=fnt) <= larg: atual = t
        else: linhas.append(atual); atual = p
    linhas.append(atual)
    return [l for l in linhas if l][:2]

def centro(base, im, cy):
    base.alpha_composite(im, (int((W - im.width) / 2), int(cy - im.height / 2)))

try:
    LOGO = Image.open("../achadinho/logo.png").convert("RGBA").resize((84, 84))
    m = Image.new("L", (84, 84), 0); ImageDraw.Draw(m).ellipse((0, 0, 83, 83), fill=255); LOGO.putalpha(m)
except Exception:
    LOGO = None

for n, it in enumerate(json.loads(os.environ["ITENS"]), 1):
    C1, C2 = PAL.get(it.get("cat", ""), ((246, 242, 236), (228, 220, 208)))
    g = Image.new("RGB", (1, H)); px = g.load()
    for y in range(H):
        k = y / (H - 1); px[0, y] = tuple(int(C1[c] + (C2[c] - C1[c]) * k) for c in range(3))
    fr = g.resize((W, H)).convert("RGBA")
    luz = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(luz).ellipse((90, 380, W - 90, 1220), fill=(255, 255, 255, 130))
    fr.alpha_composite(luz.filter(ImageFilter.GaussianBlur(120)))
    if LOGO:
        nome = texto("Achei Barato!", fonte("Bold", 38), ESCURO, pad=(0, 0))
        marca = Image.new("RGBA", (84 + 18 + nome.width + 40, 104), (0, 0, 0, 0)); dm = ImageDraw.Draw(marca)
        dm.rounded_rectangle((0, 0, marca.width - 1, 103), 52, fill=(255, 255, 255, 190))
        marca.alpha_composite(LOGO, (10, 10)); marca.alpha_composite(nome, (84 + 28, (104 - nome.height) // 2))
        fr.alpha_composite(marca, (40, 70))
    centro(fr, texto("ACHADINHO DO DIA", fonte("Bold", 40), (255, 255, 255), bg=LARANJA, pad=(34, 14)), 250)
    ft = fonte("ExtraBold", 74); y = 360
    for l in quebra(it.get("titulo", ""), ft, 940):
        centro(fr, texto(l, ft, ESCURO, pad=(6, 4)), y); y += 92
    prod = baixa(it["img"]); rec = None
    if prod is not None and SESS is not None:
        try:
            cut = remove(prod, session=SESS); a = cut.getchannel("A")
            area = sum(1 for v in a.getdata() if v > 40) / (a.width * a.height)
            if 0.06 < area < 0.93:
                bb = a.point(lambda v: 255 if v > 40 else 0).getbbox(); rec = cut.crop(bb) if bb else cut
        except Exception as e:
            print("sem recorte:", e, file=sys.stderr)
    if rec is None and prod is not None:
        foto = ImageOps.contain(prod.convert("RGB"), (700, 700))
        mk = Image.new("L", foto.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, foto.width - 1, foto.height - 1), 44, fill=255)
        rec = foto.convert("RGBA"); rec.putalpha(mk)
    if rec is not None:
        rec = ImageOps.contain(rec, (720, 640), Image.LANCZOS)
        sombra = Image.new("RGBA", (int(rec.width * 0.7) + 200, 210), (0, 0, 0, 0))
        ImageDraw.Draw(sombra).ellipse((60, 60, sombra.width - 61, 149), fill=tuple(int(c * 0.5) for c in C2) + (110,))
        sombra = sombra.filter(ImageFilter.GaussianBlur(30))
        centro(fr, sombra, 830 + rec.height / 2 + 10)
        centro(fr, rec, 830)
    if it.get("precoDe"):
        centro(fr, texto("de " + it["precoDe"], fonte("Medium", 46), CINZA, pad=(10, 4), risco=True), 1235)
    centro(fr, texto(it["preco"], fonte("Black", 140), ESCURO, pad=(10, 6)), 1340)
    centro(fr, texto("toque no link abaixo", fonte("SemiBold", 44), CINZA, pad=(10, 4)), 1490)
    # 1560-1800 fica livre pra figurinha de link do Instagram
    fr.convert("RGB").save("story_%d.png" % n, optimize=True)
    print("story", n, "ok")
