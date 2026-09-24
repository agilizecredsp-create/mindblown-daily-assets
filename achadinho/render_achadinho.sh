#!/bin/bash
set -e
# ============================================================
# Video vertical de achadinho (1080x1920, ~15-30s), 100% gratis:
#   foto do produto + preco/desconto na tela + narracao pt-BR (edge-tts)
#   + legenda sincronizada por palavra (3 palavras por vez).
# Variaveis: IMAGE_URL, NARRACAO, PRECO ("R$ 49,90"), PRECO_DE ("R$ 83,17" ou ""),
#            DESCONTO ("-40%" ou ""), SELO (texto do topo), CTA (texto do rodape)
# Saida: render_work/video.mp4 e render_work/capa.jpg
# ============================================================
WORKDIR="render_work"
rm -rf "$WORKDIR" && mkdir -p "$WORKDIR"
cd "$WORKDIR"

pip install edge-tts pillow --break-system-packages --quiet 2>/dev/null || pip install edge-tts pillow --quiet

echo "== Baixando foto do produto =="
ok=0
for i in 1 2 3 4 5 6; do
  if curl -sL --fail --max-time 30 -A "Mozilla/5.0" -o produto.bin "$IMAGE_URL" && [ -s produto.bin ]; then ok=1; break; fi
  echo "  tentativa $i falhou"; sleep 4
done
[ "$ok" = 1 ] || { echo "ERRO: nao baixou a imagem"; exit 1; }

echo "== Narracao (edge-tts, gratis) + tempos de cada palavra =="
cat > tts.py << 'PYEOF'
import asyncio, json, os, edge_tts
async def main():
    com = edge_tts.Communicate(os.environ["NARRACAO"], "pt-BR-FranciscaNeural", rate="+10%", boundary="WordBoundary")
    palavras = []
    with open("narracao.mp3", "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                palavras.append({"start": ch["offset"] / 1e7, "end": (ch["offset"] + ch["duration"]) / 1e7, "text": ch["text"]})
    json.dump(palavras, open("palavras.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(len(palavras), "palavras")
asyncio.run(main())
PYEOF
python3 tts.py
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 narracao.mp3)
TOTAL=$(python3 -c "print(round($DUR + 1.2, 2))")
echo "Narracao: ${DUR}s  Video: ${TOTAL}s"

echo "== Montando a arte (Pillow) =="
cat > arte.py << 'PYEOF'
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
W, H = 1080, 1920
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
LARANJA, AMARELO = (238, 77, 45), (255, 214, 0)

prod = Image.open("produto.bin").convert("RGB")
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
    return w, h

# selo do topo
centro(os.environ.get("SELO", "ACHADINHO DO DIA"), 130, f(B, 58), (255, 255, 255), pad=(44, 24), bg=LARANJA)

# card branco com a foto
card = ImageOps.contain(prod, (860, 860))
cw, ch = card.size
cx, cy = (W - 900) // 2, 290
d.rounded_rectangle((cx, cy, cx + 900, cy + 900), 48, fill=(255, 255, 255))
fundo.paste(card, (cx + (900 - cw) // 2, cy + (900 - ch) // 2))

# preco (a faixa 1230-1430 fica livre pra legenda)
y = 1470
de, desc = os.environ.get("PRECO_DE", ""), os.environ.get("DESCONTO", "")
if de:
    fde = f(R, 54)
    x0, y0, x1, y1 = d.textbbox((0, 0), "de " + de, font=fde)
    x = (W - (x1 - x0)) // 2
    d.text((x - x0, y - y0), "de " + de, font=fde, fill=(210, 210, 210))
    dx = d.textlength("de ", font=fde)
    d.line((x + dx, y + (y1 - y0) // 2 + 4, x + (x1 - x0), y + (y1 - y0) // 2 + 4), fill=(210, 210, 210), width=5)
    y += 80
centro("por " + os.environ["PRECO"], y, f(B, 112), AMARELO)
if desc:
    centro(desc + " OFF", y + 150, f(B, 50), (255, 255, 255), pad=(30, 14), bg=(220, 20, 60), raio=24)

centro(os.environ.get("CTA", "LINK NA BIO"), 1800, f(B, 50), (255, 255, 255))
fundo.save("arte.png")
fundo.save("capa.jpg", quality=90)
PYEOF
python3 arte.py

echo "== Legenda (.ass, 3 palavras por vez) =="
cat > legenda.py << 'PYEOF'
import json
p = json.load(open("palavras.json", encoding="utf-8"))
t = lambda s: "%d:%02d:%05.2f" % (s // 3600, (s % 3600) // 60, s % 60)
out = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: L,DejaVu Sans,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,60,60,560,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for i in range(0, len(p), 3):
    g = p[i:i + 3]
    fim = p[i + 3]["start"] if i + 3 < len(p) else g[-1]["end"] + 0.4
    out.append("Dialogue: 0,%s,%s,L,,0,0,0,,%s" % (t(g[0]["start"]), t(fim), " ".join(w["text"] for w in g).upper()))
open("legenda.ass", "w", encoding="utf-8").write("\n".join(out) + "\n")
PYEOF
python3 legenda.py

echo "== Renderizando =="
FRAMES=$(python3 -c "import math; print(math.ceil($TOTAL * 30))")
ffmpeg -y -i arte.png -i narracao.mp3   -filter_complex "[0:v]scale=1188:2112,zoompan=z='min(zoom+0.0005,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=1080x1920:fps=30,ass=legenda.ass[v];[1:a]apad=pad_dur=1.2[a]"   -map "[v]" -map "[a]" -t "$TOTAL" -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart video.mp4 -loglevel error
ls -la video.mp4 capa.jpg
