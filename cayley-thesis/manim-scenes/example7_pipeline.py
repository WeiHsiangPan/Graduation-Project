"""Example 7: data-driven gluing and vertex-link lesson, no LaTeX required."""
from pathlib import Path
import json
import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/week1-example7-demo"
DATA = json.loads((OUTPUT / "example7_data.json").read_text(encoding="utf-8"))
FONT = "Microsoft JhengHei"
BG, INK, MUTED = "#101927", "#E9EDF5", "#9CACBF"
BLUE, GREEN, GOLD = "#729EFF", "#5AD9BD", "#F6BC60"
PINK, PURPLE = "#FF8C99", "#C4A5FA"


def txt(value, size=25, color=INK):
    return Text(value, font=FONT, font_size=size, color=color)


class Example7Pipeline(Scene):
    def header(self, chapter, title, subtitle):
        self.clear()
        self.camera.background_color = BG
        self.add(txt(f"0{chapter} / 09", 19, GREEN).move_to([-6.15, 3.52, 0]))
        title_m = txt(title, 32)
        if title_m.width > 12.7:
            title_m.scale_to_fit_width(12.7)
        self.add(title_m.move_to([0, 2.98, 0]))
        subtitle_m = txt(subtitle, 20, MUTED)
        if subtitle_m.width > 13:
            subtitle_m.scale_to_fit_width(13)
        self.add(subtitle_m.move_to([0, 2.43, 0]))
        self.add(Line([-6.6, 2.1, 0], [6.6, 2.1, 0], color="#34445B"))

    def footer(self, value):
        item = txt(value, 19, MUTED)
        if item.width > 13:
            item.scale_to_fit_width(13)
        self.add(item.move_to([0, -3.53, 0]))

    def tetrahedron(self, center, name, color=BLUE, scale=1):
        origin = np.array([*center, 0.0])
        coords = [(-1.25, -1), (1.25, -1), (0, 1.25), (0.45, -0.15)]
        points = {i: origin + np.array([x, y, 0.0]) * scale for i, (x, y) in enumerate(coords)}
        edges = VGroup()
        for a in range(4):
            for b in range(a + 1, 4):
                line = DashedLine(points[a], points[b], color=color, stroke_width=2) if 3 in (a, b) else Line(points[a], points[b], color=color, stroke_width=3)
                edges.add(line.set_z_index(1))
        dots = {i: Dot(p, radius=0.075, color=INK).set_z_index(3) for i, p in points.items()}
        labels = VGroup()
        offsets = [LEFT * 0.22 + DOWN * 0.22, RIGHT * 0.22 + DOWN * 0.22, UP * 0.23, RIGHT * 0.25]
        for i, p in points.items():
            labels.add(txt(str(i), 23).move_to(p + offsets[i]).set_z_index(4))
        name_position = origin + np.array([-1.1 * scale, 1.6 * scale, 0])
        name_position[1] = min(name_position[1], 1.8)
        group = VGroup(edges, VGroup(*dots.values()), labels,
                       txt(name, 25, color).move_to(name_position))
        self.add(group)
        return group, points, dots

    def face(self, points, indices, color):
        return Polygon(*(points[i] for i in indices), fill_color=color, fill_opacity=0.24,
                       stroke_color=color, stroke_width=3).set_z_index(0)

    def note(self, rows, center=(0, -2.3), size=23):
        group = VGroup(*(txt(line, size, color) for line, color in rows)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        if group.width > 12.6:
            group.scale_to_fit_width(12.6)
        group.move_to([*center, 0])
        self.play(FadeIn(group), run_time=0.5)
        return group

    def snapshot(self, name):
        self.wait(0.2)
        (OUTPUT / "figures").mkdir(exist_ok=True)
        self.renderer.camera.get_image().save(OUTPUT / "figures" / f"{name}.png")

    def construct(self):
        self.header(1, "Example 7：兩個四面體，先分清兩份輸入", "Burton–Pettersson v2；教學採與表格一致的推定版，並保存原文照字面版")
        self.tetrahedron((-3.3, 0.1), "t0", BLUE)
        self.tetrahedron((3.3, 0.1), "t1", GREEN)
        self.note([
            ("第一次：t0:012 ↔ t1:012（兩版本相同）", INK),
            ("原文第二次：t1:023 ↔ t1:321", PINK),
            ("本次推定版：t0:023 ↔ t1:321", GOLD),
        ], center=(0, -2.2))
        self.footer("推定版能重現原文 Ce、Cv；不是作者官方勘誤。透視線只是抽象四面體示意。")
        self.snapshot("01-inputs")
        self.wait(5)

        self.header(2, "第一次貼合：012 ↔ 012", "逐個識別 0↔0、1↔1、2↔2；3 與 3 尚未識別")
        _, p0, d0 = self.tetrahedron((-3.3, 0.2), "t0", BLUE)
        _, p1, d1 = self.tetrahedron((3.3, 0.2), "t1", GREEN)
        self.play(FadeIn(self.face(p0, [0, 1, 2], BLUE)), FadeIn(self.face(p1, [0, 1, 2], GREEN)), run_time=0.7)
        for vertex, color in [(0, GOLD), (1, PURPLE), (2, PINK)]:
            self.play(d0[vertex].animate.set_color(color), d1[vertex].animate.set_color(color), run_time=0.4)
        self.note([
            ("{t0:0,t1:0}   {t0:1,t1:1}   {t0:2,t1:2}", INK),
            ("{t0:3}   {t1:3}     → 共 5 個頂點類", GOLD),
            ("8 個邊界面 → 6 個；每個頂點 link 仍是圓盤", GREEN),
        ], center=(0, -2.15))
        self.footer("貼合要求指定三個頂點的對應；只說兩面相貼，不足以決定結果。")
        self.snapshot("02-first-glue")
        self.wait(5)

        self.header(3, "第二次貼合：t0:023 ↔ t1:321", "對應為 t0:0↔t1:3、t0:2↔t1:2、t0:3↔t1:1")
        _, p0, d0 = self.tetrahedron((-3.3, 0.2), "t0", BLUE)
        _, p1, d1 = self.tetrahedron((3.3, 0.2), "t1", GREEN)
        self.play(FadeIn(self.face(p0, [0, 2, 3], GOLD)), FadeIn(self.face(p1, [3, 2, 1], GOLD)), run_time=0.7)
        classes = DATA["inferred_stages"][-1]["vertex_classes"]
        for members, color in zip(classes, [GOLD, PURPLE, PINK]):
            self.play(*( (d0 if t == 0 else d1)[v].animate.set_color(color) for t, v in members), run_time=0.5)
        self.note([
            ("A = {t0:0, t1:0, t1:3}", GOLD),
            ("B = {t0:1, t0:3, t1:1}", PURPLE),
            ("C = {t0:2, t1:2}   ← 要檢查的夾點", PINK),
        ], center=(0, -2.1))
        self.footer("等價類由兩次對應取傳遞閉包得到；共有 3 類、4 個尚未貼合的邊界面。")
        self.snapshot("03-vertex-classes")
        self.wait(6)

        self.header(4, "Link 是什麼？在頂點 2 附近切一個小角", "每個四面體角提供一片三角形；不是原四面體的整個面")
        _, p, _ = self.tetrahedron((-3.7, -0.1), "t0", BLUE, scale=1.25)
        cut_points = {w: p[2] + 0.28 * (p[w] - p[2]) for w in (0, 1, 3)}
        cut = Polygon(*(cut_points[w] for w in (0, 1, 3)), fill_color=PINK, fill_opacity=0.7, color=PINK).set_z_index(5)
        self.play(FadeIn(cut), run_time=0.6)
        q = {0: np.array([1.0, -1.25, 0]), 1: np.array([5.6, -1.25, 0]), 3: np.array([3.3, 1.1, 0])}
        enlarged = Polygon(q[0], q[1], q[3], fill_color=PINK, fill_opacity=0.15, color=PINK)
        self.play(TransformFromCopy(cut, enlarged), run_time=1.0)
        for w, offset in [(0, DOWN * 0.3), (1, DOWN * 0.3), (3, UP * 0.3)]:
            self.add(txt(f"朝 {w}", 22, PINK).move_to(q[w] + offset))
        self.add(txt("L(t0:2)", 27, PINK).move_to([3.3, -2.05, 0]))
        self.note([("三個角對應原邊 20、21、23；三條小邊對應包含頂點 2 的三個面。", INK)], center=(0, -2.85), size=22)
        self.footer("放大並攤平是組合示意；真正判定由小三角形的邊與角識別計算。")
        self.snapshot("04-link-triangle")
        self.wait(6)

        self.header(5, "頂點類 C 有兩片三角形：先貼共同的 01 小邊", "第一次面貼合 012↔012，在兩個頂點 2 的 links 中誘導 01↔01")
        left = {0: np.array([-6.0, -1.3, 0]), 1: np.array([-2.0, 1.1, 0]), 3: np.array([-6.0, 1.1, 0])}
        right = {0: np.array([1.9, -1.3, 0]), 1: np.array([5.9, 1.1, 0]), 3: np.array([5.9, -1.3, 0])}
        triangle0 = Polygon(left[0], left[1], left[3], color=BLUE, fill_color=BLUE, fill_opacity=0.25)
        triangle1 = Polygon(right[0], right[1], right[3], color=GREEN, fill_color=GREEN, fill_opacity=0.25)
        labels = VGroup()
        name_labels = []
        for coords, name, color in [(left, "t0:2", BLUE), (right, "t1:2", GREEN)]:
            name_label = txt(name, 25, color).move_to([(coords[0][0] + coords[1][0]) / 2, -1.85, 0])
            name_labels.append(name_label)
            self.add(name_label)
            for w in (0, 1, 3):
                labels.add(txt(str(w), 22).move_to(coords[w] + DOWN * 0.26))
        self.add(triangle0, triangle1, labels)
        diagonal0 = Line(left[0], left[1], color=GOLD, stroke_width=7)
        diagonal1 = Line(right[0], right[1], color=GOLD, stroke_width=7)
        self.play(Create(diagonal0), Create(diagonal1), run_time=0.8)
        self.wait(1.8)
        self.play(FadeOut(labels), FadeOut(diagonal0), FadeOut(diagonal1), run_time=0.4)
        A, C, D, B = (np.array(v) for v in [(-2.7, -1.3, 0), (2.7, 1.1, 0), (-2.7, 1.1, 0), (2.7, -1.3, 0)])
        self.play(Transform(triangle0, Polygon(A, C, D, color=BLUE, fill_color=BLUE, fill_opacity=0.25)),
                  Transform(triangle1, Polygon(A, C, B, color=GREEN, fill_color=GREEN, fill_opacity=0.25)),
                  name_labels[0].animate.move_to([-1.3, 0.4, 0]),
                  name_labels[1].animate.move_to([1.3, -0.6, 0]), run_time=1.3)
        self.add(Line(A, C, color=GOLD, stroke_width=5))
        self.add(txt("先貼對角線，得到一個四邊形圓盤", 26).move_to([0, -2.65, 0]))
        self.footer("這個四邊形是兩片 link 三角形的展開圖；還沒進行第二次邊識別。")
        self.snapshot("05-two-triangles")
        self.wait(5)

        self.header(6, "第二次貼合把左邊 03 識別到右邊 31", "0→3、3→1：上下端分別對應，不扭轉；頂點 2 對應自身的類")
        A, C, D, B = (np.array(v) for v in [(-6.1, -1.3, 0), (-1.4, 1.1, 0), (-6.1, 1.1, 0), (-1.4, -1.3, 0)])
        self.add(Polygon(A, C, D, color=BLUE, fill_color=BLUE, fill_opacity=0.2),
                 Polygon(A, C, B, color=GREEN, fill_color=GREEN, fill_opacity=0.2))
        self.add(Line(D, C, color=PURPLE, stroke_width=6), Line(A, B, color=GOLD, stroke_width=6))
        self.play(GrowArrow(Arrow(A, D, buff=0.03, color=PINK, stroke_width=6)),
                  GrowArrow(Arrow(B, C, buff=0.03, color=PINK, stroke_width=6)), run_time=0.8)
        for position, label in [(A, "t0:0"), (D, "t0:3"), (B, "t1:3"), (C, "t1:1")]:
            self.add(txt(label, 18).move_to(position + (DOWN * 0.35 if position[1] < 0 else UP * 0.35)))
        self.add(txt("t0:2", 23, BLUE).move_to([-4.7, 0.3, 0]), txt("t1:2", 23, GREEN).move_to([-2.8, -0.6, 0]))
        ring = Annulus(inner_radius=0.77, outer_radius=1.55, color=INK, fill_color=BLUE, fill_opacity=0.25).move_to([3.7, -0.1, 0])
        self.play(FadeIn(ring), GrowArrow(Arrow([-0.75, -0.1, 0], [1.45, -0.1, 0], color=INK)), run_time=0.8)
        self.add(Circle(radius=1.55, color=PURPLE, stroke_width=6).move_to([3.7, -0.1, 0]),
                 Circle(radius=0.77, color=GOLD, stroke_width=6).move_to([3.7, -0.1, 0]))
        self.add(txt("環帶同胚型示意", 24).move_to([3.7, -2.2, 0]))
        self.note([("紫、黃兩條邊分別閉合成兩個邊界圈；它們沒有互相貼在一起。", INK)], center=(0, -2.85), size=22)
        self.footer("環帶 = S¹×[0,1]；不是環面。右圖呈現已由組合驗證確定的同胚型。")
        self.snapshot("06-annulus")
        self.wait(7)

        self.header(7, "計算所有 links：不能只看 Euler characteristic", "先驗證曲面局部條件、連通、可定向與邊界圈，再使用曲面分類")
        rows = [["頂點類", "V", "E", "F", "χ", "邊界圈", "類型"]]
        for letter, link in zip("ABC", DATA["inferred_stages"][-1]["links"]):
            rows.append([letter, str(link["V"]), str(link["E"]), str(link["F"]), str(link["chi"]),
                         str(link["boundary_components"]), "環帶" if link["type"] == "annulus" else "圓盤"])
        xs = [-5.1, -3.3, -1.8, -0.3, 1.2, 3.2, 5.25]
        for j, row in enumerate(rows):
            for i, value in enumerate(row):
                self.add(txt(value, 26, GOLD if j == 0 else INK).move_to([xs[i], 1.35 - j * 0.65, 0]))
        self.note([
            ("C：2 個角類 − 4 個小邊類 + 2 片三角形 = 0", PINK),
            ("可定向、連通、b=2：χ = 2 − 2g − b ⇒ g=0", GREEN),
            ("A、B：χ=1、b=1，均為圓盤", INK),
        ], center=(0, -2.0), size=25)
        self.footer("局部檢查還包括：每個 link 頂點的小鄰域為 interval 或 circle；不是只比 V−E+F。")
        self.snapshot("07-link-table")
        self.wait(7)

        self.header(8, "Partial-3-manifold 不等於真正的三維流形", "推定版符合論文 Definition 5；但環帶 link 讓夾點不是流形頂點")
        for x, kind, color in [(-4.7, "圓盤", GREEN), (0, "球面", BLUE), (4.7, "環帶", PINK)]:
            if kind == "圓盤":
                shape = Circle(radius=0.85, color=color, fill_color=color, fill_opacity=0.25)
            elif kind == "球面":
                shape = VGroup(Circle(radius=0.85, color=color), Ellipse(width=1.7, height=0.45, color=color))
            else:
                shape = Annulus(inner_radius=0.4, outer_radius=0.85, color=color, fill_color=color, fill_opacity=0.25)
            self.add(shape.move_to([x, 0.6, 0]), txt(kind, 27, color).move_to([x, -0.65, 0]))
        self.add(txt("邊界頂點可有", 23, GREEN).move_to([-4.7, -1.25, 0]),
                 txt("內部頂點可有", 23, BLUE).move_to([0, -1.25, 0]),
                 txt("本例：不符合", 23, PINK).move_to([4.7, -1.25, 0]))
        self.note([
            ("原文照字面版：頂點 2 的 link 是莫比烏斯帶，χ=0、b=1、非可定向。", GOLD),
            ("與推定版的環帶同為 χ=0，卻不是同一曲面；也不符合原文 Ce/Cv。", INK),
        ], center=(0, -2.5), size=22)
        self.footer("此處是三維分片線性三角剖分的頂點 link 判準；另已檢查邊不會反向自我識別。")
        self.snapshot("08-manifold-test")
        self.wait(8)

        self.header(9, "與 D4 的共同 pipeline：主張必須配對證據", "兩個例子都把『看起來合理』拆成輸入、局部檢查、摘要與反例")
        rows = [
            ("D4", "Example 7"),
            ("群、生成元、貼面", "四面體、面上頂點對應"),
            ("BFS 真值、最短路徑證書", "等價類、完整 link 重建"),
            ("不可改寫 ≠ 最短", "χ=0 ≠ 環帶；partial ≠ 流形"),
            ("重播搜尋＋獨立檢查", "圖閉包＋另一套程式交叉核對"),
        ]
        for j, (left, right) in enumerate(rows):
            self.add(txt(left, 27 if j == 0 else 23, GREEN if j == 0 else INK).move_to([-3.35, 1.45 - j * 0.65, 0]),
                     txt(right, 27 if j == 0 else 23, GOLD if j == 0 else INK).move_to([3.35, 1.45 - j * 0.65, 0]))
        self.note([
            ("Ce：六筆邊界邊配對；Cv：三個邊界頂點類。", GREEN),
            ("本週可報告：兩個輸入版本、三個 links、完整手算與可重現動畫。", INK),
            ("尚未完成：一般樹分解 DP、三維同胚分類、Lean 形式化。", MUTED),
        ], center=(0, -2.25), size=22)
        self.footer("原始資料、8 項測試、4 階段交叉驗證與操作命令隨講義交付。")
        self.snapshot("09-pipeline")
        self.wait(8)
