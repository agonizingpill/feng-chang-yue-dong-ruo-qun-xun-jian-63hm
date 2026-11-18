from datetime import datetime
from sqlalchemy import String,ForeignKey,JSON,CheckConstraint,DateTime,func
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class ColonyMerge(Base):
    __tablename__='colony_merges'
    __table_args__=(CheckConstraint('donor_hive_id<>recipient_hive_id'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str|None]=mapped_column(String(50),unique=True,nullable=True)
    donor_hive_id:Mapped[int]=mapped_column(ForeignKey('hives.id'))
    recipient_hive_id:Mapped[int]=mapped_column(ForeignKey('hives.id'))
    request_key:Mapped[str]=mapped_column(String(80),unique=True)
    reason:Mapped[str]=mapped_column(String(400))
    state:Mapped[str]=mapped_column(String(24),default='requested')
    donor_snapshot:Mapped[dict]=mapped_column(JSON)
    recipient_snapshot:Mapped[dict]=mapped_column(JSON)
    provenance:Mapped[dict]=mapped_column(JSON,default=dict)
    merged_visit_id:Mapped[int|None]=mapped_column(ForeignKey('visits.id'),nullable=True)
    requested_by:Mapped[str]=mapped_column(String(120))
    approved_by:Mapped[str]=mapped_column(String(120),default='')
    merged_by:Mapped[str]=mapped_column(String(120),default='')
    cancelled_by:Mapped[str]=mapped_column(String(120),default='')
    cancel_reason:Mapped[str]=mapped_column(String(400),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
    approved_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    merged_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    cancelled_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
