from fastapi import APIRouter,Depends
from sqlalchemy import select
from .database import session
from .auth import current,editor,admin
from .merge_models import ColonyMerge
from .merge_schemas import MergeRequestInput,MergeCompleteInput,MergeCancelInput
from . import merge_service
router=APIRouter()
@router.get('/colony-merges')
def merges(user=Depends(current),db=Depends(session)):
    return db.scalars(select(ColonyMerge).order_by(ColonyMerge.id.desc())).all()
@router.post('/colony-merges')
def request_merge(body:MergeRequestInput,user=Depends(editor),db=Depends(session)):
    return merge_service.request_merge(db,body,user)
@router.post('/colony-merges/{key}/approve')
def approve(key:int,user=Depends(admin),db=Depends(session)):
    return merge_service.approve(db,key,user)
@router.post('/colony-merges/{key}/complete')
def complete(key:int,body:MergeCompleteInput,user=Depends(editor),db=Depends(session)):
    return merge_service.complete(db,key,body,user)
@router.post('/colony-merges/{key}/cancel')
def cancel(key:int,body:MergeCancelInput,user=Depends(editor),db=Depends(session)):
    return merge_service.cancel(db,key,body,user)
