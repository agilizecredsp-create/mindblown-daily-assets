# Kit de Stories do dia (04/10; arte refeita 06/10 — a Leydiane achou a 1a versao "feia e mal feita"):
# foto ORIGINAL do produto grande num card branco com sombra (o recorte do rembg deixava borda torta), selos de nota e vendidos,
# etiqueta do tema, preco em destaque e espaco embaixo pra figurinha de LINK do Instagram (a API nao coloca link no Story).
# Env ITENS = JSON [{img, titulo, preco, precoDe, desconto, nota, vendas, cat}] ; ROTULO (etiqueta do topo) ; PERGUNTA (Story de caixinha)
# Saida: story_1.png ... story_N.png e story_pergunta.png
import io, json, math, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
FD = os.path.expanduser("~/.fonts/")
def fonte(peso, tam):
    try: return ImageFont.truetype(FD + "Poppins-%s.ttf" % peso, tam)
    except Exception: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", tam)
ESCURO, CINZA, LARANJA, AMARELO = (28, 28, 34), (110, 110, 118), (238, 77, 45), (255, 196, 0)
PAL = {  # (cima, baixo, destaque)
    "casa": ((250, 245, 237), (236, 222, 202), (214, 170, 120)), "moveis": ((250, 245, 237), (236, 222, 202), (214, 170, 120)),
    "cama": ((250, 245, 237), (236, 222, 202), (214, 170, 120)), "mercado": ((250, 245, 237), (236, 222, 202), (214, 170, 120)),
    "ferramentas": ((242, 240, 236), (220, 216, 208), (160, 160, 170)),
    "beleza": ((253, 240, 242), (242, 212, 220), (236, 140, 170)), "perfumaria": ((253, 240, 242), (242, 212, 220), (236, 140, 170)),
    "pet": ((236, 248, 242), (204, 234, 222), (110, 200, 160)),
    "familia": ((237, 245, 255), (206, 224, 248), (120, 170, 240)), "brinquedos": ((240, 244, 255), (214, 222, 252), (150, 130, 245)),
    "presentes": ((253, 240, 244), (240, 214, 228), (240, 120, 160)),
    "moda": ((244, 239, 252), (224, 212, 244), (170, 130, 230)), "masculino": ((238, 242, 246), (212, 222, 232), (120, 150, 190)),
    "tech": ((238, 242, 246), (212, 222, 232), (120, 150, 190)), "viral": ((253, 244, 232), (246, 222, 196), (250, 150, 80)),
    "fitness": ((253, 240, 230), (246, 216, 196), (250, 140, 90)),
}
PADRAO = ((248, 243, 236), (232, 222, 208), (220, 160, 110))

def baixa(url):
    for _ in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
        except Exception as e:
            print("imagem falhou:", e, file=sys.stderr)
    return None

def texto(txt, fnt, cor, bg=None, pad=(30, 14), risco=False, borda=None):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    x0, y0, x1, y1 = d0.textbbox((0, 0), txt, font=fnt)
    im = Image.new("RGBA", (x1 - x0 + 2 * pad[0], y1 - y0 + 2 * pad[1]), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if bg: d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=bg, outline=borda, width=3 if borda else 0)
    d.text((pad[0] - x0, pad[1] - y0), txt, font=fnt, fill=cor)
    if risco: d.line((pad[0], im.height // 2 + 2, im.width - pad[0], im.height // 2 + 2), fill=cor, width=4)
    return im

def quebra(txt, fnt, larg, maxl=2):
    pal, linhas, atual = txt.split(), [], ""
    for p in pal:
        t = (atual + " " + p).strip()
        if ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(t, font=fnt) <= larg: atual = t
        else: linhas.append(atual); atual = p
    linhas.append(atual)
    return [l for l in linhas if l][:maxl]

def centro(base, im, cy, cx=W / 2):
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def estrela(r, cor):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((r + rr * math.cos(a), r + rr * math.sin(a)))
    ImageDraw.Draw(im).polygon(pts, fill=cor); return im

def fundo(cat):
    C1, C2, AC = PAL.get(cat or "", PADRAO)
    g = Image.new("RGB", (1, H)); px = g.load()
    for y in range(H):
        k = y / (H - 1); px[0, y] = tuple(int(C1[c] + (C2[c] - C1[c]) * k) for c in range(3))
    fr = g.resize((W, H)).convert("RGBA")
    bolhas = Image.new("RGBA", (W, H), (0, 0, 0, 0)); db = ImageDraw.Draw(bolhas)
    db.ellipse((-260, 120, 520, 900), fill=AC + (70,)); db.ellipse((640, 980, 1380, 1720), fill=AC + (60,))
    fr.alpha_composite(bolhas.filter(ImageFilter.GaussianBlur(110)))
    return fr, AC

def marca(fr):
    try:
        lg = Image.open("../achadinho/logo.png").convert("RGBA").resize((84, 84))
        m = Image.new("L", (84, 84), 0); ImageDraw.Draw(m).ellipse((0, 0, 83, 83), fill=255); lg.putalpha(m)
        nome = texto("Achei Barato!", fonte("Bold", 38), ESCURO, pad=(0, 0))
        mc = Image.new("RGBA", (84 + 18 + nome.width + 40, 104), (0, 0, 0, 0)); dm = ImageDraw.Draw(mc)
        dm.rounded_rectangle((0, 0, mc.width - 1, 103), 52, fill=(255, 255, 255, 215))
        mc.alpha_composite(lg, (10, 10)); mc.alpha_composite(nome, (84 + 28, (104 - nome.height) // 2))
        fr.alpha_composite(mc, (40, 60))
    except Exception as e:
        print("sem marca:", e, file=sys.stderr)

def mil(v):
    v = int(v or 0)
    return ("+%d mil vendidos" % (v // 1000)) if v >= 1000 else ("+%d vendidos" % v if v >= 50 else "")

ROTULO = os.environ.get("ROTULO") or "ACHADINHO DO DIA"
for n, it in enumerate(json.loads(os.environ.get("ITENS") or "[]") or [], 1):
    fr, AC = fundo(it.get("cat"))
    marca(fr)
    centro(fr, texto(ROTULO, fonte("Bold", 38), (255, 255, 255), bg=LARANJA, pad=(36, 14)), 225)
    # card branco grande com a foto original
    CX, CY, CW, CH = 70, 290, 940, 940
    sombra = Image.new("RGBA", (CW + 160, CH + 160), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((80, 100, CW + 80, CH + 80), 60, fill=(0, 0, 0, 70))
    fr.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(34)), (CX - 80, CY - 80))
    card = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); ImageDraw.Draw(card).rounded_rectangle((0, 0, CW - 1, CH - 1), 56, fill=(255, 255, 255, 255))
    foto = baixa(it["img"])
    if foto is not None:
        foto = ImageOps.contain(foto, (CW - 60, CH - 60), Image.LANCZOS).convert("RGBA")
        mk = Image.new("L", foto.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, foto.width - 1, foto.height - 1), 36, fill=255)
        foto.putalpha(mk); card.alpha_composite(foto, ((CW - foto.width) // 2, (CH - foto.height) // 2))
    fr.alpha_composite(card, (CX, CY))
    # selos sobre o card: nota e vendidos (embaixo) e desconto (canto)
    selos = []
    if it.get("nota"):
        nt = texto(("%.1f" % float(it["nota"])).replace(".", ","), fonte("Bold", 36), ESCURO, pad=(0, 0))
        s = Image.new("RGBA", (nt.width + 98, 66), (0, 0, 0, 0)); ds = ImageDraw.Draw(s)
        ds.rounded_rectangle((0, 0, s.width - 1, 65), 33, fill=(255, 255, 255, 240), outline=(230, 230, 236), width=2)
        s.alpha_composite(estrela(19, AMARELO), (24, 14)); s.alpha_composite(nt, (72, (66 - nt.height) // 2 - 2)); selos.append(s)
    if mil(it.get("vendas")):
        selos.append(texto(mil(it.get("vendas")), fonte("SemiBold", 34), ESCURO, bg=(255, 255, 255, 240), pad=(26, 12), borda=(230, 230, 236)))
    x = CX + 30
    for s in selos:
        fr.alpha_composite(s, (x, CY + CH - s.height - 30)); x += s.width + 14
    if it.get("desconto"):
        dsc = Image.new("RGBA", (190, 190), (0, 0, 0, 0)); dd = ImageDraw.Draw(dsc)
        dd.ellipse((0, 0, 189, 189), fill=LARANJA, outline=(255, 255, 255), width=8)
        t1 = texto(it["desconto"], fonte("Black", 52), (255, 255, 255), pad=(0, 0)); t2 = texto("OFF", fonte("Bold", 32), (255, 255, 255), pad=(0, 0))
        dsc.alpha_composite(t1, ((190 - t1.width) // 2, 52)); dsc.alpha_composite(t2, ((190 - t2.width) // 2, 112))
        fr.alpha_composite(dsc.rotate(-10, resample=Image.BICUBIC), (CX + CW - 165, CY - 45))
    # nome do produto
    ft = fonte("ExtraBold", 62); y = 1300
    for l in quebra(it.get("titulo", ""), ft, 960):
        centro(fr, texto(l, ft, ESCURO, pad=(6, 4)), y); y += 80
    # preco
    y = max(y + 20, 1450)
    if it.get("precoDe"):
        centro(fr, texto("de " + it["precoDe"], fonte("Medium", 44), CINZA, pad=(10, 4), risco=True), y); y += 70
    centro(fr, texto(it["preco"], fonte("Black", 136), LARANJA, pad=(10, 6)), y + 40)
    # chamada + seta pra figurinha de link (1720-1880 fica livre)
    ch = texto("toque no link e garanta o seu", fonte("SemiBold", 40), ESCURO, pad=(10, 4))
    centro(fr, ch, y + 165)
    seta = Image.new("RGBA", (60, 40), (0, 0, 0, 0)); ImageDraw.Draw(seta).polygon([(0, 0), (60, 0), (30, 36)], fill=LARANJA)
    centro(fr, seta, y + 220)
    fr.convert("RGB").save("story_%d.png" % n, optimize=True)
    print("story", n, "ok")

# 06/10: Story da caixa de perguntas (engaja e mostra o que o publico quer comprar). Espaco livre no meio pra figurinha "Perguntas".
if os.environ.get("PERGUNTA"):
    fr, AC = fundo("viral")
    marca(fr)
    centro(fr, texto("ME CONTA!", fonte("Bold", 44), (255, 255, 255), bg=LARANJA, pad=(40, 16)), 360)
    ft = fonte("Black", 104); y = 520
    for l in quebra(os.environ["PERGUNTA"], ft, 960):
        centro(fr, texto(l, ft, ESCURO, pad=(6, 4)), y); y += 124
    fs = fonte("SemiBold", 48); y += 30
    for l in quebra(os.environ.get("PERGUNTA_SUB", "Eu procuro e acho mais barato pra você!"), fs, 900):
        centro(fr, texto(l, fs, CINZA, pad=(6, 4)), y); y += 64
    # 1000-1500 livre pra figurinha de perguntas
    centro(fr, texto("toque na caixinha e responda", fonte("SemiBold", 42), CINZA, pad=(10, 4)), 1620)
    fr.convert("RGB").save("story_pergunta.png", optimize=True)
    print("pergunta ok")
