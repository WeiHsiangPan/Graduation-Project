"""Optional Pillow diagram of the verified augmented-state experiment."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/enhanced-boundary-state'


def draw(run,output):
    data=json.loads((run/'results.json').read_text(encoding='utf-8'))
    verification=json.loads((run/'independent-verification.json').read_text(encoding='utf-8'))
    if verification['status']!='PASS':
        raise ValueError('Only draw a verified run')
    histories={h['history_id']:h for h in data['histories']}
    im=Image.new('RGB',(1500,1110),'#101927')
    pen=ImageDraw.Draw(im)
    def text(value,xy,size=25,fill='#EDF2F8'):
        pen.text(xy,value,font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',size),fill=fill)
    def card(box,fill):
        pen.rounded_rectangle(box,radius=18,fill=fill)
    text('Ce/Cv + 邊界同調映射：區分歷史，預測末貼合',(42,26),38)
    text('固定邊界標記；內部生成元 u 換成 -u 視為同一映射',(45,83),25,'#AABBD0')
    card((44,140,1456,251),'#25334A')
    text('共同 Ce/Cv：第一次 130 與 301 原本被合併',(70,154),29)
    text('共同邊界圈 x=[03]、y=[13]、z=[23]=x+y；程式固定基底採 (x,z)',(70,205),25)
    for first,x,color in [('130',44,'#224B68'),('301',774,'#4B3E68')]:
        card((x,292,x+682,540),color)
        matrix=histories[first]['augmentation']['canonical_map_key']['matrix'][0]
        text('第一次貼合 '+first,(x+25,310),31)
        text('固定 (x,z) 基底：i_* = '+str(matrix),(x+25,365),29)
        familiar='x -> 2u，y -> u' if first=='130' else 'x -> u，y -> 2u'
        text('換成 (x,y)：'+familiar,(x+25,418),27)
        text('內部 H1 = Z；整列換號已規範為相同',(x+25,481),23,'#C7D6E7')
    card((44,582,1456,687),'#25334A')
    text('共同最後貼合 023 -> 231：加入 x + 2y = 0',(70,596),30)
    text('預測器只接收邊界、i_* 與這次貼合，沒有讀取原始歷史或最後真值',(70,648),24,'#C7D6E7')
    for x,first,result,color in [(44,'130','4u = 0  ->  H1 = Z/4','#164F40'),(774,'301','5u = 0  ->  H1 = Z/5','#625227')]:
        card((x,725,x+682,826),color)
        text(result,(x+25,749),32)
    text('實際驗證：9 個狀態預測 / 9 個符合完整歷史真值',(45,865),29)
    text('原 Ce/Cv：2 組、2 個同調反例；增強後：3 組、0 個剩餘反例',(45,915),26)
    text('限制：三種合法歷史都被分開，相同增強狀態的不同歷史比較數為 0。',(45,970),26,'#F4CD78')
    text('所以本輪驗證了已知反例與 9 次 H1 預測，尚未證明一般充分性或壓縮效益。',(45,1015),25,'#F4CD78')
    text('原始 36 案、6 個歷史、90 個配對、拒絕原因、反例與整數證書均保存。',(45,1066),21,'#AABBD0')
    output.parent.mkdir(parents=True,exist_ok=True)
    im.save(output)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path)
    p.add_argument('--output',type=Path,default=REPORT/'overview.png')
    a=p.parse_args()
    run=a.run or Path(json.loads((REPORT/'latest-run.json').read_text(encoding='utf-8'))['run_directory'])
    draw(run,a.output)
    print(a.output)


if __name__=='__main__':
    main()
