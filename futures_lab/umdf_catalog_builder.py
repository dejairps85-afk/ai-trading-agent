"""Conservative catalog assembly from decoded definition records."""
from .umdf_catalog import Catalog, Instrument

class CatalogBuilder:
    def __init__(self):
        self.catalog=Catalog()
        self.total=None
        self.count=0
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
                self.catalog.add(Instrument(entry["SecurityID"],entry["Symbol"]))
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
