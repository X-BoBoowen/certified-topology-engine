from __future__ import annotations
from fractions import Fraction as F
from dataclasses import dataclass
from .polynomial import Polynomial2D
from .field import PiecewisePolynomialField2D
from .circle_proposal import CircleSpec,CircleProposal

@dataclass(frozen=True)
class Scenario:
    name:str; circles:tuple; r0:F; expected:str; knots_x:tuple=(); knots_y:tuple=(); epsilon:F=F(1,1000000)

def circle(cx,cy,r): return CircleSpec(F(cx),F(cy),F(r))

def base_circle_scenarios():
    # 22 deterministic exact-rational differential cases.
    return [
      Scenario('S1_single_circle',(circle(0,0,3),),F(2),'VALID'),
      Scenario('S2_two_separated_circles',(circle(-5,0,2),circle(5,0,2)),F(3,2),'VALID'),
      Scenario('S3_concentric_annulus',(circle(0,0,2),circle(0,0,5)),F(7,5),'VALID'),
      Scenario('S3b_annulus_equality',(circle(0,0,2),circle(0,0,5)),F(3,2),'UNKNOWN_ALLOWED'),
      Scenario('S4_near_parallel_large_loops',(circle(-101,0,100),circle(101,0,100)),F(19,20),'VALID'),
      Scenario('S5_exact_equality_pair',(circle(-3,0,2),circle(3,0,2)),F(1),'UNKNOWN_ALLOWED'),
      Scenario('S6_high_curvature_fails',(circle(0,0,F(3,4)),),F(1),'NOT_VALID'),
      Scenario('S6b_high_curvature_strict_valid',(circle(0,0,F(3,4)),),F(7,10),'VALID'),
      Scenario('S7_low_curvature_global_bottleneck',(circle(F(-251,5),0,50),circle(F(251,5),0,50)),F(1),'NOT_VALID'),
      Scenario('S8_nested_and_multiple_components',(circle(0,0,2),circle(0,0,5),circle(20,0,3)),F(7,5),'VALID'),
      Scenario('A01_external_gap',(circle(0,0,2),circle(7,0,2)),F(7,5),'VALID'),
      Scenario('A02_external_above',(circle(0,0,2),circle(7,0,2)),F(8,5),'NOT_VALID'),
      Scenario('A03_nested_strict',(circle(0,0,2),circle(0,0,8)),F(3,2),'VALID'),
      Scenario('A04_nested_above',(circle(0,0,2),circle(0,0,8)),F(16,5),'NOT_VALID'),
      Scenario('A05_seam_bottleneck',(circle(0,0,3),circle(0,8,3)),F(9,10),'VALID'),
      Scenario('A06_seam_above',(circle(0,0,3),circle(0,8,3)),F(11,10),'NOT_VALID'),
      Scenario('A07_three_hidden_gap',(circle(-8,0,3),circle(0,0,3),circle(20,0,4)),F(9,10),'VALID'),
      Scenario('A08_three_hidden_gap_above',(circle(-8,0,3),circle(0,0,3),circle(20,0,4)),F(11,10),'NOT_VALID'),
      Scenario('A09_large_margin',(circle(-20,-5,4),circle(15,6,5)),F(3),'VALID'),
      Scenario('A10_single_fractional',(circle(F(1,3),F(-2,5),F(7,3)),),F(2),'VALID'),
      Scenario('A11_nested_fractional',(circle(F(1,4),F(1,7),F(5,2)),circle(F(1,4),F(1,7),F(15,2))),F(2),'VALID'),
      Scenario('A12_equality_single',(circle(0,0,2),),F(2),'UNKNOWN_ALLOWED'),
    ]

def truncated_cube_poly(axis,k,active):
    if not active: return Polynomial2D.zero()
    V=Polynomial2D.x() if axis=='x' else Polynomial2D.y()
    return (V-F(k))*(V-F(k))*(V-F(k))

def make_field(s:Scenario,extra_knots_x=(),extra_knots_y=(),label=None):
    cs=s.circles
    maxabs=max([abs(c.cx)+c.radius for c in cs]+[abs(c.cy)+c.radius for c in cs])+F(3)
    xmin=-maxabs; xmax=maxabs; ymin=-maxabs; ymax=maxabs
    kx=tuple(sorted({F(k) for k in (s.knots_x+tuple(extra_knots_x)) if xmin<F(k)<xmax}))
    ky=tuple(sorted({F(k) for k in (s.knots_y+tuple(extra_knots_y)) if ymin<F(k)<ymax}))
    xs=(xmin,)+kx+(xmax,); ys=(ymin,)+ky+(ymax,)
    g=Polynomial2D.one()
    for c in cs: g=g*c.factor()
    pieces={}; mult={}
    for i in range(len(xs)-1):
      for j in range(len(ys)-1):
        h=Polynomial2D.one()
        for k in kx: h=h+s.epsilon*truncated_cube_poly('x',k,xs[i]>=k)
        for k in ky: h=h+s.epsilon*truncated_cube_poly('y',k,ys[j]>=k)
        pieces[i,j]=h*g; mult[i,j]=h
    field=PiecewisePolynomialField2D(xs,ys,pieces,label or s.name)
    return field,CircleProposal(tuple(cs),mult)

def knot_scenarios():
    base=Scenario('knot_base',(circle(0,0,2),),F(1),'VALID')
    return [
      Scenario('K1_vertical_knot',base.circles,F(1),'VALID',(F(0),),()),
      Scenario('K2_horizontal_knot',base.circles,F(1),'VALID',(),(F(0),)),
      Scenario('K3_corner_knot',base.circles,F(1),'VALID',(F(0),),(F(0),)),
      Scenario('K4_multi_knots',base.circles,F(1),'VALID',(F(-1),F(0),F(1)),(F(-1),F(0),F(1))),
      Scenario('K5_two_loops',(circle(-4,0,2),circle(4,0,2)),F(9,10),'VALID',(F(0),),(F(0),)),
      Scenario('K6_nested',(circle(0,0,2),circle(0,0,6)),F(3,2),'VALID',(F(0),),(F(0),)),
      Scenario('K7_near_bottleneck',(circle(-3,0,2),circle(3,0,2)),F(9,10),'VALID',(F(0),),(F(0),)),
      Scenario('K8_equality',(circle(-3,0,2),circle(3,0,2)),F(1),'UNKNOWN_ALLOWED',(F(0),),(F(0),)),
      Scenario('K9_above',(circle(-3,0,2),circle(3,0,2)),F(11,10),'NOT_VALID',(F(0),),(F(0),)),
    ]

def expected_ok(expected,status):
    if expected=='VALID': return status=='VALID'
    if expected=='NOT_VALID': return status!='VALID'
    if expected=='UNKNOWN_ALLOWED': return status in ('VALID','UNKNOWN')
    raise ValueError(expected)
