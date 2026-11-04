"""Optional Pillow overview of the verified 36-case census."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/one-tetrahedron-36'


def draw(run, output):
    data = json.loads((run / 'results.json').read_text(encoding='utf-8'))
    verified = json.loads((run / 'independent-verification.json').read_text(encoding='utf-8'))
    if verified['status'] != 'PASS':
        raise ValueError('Only draw a verified run')
    canvas = Image.new('RGB',(1440,1150),'#101927')
    pen = ImageDraw.Draw(canvas)
    font_path = 'C:/Windows/Fonts/msjh.ttc'
    def text(message, xy, size=24, fill='#E9EDF5'):
        pen.text(xy,message,font=ImageFont.truetype(font_path,size),fill=fill)
    text('單四面體：36 種完整貼合', (46,28),42)
    text('固定 012 -> perm(013)，023 -> perm(123)；保留全部標記案例', (48,92),25,'#AABBD0')
    text('9 案通過 / 27 案拒絕；通過者 H0=H3=Z，H2=0', (48,133),25)
    rows = sorted({c['case_id'].split('-')[0] for c in data['cases']})
    columns = sorted({c['case_id'].split('-')[1] for c in data['cases']})
    cells = {c['case_id']:c for c in data['cases']}
    left, top, cw, ch = 205,242,192,104
    text('第二次目標', (1030,170),23,'#AABBD0')
    for j,label in enumerate(columns):
        text(label,(left+j*cw+66,203),28)
    for i,label in enumerate(rows):
        text(label,(75,top+i*ch+26),29)
        for j,column in enumerate(columns):
            case = cells[label+'-'+column]
            d = case['decision']
            if d['accepted']:
                h = case['homology']['groups']['H1']['label']
                color = {'0':'#164F40','Z/4':'#244A77','Z/5':'#665327'}[h]
                title, sub = 'H1 = '+h, '通過；球面 links'
            elif not d['edge_orientation_consistent']:
                color,title = '#602D3C','邊反向自識別'
                sub = '球面 links 仍拒絕' if d['all_links_spheres'] else '另有 link / 方向失敗'
            else:
                color,title,sub = '#493D65','link 非球面','Klein bottle'
            x,y = left+j*cw,top+i*ch
            pen.rounded_rectangle((x+3,y+3,x+cw-4,y+ch-4),radius=10,fill=color)
            text(title,(x+13,y+18),23)
            text(sub,(x+13,y+58),17,'#CFD9E8')
    text('第一次目標', (35,193),23,'#AABBD0')
    y = 890
    text('同調分布：H1=0 有 5 案；Z/4 有 2 案；Z/5 有 2 案', (48,y),27)
    text('關鍵對照：130 與 301 的第一次 Ce/Cv 相同；都接上末貼合 231，', (48,y+50),25)
    text('最後 H1 卻是 Z/4 與 Z/5。Ce/Cv 沒有保存邊界到內部的同調映射。', (48,y+91),25,'#F4CD78')
    text('24 種頂點重標號後有 4 個通過組合類；這不是不同胚類數。', (48,y+146),22,'#AABBD0')
    text('各案包含完整 link、拒絕證據、整數矩陣與 Smith 證書；已由另一實作核對 36 案。', (48,y+184),20,'#AABBD0')
    output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path)
    parser.add_argument('--output',type=Path,default=REPORT/'overview.png')
    args = parser.parse_args()
    run = args.run or Path(json.loads((REPORT/'latest-run.json').read_text(encoding='utf-8'))['run_directory'])
    draw(run,args.output)
    print(args.output)


if __name__ == '__main__':
    main()
