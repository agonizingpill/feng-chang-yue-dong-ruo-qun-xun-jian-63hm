from enum import StrEnum
class Role(StrEnum):
    ADMIN='admin'
    BEEKEEPER='beekeeper'
    VIEWER='viewer'
class CareKind(StrEnum):
    FEED='feed'
    REQUEEN='requeen'
class CareState(StrEnum):
    PLANNED='planned'
    EXECUTED='executed'
    RECHECKED='rechecked'
    NEEDS_REQUEEN='needs_requeen'
    CLOSED='closed'
    CANCELLED='cancelled'
class VisitState(StrEnum):
    RECORDED='recorded'
    SCREENING='screening'
    SCREENED='screened'
    CARING='caring'
    FOLLOWUP='followup'
    NEEDS_REQUEEN='needs_requeen'
    CLOSED='closed'
    STALE='stale'
    BLOCKED='blocked'
class MergeState(StrEnum):
    REQUESTED='requested'
    APPROVED='approved'
    MERGED='merged'
    CANCELLED='cancelled'
ACTIVE_MERGE_STATES=['requested','approved']
FINISHED_MERGE_STATES=['merged','cancelled']
