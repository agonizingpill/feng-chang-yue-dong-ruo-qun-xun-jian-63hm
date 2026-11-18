import uuid
from pydantic import BaseModel,ConfigDict,Field
class Input(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
class MergeRequestInput(Input):
    donor_hive_id:int
    recipient_hive_id:int
    reason:str=Field(min_length=5,max_length=400)
    request_key:str=Field(min_length=8,max_length=80,default_factory=lambda:uuid.uuid4().hex)
class MergeCompleteInput(Input):
    code:str=Field(min_length=1,max_length=50)
    weight_kg:float=Field(gt=0,le=100)
    temperature:float=Field(ge=-10,le=50)
    activity:float=Field(ge=0,le=500)
    feed_left:float=Field(ge=0,le=20)
    queen_seen:bool=True
    colony_frames:int=Field(ge=0,le=20)
class MergeCancelInput(Input):
    reason:str=Field(min_length=5,max_length=400)
