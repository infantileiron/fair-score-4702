"""端到端集成验证：SQLite + 桩 Redis，跑通两种口径的完整工作流。

运行：PYTHONPATH=/tmp/pylibbs python3 verify_integration.py
"""
import os,sys,types,tempfile
# 隔离环境与数据库
_tmp=tempfile.mkdtemp()
os.environ["DATABASE_URL"]=f"sqlite:///{_tmp}/fair.db"
os.environ["REDIS_URL"]="redis://stub:6379/0"
os.environ["SEED_DEMO"]="false"
os.environ.setdefault("JWT_SECRET","test-secret")
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","backend"))

# 桩 Redis：记录队列，worker.brpop 同步取任务
class StubRedis:
 def __init__(self): self.q=[]
 def lpush(self,k,v): self.q.insert(0,v if isinstance(v,str) else v.decode())
 def brpop(self,k,timeout=1): return (k,self.q.pop().encode()) if self.q else None
 def ping(self): return True
stub=StubRedis()
import redis as _redis
redis_mod=sys.modules["redis"]
_orig_from_url=_redis.Redis.from_url
redis_mod.Redis.from_url=staticmethod(lambda *a,**k:stub)

from fastapi.testclient import TestClient
from src.config.database import Base,engine,Session
from src.models import User,CandidateDataset,ScorePolicy
from src.utils.security import hash_password
from src.utils.time import now
from src.main import app,upgrade_schema

# 1) 模拟“历史库”：先建不含 quota 列的旧表，再验证在线升级
Base.metadata.create_all(engine)
import src.worker as worker_mod
with engine.begin() as conn:
 cols=[r[1] for r in conn.exec_driver_sql("PRAGMA table_info(score_policies)").fetchall()]
assert "quota" in cols, "新建库应直接含 quota 列"
# 制造旧库场景：删列（SQLite 需重建表），再跑升级
with engine.begin() as conn:
 conn.exec_driver_sql("CREATE TABLE sp_old AS SELECT id,name,threshold,dataset_id,max_gap,created_at FROM score_policies")
 conn.exec_driver_sql("DROP TABLE score_policies")
 conn.exec_driver_sql("ALTER TABLE sp_old RENAME TO score_policies")
 cols=[r[1] for r in conn.exec_driver_sql("PRAGMA table_info(score_policies)").fetchall()]
assert "quota" not in cols
upgrade_schema()  # 历史数据升级
with engine.begin() as conn:
 cols=[r[1] for r in conn.exec_driver_sql("PRAGMA table_info(score_policies)").fetchall()]
assert "quota" in cols, "升级后应补齐 quota 列，旧数据为 NULL"
print("历史库在线升级 OK，旧方案 quota =", end=" ")

# 基础数据
with Session() as db:
 db.add(User(id="admin",email="admin@hengchi.demo",password=hash_password("Review2026!"),role="admin"))
 db.add(User(id="analyst",email="analyst@hengchi.demo",password=hash_password("Review2026!"),role="analyst"))
 db.commit()
 # 三组同分样本（27 行）
 scores={"评估组甲":[95,90,88,70,70,60,55,50],
  "评估组乙":[92,85,70,70,70,65,58,52,48],
  "评估组丙":[89,82,75,70,70,70,68,60,55,45]}
 rows=[];idx=0
 for g,vs in scores.items():
  for s in vs:
   idx+=1;rows.append({"candidate_id":f"HQ-{idx:03}","group":g,"score":s,"qualified":1 if s>=70 else 0})
 ds=CandidateDataset(id="qdata",name="三组同分边界样本",source="tie.json",rows=rows,created_at=now())
 db.add(ds);db.commit()

client=TestClient(app)
# 登录
r=client.post("/auth/login",json={"email":"analyst@hengchi.demo","password":"Review2026!"})
assert r.status_code==200,r.text
token=r.json()["token"]; H={"Authorization":f"Bearer {token}"}

# 2) 创建固定名额方案
r=client.post("/policies",headers=H,json={"name":"名额12复核","dataset_id":"qdata","threshold":0,"max_gap":0.1,"quota":12})
assert r.status_code==200,r.text
policy=r.json(); assert policy["quota"]==12
# 名额超样本量应被拒
r=client.post("/policies",headers=H,json={"name":"超额","dataset_id":"qdata","threshold":0,"max_gap":0.1,"quota":999})
assert r.status_code==422,r.text
# 旧分数线模式仍可用（不传 quota）
r=client.post("/policies",headers=H,json={"name":"分数线70","dataset_id":"qdata","threshold":70,"max_gap":0.1})
assert r.status_code==200 and r.json()["quota"] is None
print("方案创建（两种口径 + 校验）OK")

# 3) 运行固定名额复核，worker 同步消费
r=client.post("/runs",headers=H,json={"policy_id":policy["id"]})
assert r.status_code==200,r.text
run_id=r.json()["id"]
worker_mod.execute(run_id)
r=client.get(f"/runs/{run_id}",headers=H); result=r.json()
assert r.json()["status"]=="completed",r.json()
res=result["result"]
assert res["mode"]=="quota" and res["quota"]==12 and res["cutoff_score"]==70
b=res["quota_boundary"]
assert b["tie_total"]==8 and b["tie_to_pick"]==4
# 端点见证必须恰好录满
for ep in ("gap_min","gap_max"):
 assert sum(b[ep]["selected"].values())==12
assert abs(b["gap_min"]["value"]-0.1)<1e-9 and abs(b["gap_max"]["value"]-0.4027777777777778)<1e-12
# 与全枚举结论一致的关键边界
gb={x["group"]:x for x in b["group_bounds"]}
assert (gb["评估组甲"]["selected_min"],gb["评估组甲"]["selected_max"])==(3,5)
assert (gb["评估组乙"]["selected_min"],gb["评估组乙"]["selected_max"])==(2,5)
assert (gb["评估组丙"]["selected_min"],gb["评估组丙"]["selected_max"])==(3,6)
print("固定名额运行结果 OK：差距范围 [%.4f, %.4f]"%(b["gap_min"]["value"],b["gap_max"]["value"]))

# 4) 分数线模式运行，确认旧口径不受影响
tp=[p for p in client.get("/policies",headers=H).json() if p["name"]=="分数线70"][0]
r=client.post("/runs",headers=H,json={"policy_id":tp["id"]}); trun=r.json()["id"]
worker_mod.execute(trun)
tres=client.get(f"/runs/{trun}",headers=H).json()["result"]
assert tres["mode"]=="threshold" and "quota_boundary" not in tres and tres["threshold"]==70
assert len(tres["frontier"])==21 and tres["accuracy"] is not None
# 名额模式也保留前沿，供按原分数线复核讨论
assert len(res["frontier"])==21
print("分数线模式兼容 OK")

# 5) 人工复核 + 管理员归档 + CSV 依据导出
r=client.post("/reviews",headers=H,json={"run_id":run_id,"decision":"accepted",
 "note":"边界70分有8人同分仅任选4人，结论以可达区间与录满见证为准，样本量有限。"})
assert r.status_code==200,r.text
ra=client.post("/auth/login",json={"email":"admin@hengchi.demo","password":"Review2026!"}).json()["token"]
HA={"Authorization":f"Bearer {ra}"}
r=client.post("/reports",headers=HA,json={"run_id":run_id,"title":"固定名额归档·三组同分"})
assert r.status_code==200,r.text
report_id=r.json()["id"]
r=client.get(f"/reports/{report_id}/csv",headers=H)
assert r.status_code==200
csv_text=r.content.decode("utf-8-sig")
for needle in ("固定名额","边界分数线,70","边界同分需任选人数,4","可达最小差距","可达最大差距","见证合计,12","入选率下限","tp_min"):
 assert needle in csv_text,needle
# 重复归档被拒
assert client.post("/reports",headers=HA,json={"run_id":run_id,"title":"重复"}).status_code==409
print("归档 CSV 保留取舍依据 OK")

# 6) 分数线模式归档导出仍是旧表头
r=client.post("/reviews",headers=H,json={"run_id":trun,"decision":"accepted","note":"旧分数线口径复核留痕，至少八个字。"})
assert r.status_code==200
r=client.post("/reports",headers=HA,json={"run_id":trun,"title":"分数线归档"})
rid2=r.json()["id"]
old_csv=client.get(f"/reports/{rid2}/csv",headers=H).content.decode("utf-8-sig")
assert old_csv.splitlines()[0]=="group,n,selected,qualified,tp,fp,fn,tn,selection_rate,tpr,fpr"
print("旧口径 CSV 表头不变 OK")
print("\n全部端到端集成验证通过")
