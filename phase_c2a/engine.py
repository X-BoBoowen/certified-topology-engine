from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from fractions import Fraction
from .exact_types import require_fraction,ExactInputError
from .field import PiecewisePolynomialField2D,FieldStatus
from .circle_proposal import CircleProposal
from .frozen_oracle import (
    FrozenArtifactError,
    load_frozen_module,
    resolve_frozen_artifacts,
)
from .proof_log import seal,verify_seal
from .version import ALGORITHM_VERSION,PACKAGE_NAME,PACKAGE_VERSION


FROZEN_ORACLE_MAX_DEPTH=40
FROZEN_ORACLE_MAX_BOXES=10_000

class EngineStatus(str,Enum):
    VALID='VALID'; UNKNOWN='UNKNOWN'; CURVATURE_FAIL='CURVATURE_FAIL'; INPUT_INVALID='INPUT_INVALID'
@dataclass(frozen=True)
class EngineResult:
    status:EngineStatus
    reason:str
    data:dict=field(default_factory=dict)


def _validated_oracle_transcript(result,r0):
    status=getattr(getattr(result,'status',None),'name',None)
    reason=getattr(result,'reason',None)
    result_r0=getattr(result,'r0',None)
    if status not in {'VALID','UNKNOWN','CURVATURE_FAIL','INPUT_INVALID'}:
        raise ValueError('unsupported frozen oracle status')
    if type(reason) is not str or type(result_r0) is not Fraction or result_r0!=r0:
        raise ValueError('frozen oracle result identity mismatch')
    as_dict=getattr(result,'as_dict',None)
    if not callable(as_dict):
        raise ValueError('frozen oracle result has no stats')
    stats=as_dict()
    if type(stats) is not dict:
        raise ValueError('frozen oracle stats are invalid')
    stats=dict(stats)
    stats.pop('runtime_seconds',None)
    if (
        stats.get('status')!=status
        or stats.get('r0')!=str(r0)
        or stats.get('reason')!=reason
    ):
        raise ValueError('frozen oracle transcript mismatch')
    count_keys=(
        'patch_count','all_patch_pairs','initial_pair_boxes','local_pruned',
        'distance_pruned','normal_pruned','interval_boxes',
        'subdivision_children_enqueued','subdivision_parent_boxes',
        'generated_boxes','queued_boxes_at_exit','max_depth_seen',
        'max_depth_unresolved_boxes','unresolved_boxes',
    )
    if any(type(stats.get(key)) is not int for key in count_keys):
        raise ValueError('frozen oracle numeric stats are invalid')
    accounting_keys=(
        'accounting_ok','processing_accounting_ok','unresolved_accounting_ok'
    )
    if any(type(stats.get(key)) is not bool for key in accounting_keys):
        raise ValueError('frozen oracle accounting stats are invalid')
    if not all(stats[key] for key in accounting_keys):
        raise ValueError('frozen oracle accounting failed')
    if status=='VALID' and (
        stats['unresolved_boxes']!=0
        or stats['queued_boxes_at_exit']!=0
        or stats['max_depth_unresolved_boxes']!=0
    ):
        raise ValueError('frozen VALID result contains unresolved boxes')
    numeric_certificate={
        'certified_r0':str(result_r0),
        'patch_count':stats['patch_count'],
        'all_patch_pairs':stats['all_patch_pairs'],
        'interval_boxes':stats['interval_boxes'],
        'generated_boxes':stats['generated_boxes'],
        'unresolved_boxes':stats['unresolved_boxes'],
        'max_depth_seen':stats['max_depth_seen'],
        'accounting_ok':stats['accounting_ok'],
        'processing_accounting_ok':stats['processing_accounting_ok'],
        'unresolved_accounting_ok':stats['unresolved_accounting_ok'],
    }
    return status,reason,stats,numeric_certificate

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
            oracle=load_frozen_module()
        except FrozenArtifactError as e:
            return EngineResult(EngineStatus.UNKNOWN,'FROZEN_ARTIFACT_VALIDATION_FAILED',{'error':str(e)})
        except Exception as e:
            return EngineResult(
                EngineStatus.UNKNOWN,
                'FROZEN_ORACLE_EXECUTION_FAILED',
                {'error':f'{type(e).__name__}: {e}'},
            )
        oracle_budgets={
            'pieces_per_quarter':self.pieces_per_quarter,
            'max_depth':min(self.max_depth,FROZEN_ORACLE_MAX_DEPTH),
            'max_boxes':min(self.max_boxes,FROZEN_ORACLE_MAX_BOXES),
        }
        try:
            circles=[oracle.Circle(c.cx,c.cy,c.radius) for c in proposal.circles]
            ores=oracle.ReachEngine(**oracle_budgets).certify(circles,r0)
        except Exception as e:
            return EngineResult(
                EngineStatus.UNKNOWN,
                'FROZEN_ORACLE_EXECUTION_FAILED',
                {'error':f'{type(e).__name__}: {e}'},
            )
        try:
            oracle_name,oracle_reason,oracle_stats,numeric_certificate=(
                _validated_oracle_transcript(ores,r0)
            )
        except (TypeError,ValueError) as e:
            return EngineResult(
                EngineStatus.UNKNOWN,
                'FROZEN_ORACLE_RESULT_INCONSISTENT',
                {'error':str(e)},
            )
        if oracle_name=='VALID':
            status=EngineStatus.VALID
        elif oracle_name=='CURVATURE_FAIL':
            status=EngineStatus.CURVATURE_FAIL
        else:
            status=EngineStatus.UNKNOWN
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
            'oracle':{
                'status':oracle_name,'reason':oracle_reason,
                'stats':oracle_stats,'budgets':oracle_budgets,
            },
            'oracle_numeric_certificate':numeric_certificate,
            'decision':status.value,
            'field_only_gap':'automatic field-only loop discovery is not implemented',
        })
        return EngineResult(status,oracle_reason,{'proof_log':log,'oracle_status':oracle_name,'field_validation':fv.data,'factorization':zv.data})
    def replay(self,field,r0,proposal,log):
        if not verify_seal(log): return False
        fresh=self.certify(field,r0,proposal)
        if 'proof_log' not in fresh.data: return False
        return fresh.data['proof_log']==log
