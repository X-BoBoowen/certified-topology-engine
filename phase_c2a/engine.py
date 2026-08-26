from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from fractions import Fraction
from .exact_types import require_fraction,ExactInputError
from .field import PiecewisePolynomialField2D,FieldStatus
from .circle_proposal import CircleProposal
from .frozen_oracle import FrozenArtifactError,resolve_frozen_artifacts
from .proof_log import seal,verify_seal
from .version import ALGORITHM_VERSION,PACKAGE_NAME,PACKAGE_VERSION

class EngineStatus(str,Enum):
    VALID='VALID'; UNKNOWN='UNKNOWN'; CURVATURE_FAIL='CURVATURE_FAIL'; INPUT_INVALID='INPUT_INVALID'
@dataclass(frozen=True)
class EngineResult:
    status:EngineStatus
    reason:str
    data:dict=field(default_factory=dict)

class GeneralReachEngine:
    def __init__(self,pieces_per_quarter:int=4,max_depth:int=40,max_boxes:int=500000):
        if type(pieces_per_quarter) is not int or type(max_depth) is not int or type(max_boxes) is not int or isinstance(pieces_per_quarter,bool):
            raise TypeError('budgets must be built-in int')
        self.pieces_per_quarter=pieces_per_quarter; self.max_depth=max_depth; self.max_boxes=max_boxes
    def certify(self,field:PiecewisePolynomialField2D,r0,proposal:CircleProposal|None=None):
        try: r0=require_fraction(r0,'r0')
        except (ExactInputError,ValueError) as e: return EngineResult(EngineStatus.INPUT_INVALID,str(e),{})
        if r0<=0: return EngineResult(EngineStatus.INPUT_INVALID,'r0 must be positive',{})
        if not isinstance(field,PiecewisePolynomialField2D): return EngineResult(EngineStatus.INPUT_INVALID,'invalid field object',{})
        fv=field.validate()
        if fv.status is FieldStatus.INPUT_INVALID: return EngineResult(EngineStatus.INPUT_INVALID,fv.reason,{'field_validation':fv.data})
        if fv.status is not FieldStatus.VALID: return EngineResult(EngineStatus.UNKNOWN,fv.reason,{'field_validation':fv.data})
        if proposal is None:
            return EngineResult(EngineStatus.UNKNOWN,'FIELD_ONLY_LOOP_DISCOVERY_NOT_IMPLEMENTED',{'field_validation':fv.data})
        if not isinstance(proposal,CircleProposal): return EngineResult(EngineStatus.INPUT_INVALID,'invalid proposal object',{})
        lv=proposal.validate_link()
        if lv.status is not FieldStatus.VALID: return EngineResult(EngineStatus.INPUT_INVALID,lv.reason,{'proposal_validation':lv.data})
        zv=proposal.validate_field_factorization(field,max_depth=min(24,self.max_depth),max_boxes=self.max_boxes)
        if zv.status is FieldStatus.INPUT_INVALID: return EngineResult(EngineStatus.INPUT_INVALID,zv.reason,{'factorization':zv.data})
        if zv.status is not FieldStatus.VALID: return EngineResult(EngineStatus.UNKNOWN,zv.reason,{'factorization':zv.data})
        try:
            frozen_artifacts=resolve_frozen_artifacts()
        except FrozenArtifactError as e:
            return EngineResult(EngineStatus.UNKNOWN,'FROZEN_ARTIFACT_VALIDATION_FAILED',{'error':str(e)})
        # Exact analytic circle-link certificate.  The field certificate above proves
        # that the general piecewise-polynomial zero set is exactly this link.
        cs=proposal.circles
        if any(c.radius < r0 for c in cs):
            status=EngineStatus.CURVATURE_FAIL
            oracle_name='CURVATURE_FAIL'
            oracle_reason='exact curvature radius below r0'
        else:
            strict=all(c.radius > r0 for c in cs)
            for i in range(len(cs)):
                for j in range(i+1,len(cs)):
                    a,b=cs[i],cs[j]
                    dx=a.cx-b.cx; dy=a.cy-b.cy; d2=dx*dx+dy*dy
                    sp=a.radius+b.radius; df=abs(a.radius-b.radius); two=Fraction(2)*r0
                    if d2>sp*sp:
                        strict = strict and d2>(sp+two)*(sp+two)
                    else:
                        strict = strict and df>two and d2<(df-two)*(df-two)
            status=EngineStatus.VALID if strict else EngineStatus.UNKNOWN
            oracle_name=status.value
            oracle_reason='strict exact analytic circle-link margin' if strict else 'equality or insufficient exact margin'
        class _O: pass
        ores=_O(); ores.reason=oracle_reason; ores.stats={'mode':'exact_analytic_circle_link'}
        log=seal({
            'schema':'phase-c2a-proof-v1','field_hash':field.field_hash(),'proposal_hash':proposal.proposal_hash(),'r0':str(r0),
            'engine':{
              'package':PACKAGE_NAME,'version':PACKAGE_VERSION,'algorithm':ALGORITHM_VERSION,
              'work_budgets':{
                'pieces_per_quarter':self.pieces_per_quarter,'max_depth':self.max_depth,
                'factorization_max_depth':min(24,self.max_depth),'max_boxes':self.max_boxes,
              },
            },
            'field_validation':fv.data,'proposal_validation':lv.data,'zero_set_certificate':zv.data,
            'frozen_phase_c1':frozen_artifacts,
            'oracle':{'status':oracle_name,'reason':getattr(ores,'reason',''),'stats':getattr(ores,'stats',{})},
            'decision':status.value,
            'field_only_gap':'automatic field-only loop discovery is not implemented',
        })
        return EngineResult(status,getattr(ores,'reason',oracle_name),{'proof_log':log,'oracle_status':oracle_name,'field_validation':fv.data,'factorization':zv.data})
    def replay(self,field,r0,proposal,log):
        if not verify_seal(log): return False
        fresh=self.certify(field,r0,proposal)
        if 'proof_log' not in fresh.data: return False
        return fresh.data['proof_log']==log
