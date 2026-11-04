"""Data-driven Chinese D4 lesson. No LaTeX or network required.

Render from repository root with the existing Manim environment:
  cayley-thesis/manim-scenes/.venv/Scripts/python.exe -m manim -ql \
      cayley-thesis/manim-scenes/d4_pipeline.py D4Pipeline
"""
from pathlib import Path
import json
import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/week1-d4-demo"
DATA = json.loads((OUTPUT / "d4_lesson_data.json").read_text(encoding="utf-8"))
FONT = "Microsoft JhengHei"
INK = "#E9EDF5"
MUTED = "#9CACBF"
BG = "#101927"
ACCENT = "#F6BC60"
ROTATION = "#729EFF"
REFLECTION = "#5AD9BD"


def text(value, size=25, color=INK):
    return Text(value, font=FONT, font_size=size, color=color)


class D4Pipeline(Scene):
    def header(self, number, title, subtitle):
        self.clear()
        self.camera.background_color = BG
        self.add(text(f"0{number} / 06", 19, REFLECTION).move_to([-6.2, 3.52, 0]))
        self.add(text(title, 33).move_to([0, 2.98, 0]))
        self.add(text(subtitle, 19, MUTED).move_to([0, 2.45, 0]))
        self.add(Line([-6.6, 2.12, 0], [6.6, 2.12, 0], color="#34445B"))

    def footer(self, value):
        footer = text(value, 19, MUTED).move_to([0, -3.55, 0])
        if footer.width > 13:
            footer.scale_to_fit_width(13)
        self.add(footer)

    def graph(self):
        self.positions = {}
        for state, (rotation, flip) in enumerate(DATA["case"]["elements"]):
            radius = 1.08 if flip else 2.05
            corners = [(-radius, radius), (radius, radius), (radius, -radius), (-radius, -radius)]
            x, y = corners[rotation]
            self.positions[state] = np.array([-3.75 + x, -0.35 + y, 0.0])
        self.nodes = {}
        lines = VGroup()
        seen = set()
        for state, successors in enumerate(DATA["case"]["transitions"]):
            for move, following in enumerate(successors):
                pair = tuple(sorted((state, following)))
                if pair in seen:
                    continue
                seen.add(pair)
                lines.add(Line(self.positions[state], self.positions[following],
                               color=REFLECTION if move == 2 else ROTATION,
                               stroke_width=3).set_z_index(1))
        nodes = VGroup()
        labels = VGroup()
        for state, position in self.positions.items():
            node = Circle(radius=0.13, color=INK, fill_color=BG, fill_opacity=1).move_to(position).set_z_index(3)
            self.nodes[state] = node
            nodes.add(node)
            direction = position - np.array([-3.75, -0.35, 0])
            direction /= np.linalg.norm(direction)
            labels.add(text(DATA["state_names"][state], 20).move_to(position + direction * 0.37).set_z_index(4))
        self.add(lines, nodes, labels)
        self.add(text("藍：r 與 r^-1 的無向邊　綠：s", 16, MUTED).move_to([-3.75, -2.99, 0]))

    def panel(self, rows):
        items = VGroup(*(text(value, size, color) for value, size, color in rows))
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.27)
        if items.width > 6.5:
            items.scale_to_fit_width(6.5)
        items.move_to([3.0, -0.25, 0])
        self.play(FadeIn(items, shift=UP * 0.12), run_time=0.6)
        return items

    def walk(self, word, color=ACCENT, duration=0.6):
        state = DATA["case"]["identity"]
        marker = Dot(self.positions[state], radius=0.1, color=color).set_z_index(5)
        self.add(marker)
        segments = VGroup()
        for move in word:
            following = DATA["case"]["transitions"][state][move]
            segment = Line(self.positions[state], self.positions[following], color=color, stroke_width=7).set_z_index(2)
            self.play(Create(segment), marker.animate.move_to(self.positions[following]), run_time=duration)
            segments.add(segment)
            state = following
        self.wait(0.3)
        return VGroup(marker, segments)

    def snapshot(self, name):
        self.wait(0.2)
        (OUTPUT / "figures").mkdir(exist_ok=True)
        self.renderer.camera.get_image().save(OUTPUT / "figures" / f"{name}.png")

    def construct(self):
        self.header(1, "D4：先做一個能逐步檢查的實驗", "固定右乘 x → xs；每個基本操作成本為 1")
        self.graph()
        self.panel([
            ("D4 = {e, r, r², r³, s, rs, r²s, r³s}", 24, INK),
            ("r⁴ = e     s² = e     srs = r^-1", 27, ACCENT),
            ("生成元順序：r、r^-1、s", 24, INK),
            ("BFS 真值 → 關係 → 剪枝 → 獨立驗證", 23, REFLECTION),
            ("本例只選一條長度 4 的關係", 23, INK),
            ("一般組抽樣 seed = 0", 22, MUTED),
        ])
        self.footer("這是小群方法驗證；不是四階魔方結果，也沒有複雜度突破的主張。")
        self.snapshot("01-model")
        self.wait(5)

        self.header(2, "BFS 真值：一層一層走遍所有狀態", "距離層數 1、3、3、1；最遠狀態 r²s，距離為 3")
        self.graph()
        colors = [INK, REFLECTION, ACCENT, "#FF8C99"]
        layer_labels = []
        for depth in range(4):
            label = text(f"距離 {depth}：" + "、".join(DATA["layers"][str(depth)]), 25, colors[depth])
            label.move_to([3, 1.25 - depth * 0.75, 0])
            if label.width > 6.3:
                label.scale_to_fit_width(6.3)
            states = [int(k) for k, w in DATA["case"]["truth_paths"].items() if len(w) == depth]
            self.play(FadeIn(label), *(self.nodes[s].animate.set_fill(colors[depth], opacity=1) for s in states), run_time=0.7)
            layer_labels.append(label)
            self.wait(0.5)
        self.add(text("最短字：r²s = r · r · s", 28, ACCENT).move_to([3, -2.15, 0]))
        self.walk([0, 0, 2])
        self.footer("BFS 未使用貼面或改寫規則；獨立檢查路徑與每條邊的距離不等式。")
        self.snapshot("02-bfs")
        self.wait(4)

        self.header(3, "貼面關係：選一個四邊形面", "球面胞腔分解 V=8、E=12、F=6，因此 genus=0")
        self.graph()
        face = Polygon(*(self.positions[s] for s in [0, 2, 4, 6]), fill_color=ROTATION,
                       fill_opacity=0.15, stroke_width=0).set_z_index(0)
        self.add(face)
        self.panel([
            ("面邊界：r r r r = e", 29, ACCENT),
            ("切成兩段 → 相等操作字", 24, INK),
            ("r r r  →  r^-1", 31, REFLECTION),
            ("r^-1 r^-1  →  r r", 27, REFLECTION),
            ("先比長度，再比生成元字典序", 22, MUTED),
            ("每條規則都必須保留終點", 24, INK),
        ])
        self.walk([0, 0, 0, 0])
        self.footer("此圖是球面嵌入的平面示意；換貼面可以改 genus，但不會改原圖距離。")
        self.snapshot("03-face")
        self.wait(5)

        self.header(4, "一般短關係：同樣一條、同樣長度 4", "seed=0 抽到 rsrs=e；來源不同，但合法性檢查相同")
        self.graph()
        face = Polygon(*(self.positions[s] for s in [0, 2, 3, 1]), fill_color=REFLECTION,
                       fill_opacity=0.18, stroke_width=0).set_z_index(0)
        self.add(face)
        self.panel([
            ("一般組：r s r s = e", 29, ACCENT),
            ("例如：r s r  →  s", 30, REFLECTION),
            ("一般閉合字也可能恰是面邊界", 23, INK),
            ("本例兩組選到不同的關係", 23, INK),
            ("原始預算相同，展開規則數不同", 22, MUTED),
            ("一般組 13 條；貼面組 8 條", 24, INK),
        ])
        self.walk([0, 2, 0, 2])
        self.footer("三組都包含 r r^-1→e、r^-1 r→e、s s→e；比較的是額外關係。")
        self.snapshot("04-ordinary")
        self.wait(5)

        self.header(5, "反例：無法再改寫，不代表最短", "下面是各組規則的限制；不是群關係錯誤或剪枝不安全")
        self.graph()
        first = self.panel([
            ("只選 r⁴=e 的貼面組", 26, ROTATION),
            ("r s r：不可改寫，長度 3", 27, INK),
            ("BFS：同一終點 s，只需 1 步", 27, REFLECTION),
            ("缺少可處理這個字的關係", 23, MUTED),
        ])
        long_path = self.walk([0, 2, 0], "#FF8C99")
        self.snapshot("05-face-counterexample")
        self.wait(3)
        self.play(FadeOut(first), FadeOut(long_path))
        self.panel([
            ("只選 rsrs=e 的一般組", 26, REFLECTION),
            ("r r r：不可改寫，長度 3", 27, INK),
            ("BFS：同一終點 r^-1，只需 1 步", 26, ACCENT),
            ("兩組各自缺少另一種資訊", 23, MUTED),
        ])
        self.walk([0, 0, 0], "#FF8C99")
        self.footer("反例由程式搜尋並重播驗證；沒有找到反例，只代表指定長度內沒找到。")
        self.snapshot("05-ordinary-counterexample")
        self.wait(4)

        self.header(6, "為什麼目前沒有減少生成節點？", "完整重播證實：所有額外剪枝都發生在當輪深度界")
        rows = [["方法", "生成", "進入", "展開", "規則檢查"]]
        translations = {"cancellation_only": "只消去逆操作", "ordinary": "一般短關係", "faces": "貼面關係"}
        for m in DATA["metrics"]:
            rows.append([translations[m["method"]], str(m["generated"]), str(m["entered"]),
                         str(m["expanded"]), str(m["rule_checks"])])
        xs = [-4.7, -1.8, 0.15, 2.15, 4.65]
        for j, row in enumerate(rows):
            for i, value in enumerate(row):
                self.add(text(value, 25 if i else 23, ACCENT if j == 0 else INK).move_to([xs[i], 1.45 - j * 0.65, 0]))
        explanation = VGroup(
            text("在深度界，即使不剪枝，也不會再產生子節點。", 27, REFLECTION),
            text("因此進入節點略減，生成與展開節點仍相同。", 26),
            text("貼面組檢查少於一般組；兩者都多於只消去逆操作。", 24),
            text("結論限於本例、字母順序、預算與搜尋器；不是普遍否定。", 22, MUTED),
        ).arrange(DOWN, buff=0.25).move_to([0, -1.95, 0])
        self.play(FadeIn(explanation), run_time=0.7)
        self.footer("本週交付：BFS 證書＋合法規則＋搜尋 trace＋反例；三維主線仍依期中計畫。")
        self.snapshot("06-results")
        self.wait(8)
