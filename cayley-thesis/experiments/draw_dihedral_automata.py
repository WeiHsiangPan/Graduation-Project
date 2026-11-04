"""Optional Pillow report figure, reading only the latest verified run."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/dihedral-automata"
FONT = "C:/Windows/Fonts/msjh.ttc"
BG, CARD, INK, MUTED = "#101927", "#182436", "#E9EDF5", "#9CACBF"
GREEN, BLUE, GOLD, PINK = "#5AD9BD", "#729EFF", "#F6BC60", "#FF8C99"


def main():
    latest = json.loads((REPORT / "latest-run.json").read_text(encoding="utf-8"))
    run = Path(latest["run_directory"])
    report = json.loads((run / "results.json").read_text(encoding="utf-8"))
    width = 1600
    image = Image.new("RGB", (width, 1030), BG)
    draw = ImageDraw.Draw(image)
    def text(value, x, y, size=28, color=INK, anchor="mm"):
        draw.text((x,y), value, font=ImageFont.truetype(FONT,size), fill=color, anchor=anchor)
    text("D8／D16：有效的是少量好關係，還是面本身？",800,48,41)
    text("Dn 階數為 2n；生成元 r、r^-1、s；BFS 真值與 DFA 證書分開計算",800,107,27,MUTED)
    for column, group in enumerate(report["groups"]):
        left = 30 + column*785
        center = left+377
        n = group["n"]
        source = json.loads((run/report["sources"][str(n)]).read_text(encoding="utf-8"))
        by_id = {s["id"]:s for s in group["steps"]}
        face = by_id[group["sequences"]["face_prefix"]["tested_stage_ids"][-1]]
        generic = by_id[group["sequences"]["ordinary_shortlex_prefix"]["tested_stage_ids"][-1]]
        draw.rounded_rectangle((left,160,left+750,900),radius=20,fill=CARD,outline="#34445B",width=2)
        text(f"D{n}：{2*n} 個元素，BFS 直徑 {group['diameter']}",center,207,34,GOLD)
        rows = [("首次有限", "貼面排序", "一般最短優先"),
                ("原始關係數 K",str(face["budget"]),str(generic["budget"])),
                ("展開規則數",str(face["costs"]["expanded_rules"]),f"{generic['costs']['expanded_rules']:,}"),
                ("活 DFA 狀態",str(face["costs"]["live_dfa_states"]),str(generic["costs"]["live_dfa_states"])),
                ("上界 U",str(face["upper_bound"]),str(generic["upper_bound"])),
                ("差距 U - D",str(face["gap"]),str(generic["gap"]))]
        xs=[left+140,left+365,left+600]
        for j,row in enumerate(rows):
            for i,value in enumerate(row):
                text(value,xs[i],282+j*64,24 if j==0 else 28,GOLD if j==0 else GREEN if i==1 else INK)
        draw.line((left+35,650,left+715,650),fill="#34445B",width=2)
        text("但一般池真正最少也只需 2 條",center,692,30,PINK)
        counts=group["matched_pair_counts"]
        text(f"等長兩條配對：只有 {counts['finite']}/{counts['tested']} 組有限",center,754,29)
        text(f"唯一成功長關係：r^{n}=e",center,813,29,GREEN)
        text(f"成功接受字 {2*n} 個；最長 r^{n//2}s",center,866,25,MUTED)
    text("嚴格長度 <=6 的一般池在兩群都仍無限；不能拿它與含長度 8／16 面關係的策略直接比勝負。",800,946,25,MUTED)
    text("本例支持稀疏關係選擇與可驗證上界；未證明比 BFS 快，也未證明拓撲獨有優勢。",800,990,27,GOLD)
    output=REPORT/"comparison.png"
    image.save(output)
    print(output)


if __name__=="__main__":
    main()
