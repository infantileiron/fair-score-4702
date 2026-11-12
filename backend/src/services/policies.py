import uuid
from fastapi import HTTPException
from sqlalchemy import select
from src.models import ScorePolicy
from src.services.datasets import require
from src.utils.serialization import serialize
from src.utils.time import now
def create(db,payload):
 dataset=require(db,payload.dataset_id)
 if db.scalar(select(ScorePolicy).where(ScorePolicy.name==payload.name)): raise HTTPException(409,"方案名称已存在")
 if payload.quota is not None and payload.quota>len(dataset.rows):
  raise HTTPException(422,"名额不能超过数据集样本量")
 item=ScorePolicy(id=str(uuid.uuid4()),created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
