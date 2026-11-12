import uuid,csv,io
from fastapi import HTTPException
from sqlalchemy import select
from src.models import AuditReport,GroupReview
from src.services.runs import require_completed
from src.utils.time import now
from src.utils.serialization import serialize
def create(db,payload,user):
 require_completed(db,payload.run_id)
 reviews=list(db.scalars(select(GroupReview).where(GroupReview.run_id==payload.run_id).order_by(GroupReview.created_at.desc())))
 if not reviews or reviews[0].decision!="accepted": raise HTTPException(409,"最新复核须为接受后才能归档")
 if db.scalar(select(AuditReport).where(AuditReport.run_id==payload.run_id)): raise HTTPException(409,"本次计算已归档")
 item=AuditReport(id=str(uuid.uuid4()),published_by=user["email"],created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
def export(db,id):
 report=db.get(AuditReport,id)
 if not report: raise HTTPException(404,"归档报告不存在")
 run=require_completed(db,report.run_id)
 result=run.result
 buf=io.StringIO()
 if result.get("mode")=="quota":
  _export_quota(buf,result)
 else:
  _export_threshold(buf,result)
 return "\ufeff"+buf.getvalue()
def _export_threshold(buf,result):
 cols=["group","n","selected","qualified","tp","fp","fn","tn","selection_rate","tpr","fpr"]
 writer=csv.DictWriter(buf,cols,extrasaction="ignore");writer.writeheader();writer.writerows(result["groups"])
def _export_quota(buf,result):
 b=result["quota_boundary"]
 writer=csv.writer(buf)
 # 口径与边界依据
 writer.writerow(["复核口径","固定名额"])
 writer.writerow(["名额",b["quota"]])
 writer.writerow(["边界分数线",b["cutoff_score"]])
 writer.writerow(["边界同分人数",b["tie_total"]])
 writer.writerow(["边界同分需任选人数",b["tie_to_pick"]])
 writer.writerow(["是否存在同分争议","否" if b["deterministic"] else "是"])
 writer.writerow(["样本校验码",result["checksum"]])
 writer.writerow([])
 # 各组入选率可达范围及人数依据
 writer.writerow(["group","n","必录(高于边界)","边界同分","入选人数下限","入选人数上限",
  "入选率下限","入选率上限"])
 for g in b["group_bounds"]:
  writer.writerow([g["group"],g["n"],g["above_cut"],g["at_cut"],g["selected_min"],
   g["selected_max"],g["selection_rate_min"],g["selection_rate_max"]])
 writer.writerow([])
 # 全组差距两个端点，各附能恰好录满名额的分组人数
 for key,label in (("gap_min","可达最小差距"),("gap_max","可达最大差距")):
  node=b[key]
  writer.writerow([label,node["value"]])
  writer.writerow(["group","见证分组入选人数","见证入选率"])
  for g,count in node["selected"].items():
   writer.writerow([g,count,node["selection_rates"][g]])
  writer.writerow(["见证合计",sum(node["selected"].values()),"须等于名额"])
  writer.writerow([])
 # 标签口径（TP 可达区间，最小差距见证）
 writer.writerow(["标签口径(边界分数线复核)"])
 cols=["group","n","selected","qualified","tp_min","tp_max","fp","fn","tn","selection_rate","tpr","fpr"]
 dict_writer=csv.DictWriter(buf,cols,extrasaction="ignore");dict_writer.writeheader()
 dict_writer.writerows(result["groups"])
