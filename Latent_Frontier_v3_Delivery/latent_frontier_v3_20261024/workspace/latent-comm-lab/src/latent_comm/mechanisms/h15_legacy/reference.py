from random import Random
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matvec
from .types import PairPlan
class AdapterRegistry:
    def __init__(self):self.members={}
    def register(self,member):
        key=(member.model_id,member.model_revision)
        if key in self.members:raise ContractError('VersionConflict','model interface revisions immutable')
        self.members[key]=member
    def get(self,id,revision):
        if (id,revision) not in self.members:raise ContractError('NewModelNeedsAdaptation','unseen model is not merely an unseen pair')
        return self.members[id,revision]

def eligible_pair(sender,receiver,required):
    return sender.interface_trained and receiver.interface_trained and set(required)<=sender.capabilities&receiver.capabilities and sender.versions.matches(receiver.versions,('frame','task','ontology')) and len(sender.writer)==len(receiver.reader[0]) and sender.behavior_coordinates==receiver.behavior_coordinates

def sample_pairs(members,*,held_out_pairs,required,count,seed,receiver_dropout=(),budget=StepBudget()):
    if not 1<=count<=64 or len(members)>8:raise ContractError('BudgetExhausted','finite population schedule')
    meter=budget.meter();eligible=[]
    for sender in members:
        for receiver in members:
            meter.consume(cases=1)
            pair=(sender.model_id,receiver.model_id)
            if sender.model_id!=receiver.model_id and pair not in held_out_pairs and receiver.model_id not in receiver_dropout and eligible_pair(sender,receiver,required):eligible.append(pair)
    if not eligible:raise ContractError('NoCompatiblePair','capability/heldout/dropout restrictions leave no training edge')
    rng=Random(seed);pairs=[]
    for _ in range(count):meter.consume(steps=1);pairs.append(rng.choice(eligible))
    return PairPlan(tuple(pairs),frozenset(held_out_pairs),frozenset(m.model_id for m in members if not m.interface_trained),seed)
def transmit(sender,receiver,state,*,required):
    if not eligible_pair(sender,receiver,required):raise ContractError('UnsupportedPair','missing trained interface/common behavior/capability')
    return matvec(receiver.reader,matvec(sender.writer,state))
def coverage(members,observed_pairs):
    all_pairs={(a.model_id,b.model_id) for a in members for b in members if a.model_id!=b.model_id}
    return {'observed':tuple(sorted(set(observed_pairs))),'unseen_pairs':tuple(sorted(all_pairs-set(observed_pairs))),'new_model_adaptation_required':tuple(m.model_id for m in members if not m.interface_trained)}
