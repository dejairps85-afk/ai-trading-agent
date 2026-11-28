"""Conservative catalog assembly from decoded definition records."""
from .umdf_catalog import Catalog, Instrument

class CatalogBuilder:
    def __init__(self):
        self.catalog=Catalog()
        self.total=None
        self.count=0
        self._seen=set()
        self.complete=False

    def ingest(self,message):
        try:
            if self.complete or not self.catalog.valid:
                raise ValueError("Catalog closed or invalid")
            total=message["TotNoRelatedSym"]
            entries=message["RelatedSym"]
            last=message["LastFragment"]
            if type(total) is not int or total<=0 or last not in ("Y","N"):
                raise ValueError("Invalid fragment metadata")
            if self.total is not None and self.total!=total:
                raise ValueError("Inconsistent total")
            self.total=total
            for entry in entries:
                security_id=entry["SecurityID"]
                if type(security_id) is not int or security_id in self._seen:
                    raise ValueError("Duplicate or invalid security ID")
                self.catalog.add(Instrument(security_id,entry["Symbol"]))
                self._seen.add(security_id)
                self.count+=1
            if self.count>total or (last=="Y")!=(self.count==total):
                raise ValueError("Inconsistent fragment count")
            self.complete=last=="Y"
        except Exception:
            self.catalog.valid=False
            self.complete=False
            raise

    def resolve(self,security_id):
        if not self.complete or not self.catalog.valid:
            raise RuntimeError("Catalog not ready")
        return self.catalog.resolve(security_id)
