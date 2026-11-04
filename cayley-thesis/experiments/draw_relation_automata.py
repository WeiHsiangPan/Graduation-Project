"""Optional Pillow diagrams from saved DFA proofs. R denotes r^-1."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/d4-relation-automata"
BG, CARD, INK, MUTED = "#101927", "#182436", "#E9EDF5", "#9CACBF"
BLUE, GREEN, GOLD, PINK = "#729EFF", "#5AD9BD", "#F6BC60", "#FF8C99"
FONT = "C:/Windows/Fonts/msjh.ttc"


def main():
    latest = json.loads((REPORT / "latest-run.json").read_text(encoding="utf-8"))
    run = Path(latest["run_directory"])
    report = json.loads((run / "results.json").read_text(encoding="utf-8"))
    cases = {(c["budget"], c["method"]): c for c in report["cases"]}
    image = Image.new("RGB", (1600, 1050), BG)
    draw = ImageDraw.Draw(image)
    def text(value, point, size=25, color=INK, anchor="mm"):
        draw.text(point, value, font=ImageFont.truetype(FONT, size), fill=color, anchor=anchor)
    def curve(points, color=INK, width=4):
        if len(points) == 2:
            path = points
        else:
            a, b, c = points
            path = [((1-t)**2*a[0]+2*(1-t)*t*b[0]+t*t*c[0],
                     (1-t)**2*a[1]+2*(1-t)*t*b[1]+t*t*c[1]) for t in [i/40 for i in range(41)]]
        draw.line(path, fill=color, width=width)
        dx, dy = path[-1][0]-path[-2][0], path[-1][1]-path[-2][1]
        norm = math.hypot(dx, dy)
        ux, uy = dx/norm, dy/norm
        x, y = path[-1]
        draw.polygon([(x,y),(x-15*ux+7*uy,y-15*uy-7*ux),(x-15*ux-7*uy,y-15*uy+7*ux)], fill=color)
    def node(point, name, radius=29, color=GREEN):
        x, y = point
        draw.ellipse((x-radius,y-radius,x+radius,y+radius), fill=CARD, outline=color, width=3)
        draw.ellipse((x-radius+5,y-radius+5,x+radius-5,y+radius-5), outline=color, width=2)
        text(name, point, 23)
    text("D4：有限狀態機，不一定只接受有限多個字", (800, 48), 43)
    text("R = r^-1；eps = 空字；雙圈為接受狀態；記憶狀態不是群元素", (800, 105), 26, MUTED)
    specs = [("single_relation", "ordinary", "一條一般關係：rsrs=e"),
             ("single_relation", "faces", "一條貼面關係：rrrr=e"),
             ("full_budget", "faces", "兩條關係：rrrr、rsrs")]
    for column, (budget, method, title) in enumerate(specs):
        left = 20 + column * 530
        cx = left + 250
        item = cases[budget, method]
        draw.rounded_rectangle((left,155,left+510,920), radius=18, fill=CARD, outline="#34445B", width=2)
        text(title, (cx, 194), 26, GOLD)
        if column == 0:
            cert = item["language"]["certificate"]
            assert cert["prefix"] == [0] and cert["cycle"] == [0]
            curve([(cx,310),(cx,413)], BLUE)
            text("r", (cx+25,365), 25, BLUE)
            draw.arc((cx+5,398,cx+130,515), 210, 510, fill=PINK, width=4)
            curve([(cx+57,502),(cx+26,481)], PINK)
            text("r", (cx+132,453), 27, PINK)
            node((cx,280), "eps")
            node((cx,445), "r")
            text("可達接受狀態有自迴圈", (cx,580), 25, PINK)
            text("接受 r、rr、rrr、rrrr…", (cx,640), 25)
            text("無限語言", (cx,735), 33, PINK)
            text("r^4=e，但規則仍容許重複 r", (cx,805), 23, MUTED)
            text("本欄只畫循環證據", (cx,870), 22, MUTED)
        elif column == 1:
            cert = item["language"]["certificate"]
            assert cert["prefix"] == [0] and cert["cycle"] == [2,0]
            r, s = (left+140,445), (left+380,445)
            curve([(cx-15,310),(r[0]+8,410)], BLUE)
            text("r", (left+175,360), 25, BLUE)
            curve([(r[0]+25,423),(cx,355),(s[0]-25,423)], PINK)
            text("s", (cx,382), 26, PINK)
            curve([(s[0]-25,470),(cx,550),(r[0]+25,470)], PINK)
            text("r", (cx,520), 26, PINK)
            node((cx,280), "eps")
            node(r,"r")
            node(s,"s")
            text("前綴 r，再重複循環 sr", (cx,580), 25, PINK)
            text("接受 r(sr)^k，k=0,1,2…", (cx,640), 24)
            text("無限語言", (cx,735), 33, PINK)
            text("不是 D4 無限；是代表字重複", (cx,805), 23, MUTED)
            text("本欄只畫循環證據", (cx,870), 22, MUTED)
        else:
            dfa = item["dfa"]
            positions = {(): (cx,275), (0,):(left+130,390), (1,):(left+390,390),
                         (2,):(left+60,555), (0,0):(left+200,555),
                         (0,2):(left+250,700), (1,2):(left+420,700)}
            assert {tuple(w) for w in dfa["memory"] if w is not None} == set(positions)
            def trim(a,b):
                dx,dy=b[0]-a[0],b[1]-a[1]
                length=math.hypot(dx,dy)
                return (a[0]+31*dx/length,a[1]+31*dy/length),(b[0]-31*dx/length,b[1]-31*dy/length)
            for state in dfa["accepting"]:
                w=tuple(dfa["memory"][state])
                for symbol, target in enumerate(dfa["transitions"][state]):
                    if target==dfa["dead"]:
                        continue
                    v=tuple(dfa["memory"][target])
                    a,b=trim(positions[w],positions[v])
                    if w==(0,) and v==(0,2):
                        control=(left+55,610)
                        curve([a,control,b],GOLD)
                        text("s",(left+120,585),23,GOLD)
                    elif not w and v==(2,):
                        curve([a,(left+5,320),b],BLUE)
                        text("s",(left+75,385),23,BLUE)
                    else:
                        curve([a,b],BLUE)
                        text(["r","R","s"][symbol],((a[0]+b[0])/2+17,(a[1]+b[1])/2),23,BLUE)
            for word,point in positions.items():
                node(point,"".join(["r","R","s"][x] for x in word) or "eps",26)
            text("無活迴圈：最長接受字 rrs", (cx,775), 25, GREEN)
            text("8 個字；U=3=BFS 直徑", (cx,825), 25, GREEN)
            text("本欄畫全部活轉移", (cx,875), 22, MUTED)
    text("為閱讀省略拒絕狀態及指向它的轉移；完整表與 .dot 檔另存。拒絕狀態自迴圈不能證明語言無限。", (800,971),25,MUTED)
    output=REPORT/"automata-comparison.png"
    image.save(output)
    print(output)


if __name__ == "__main__":
    main()
