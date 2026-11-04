"""Optional Pillow teaching diagram; uses the saved, verified cases."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/week1-example7-six-choice"
FONT = Path("C:/Windows/Fonts/msjh.ttc")
BG, INK, MUTED = "#101927", "#E9EDF5", "#9CACBF"
BLUE, GREEN, GOLD, PINK, PURPLE = "#729EFF", "#5AD9BD", "#F6BC60", "#FF8C99", "#C4A5FA"


def main():
    latest = json.loads((REPORT / "latest-run.json").read_text(encoding="utf-8"))
    run = Path(latest["run_directory"])
    cases = {name: json.loads((run / "cases" / f"{name}.json").read_text(encoding="utf-8")) for name in ("321", "123")}
    image = Image.new("RGB", (1500, 1010), BG)
    draw = ImageDraw.Draw(image)
    def text(value, x, y, size=28, color=INK, anchor=None):
        draw.text((x, y), value, font=ImageFont.truetype(str(FONT), size), fill=color, anchor=anchor)
    text("321 與 123：相同 χ，為什麼判定不同？", 750, 32, 42, anchor="mt")
    text("共同起點：t0:012 <-> t1:012；每欄皆是頂點 2 的兩片 link 三角形", 750, 94, 26, MUTED, "mt")
    for column, name in enumerate(("321", "123")):
        offset = 35 + column * 745
        case = cases[name]
        apex = next(link for link in case["after"]["links"] if [0, 2] in link["members"])
        color = GREEN if name == "321" else PINK
        draw.rounded_rectangle((offset, 153, offset + 685, 885), radius=20, fill="#182436", outline="#34445B", width=2)
        text(f"023 <-> {name}", offset + 342, 180, 37, color, "mt")
        text("紫、黃分別形成兩個圈" if name == "321" else "紫、黃接續成同一個圈", offset + 342, 244, 24, MUTED, "mt")
        x0, x1, y0, y1 = offset + 90, offset + 590, 315, 535
        A, C, D, B = (x0, y1), (x1, y0), (x0, y0), (x1, y1)
        draw.polygon([A, C, D], fill="#283C60")
        draw.polygon([A, C, B], fill="#254D4A")
        draw.line([A, C], fill=MUTED, width=4)
        draw.line([D, C], fill=PURPLE, width=6)
        draw.line([A, B], fill=GOLD, width=6)
        def arrow(x, upward):
            start, end = ((x, y1), (x, y0)) if upward else ((x, y0), (x, y1))
            draw.line([start, end], fill=PINK, width=6)
            dy = 1 if upward else -1
            draw.polygon([end, (x - 11, end[1] + 19 * dy), (x + 11, end[1] + 19 * dy)], fill=PINK)
        arrow(x0, True)
        arrow(x1, name == "321")
        for value, x, y in [("t0 朝3", x0, y0 - 40), ("t1 朝1", x1, y0 - 40),
                            ("t0 朝0", x0, y1 + 14), ("t1 朝3", x1, y1 + 14)]:
            text(value, x, y, 24, INK, "mt")
        text("t0:2", offset + 225, 365, 28, BLUE)
        text("t1:2", offset + 430, 455, 28, GREEN)
        text("左右同向識別：0→3、3→1" if name == "321" else "左右反向識別：0→1、3→3", offset + 342, 605, 29, color, "mt")
        text(f"V={apex['V']}　E={apex['E']}　F={apex['F']}　χ={apex['chi']}", offset + 342, 665, 28, INK, "mt")
        text(f"邊界圈 b={apex['boundary_components']}；" + ("可定向" if apex["orientable"] else "非可定向"), offset + 342, 710, 30, color, "mt")
        text("環帶：通過 partial" if name == "321" else "莫比烏斯帶：拒絕 partial", offset + 342, 763, 32, color, "mt")
        signs = [eq["target_sign_over_source"] for eq in case["apex_orientation_trace"]["equations"]]
        text(f"兩次貼邊要求 t1 方向：{signs[0]:+d}、{signs[1]:+d}", offset + 342, 822, 25, MUTED, "mt")
    text("此處 123 是 t0:023 <-> t1:123，不是原文照字面的 t1 自貼版本。", 750, 921, 25, MUTED, "mt")
    text("圖由已保存結果產生；判定另檢查曲面局部條件、原邊方向與完整 links。", 750, 959, 24, MUTED, "mt")
    output = REPORT / "comparison321-123.png"
    image.save(output)
    print(output)


if __name__ == "__main__":
    main()
