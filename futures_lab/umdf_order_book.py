"""Normalized offline MBO book; wire mapping is not yet validated."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Order:
    order_id: int
    side: str
    ticks: int
    quantity: int

class OrderBook:
    def __init__(self,max_orders=100000):
        if type(max_orders) is not int or max_orders<=0:
            raise ValueError("Invalid capacity")
        self.max_orders=max_orders
        self.valid=False
        self._orders={}

    @staticmethod
    def _validate(order):
        if not isinstance(order,Order) or order.side not in ("buy","sell") or any(type(v) is not int or v<=0 for v in (order.order_id,order.ticks,order.quantity)):
            raise ValueError("Invalid order")

    def initialize(self,orders):
        self.valid=False
        pending={}
        for order in orders:
            self._validate(order)
            if order.order_id in pending or len(pending)>=self.max_orders:
                raise ValueError("Duplicate order or capacity exceeded")
            pending[order.order_id]=order
        self._orders=pending
        self.valid=True

    def apply(self,updates):
        if not self.valid:
            raise RuntimeError("Snapshot required")
        pending=self._orders.copy()
        try:
            for action,order in updates:
                self._validate(order)
                exists=order.order_id in pending
                if action=="add" and not exists:
                    pending[order.order_id]=order
                elif action=="change" and exists and pending[order.order_id].side==order.side:
                    pending[order.order_id]=order
                elif action=="delete" and exists and pending[order.order_id]==order:
                    del pending[order.order_id]
                else:
                    raise ValueError("Invalid order transition")
                if len(pending)>self.max_orders:
                    raise ValueError("Capacity exceeded")
        except Exception:
            self.valid=False
            raise
        self._orders=pending

    def levels(self,side):
        if not self.valid:
            raise RuntimeError("Book invalid")
        if side not in ("buy","sell"):
            raise ValueError("Invalid side")
        totals={}
        for order in self._orders.values():
            if order.side==side:
                totals[order.ticks]=totals.get(order.ticks,0)+order.quantity
        return tuple(sorted(totals.items(),reverse=side=="buy"))
