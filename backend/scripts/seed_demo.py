import random,json
from sqlalchemy import select,func
from src.config.database import Base,engine,Session
from src.models import User,CandidateDataset,ScorePolicy,AuditRun,GroupReview,AuditReport
from src.utils.security import hash_password
from src.utils.time import now
from src.services.analysis import analyze
def quota_demo_rows():
 # 三组在边界分70同分（甲2/乙3/丙3，共8人），名额12时边界任选4人
 scores={"评估组甲":[95,90,88,70,70,60,55,50],
  "评估组乙":[92,85,70,70,70,65,58,52,48],
  "评估组丙":[89,82,75,70,70,70,68,60,55,45]}
 rows=[];idx=0
 for group,values in scores.items():
  for score in values:
   idx+=1
   rows.append({"candidate_id":f"HQ-{idx:03}","group":group,"score":score,
    "qualified":1 if score>=70 else 0})
 return rows
def seed():
 Base.metadata.create_all(engine)
 with Session() as db:
  for role in ("admin","analyst","viewer"):
   if not db.get(User,role): db.add(User(id=role,email=role+"@hengchi.demo",password=hash_password("Review2026!"),role=role))
  rng=random.Random(2203)
  observations=[]
  for i in range(800):
   group="评估组A" if i%2==0 else "评估组B"
   skill=rng.gauss(66,15);score=max(0,min(100,skill+rng.gauss(0,9)-(5 if group=="评估组B" else 0)))
   observations.append({"candidate_id":f"HC-{i+1:04}","group":group,"score":round(score,2),"qualified":int(skill>=63)})
  if not db.get(CandidateDataset,"demo-data"): db.add(CandidateDataset(id="demo-data",name="2026秋季统一测评·匿名样本",source="hengchi_candidates_202611.json",rows=observations,created_at=now()));db.flush()
  if not db.get(ScorePolicy,"demo-policy"): db.add(ScorePolicy(id="demo-policy",name="统一分数线65·回顾性复核",threshold=65,dataset_id="demo-data",max_gap=0.1,quota=None,created_at=now()));db.flush()
  if not db.get(AuditRun,"demo-run"): db.add(AuditRun(id="demo-run",policy_id="demo-policy",status="completed",result=analyze(observations,65,0.1),error="",created_at=now()));db.flush()
  if not db.get(GroupReview,"demo-review"): db.add(GroupReview(id="demo-review",run_id="demo-run",note="标签取自统一测评，已记录组间样本分母。下一轮核验标签偏差，不用于自动招聘决策。",decision="accepted",author="analyst@hengchi.demo",created_at=now()));db.flush()
  if not db.get(AuditReport,"demo-report"): db.add(AuditReport(id="demo-report",run_id="demo-run",title="秋季筛选·回顾性公平复核",published_by="admin@hengchi.demo",created_at=now()))
  # 固定名额复核演示：三组同分争抢剩余名额
  quota_rows=quota_demo_rows()
  if not db.get(CandidateDataset,"quota-data"): db.add(CandidateDataset(id="quota-data",name="固定名额·三组同分边界样本",source="hengchi_quota_tie_demo.json",rows=quota_rows,created_at=now()));db.flush()
  if not db.get(ScorePolicy,"quota-policy"): db.add(ScorePolicy(id="quota-policy",name="固定名额12·边界同分别强定",threshold=0,dataset_id="quota-data",max_gap=0.1,quota=12,created_at=now()));db.flush()
  if not db.get(AuditRun,"quota-run"): db.add(AuditRun(id="quota-run",policy_id="quota-policy",status="completed",result=analyze(quota_rows,0,0.1,12),error="",created_at=now()));db.flush()
  db.commit()
  return {m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in (User,CandidateDataset,ScorePolicy,AuditRun,GroupReview,AuditReport)}
if __name__=="__main__": print(json.dumps(seed(),ensure_ascii=False))
