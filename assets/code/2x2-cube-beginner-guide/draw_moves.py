"""Generate geometrically projected cube move diagrams. Python 3, no dependencies."""
from math import sin, cos, radians, sqrt
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[2] / 'img'
PREFIX = '2026-11-15-2x2-cube'
N = {'R': (1,0,0), 'L': (-1,0,0), 'U': (0,1,0),
     'D': (0,-1,0), 'F': (0,0,1), 'B': (0,0,-1)}
KOREAN = {'R': '오른쪽', 'L': '왼쪽', 'U': '위', 'D': '아래', 'F': '앞', 'B': '뒤'}
CAM = {'R': (4,3,4), 'L': (-4,3,4), 'U': (4,5,4),
       'D': (4,-5,4), 'F': (4,3,5), 'B': (4,3,-5)}

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):
    d=sqrt(dot(a,a))
    return tuple(x/d for x in a)
def vec(n,r,u,x,y,depth=1): return tuple(depth*n[i]+x*r[i]+y*u[i] for i in range(3))
def basis(face):
    up=(0,0,-1) if face=='U' else (0,0,1) if face=='D' else (0,1,0)
    return cross(up,N[face]),up

def text(x,y,value,size=24,weight=400,fill='#263b38'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="middle">{escape(value)}</text>'

def cube(face,cx,cy,scale=68,prime=False,half=False):
    camera=norm(CAM[face])
    right=norm(cross((0,1,0),camera))
    up=cross(camera,right)
    def project(v): return (cx+scale*dot(v,right), cy-scale*dot(v,up))
    def coords(v): return f'{v[0]:.2f},{v[1]:.2f}'
    shapes=[]
    visible=[f for f in N if dot(N[f],camera)>0]
    for f in visible:
        r,u=basis(f)
        for x in (-1,0):
            for y in (-1,0):
                points=[project(vec(N[f],r,u,a,b)) for a,b in ((x,y),(x+1,y),(x+1,y+1),(x,y+1))]
                fill='#bee2d8' if f==face else '#e5e8e2'
                shapes.append(f'<polygon points="{" ".join(map(coords,points))}" fill="{fill}" stroke="#33433e" stroke-width="2.5" stroke-linejoin="round"/>')
        px,py=project(N[f])
        shapes.append(text(round(px),round(py+8),f,24,700))
    r,u=basis(face)
    # In the selected face's outward-facing (right,up) basis, decreasing
    # angles are clockwise. Projection preserves that outward view.
    start=140 if not prime else 40
    sweep=(180 if half else 90)*(1 if prime else -1)
    points=[]
    for i in range(41):
        theta=radians(start+sweep*i/40)
        points.append(project(vec(N[face],r,u,.80*cos(theta),.80*sin(theta),1.05)))
    path='M'+' L'.join(coords(p) for p in points)
    shapes.append(f'<path d="{path}" fill="none" stroke="#fffdf6" stroke-width="11" stroke-linecap="round"/>')
    shapes.append(f'<path d="{path}" fill="none" stroke="#007d7f" stroke-width="6" stroke-linecap="round" marker-end="url(#arrow)"/>')
    return ''.join(shapes)

def svg(width,height,title,description,body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<defs><marker id="arrow" markerWidth="4" markerHeight="4" refX="3" refY="2" orient="auto"><path d="M0 0L4 2L0 4Z" fill="#007d7f"/></marker></defs>
<g font-family="Malgun Gothic, Noto Sans CJK KR, sans-serif"><rect width="100%" height="100%" rx="18" fill="#fbf5e9"/>{body}</g></svg>'''

def main():
    body=text(500,55,'어느 면을 돌릴까? R · L · U · D · F · B',31,700)
    body+=text(500,96,'청록색 면만 90° 회전 · 해당 면을 정면에서 보면 시계 방향',23)
    body+=text(500,132,'아래 그림마다 관찰 위치가 다릅니다. 공식 도중에는 큐브 전체 방향을 유지하세요.',19)
    for i,face in enumerate(('R','L','U','D','F','B')):
        x=25+(i%2)*490
        y=160+(i//2)*345
        body+=f'<rect x="{x}" y="{y}" width="460" height="325" rx="15" fill="#fffdf7" stroke="#d9ded2" stroke-width="2"/>'
        body+=text(x+230,y+40,f'{face}  |  {KOREAN[face]}쪽 면' if face in 'UD' else f'{face}  |  {KOREAN[face]} 면',27,700)
        body+=cube(face,x+230,y+163,60)
        viewpoint={'R':'오른쪽에서','L':'왼쪽에서','U':'위에서 내려다보고','D':'아래에서 올려다보고','F':'앞에서','B':'뒤에서'}[face]
        if face in 'R L F B'.split(): viewpoint+=' 바라보고'
        body+=text(x+230,y+292,f'{viewpoint} 시계 방향',21)
    body+=text(500,1225,'면의 글자는 현재 잡은 위치를 뜻합니다. 색 이름이 아닙니다.',23,700)
    (OUT/f'{PREFIX}-six-face-turns.svg').write_text(svg(1000,1260,'2×2 큐브 여섯 면의 90도 회전 방향','오른쪽 R, 왼쪽 L, 위 U, 아래 D, 앞 F, 뒤 B의 회전할 면과 시계 방향 화살표.',body),encoding='utf-8')
    body=text(540,55,'R · R′ · R2는 무엇이 다를까?',32,700)
    body+=text(540,97,'세 그림 모두 같은 오른쪽 면을 봅니다.',23)
    for i,(label,prime,half,caption) in enumerate((('R',False,False,'시계 방향 90°'),('R′',True,False,'반시계 방향 90°'),('R2',False,True,'180° · 반 바퀴'))):
        x=20+i*355
        body+=f'<rect x="{x}" y="125" width="330" height="355" rx="15" fill="#fffdf7" stroke="#d9ded2" stroke-width="2"/>'
        body+=text(x+165,172,label,36,700)
        body+=cube('R',x+165,302,66,prime,half)
        body+=text(x+165,452,caption,24,700)
    body+=text(540,525,'작은따옴표(′)는 역방향 · 2는 어느 방향으로 돌려도 반 바퀴',24)
    (OUT/f'{PREFIX}-prime-and-double-turns.svg').write_text(svg(1080,565,'R과 R 프라임 및 R2 비교','같은 오른쪽 면에서 R은 시계 방향 90도, R 프라임은 반시계 방향 90도, R2는 180도 회전.',body),encoding='utf-8')
    print('Generated six-face-turns.svg and prime-and-double-turns.svg')

if __name__=='__main__': main()
