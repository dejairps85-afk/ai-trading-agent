"""Research-only replenishment hypothesis at one instrument, side and price."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Observation:
    before: int
    executed: int
    after: int

def detect_replenishment(observations, *, min_cycles=3, min_replenished=1):
    if any(type(v) is not int or v<=0 for v in (min_cycles,min_replenished)):
        raise ValueError("Invalid thresholds")
    cycles=total=0
    previous=None
    for obs in observations:
        if not isinstance(obs,Observation) or any(type(v) is not int or v<0 for v in (obs.before,obs.executed,obs.after)):
            raise ValueError("Invalid observation")
        if previous is not None and obs.before!=previous:
            raise ValueError("Discontinuous observations")
        if obs.executed>obs.before:
            raise ValueError("Execution exceeds displayed quantity")
        restored=obs.after-(obs.before-obs.executed)
        if obs.executed>0 and restored>=min_replenished:
            cycles+=1
            total+=restored
        previous=obs.after
    return {"cycles":cycles,"replenished":total,"possible_replenishment":cycles>=min_cycles,"hidden_order_confirmed":False}
