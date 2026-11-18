from datetime import datetime
from sqlalchemy import select
from fastapi import HTTPException
from .constants import ACTIVE_MERGE_STATES
from .models import Hive,Visit,CareAction
from .merge_models import ColonyMerge
from .yard_service import require,audit,latest

def active_merge(db,hive_id):
    return db.scalar(select(ColonyMerge).where(ColonyMerge.state.in_(ACTIVE_MERGE_STATES),
        (ColonyMerge.donor_hive_id==hive_id)|(ColonyMerge.recipient_hive_id==hive_id)))

def ensure_not_frozen(db,hive_id,label='该蜂箱'):
    row=active_merge(db,hive_id)
    if row:raise HTTPException(409,f'{label}存在未完成并群单（MG-{row.id}），两箱业务已冻结，请先完成或撤销并群')

def ensure_in_play(db,hive_id,label='该蜂箱'):
    hive=db.get(Hive,hive_id)
    if hive and hive.care_state=='retired':raise HTTPException(409,f'{label}已退役并群，不能再办理业务')
    ensure_not_frozen(db,hive_id,label)
    return hive

def _lock_pair(db,a_id,b_id):
    first,second=sorted((a_id,b_id))
    donor=db.scalar(select(Hive).where(Hive.id==first).with_for_update())
    other=db.scalar(select(Hive).where(Hive.id==second).with_for_update())
    return (donor,other) if donor.id==a_id else (other,donor)

def _hive_snapshot(db,h):
    lid=latest(db,h.id)
    v=db.get(Visit,lid) if lid else None
    return {'hive_id':h.id,'hive_code':h.code,'site':h.site,'queen_present':h.queen_present,
            'frames':h.colony_frames,'care_state':h.care_state,
            'latest_visit_id':v.id if v else None,'latest_visit_code':v.code if v else None,
            'latest_visit_status':v.status if v else None,'weight_kg':v.weight_kg if v else None,
            'anomaly_score':v.anomaly_score if v else None}

def _open_care(db,hive_id):
    return db.scalar(select(CareAction.id).join(Visit,CareAction.visit_id==Visit.id)
        .where(Visit.hive_id==hive_id,CareAction.status.in_(['planned','executed','rechecked'])))

def _inflight_screen(db,hive_id):
    lid=latest(db,hive_id)
    if not lid:return False
    v=db.get(Visit,lid)
    return v is not None and v.status=='screening'

def _inflight_move(db,hive_id):
    from .season_models import ApiaryMove
    return db.scalar(select(ApiaryMove.id).where(ApiaryMove.hive_id==hive_id,ApiaryMove.state.in_(['requested','approved'])))

def _verify_pair(db,donor,recipient,exclude_id=None):
    if donor.id==recipient.id:raise HTTPException(409,'供群与受群必须是两只不同蜂箱')
    if donor.site!=recipient.site:raise HTTPException(409,'并群仅限同场蜂箱，供群与受群场址不一致')
    for h,label in [(donor,'供群'),(recipient,'受群')]:
        if h.care_state=='retired':raise HTTPException(409,f'{label}{h.code}已退役，不能再次并群')
        other=active_merge(db,h.id)
        if other and other.id!=exclude_id:raise HTTPException(409,f'{label}{h.code}已有未完成并群单，不能重复申请')
        if _open_care(db,h.id):raise HTTPException(409,f'{label}{h.code}有未结处置，请先闭环或取消')
        if _inflight_move(db,h.id):raise HTTPException(409,f'{label}{h.code}有在途转场，请先完成或取消转场')
        if _inflight_screen(db,h.id):raise HTTPException(409,f'{label}{h.code}有待算筛查，请等筛查结果出来后再申请')
    if donor.queen_present:raise HTTPException(409,'供群必须是无王群，有王群不能并入他箱')
    if not recipient.queen_present:raise HTTPException(409,'受群必须是有王群，无王箱不能承接并群')

def request_merge(db,body,user):
    existing=db.scalar(select(ColonyMerge).where(ColonyMerge.request_key==body.request_key))
    if existing:return existing
    donor,recipient=_lock_pair(db,body.donor_hive_id,body.recipient_hive_id)
    if not donor or not recipient:raise HTTPException(404,'蜂场记录不存在')
    _verify_pair(db,donor,recipient)
    row=ColonyMerge(donor_hive_id=donor.id,recipient_hive_id=recipient.id,request_key=body.request_key,
        reason=body.reason.strip(),state='requested',requested_by=user.email,
        donor_snapshot=_hive_snapshot(db,donor),recipient_snapshot=_hive_snapshot(db,recipient))
    db.add(row);db.flush();row.code=f'MG-{row.id:04}'
    audit(db,user,f'申请并群 {donor.code}（无王供群）并入 {recipient.code}（有王受群），两箱业务冻结')
    db.commit();return row

def approve(db,key,user):
    row=require(db,ColonyMerge,key)
    donor,recipient=_lock_pair(db,row.donor_hive_id,row.recipient_hive_id)
    row=require(db,ColonyMerge,key,True)
    if row.state!='requested':raise HTTPException(409,'仅待批准的并群申请可以签发')
    _verify_pair(db,donor,recipient,exclude_id=row.id)
    row.state='approved';row.approved_by=user.email;row.approved_at=datetime.utcnow()
    audit(db,user,f'主管批准并群单 {row.code}，等待蜂师填报合并实测读数')
    db.commit();return row

def complete(db,key,body,user):
    row=require(db,ColonyMerge,key)
    donor,recipient=_lock_pair(db,row.donor_hive_id,row.recipient_hive_id)
    row=require(db,ColonyMerge,key,True)
    if row.state=='merged':
        existing=db.get(Visit,row.merged_visit_id)
        if existing and existing.code==body.code:return row
        raise HTTPException(409,'并群单已完成，回执以原单为准，不能重复生成合并巡检')
    if row.state!='approved':raise HTTPException(409,'须主管批准后才能填报合并读数')
    if not body.queen_seen:raise HTTPException(409,'合并后实测必须见王（受群原有蜂王），未见王不能完成并群')
    if not recipient.queen_present:raise HTTPException(409,'受群王况已变化为无王，不能承接并群，请撤销后重新安排')
    if db.scalar(select(Visit).where(Visit.code==body.code)):raise HTTPException(409,'巡检编号已存在，请使用原回执编号重试')
    donor_snapshot=_hive_snapshot(db,donor);recipient_snapshot=_hive_snapshot(db,recipient)
    visit=Visit(code=body.code,hive_id=recipient.id,weight_kg=body.weight_kg,temperature=body.temperature,
        activity=body.activity,feed_left=body.feed_left,queen_seen=True,colony_frames=body.colony_frames,status='recorded')
    db.add(visit);db.flush()
    provenance={'merge_id':row.id,'merge_code':row.code,'donor_hive_id':donor.id,'donor_hive_code':donor.code,
        'recipient_hive_id':recipient.id,'recipient_hive_code':recipient.code,
        'donor_final_snapshot':donor_snapshot,'recipient_pre_merge_snapshot':recipient_snapshot,
        'old_scores_trace_only':True,'note':'供群旧分值仅供追溯；合并新读数按原算法筛查后才可建处置'}
    visit.model_evidence={'merge_provenance':provenance}
    donor.care_state='retired'
    recipient.queen_present=True;recipient.colony_frames=body.colony_frames;recipient.care_state='observe'
    row.state='merged';row.merged_by=user.email;row.merged_at=datetime.utcnow();row.merged_visit_id=visit.id
    row.donor_snapshot=donor_snapshot;row.recipient_snapshot=recipient_snapshot;row.provenance=provenance
    audit(db,user,f'完成并群 {row.code}：{donor.code}退役并入{recipient.code}，合并巡检{visit.code} {body.weight_kg}kg待筛查')
    db.commit();return row

def cancel(db,key,body,user):
    row=require(db,ColonyMerge,key,True)
    if row.state not in ACTIVE_MERGE_STATES:raise HTTPException(409,'并群单已完成或已撤销，不能重复操作')
    row.state='cancelled';row.cancelled_by=user.email;row.cancelled_at=datetime.utcnow();row.cancel_reason=body.reason.strip()
    audit(db,user,f'撤销并群单 {row.code}，解除两箱业务冻结，依据：{body.reason.strip()}')
    db.commit();return row
