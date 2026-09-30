# "Top 3 do dia" (30/09): uma arte por produto (#3, #2, #1) com preco e o Nº do achado (pra achar na pagina da bio).
# Entrada: env ITENS = JSON [{img, preco, precoDe, desconto, num, nome}] ja na ordem de exibicao (#3 -> #1).
# Saida: seg1.png, seg2.png, seg3.png e capa.jpg (capa = #1 com o selo do topo)
import io, json, os, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
LARANJA, AMARELO, VERMELHO = (238, 77, 45), (255, 214, 0), (220, 20, 60)
itens = json.loads(os.environ["ITENS"])

def baixa(url):
    for _ in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
        except Exception as e:
            print("  imagem falhou:", e)
    return Image.new("RGB", (800, 800), (240, 240, 240))

try:
    LOGO = Image.open("../achadinho/logo.png").convert("RGBA").resize((150, 150))
    m = Image.new("L", (150, 150), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 150, 150), 32, fill=255); LOGO.putalpha(m)
except Exception:
    LOGO = None

for k, it in enumerate(itens):
    rank = len(itens) - k
    prod = baixa(it["img"])
    fundo = ImageOps.fit(prod, (W, H)).filter(ImageFilter.GaussianBlur(40))
    fundo = Image.blend(fundo, Image.new("RGB", (W, H), (0, 0, 0)), 0.55)
    d = ImageDraw.Draw(fundo)

    def centro(txt, y, fonte, cor, pad=None, bg=None, raio=40):
        x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=fonte)
        w, h = x1 - x0, y1 - y0
        x = (W - w) // 2
        if bg:
            px, py = pad
            d.rounded_rectangle((x - px, y - py, x + w + px, y + h + py + 8), raio, fill=bg)
        d.text((x - x0, y - y0), txt, font=fonte, fill=cor)

    if LOGO: fundo.paste(LOGO, (30, 30), LOGO)
    centro(os.environ.get("SELO") or "TOP 3 DO DIA", 130, f(B, 58), (255, 255, 255), pad=(44, 24), bg=LARANJA)
    card = ImageOps.contain(prod, (860, 860))
    cx, cy = (W - 900) // 2, 290
    d.rounded_rectangle((cx, cy, cx + 900, cy + 900), 48, fill=(255, 255, 255))
    fundo.paste(card, (cx + (900 - card.width) // 2, cy + (900 - card.height) // 2))
    # medalha com a posicao
    r = 120
    d.ellipse((cx - 30, cy - 50, cx - 30 + 2 * r, cy - 50 + 2 * r), fill=VERMELHO if rank == 1 else LARANJA, outline=(255, 255, 255), width=10)
    t = "#%d" % rank; fo = f(B, 110)
    x0, y0, x1, y1 = d.textbbox((0, 0), t, font=fo)
    d.text((cx - 30 + r - (x1 - x0) / 2 - x0, cy - 50 + r - (y1 - y0) / 2 - y0), t, font=fo, fill=(255, 255, 255))
    # preco (a faixa 1230-1430 fica livre pra legenda)
    y = 1470
    if it.get("precoDe"):
        fde = f(R, 54); txt = "de " + it["precoDe"]
        x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=fde)
        x = (W - (x1 - x0)) // 2
        d.text((x - x0, y - y0), txt, font=fde, fill=(210, 210, 210))
        dx = d.textlength("de ", font=fde)
        d.line((x + dx, y + (y1 - y0) // 2 + 4, x + (x1 - x0), y + (y1 - y0) // 2 + 4), fill=(210, 210, 210), width=5)
        y += 80
    centro("por " + it["preco"], y, f(B, 112), AMARELO)
    centro("ACHADO Nº %s" % it["num"], y + 160, f(B, 52), (255, 255, 255), pad=(30, 14), bg=VERMELHO, raio=24)
    centro("LINKS NO PERFIL • PROCURE O Nº", 1810, f(B, 46), (255, 255, 255))
    fundo.save("seg%d.png" % (k + 1))
    if rank == 1: fundo.save("capa.jpg", quality=90)
print(len(itens), "artes")
