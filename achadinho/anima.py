# Estilo "animado" (29/09): produto recortado (rembg) animado sobre fundo em movimento + preco "pulando".
# Gera os quadros e manda direto pro ffmpeg (stdout em rawvideo). Uso: python3 anima.py <duracao_s> | ffmpeg ...
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
DUR = float(sys.argv[1]); N = int(math.ceil(DUR * FPS))
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
LAR, AMA, ROSA = (238, 77, 45), (255, 214, 0), (233, 30, 99)

# ---------- produto: tenta recortar o fundo; se nao der, usa card branco com a foto ----------
prod = Image.open("produto.bin").convert("RGBA")
recorte = None
try:
    from rembg import remove, new_session
    cut = remove(prod, session=new_session("isnet-general-use"))
    a = cut.getchannel("A"); area = sum(1 for v in a.getdata() if v > 40) / (a.width * a.height)
    if 0.06 < area < 0.93:
        bb = a.point(lambda v: 255 if v > 40 else 0).getbbox()
        recorte = cut.crop(bb) if bb else cut
    print("recorte area", round(area, 2), file=sys.stderr)
except Exception as e:
    print("sem recorte:", e, file=sys.stderr)
if recorte is None:  # fallback: card branco arredondado com a foto
    foto = ImageOps.contain(prod.convert("RGB"), (800, 800))
    card = Image.new("RGBA", (foto.width + 40, foto.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 40, fill=(255, 255, 255, 255))
    card.paste(foto, (20, 20)); recorte = card
recorte = ImageOps.contain(recorte, (820, 820), Image.LANCZOS)
# sombra suave embaixo do produto
sombra = Image.new("RGBA", (recorte.width + 120, 90), (0, 0, 0, 0))
ImageDraw.Draw(sombra).ellipse((0, 0, sombra.width - 1, 89), fill=(0, 0, 0, 90))
sombra = sombra.filter(ImageFilter.GaussianBlur(18))

# ---------- fundo: degrade alto que "desce" devagar ----------
def degrade(h):
    g = Image.new("RGB", (1, h)); px = g.load()
    cores = [LAR, ROSA, (255, 140, 0), LAR]
    for y in range(h):
        t = (y / h) * (len(cores) - 1); i = min(int(t), len(cores) - 2); k = t - i
        px[0, y] = tuple(int(cores[i][c] + (cores[i + 1][c] - cores[i][c]) * k) for c in range(3))
    return g.resize((W, h))
FUNDO = degrade(H * 2)
brilho = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
ImageDraw.Draw(brilho).ellipse((0, 0, 899, 899), fill=(255, 255, 255, 110))
brilho = brilho.filter(ImageFilter.GaussianBlur(90))

# ---------- textos fixos ----------
def texto_img(txt, fonte, cor, bg=None, pad=(36, 18), raio=34, contorno=0):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    x0, y0, x1, y1 = d0.textbbox((0, 0), txt, font=fonte, stroke_width=contorno)
    w, h = x1 - x0, y1 - y0
    im = Image.new("RGBA", (w + 2 * pad[0], h + 2 * pad[1] + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if bg: d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), raio, fill=bg)
    d.text((pad[0] - x0, pad[1] - y0), txt, font=fonte, fill=cor, stroke_width=contorno, stroke_fill=(0, 0, 0))
    return im
SELO = texto_img(os.environ.get("SELO", "ACHEI BARATO!"), f(B, 56), (255, 255, 255), bg=(0, 0, 0, 150))
PRECO = texto_img("por " + os.environ["PRECO"], f(B, 118), AMA, contorno=6, pad=(10, 6))
DE = texto_img("de " + os.environ.get("PRECO_DE", ""), f(R, 54), (255, 255, 255), pad=(10, 4)) if os.environ.get("PRECO_DE") else None
if DE:  # risco no "de R$"
    dd = ImageDraw.Draw(DE); dx = dd.textlength("de ", font=f(R, 54)) + 10
    dd.line((dx, DE.height // 2 + 2, DE.width - 10, DE.height // 2 + 2), fill=(255, 255, 255), width=5)
REVELA = float(os.environ["REVELA"]) if os.environ.get("REVELA") else None
PERGUNTA = texto_img("QUANTO CUSTA?", f(B, 90), (255, 255, 255), bg=(220, 20, 60), pad=(40, 22), raio=40)
CTA = texto_img(os.environ.get("CTA", "LINK PRA COMPRAR NO PERFIL"), f(B, 46), (255, 255, 255), bg=(0, 0, 0, 140))
DESC = None
if os.environ.get("DESCONTO"):
    DESC = Image.new("RGBA", (250, 250), (0, 0, 0, 0)); dd = ImageDraw.Draw(DESC)
    dd.ellipse((0, 0, 249, 249), fill=(220, 20, 60), outline=(255, 255, 255), width=8)
    t = os.environ["DESCONTO"]; fo = f(B, 70 if len(t) <= 4 else 58)
    x0, y0, x1, y1 = dd.textbbox((0, 0), t, font=fo); dd.text((125 - (x1 - x0) / 2 - x0, 95 - (y1 - y0) / 2 - y0), t, font=fo, fill=(255, 255, 255))
    x0, y0, x1, y1 = dd.textbbox((0, 0), "OFF", font=f(B, 44)); dd.text((125 - (x1 - x0) / 2 - x0, 150), "OFF", font=f(B, 44), fill=AMA)
LOGO = None
try:
    LOGO = Image.open("../achadinho/logo.png").convert("RGBA").resize((140, 140))
    m = Image.new("L", (140, 140), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 139, 139), 30, fill=255); LOGO.putalpha(m)
except Exception:
    pass

def eas(t):  # easeOutBack (entrada com "pulinho")
    c1 = 1.70158; c3 = c1 + 1; t = max(0.0, min(1.0, t))
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def pop(t, ini, dur=0.35):
    return eas((t - ini) / dur) if t >= ini else 0.0
def cola(base, im, cx, cy, esc=1.0, ang=0.0):
    if esc <= 0.02: return
    if esc != 1.0: im = im.resize((max(1, int(im.width * esc)), max(1, int(im.height * esc))), Image.BILINEAR)
    if ang: im = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

out = sys.stdout.buffer
for i in range(N):
    t = i / FPS
    off = int((t * 60) % H)
    fr = FUNDO.crop((0, off, W, off + H)).convert("RGBA")
    cola(fr, brilho, W / 2, 720 + 15 * math.sin(t * 2))
    # produto: entra de baixo com pulinho (0-0,6s), depois flutua e gira de leve
    ent = pop(t, 0.0, 0.6)
    py = 720 + (1 - ent) * 900 + 18 * math.sin(t * 2.4)
    ang = 3.0 * math.sin(t * 1.7)
    esc = 0.9 + 0.1 * ent + 0.02 * math.sin(t * 3.1)
    cola(fr, sombra, W / 2, 720 + recorte.height * esc / 2 + 30, 1.0)
    cola(fr, recorte, W / 2, py, esc, ang)
    # 30/09: modo "adivinha" — preco/desconto escondidos ate REVELA (s); antes disso, "QUANTO CUSTA?" pulsando
    ini = REVELA if REVELA is not None else 0.0
    if DESC: cola(fr, DESC, W / 2 + 330, 380, pop(t, ini + 0.5 if REVELA is None else ini + 0.25) * (1 + 0.04 * math.sin(t * 6)), 12 * math.sin(t * 3))
    if LOGO: fr.alpha_composite(LOGO, (30, 30))
    cola(fr, SELO, W / 2 + 60, 105, 1.0)
    if REVELA is not None and t < REVELA:
        cola(fr, PERGUNTA, W / 2, 1540, pop(t, 0.3, 0.4) * (1 + 0.06 * math.sin(t * 7)), 3 * math.sin(t * 4))
    else:
        if DE: cola(fr, DE, W / 2, 1470, pop(t, ini + 0.9 if REVELA is None else ini))
        cola(fr, PRECO, W / 2, 1570, pop(t, 1.0 if REVELA is None else ini + 0.1, 0.4) * (1 + 0.03 * math.sin(t * 5)))
    cola(fr, CTA, W / 2, 1810, 1.0 + 0.04 * math.sin(t * 6))
    if i == int(1.6 * FPS): fr.convert("RGB").save("capa.jpg", quality=90)
    out.write(fr.convert("RGB").tobytes())
