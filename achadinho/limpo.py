# Estilo "limpo" (01/10): visual de catalogo — fundo de estudio em tom pastel (cor por categoria), produto recortado (rembg)
# com sombra suave, fonte Poppins e pouco texto. Substitui o fundo rosa/letreiro amarelo que a Leydiane achou feio.
# Gera os quadros e manda pro ffmpeg (stdout rawvideo). Uso: python3 limpo.py <duracao_s> | ffmpeg ...
# Env: PRECO, PRECO_DE, DESCONTO, CATEGORIA (grupo do produto), REVELA (s; modo "adivinha o preco")
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
DUR = float(sys.argv[1]); N = int(math.ceil(DUR * FPS))
FD = os.path.expanduser("~/.fonts/")
def fonte(peso, tam):
    try: return ImageFont.truetype(FD + "Poppins-%s.ttf" % peso, tam)
    except Exception: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", tam)
ESCURO, CINZA, LARANJA = (30, 30, 34), (120, 120, 128), (238, 77, 45)

# paleta pastel por categoria (cor de cima, cor de baixo)
PAL = {
    "casa": ((247, 241, 232), (232, 219, 200)), "moveis": ((247, 241, 232), (232, 219, 200)), "cama": ((247, 241, 232), (232, 219, 200)),
    "mercado": ((247, 241, 232), (232, 219, 200)), "ferramentas": ((240, 238, 234), (218, 214, 206)),
    "beleza": ((251, 236, 238), (240, 210, 217)), "perfumaria": ((251, 236, 238), (240, 210, 217)),
    "pet": ((232, 246, 240), (202, 232, 220)),
    "familia": ((233, 242, 253), (208, 225, 246)), "brinquedos": ((233, 242, 253), (208, 225, 246)), "presentes": ((252, 238, 242), (238, 214, 226)),
    "moda": ((241, 236, 250), (221, 210, 240)), "masculino": ((236, 240, 244), (212, 220, 230)),
    "tech": ((236, 240, 244), (212, 220, 230)), "viral": ((252, 242, 228), (244, 222, 196)), "fitness": ((252, 238, 228), (244, 214, 196)),
}
C1, C2 = PAL.get(os.environ.get("CATEGORIA", ""), ((246, 242, 236), (228, 220, 208)))

# ---------- fundo de estudio: degrade vertical + luz atras do produto + sombra nas bordas ----------
g = Image.new("RGB", (1, H)); px = g.load()
for y in range(H):
    k = y / (H - 1)
    px[0, y] = tuple(int(C1[c] + (C2[c] - C1[c]) * k) for c in range(3))
FUNDO = g.resize((W, H)).convert("RGBA")
luz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(luz).ellipse((90, 340, W - 90, 1260), fill=(255, 255, 255, 120))
FUNDO.alpha_composite(luz.filter(ImageFilter.GaussianBlur(120)))
vin = Image.new("L", (W, H), 0)
ImageDraw.Draw(vin).rectangle((0, 0, W, H), outline=70, width=90)
vin = vin.filter(ImageFilter.GaussianBlur(120))
FUNDO = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), FUNDO, vin.point(lambda v: v // 3))

# ---------- produto recortado (se o recorte falhar, foto com cantos arredondados) ----------
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
if recorte is None:
    foto = ImageOps.contain(prod.convert("RGB"), (820, 820))
    m = Image.new("L", foto.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, foto.width - 1, foto.height - 1), 44, fill=255)
    recorte = foto.convert("RGBA"); recorte.putalpha(m)
recorte = ImageOps.contain(recorte, (800, 800), Image.LANCZOS)
sombra = Image.new("RGBA", (int(recorte.width * 0.9) + 160, 120), (0, 0, 0, 0))
ImageDraw.Draw(sombra).ellipse((0, 0, sombra.width - 1, 119), fill=tuple(int(c * 0.55) for c in C2) + (150,))
sombra = sombra.filter(ImageFilter.GaussianBlur(26))
CY = 800  # centro do produto (a legenda fica por volta de y=1280-1360)

# ---------- textos fixos ----------
def texto(txt, fnt, cor, bg=None, pad=(30, 14), raio=999, risco=False):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    x0, y0, x1, y1 = d0.textbbox((0, 0), txt, font=fnt)
    w, h = x1 - x0, y1 - y0
    im = Image.new("RGBA", (w + 2 * pad[0], h + 2 * pad[1]), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if bg: d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), min(raio, im.height // 2), fill=bg)
    d.text((pad[0] - x0, pad[1] - y0), txt, font=fnt, fill=cor)
    if risco: d.line((pad[0], im.height // 2 + 2, im.width - pad[0], im.height // 2 + 2), fill=cor, width=4)
    return im
PRECO = texto(os.environ["PRECO"], fonte("Black", 132), ESCURO, pad=(10, 6))
DE = texto("de " + os.environ["PRECO_DE"], fonte("Medium", 46), CINZA, pad=(10, 4), risco=True) if os.environ.get("PRECO_DE") else None
DESC = texto(os.environ["DESCONTO"] + " OFF", fonte("Bold", 46), (255, 255, 255), bg=LARANJA, pad=(26, 10)) if os.environ.get("DESCONTO") else None
PERGUNTA = texto("Quanto custa?", fonte("ExtraBold", 96), ESCURO, pad=(10, 6))
CTA = texto("link pra comprar no perfil", fonte("SemiBold", 40), (90, 90, 98), bg=(255, 255, 255, 170), pad=(34, 16))
MARCA = None
try:
    lg = Image.open("../achadinho/logo.png").convert("RGBA").resize((84, 84))
    m = Image.new("L", (84, 84), 0); ImageDraw.Draw(m).ellipse((0, 0, 83, 83), fill=255); lg.putalpha(m)
    nome = texto("Achei Barato!", fonte("Bold", 38), ESCURO, pad=(0, 0))
    MARCA = Image.new("RGBA", (84 + 18 + nome.width + 40, 104), (0, 0, 0, 0)); dm = ImageDraw.Draw(MARCA)
    dm.rounded_rectangle((0, 0, MARCA.width - 1, 103), 52, fill=(255, 255, 255, 190))
    MARCA.alpha_composite(lg, (10, 10)); MARCA.alpha_composite(nome, (84 + 28, (104 - nome.height) // 2))
except Exception as e:
    print("sem marca:", e, file=sys.stderr)
REVELA = float(os.environ["REVELA"]) if os.environ.get("REVELA") else None

def eas(t):  # easeOutBack
    c1 = 1.70158; c3 = c1 + 1; t = max(0.0, min(1.0, t))
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def pop(t, ini, dur=0.4):
    return eas((t - ini) / dur) if t >= ini else 0.0
def fade(t, ini, dur=0.35):
    return max(0.0, min(1.0, (t - ini) / dur))
def cola(base, im, cx, cy, esc=1.0, alfa=1.0):
    if esc <= 0.02 or alfa <= 0.01: return
    if esc != 1.0: im = im.resize((max(1, int(im.width * esc)), max(1, int(im.height * esc))), Image.BILINEAR)
    if alfa < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alfa)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

out = sys.stdout.buffer
for i in range(N):
    t = i / FPS
    fr = FUNDO.copy()
    ent = fade(t, 0.0, 0.5)
    esc = (0.94 + 0.06 * eas(min(1.0, t / 0.6))) * (1 + 0.035 * t / max(DUR, 1))  # entra e vai aproximando devagar
    py = CY + (1 - ent) * 40 + 10 * math.sin(t * 1.6)
    cola(fr, sombra, W / 2, CY + recorte.height * esc / 2 + 20, 0.9 + 0.1 * ent, 0.9 * ent)
    cola(fr, recorte, W / 2, py, esc, ent)
    if MARCA: fr.alpha_composite(MARCA, (40, 60))
    ini = REVELA if REVELA is not None else 0.6
    if REVELA is not None and t < REVELA:
        cola(fr, PERGUNTA, W / 2, 1585, pop(t, 0.3) * (1 + 0.03 * math.sin(t * 5)))
    else:
        if DE: cola(fr, DE, W / 2, 1490, 1.0, fade(t, ini))
        cola(fr, PRECO, W / 2, 1590, pop(t, ini + 0.1))
        if DESC: cola(fr, DESC, W / 2, 1712, pop(t, ini + 0.3))
    cola(fr, CTA, W / 2, 1830, 1.0, fade(t, 0.8))
    if i == int(1.6 * FPS): fr.convert("RGB").save("capa.jpg", quality=92)
    out.write(fr.convert("RGB").tobytes())
