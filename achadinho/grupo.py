# Video de convite pro Grupo VIP (02/10), no visual "limpo": fundo de estudio, achadinhos reais passando em carrossel
# (recortados com rembg, preco embaixo) e botao verde "ENTRAR NO GRUPO VIP" pulsando.
# Env: ITENS = JSON [{img, preco}] ; saida: quadros rawvideo no stdout + capa.jpg. Uso: python3 grupo.py <duracao_s> | ffmpeg ...
import io, json, math, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
DUR = float(sys.argv[1]); N = int(math.ceil(DUR * FPS))
FD = os.path.expanduser("~/.fonts/")
def fonte(peso, tam):
    try: return ImageFont.truetype(FD + "Poppins-%s.ttf" % peso, tam)
    except Exception: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", tam)
ESCURO, LARANJA, VERDE = (30, 30, 34), (238, 77, 45), (37, 211, 102)
C1, C2 = (252, 242, 230), (244, 222, 198)

# fundo de estudio (mesmo do limpo.py)
g = Image.new("RGB", (1, H)); px = g.load()
for y in range(H):
    k = y / (H - 1); px[0, y] = tuple(int(C1[c] + (C2[c] - C1[c]) * k) for c in range(3))
FUNDO = g.resize((W, H)).convert("RGBA")
luz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(luz).ellipse((90, 420, W - 90, 1300), fill=(255, 255, 255, 130))
FUNDO.alpha_composite(luz.filter(ImageFilter.GaussianBlur(120)))

def texto(txt, fnt, cor, bg=None, pad=(30, 14)):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    x0, y0, x1, y1 = d0.textbbox((0, 0), txt, font=fnt)
    im = Image.new("RGBA", (x1 - x0 + 2 * pad[0], y1 - y0 + 2 * pad[1]), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if bg: d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=bg)
    d.text((pad[0] - x0, pad[1] - y0), txt, font=fnt, fill=cor)
    return im

# cabecalho fixo
TIT = texto("GRUPO VIP", fonte("Black", 120), ESCURO, pad=(10, 4))
SUB = texto("achadinhos todo dia no WhatsApp", fonte("SemiBold", 46), (90, 90, 98), pad=(10, 4))
BOTAO = texto("ENTRAR NO GRUPO VIP", fonte("ExtraBold", 54), (255, 255, 255), bg=VERDE, pad=(56, 26))
GRATIS = texto("é grátis • link no perfil", fonte("SemiBold", 40), (90, 90, 98), pad=(10, 4))
try:
    lg = Image.open("../achadinho/logo.png").convert("RGBA").resize((84, 84))
    m = Image.new("L", (84, 84), 0); ImageDraw.Draw(m).ellipse((0, 0, 83, 83), fill=255); lg.putalpha(m)
    nome = texto("Achei Barato!", fonte("Bold", 38), ESCURO, pad=(0, 0))
    MARCA = Image.new("RGBA", (84 + 18 + nome.width + 40, 104), (0, 0, 0, 0)); dm = ImageDraw.Draw(MARCA)
    dm.rounded_rectangle((0, 0, MARCA.width - 1, 103), 52, fill=(255, 255, 255, 190))
    MARCA.alpha_composite(lg, (10, 10)); MARCA.alpha_composite(nome, (84 + 28, (104 - nome.height) // 2))
except Exception:
    MARCA = None

# produtos do carrossel (recorta o fundo; se nao der, foto com cantos arredondados)
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
PRODS = []
for it in json.loads(os.environ["ITENS"]):
    im = baixa(it["img"])
    if im is None: continue
    rec = None
    if SESS is not None:
        try:
            cut = remove(im, session=SESS); a = cut.getchannel("A")
            area = sum(1 for v in a.getdata() if v > 40) / (a.width * a.height)
            if 0.06 < area < 0.93:
                bb = a.point(lambda v: 255 if v > 40 else 0).getbbox(); rec = cut.crop(bb) if bb else cut
        except Exception as e:
            print("sem recorte:", e, file=sys.stderr)
    if rec is None:
        foto = ImageOps.contain(im.convert("RGB"), (720, 720))
        mk = Image.new("L", foto.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, foto.width - 1, foto.height - 1), 44, fill=255)
        rec = foto.convert("RGBA"); rec.putalpha(mk)
    rec = ImageOps.contain(rec, (720, 720), Image.LANCZOS)
    PRODS.append((rec, texto("só " + it["preco"], fonte("Bold", 56), (255, 255, 255), bg=LARANJA, pad=(34, 14))))
if not PRODS: sys.exit("nenhum produto")
SEG = (DUR - 2.2) / len(PRODS)  # os ultimos 2,2s ficam pra tela final (legenda G)

def eas(t):
    c1 = 1.70158; c3 = c1 + 1; t = max(0.0, min(1.0, t)); return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def cola(base, im, cx, cy, esc=1.0, alfa=1.0):
    if esc <= 0.02 or alfa <= 0.01: return
    if esc != 1.0: im = im.resize((max(1, int(im.width * esc)), max(1, int(im.height * esc))), Image.BILINEAR)
    if alfa < 1.0: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alfa)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

out = sys.stdout.buffer
for i in range(N):
    t = i / FPS
    fr = FUNDO.copy()
    if MARCA: fr.alpha_composite(MARCA, (40, 60))
    cola(fr, TIT, W / 2, 270, eas(t / 0.5))
    cola(fr, SUB, W / 2, 380, 1.0, min(1.0, t / 0.6))
    k = min(int(t / SEG), len(PRODS) - 1); lt = t - k * SEG
    rec, preco = PRODS[k]
    entra = eas(lt / 0.45); sai = max(0.0, (lt - (SEG - 0.3)) / 0.3) if k < len(PRODS) - 1 else 0.0
    cx = W / 2 + (1 - entra) * 700 - sai * 900
    cola(fr, rec, cx, 860 + 8 * math.sin(t * 2), 0.96 + 0.04 * min(1.0, lt / SEG))
    cola(fr, preco, cx, 1420, eas((lt - 0.25) / 0.4))
    cola(fr, BOTAO, W / 2, 1640, 1 + 0.04 * math.sin(t * 5))
    cola(fr, GRATIS, W / 2, 1770)
    if i == int(1.2 * FPS): fr.convert("RGB").save("capa.jpg", quality=92)
    out.write(fr.convert("RGB").tobytes())
