"""Data-driven 013-123 lesson: schematic identifications, not a geometric recognition."""
import sys,json
from pathlib import Path
import numpy as np
from manim import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
import example7_rebuild as core
OUT=ROOT/'reports/one-tet-013123-animation'
G=[dict(source_tet=0,source_face=[0,1,2],target_tet=0,target_face=[0,1,3]),dict(source_tet=0,source_face=[0,2,3],target_tet=0,target_face=[1,2,3])]
D=[core.analyse(G[:i],tetrahedra=1) for i in range(3)]
def text(s,n=26,c=WHITE):
 m=Text(s,font='Microsoft JhengHei',font_size=n,color=c)
 if m.width>12.6:m.scale_to_fit_width(12.6)
 return m
class OneTet013123(Scene):
 def page(self,title,sub):
  self.clear();self.camera.background_color='#101927'
  self.add(text(title,34).move_to([0,3.1,0]),text(sub,21,GREY_B).move_to([0,2.4,0]))
 def save(self,name):
  self.wait(.3);(OUT/'figures').mkdir(parents=True,exist_ok=True);self.renderer.camera.get_image().save(OUT/'figures'/f'{name}.png');self.wait(4)
 def rows(self,lines,y=-1.8):
  group=VGroup(*[text(s,25) for s in lines]).arrange(DOWN,buff=.25).move_to([0,y,0]);self.play(FadeIn(group))
 def triangle(self,labels,center,color):
  pts=[np.array(center)+v for v in [np.array([-1.1,-.7,0]),np.array([1.1,-.7,0]),np.array([0,1.05,0])]]
  g=VGroup(Polygon(*pts,color=color,fill_opacity=.2,fill_color=color))
  for p,l in zip(pts,labels):g.add(Dot(p,color=color),text(str(l),25).move_to(p+UP*.28))
  return g
 def construct(self):
  self.page('013-123：一個四面體，兩次面貼合','三角形是二維單形；四面體是三維單形。以下畫面表示識別規則。')
  pts=[np.array(v) for v in [(-2,-.5,0),(2,-.5,0),(0,1.5,0),(.6,.1,0)]]
  for a in range(4):
   for b in range(a+1,4):self.play(Create(Line(pts[a],pts[b],color=BLUE)),run_time=.12)
  for i,p in enumerate(pts):self.add(text(str(i)).move_to(p+UP*.25))
  self.rows(['四張面：012、013、023、123','同一個四面體的不同面，也允許互相貼合。'],-2.1);self.save('01-tetrahedron')
  self.page('面配對圖：一個節點、兩個環','節點代表四面體；環代表同一四面體的兩張面配成一對。')
  self.add(Circle(.4,color=WHITE),text('t0',24))
  self.play(Create(Circle(.8,color=BLUE).move_to([-1,0,0])),Create(Circle(.8,color=GREEN).move_to([1,0,0])))
  self.add(text('012 / 013',24,BLUE).move_to([-2.5,0,0]),text('023 / 123',24,GREEN).move_to([2.5,0,0]))
  self.rows(['兩個環各貢獻二度，節點度數為四。','圖記錄配對對象；尚未記錄面上三個頂點怎麼對應。'],-2);self.save('02-pairing-graph')
  for index,(source,target,color) in enumerate([('012','013',BLUE),('023','123',GREEN)]):
   self.page('第 '+str(index+1)+' 次貼合：'+source+' -> '+target,'兩片三角形是同一四面體上兩張面的分開示意，不是新增四面體。')
   a=self.triangle(source,[-3,0,0],color);b=self.triangle(target,[3,0,0],color)
   self.play(FadeIn(a),FadeIn(b))
   for j in range(3):self.play(Create(Arrow([-1.4,-.5+j*.4,0],[1.4,-.5+j*.4,0],color=color)),run_time=.35)
   s=D[index+1]
   classes='、'.join('{'+','.join(str(v) for t,v in g)+'}' for g in s['vertex_classes'])
   self.rows(['頂點對應：'+'；'.join(x+' -> '+y for x,y in zip(source,target)),'頂點等價類：'+classes,'剩餘未配對面：'+('、'.join(s['boundary_faces']) or '無')],-2)
   self.save('03-first' if index==0 else '04-second')
  self.page('Ce、Cv：只記目前外露邊界的接法','第一次貼合後還有 023、123；內部的歷史不全部放進邊界狀態。')
  self.add(self.triangle('023',[-3,.4,0],BLUE),self.triangle('123',[3,.4,0],GREEN))
  self.rows(['Cv = {0}、{1}、{2,3}','Ce：023/02 <-> 023/03，同方向','Ce：123/12 <-> 123/13，同方向','Ce：023/23 <-> 123/23，同方向'],-1.7)
  self.save('05-boundary-state')
  self.page('頂點 link：把每個角切出一片小三角形','先按面映射貼小三角形，再檢查每個頂點附近是否像球或半球。')
  for j,label in enumerate(['L(0)','L(1)','L(2)','L(3)']):
   g=self.triangle(['a','b','c'],[-4.5+j*3,.2,0],BLUE if j<2 else GREEN).scale(.65)
   self.add(g,text(label,24).move_to([-4.5+j*3,-1,0]))
  self.rows(['最後 A={0,1}：合併 L(0)、L(1)','最後 B={2,3}：合併 L(2)、L(3)','小三角形的 a,b,c 是局部方向標記，不是新的四面體頂點。'],-2.1);self.save('06-link-triangles')
  self.page('兩個 link 都是球面：兩片三角形沿整圈邊界貼合','可以想成兩個三角形圓盤，分別作球面的上、下半部。')
  for x,label in [(-3,'A={0,1}'),(3,'B={2,3}')]:
   self.play(Create(Circle(1.1,color=BLUE).move_to([x,.2,0])),Create(Ellipse(2.2,.55,color=GREEN).move_to([x,.2,0])))
   self.add(text(label,25).move_to([x,-1.3,0]))
  self.rows(['每個 link：V=3、E=3、F=2，因此 Euler characteristic = 2','程式另外檢查連通、局部圓圈、可定向與無邊界，才判定球面。'],-2.3);self.save('07-sphere-links')
  self.page('完整結果：合法的廣義三維三角剖分','頂點 link 是二維球面；整個貼合空間是三維，兩者不可混淆。')
  self.rows(['四面體數 1；面類數 2；邊類數 3；頂點類數 2','所有面已配對，所以 Ce=[]、Cv=[]；實際頂點類仍有 A、B。','沒有邊反向自識別；整體可定向；兩個頂點 links 都是球面。','整數同調：(H0,H1,H2,H3) = (Z,0,0,Z)','本動畫沒有憑同調把整個空間識別或命名為三維球面。'],0)
  self.save('08-result')
