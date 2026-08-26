from fractions import Fraction as F
from phase_c2a import Polynomial2D
from phase_c2a.intervals import RationalInterval

def test_interval_polynomial_contains_exact_points():
    p=3*Polynomial2D.x()*Polynomial2D.x()-2*Polynomial2D.x()*Polynomial2D.y()+Polynomial2D.y()+1
    xi=RationalInterval(F(-2),F(3)); yi=RationalInterval(F(-1),F(4)); iv=p.interval_evaluate(xi,yi)
    for x in (F(-2),F(0),F(3)):
      for y in (F(-1),F(1),F(4)): assert iv.contains(p.evaluate(x,y))
