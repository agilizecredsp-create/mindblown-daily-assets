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
import asyncio, json, os, re, edge_tts
# a voz pronuncia "Shopee" errado (Chopei/Shopping); "Xôpi" foi a grafia aprovada pela Leydiane (24/09).
# A legenda volta pra "Shopee" no legenda.py.
TEXTO = re.sub(r"(?i)\bshopee\b", "Xôpi", os.environ["NARRACAO"])
async def main():
    com = edge_tts.Communicate(TEXTO, os.environ.get("VOZ") or "pt-BR-ThalitaMultilingualNeural", rate=os.environ.get("VELOCIDADE") or "+10%", boundary="WordBoundary")
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
if [ -n "${AUDIO_URL:-}" ]; then
  # narracao pronta (OpenAI TTS gerada no n8n): baixa e tira os tempos das palavras com faster-whisper
  echo "== Usando narracao pronta + faster-whisper pra legenda =="
  curl -sL --fail --retry 5 --retry-delay 4 -o narracao.mp3 "$AUDIO_URL"
  pip install faster-whisper --break-system-packages --quiet 2>/dev/null || pip install faster-whisper --quiet
  cat > whisper.py << 'PYEOF'
import json
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
seg, _ = m.transcribe("narracao.mp3", word_timestamps=True, language="pt")
p = [{"start": w.start, "end": w.end, "text": w.word.strip()} for s in seg for w in s.words if w.word.strip()]
json.dump(p, open("palavras.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(p), "palavras")
PYEOF
  python3 whisper.py
else
  python3 tts.py
fi
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

# logo do Achei Barato! no canto (28/09)
try:
    lg = Image.open("../achadinho/logo.png").convert("RGBA").resize((150, 150))
    m = Image.new("L", (150, 150), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 150, 150), 32, fill=255)
    fundo.paste(lg, (30, 30), m)
except Exception as e:
    print("sem logo:", e)

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
       "Style: L,DejaVu Sans,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,60,60,560,1",
       "Style: H,DejaVu Sans,118,&H0000D6FF,&H0000D6FF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,3,10,0,5,50,50,0,1", "",
       "Style: G,DejaVu Sans,72,&H00FFFFFF,&H00FFFFFF,&H0059AA1F,&H0059AA1F,1,0,0,0,100,100,0,0,3,26,0,5,40,40,0,1",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
# 29/09: gancho gigante (amarelo, caixa escura) nos 1,8s iniciais pra segurar o scroll
import os
if os.environ.get("GANCHO"):
    out.append("Dialogue: 1,0:00:00.00,0:00:01.80,H,,0,0,0,,{\\fad(0,200)}" + os.environ["GANCHO"])
for i in range(0, len(p), 3):
    g = p[i:i + 3]
    fim = p[i + 3]["start"] if i + 3 < len(p) else g[-1]["end"] + 0.4
    out.append("Dialogue: 0,%s,%s,L,,0,0,0,,%s" % (t(g[0]["start"]), t(fim), " ".join("Shopee" + w["text"][4:] if w["text"].lower().startswith("xôpi") else w["text"] for w in g).upper()))
# 30/09: faixa verde do Grupo VIP nos ultimos 2,2s (o link em si fica no perfil: texto no video nao e clicavel)
if p:
    fim_total = p[-1]["end"] + 1.2
    out.append("Dialogue: 2,%s,%s,G,,0,0,0,,{\\fad(150,0)}GRUPO VIP NO WHATSAPP\\NOFERTAS TODO DIA\\NLINK NO PERFIL" % (t(max(0, fim_total - 2.2)), t(fim_total)))
open("legenda.ass", "w", encoding="utf-8").write("\n".join(out) + "\n")
PYEOF
python3 legenda.py

echo "== Renderizando =="
if [ "${ESTILO:-}" = "top3" ]; then
  # 30/09: "Top 3 do dia" — 3 artes (#3, #2, #1) trocando quando a narracao fala "Numero ..."
  cp ../achadinho/top3.py . && python3 top3.py
  cat > cortes.py << 'PYEOF'
import json, re, sys
p = json.load(open("palavras.json", encoding="utf-8")); total = float(sys.argv[1])
ks = [w["start"] for w in p if re.sub(r"[^a-zú]", "", w["text"].lower()) in ("número", "numero")][:3]
if len(ks) < 3: ks = [0, total / 3, 2 * total / 3]
print(round(ks[1], 2), round(ks[2] - ks[1], 2), round(total - ks[2], 2))
PYEOF
  read D1 D2 D3 < <(python3 cortes.py "$TOTAL")
  echo "Cortes: $D1 / $D2 / $D3"
  F1=$(python3 -c "import math; print(math.ceil($D1 * 30))"); F2=$(python3 -c "import math; print(math.ceil($D2 * 30))"); F3=$(python3 -c "import math; print(math.ceil($D3 * 30))")
  Z="zoompan=z='min(1+on*0.0009,1.07)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
  ffmpeg -y -i seg1.png -i seg2.png -i seg3.png -i narracao.mp3 -filter_complex "[0:v]scale=1188:2112,$Z:d=$F1,trim=duration=$D1[a];[1:v]scale=1188:2112,$Z:d=$F2,trim=duration=$D2[b];[2:v]scale=1188:2112,$Z:d=$F3,trim=duration=$D3[c];[a][b][c]concat=n=3:v=1:a=0,format=yuv420p,ass=legenda.ass[v];[3:a]apad=pad_dur=1.2[au]" -map "[v]" -map "[au]" -t "$TOTAL" -c:v libx264 -preset veryfast -crf 21 -c:a aac -b:a 128k -movflags +faststart video.mp4 -loglevel error
elif [ "${ESTILO:-}" = "animado" ] || [ "${ESTILO:-}" = "adivinha" ]; then
  # 29/09: estilo animado — produto recortado (rembg) flutuando sobre fundo em movimento + preco pulando
  # 30/09: "adivinha" = mesmo visual, mas o preco fica escondido ("QUANTO CUSTA?") ate a narracao dizer "E o preco? ..."
  if [ "${ESTILO}" = "adivinha" ]; then
    cat > revela.py << 'PYEOF'
import json, re, sys
p = json.load(open("palavras.json", encoding="utf-8"))
ks = [k for k, w in enumerate(p) if re.sub(r"[^a-zçã]", "", w["text"].lower()) in ("preço", "preco")]
k = ks[-1] if ks else -1
print(round(p[k + 1]["start"], 2) if 0 <= k < len(p) - 1 else round(float(sys.argv[1]) * 0.7, 2))
PYEOF
    export REVELA=$(python3 revela.py "$DUR")
    echo "Preco revelado em ${REVELA}s"
  fi
  pip install "rembg[cpu]" --break-system-packages --quiet 2>/dev/null || pip install "rembg[cpu]" --quiet
  cp ../achadinho/anima.py . 2>/dev/null || true
  python3 anima.py "$TOTAL" | ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i narracao.mp3 -filter_complex "[0:v]format=yuv420p,ass=legenda.ass[v];[1:a]apad=pad_dur=1.2[a]" -map "[v]" -map "[a]" -t "$TOTAL" -c:v libx264 -preset veryfast -crf 21 -c:a aac -b:a 128k -movflags +faststart video.mp4 -loglevel error
else
FRAMES=$(python3 -c "import math; print(math.ceil($TOTAL * 30))")
ffmpeg -y -i arte.png -i narracao.mp3   -filter_complex "[0:v]scale=1188:2112,zoompan=z='if(lt(on,45),1+on*0.0012,min(1.054+(on-45)*0.00015,1.08))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=1080x1920:fps=30,ass=legenda.ass[v];[1:a]apad=pad_dur=1.2[a]"   -map "[v]" -map "[a]" -t "$TOTAL" -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart video.mp4 -loglevel error
fi

# 30/09: trilha de fundo sem direitos autorais (Mixkit Free License), baixinha por baixo da voz e subindo na tela final
if [ -n "${MUSICA_URL:-}" ] && curl -sL --fail --retry 3 --max-time 60 -o musica.mp3 "$MUSICA_URL" && [ -s musica.mp3 ]; then
  FIM=$(python3 -c "print(round($TOTAL - 2.2, 2))"); SAI=$(python3 -c "print(round($TOTAL - 0.8, 2))")
  if ffmpeg -y -i video.mp4 -stream_loop -1 -ss 2 -i musica.mp3 -filter_complex "[1:a]volume='if(gt(t,$FIM),0.32,0.13)':eval=frame,afade=t=in:d=0.4,afade=t=out:st=$SAI:d=0.8[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 128k -t "$TOTAL" -movflags +faststart com_musica.mp4 -loglevel error; then
    mv com_musica.mp4 video.mp4; echo "Musica de fundo aplicada"
  else
    echo "AVISO: musica falhou, segue sem"
  fi
fi
ls -la video.mp4 capa.jpg
