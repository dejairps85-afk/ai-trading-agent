"""Research-only rolling evaluation; no model fitting or approval."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Fold:
    train: tuple
    test: tuple
    test_start: int
    test_end: int

def walk_forward(rows, *, start_ns, stop_ns, train_ns, test_ns, embargo_ns=0, max_folds=1000):
    values=(start_ns,stop_ns,train_ns,test_ns,embargo_ns,max_folds)
    if any(type(v) is not int for v in values) or not 0<=start_ns<stop_ns or min(train_ns,test_ns,max_folds)<=0 or embargo_ns<0:
        raise ValueError("Invalid fold parameters")
    rows=tuple(rows)
    seen=set()
    for r in rows:
        a,b,c=(r[k] for k in ("start_ns","end_ns","label_end_ns"))
        if any(type(v) is not int for v in (a,b,c)) or not 0<=a<b<=c:
            raise ValueError("Invalid label horizon")
        key=(r["symbol"],a,b)
        if key in seen:
            raise ValueError("Duplicate observation")
        seen.add(key)
    rows=sorted(rows,key=lambda r:(r["start_ns"],r["symbol"],r["end_ns"]))
    boundary=start_ns+train_ns+embargo_ns
    count=(stop_ns-boundary)//test_ns
    if not 0<count<=max_folds:
        raise ValueError("Invalid fold count")
    folds=[]
    for i in range(count):
        a=boundary+i*test_ns
        b=a+test_ns
        train=tuple(r for r in rows if a-embargo_ns-train_ns<=r["start_ns"] and r["label_end_ns"]<=a-embargo_ns)
        test=tuple(r for r in rows if a<=r["start_ns"] and r["label_end_ns"]<=b)
        if not train or not test:
            raise ValueError("Empty fold")
        folds.append(Fold(train,test,a,b))
    return tuple(folds)
