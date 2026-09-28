#!/bin/bash
set -e
# ============================================================
# Video de ANUNCIO do Grupo VIP (1080x1920): vitrine de 4-5 achadinhos
# (foto + preco + desconto) + tela final com a logo e "ENTRA GRATIS NO GRUPO VIP".
# Narracao edge-tts (Thalita +10%), legenda sincronizada por palavra.
# Variaveis: PRODUTOS_JSON = [{"img","titulo","preco","de","desc"}], NARRACAO
# Saida: render_work/video.mp4 e render_work/capa.jpg
# ============================================================
WORKDIR="render_work"
rm -rf "$WORKDIR" && mkdir -p "$WORKDIR"
cd "$WORKDIR"
pip install edge-tts pillow --break-system-packages --quiet 2>/dev/null || pip install edge-tts pillow --quiet

echo "$PRODUTOS_JSON" > produtos.json
python3 - << 'PYEOF'
import json, subprocess
for i, p in enumerate(json.load(open("produtos.json", encoding="utf-8"))):
    subprocess.run(["curl", "-sL", "--fail", "--retry", "5", "-A", "Mozilla/5.0", "-o", f"p{i}.bin", p["img"]], check=True)
PYEOF

cat > tts.py << 'PYEOF'
import asyncio, json, os, re, edge_tts
TEXTO = re.sub(r"(?i)\bshopee\b", "Xôpi", os.environ["NARRACAO"])
async def main():
    com = edge_tts.Communicate(TEXTO, "pt-BR-ThalitaMultilingualNeural", rate="+10%", boundary="WordBoundary")
    pal = []
    with open("narracao.mp3", "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                pal.append({"start": ch["offset"] / 1e7, "end": (ch["offset"] + ch["duration"]) / 1e7, "text": ch["text"]})
    json.dump(pal, open("palavras.json", "w", encoding="utf-8"), ensure_ascii=False)
asyncio.run(main())
PYEOF
python3 tts.py
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 narracao.mp3)
echo "Narracao: ${DUR}s"

cat > artes.py << 'PYEOF'
import json
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
W, H = 1080, 1920
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
LAR, AMA = (238, 77, 45), (255, 214, 0)
prods = json.load(open("produtos.json", encoding="utf-8"))
try:
    LOGO = Image.open("../achadinho/logo.png").convert("RGBA")
except Exception:
    LOGO = None

def logo(img, tam, x, y):
    if not LOGO: return
    lg = LOGO.resize((tam, tam)); m = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, tam, tam), tam // 5, fill=255)
    img.paste(lg, (x, y), m)

def centro(d, txt, y, fonte, cor, bg=None, pad=(40, 20), raio=36):
    x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=fonte); w = x1 - x0; x = (W - w) // 2
    if bg: d.rounded_rectangle((x - pad[0], y - pad[1], x + w + pad[0], y + (y1 - y0) + pad[1] + 8), raio, fill=bg)
    d.text((x - x0, y - y0), txt, font=fonte, fill=cor)

for i, p in enumerate(prods):
    img = Image.open(f"p{i}.bin").convert("RGB")
    fundo = Image.blend(ImageOps.fit(img, (W, H)).filter(ImageFilter.GaussianBlur(40)), Image.new("RGB", (W, H)), 0.55)
    d = ImageDraw.Draw(fundo)
    logo(fundo, 150, 30, 30)
    centro(d, "GRUPO VIP", 110, f(B, 64), (255, 255, 255), bg=LAR)
    card = ImageOps.contain(img, (820, 820)); cw, ch = card.size
    d.rounded_rectangle((110, 260, 970, 1120), 44, fill=(255, 255, 255))
    fundo.paste(card, (110 + (860 - cw) // 2, 260 + (860 - ch) // 2))
    if p.get("de"):
        centro(d, "de " + p["de"], 1480, f(R, 50), (210, 210, 210))
    centro(d, "por " + p["preco"], 1560, f(B, 104), AMA)
    if p.get("desc"):
        centro(d, p["desc"] + " OFF", 1720, f(B, 50), (255, 255, 255), bg=(220, 20, 60), pad=(28, 12), raio=22)
    fundo.save(f"s{i}.png")
    if i == 0: fundo.save("capa.jpg", quality=90)

# tela final
fundo = Image.new("RGB", (W, H), LAR); d = ImageDraw.Draw(fundo)
logo(fundo, 420, (W - 420) // 2, 150)
centro(d, "Grupo VIP de ofertas", 640, f(B, 72), AMA)
for j, t in enumerate(["Achadinhos com desconto", "todo dia no WhatsApp", "Nota alta e milhares de vendas", "Sem spam: só os admins postam"]):
    centro(d, t, 790 + j * 85, f(B, 50), (255, 255, 255))
centro(d, "ENTRA GRÁTIS", 1480, f(B, 96), LAR, bg=(255, 255, 255), pad=(50, 30), raio=48)
centro(d, "toque no botão abaixo", 1680, f(R, 50), (255, 255, 255))
fundo.save("final.png")
PYEOF
python3 artes.py

cat > legenda.py << 'PYEOF'
import json
p = json.load(open("palavras.json", encoding="utf-8"))
t = lambda s: "%d:%02d:%05.2f" % (s // 3600, (s % 3600) // 60, s % 60)
out = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: L,DejaVu Sans,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,60,60,560,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for i in range(0, len(p), 3):
    g = p[i:i + 3]; fim = p[i + 3]["start"] if i + 3 < len(p) else g[-1]["end"] + 0.4
    txt = " ".join("Shopee" + w["text"][4:] if w["text"].lower().startswith("xôpi") else w["text"] for w in g).upper()
    out.append("Dialogue: 0,%s,%s,L,,0,0,0,,%s" % (t(g[0]["start"]), t(fim), txt))
open("legenda.ass", "w", encoding="utf-8").write("\n".join(out) + "\n")
PYEOF
python3 legenda.py

# os produtos dividem o tempo da narracao; a tela final fica 3.5s
N=$(python3 -c "import json;print(len(json.load(open('produtos.json'))))")
python3 - << PYEOF
dur = float("$DUR"); n = int("$N"); fim = 3.5
por = max(1.8, (dur + 0.8 - fim) / n)
with open("lista.txt", "w") as f:
    for i in range(n): f.write(f"file 's{i}.png'\nduration {por:.3f}\n")
    f.write(f"file 'final.png'\nduration {fim}\nfile 'final.png'\n")
PYEOF
TOTAL=$(python3 -c "print(round($DUR + 0.8, 2))")
ffmpeg -y -f concat -safe 0 -i lista.txt -i narracao.mp3 \
  -filter_complex "[0:v]fps=30,format=yuv420p,ass=legenda.ass[v];[1:a]apad=pad_dur=3[a]" \
  -map "[v]" -map "[a]" -t "$TOTAL" -c:v libx264 -preset veryfast -crf 21 -c:a aac -b:a 128k -movflags +faststart video.mp4 -loglevel error
ls -la video.mp4 capa.jpg
