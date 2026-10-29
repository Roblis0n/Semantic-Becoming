"""L12: known cooperative values and source-identity-correct support calibration."""
from dataclasses import dataclass,replace
from itertools import combinations,product
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action

def source_classes(equivalence):
    n=len(equivalence)
    if not 1<=n<=6 or any(len(row)!=n for row in equivalence):raise ContractError(ErrorCode.INVALID_SHAPE,'finite square source equivalence required')
    if any(type(v) is not bool for row in equivalence for v in row):raise ContractError(ErrorCode.INVALID_SCHEMA,'source identity relation must be boolean')
    if any(not equivalence[i][i] or equivalence[i][j]!=equivalence[j][i] for i in range(n) for j in range(n)):raise ContractError(ErrorCode.INVALID_SCHEMA,'source identity must be reflexive and symmetric')
    if any(equivalence[i][j] and equivalence[j][k] and not equivalence[i][k] for i in range(n) for j in range(n) for k in range(n)):raise ContractError(ErrorCode.INVALID_SCHEMA,'source identity must be transitive')
    remaining=set(range(n));groups=[]
    while remaining:
        first=min(remaining);group=tuple(i for i in sorted(remaining) if equivalence[first][i]);groups.append(group);remaining.difference_update(group)
    return tuple(groups)

def coalition_table(sender,receiver):
    players=tuple(sender.public_task['players'])
    if players!=tuple(receiver.public_task['players']) or sender.public_task['credit_is_money'] is not False or receiver.public_task['credit_is_money'] is not False or not 2<=len(players)<=6 or len(set(players))!=len(players):raise ContractError(ErrorCode.INVALID_SCHEMA,'finite nonmonetary player identity contract required')
    table={}
    for members,value in tuple(sender.features['sender_values'])+tuple(receiver.features['receiver_values']):
        key=frozenset(members)
        if not key<=set(players) or key in table:raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown or duplicate known coalition')
        from latent_comm.core.finite import finite_scalar
        table[key]=finite_scalar(value)
    subsets=tuple(frozenset(s) for k in range(len(players)+1) for s in combinations(players,k))
    if frozenset() not in table:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'coalition baseline missing')
    return players,subsets,table

@dataclass(frozen=True)
class CoalitionOutput:
    estimates: object
    known_mask: object
    selected: object
    log_probability: object
    subsets: tuple

class CoalitionStage:
    def __init__(self,singleton_delta,pair_delta,baseline_delta,proposer,versions,*,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h41_coalitions.losses import LOSS_SPECS
        self.singleton_delta=singleton_delta;self.pair_delta=pair_delta;self.baseline_delta=baseline_delta;self.proposer=proposer;self.versions=versions;self.device=device;self.loss_specs=LOSS_SPECS;validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'coalition_value_estimator':{'singleton_delta':self.singleton_delta,'pair_delta':self.pair_delta,'baseline_delta':self.baseline_delta},'coalition_proposer':{'membership_weight':self.proposer}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h41_coalitions.adapter import tensor_coalition_value,tensor_coalition_policy
        estimates=[];masks=[];logps=[];chosen=[];subset_rows=[]
        for s,r in zip(sender.views,receiver.views):
            players,subsets,table=coalition_table(s,r);n=len(players)
            if self.singleton_delta.shape!=(n,) or self.pair_delta.shape!=(n,n):raise ContractError(ErrorCode.INVALID_SHAPE,'recipe player axis differs from role contract')
            baseline=table[frozenset()];single=[];pair=[[0.]*n for _ in players]
            for player in players:
                if frozenset((player,)) not in table:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'known singleton anchors required for this pair-synergy value family')
                single.append(table[frozenset((player,))]-baseline)
            for i in range(n):
                for j in range(i+1,n):
                    key=frozenset((players[i],players[j]))
                    if key not in table:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'known pair anchors required; unknown coalition value is not zero')
                    pair[i][j]=table[key]-baseline-single[i]-single[j]
            membership=self.singleton_delta.new_tensor([[float(p in coalition) for p in players] for coalition in subsets]);known=torch.tensor([c in table for c in subsets],device=self.device,dtype=torch.bool)
            values=tensor_coalition_value(membership.unsqueeze(0),self.singleton_delta+membership.new_tensor(single),self.pair_delta+membership.new_tensor(pair),self.baseline_delta+baseline).squeeze(0)
            scores=values.detach()+membership@self.proposer
            probabilities=tensor_coalition_policy(scores.unsqueeze(0),known.unsqueeze(0),torch.ones_like(known).unsqueeze(0)).squeeze(0);distribution=torch.distributions.Categorical(probs=probabilities);selected=distribution.sample()
            estimates.append(values);masks.append(known);chosen.append(selected);logps.append(distribution.log_prob(selected));subset_rows.append(subsets)
        return CoalitionOutput(torch.stack(estimates),torch.stack(masks),torch.stack(chosen),torch.stack(logps),tuple(subset_rows))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h41_coalitions.losses import tensor_losses
        rows=[];masks=[];utilities=[]
        for i,(subsets,view) in enumerate(zip(output.subsets,supervision.views)):
            target={frozenset(m):float(v) for m,v in view.targets['coalition_values']};mask=[s in target for s in subsets]
            rows.append([target.get(s,0.) for s in subsets]);masks.append(mask);selected=int(output.selected[i].detach())
            if subsets[selected] not in target:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'selected known coalition lacks utility supervision')
            utilities.append(target[subsets[selected]])
        valid=torch.as_tensor(masks,device=self.device,dtype=torch.bool)&output.known_mask
        return tensor_losses(output.estimates,output.estimates.new_tensor(rows),output.log_probability,output.estimates.new_tensor(utilities),(valid,torch.ones_like(output.selected,dtype=torch.bool)))

@dataclass(frozen=True)
class EvidenceOutput:
    support: object
    mode: str

class EvidenceStage:
    def __init__(self,calibration_logits,versions,*,mode='identical_atom',declaration_id=None,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h48_evidence_genealogy.losses import LOSS_SPECS
        if mode!='identical_atom' and (not declaration_id or declaration_id=='UNBOUND'):raise ContractError(ErrorCode.UNBOUND_REFERENCE,'probability factorization needs an explicit named dependence declaration, not source-link scores')
        self.calibration_logits=calibration_logits;self.versions=versions;self.mode=mode;self.declaration_id=declaration_id;self.device=device;self.loss_specs=(LOSS_SPECS[1],);validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'source_calibrator':{'atom_or_joint_logits':self.calibration_logits}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h48_evidence_genealogy.adapter import exact_support_tensor
        outputs=[]
        for s,r in zip(sender.views,receiver.views):
            if s.public_task['source_equivalence']!=r.public_task['source_equivalence']:raise ContractError(ErrorCode.CONFLICT,'source equivalence differs across roles')
            classes=source_classes(s.public_task['source_equivalence']);n=len(classes)
            if self.mode=='identical_atom':
                if n!=1 or self.calibration_logits.numel()!=1:raise ContractError(ErrorCode.INVALID_SCHEMA,'identical-atom recipe rejects distinct sources; identity is not independence')
                outputs.append(self.calibration_logits.sigmoid().reshape(()));continue
            assignments=torch.as_tensor(tuple(product((False,True),repeat=n)),device=self.device,dtype=torch.bool);truth=assignments.any(-1)
            if self.mode=='declared_independent':
                if self.calibration_logits.numel()!=n:raise ContractError(ErrorCode.INVALID_SHAPE,'one calibrated marginal per unique atom required')
                atoms=self.calibration_logits.sigmoid().unsqueeze(0);joint=None
            else:
                if self.calibration_logits.numel()!=2**n:raise ContractError(ErrorCode.INVALID_SHAPE,'explicit joint assignment count mismatch')
                joint=self.calibration_logits.softmax(-1).unsqueeze(0);atoms=joint@assignments.to(joint.dtype)
            outputs.append(exact_support_tensor(atoms,assignments,truth,dependence_mode=self.mode,declaration_id=self.declaration_id,joint_probabilities=joint).reshape(()))
        return EvidenceOutput(torch.stack(outputs),self.mode)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h48_evidence_genealogy.losses import calibration_loss
        target,mask=tensor_target(supervision,'support_union_probability',device=self.device)
        for view in supervision.views:
            expected='identical_atom' if self.mode=='identical_atom' else 'explicit_independence' if self.mode=='declared_independent' else 'explicit_joint'
            if view.targets['dependence']!=expected:raise ContractError(ErrorCode.INVALID_SCHEMA,'calibration target dependence contradicts the named forward assumption')
        return {'calibration':calibration_loss(output.support,target,mask)}

class SourceLinkStage:
    """Separate supervised source-link ranking; never grants independence."""
    def __init__(self,projection,versions,*,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h48_evidence_genealogy.losses import LOSS_SPECS
        self.projection=projection;self.versions=versions;self.device=device;self.loss_specs=(LOSS_SPECS[0],);validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'source_linker':{'projection':self.projection}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h48_evidence_genealogy.adapter import source_link_scores
        features=tensor_field(sender,'source_features',device=self.device)
        return source_link_scores(features,self.projection)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h48_evidence_genealogy.losses import link_loss
        target,mask=tensor_target(supervision,'shared_source',device=self.device)
        return {'link':link_loss(output,target,mask)}

def build_stage(variant,versions,*,players=3,unique_atoms=2,source_features=3,embedding_dim=2,declaration_id='UNBOUND',device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    def p(value):return torch.nn.Parameter(torch.as_tensor(value,device=device,dtype=getattr(torch,dtype)))
    if variant=='coalitions':return CoalitionStage(p(torch.zeros(players)),p(torch.zeros(players,players)),p(0.),p(torch.zeros(players)),versions,device=device)
    if variant=='evidence_identical':return EvidenceStage(p(torch.zeros(1)),versions,device=device)
    if variant=='evidence_independent':return EvidenceStage(p(torch.zeros(unique_atoms)),versions,mode='declared_independent',declaration_id=declaration_id,device=device)
    if variant=='evidence_joint':return EvidenceStage(p(torch.zeros(2**unique_atoms)),versions,mode='explicit_joint',declaration_id=declaration_id,device=device)
    if variant=='source_linking':return SourceLinkStage(p(torch.eye(source_features,embedding_dim)),versions,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown coalition/evidence variant')
