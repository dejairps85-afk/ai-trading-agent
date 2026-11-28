"""Experimental flow aggregation over decoded messages, not a verified feed."""
from .umdf_trade_pipeline import TradePipeline
from .umdf_flow import aggregate_flow

def measure_decoded_flow(messages, *, trade_type, new_action, tick_sizes,
                         side_field, side_mapping, max_messages=100000):
    if not isinstance(side_field,str) or not side_field or type(max_messages) is not int or max_messages<=0:
        raise ValueError("Invalid configuration")
    pipeline=TradePipeline(trade_type=trade_type,new_action=new_action,tick_sizes=tick_sizes)
    records=[]
    sides={}
    for index,(sequence,tid,message) in enumerate(messages):
        if index>=max_messages:
            raise ValueError("Message limit exceeded")
        trades=pipeline.ingest(sequence,tid,message)
        if tid in (81,158):
            for entry in message["MDEntries"]:
                if entry.get("MDEntryType")==trade_type and entry.get("MDUpdateAction")==new_action:
                    key=(entry["SecurityID"],entry["TradeID"])
                    side=entry.get(side_field)
                    if key in sides and sides[key]!=side:
                        raise ValueError("Conflicting aggression classification")
                    sides[key]=side
            records.extend((trade,sides[(trade.security_id,trade.trade_id)]) for trade in trades)
    if not pipeline.builder.complete:
        raise ValueError("Incomplete catalog")
    return aggregate_flow(records,side_mapping=side_mapping)
