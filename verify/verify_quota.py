"""固定名额复核算法的独立验证脚本（标准库，无外部依赖）。

运行：python3 -I verify_quota.py

验证内容：
1. 三组同分争抢剩余名额样本：区间、边界口径、端点见证可恰好录满；
2. 随机小规模实例上，与全枚举（笛卡尔积所有分组录取人数）对比
   入选率区间、最小/最大差距及端点见证，确保极值真实可达且无遗漏；
3. 确定性边界（无同分或全部录取）时区间退化为单点。
"""
import itertools,random,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","backend"))
from src.services.quota import quota_boundary

def brute_force(rows,quota):
 groups=sorted({r["group"] for r in rows})
 n={g:sum(1 for r in rows if r["group"]==g) for g in groups}
 ordered=sorted(rows,key=lambda r:(-r["score"],r["candidate_id"]))
 cutoff=ordered[quota-1]["score"]
 above={g:0 for g in groups};tie={g:0 for g in groups}
 for r in rows:
  if r["score"]>cutoff:above[r["group"]]+=1
  elif r["score"]==cutoff:tie[r["group"]]+=1
 a=sum(above.values());need=quota-a
 los=[above[g]+max(0,need-(sum(tie.values())-tie[g])) for g in groups]
 his=[above[g]+min(tie[g],need) for g in groups]
 feasible=[]
 for combo in itertools.product(*[range(los[i],his[i]+1) for i in range(len(groups))]):
  if sum(combo)!=quota:continue
  rates=[combo[i]/n[groups[i]] for i in range(len(groups))]
  feasible.append((combo,max(rates)-min(rates)))
 gmin=min(d for _,d in feasible);gmax=max(d for _,d in feasible)
 return groups,n,los,his,gmin,gmax,feasible

def check_instance(rows,quota,label):
 res=quota_boundary(rows,quota)
 groups,n,los,his,gmin,gmax,feasible=brute_force(rows,quota)
 gb={b["group"]:b for b in res["group_bounds"]}
 for i,g in enumerate(groups):
  assert gb[g]["selected_min"]==los[i],(label,"min",g)
  assert gb[g]["selected_max"]==his[i],(label,"max",g)
 # 端点见证必须是恰好录满的可行分配
 for key in ("gap_min","gap_max"):
  w=res[key]["selected"]
  assert set(w)==set(groups),(label,key,"groups")
  assert sum(w.values())==quota,(label,key,"sum")
  for i,g in enumerate(groups):
   assert los[i]<=w[g]<=his[i],(label,key,"range",g)
 rates=[w[g]/n[g] for g in groups]
 assert abs((max(rates)-min(rates))-res[key]["value"])<1e-12,(label,key,"value")
 assert abs(res[key]["value"]-(gmin if key=="gap_min" else gmax))<1e-12,(label,key,"extremum")
 assert abs(res["gap_min"]["value"]-gmin)<1e-12 and abs(res["gap_max"]["value"]-gmax)<1e-12
 return res

def test_three_group_tie_sample():
 # 三组在边界分 70 上同分（甲2/乙3/丙3，共8人），必录8人后争抢最后 4 个名额
 rows=[];cid=0
 def add(group,scores):
  nonlocal cid
  for s in scores:
   cid+=1;rows.append({"candidate_id":f"C{cid:03d}","group":group,"score":s,"qualified":0})
 add("甲组",[95,90,88,70,70,60,55,50])          # n=8, 必录3 边界同分2
 add("乙组",[92,85,70,70,70,65,58,52,48])       # n=9, 必录2 边界同分3
 add("丙组",[89,82,75,70,70,70,68,60,55,45])    # n=10, 必录3 边界同分3
 quota=12
 res=check_instance(rows,quota,"three-group-tie")
 # 必录 8 人（>70），边界 70 共 8 人，任选 4
 assert res["cutoff_score"]==70
 assert res["tie_to_pick"]==4 and res["tie_total"]==8
 assert not res["deterministic"]
 gb={b["group"]:b for b in res["group_bounds"]}
 # 甲: above=3, tie=2 -> lo=3+max(0,4-(8-2))=3, hi=3+min(2,4)=5
 assert (gb["甲组"]["selected_min"],gb["甲组"]["selected_max"])==(3,5)
 # 乙: above=2, tie=3 -> lo=2+max(0,4-5)=2, hi=5
 assert (gb["乙组"]["selected_min"],gb["乙组"]["selected_max"])==(2,5)
 # 丙: above=3, tie=3 -> lo=3+max(0,4-5)=3, hi=6
 assert (gb["丙组"]["selected_min"],gb["丙组"]["selected_max"])==(3,6)
 print("三组同分样本：")
 for b in res["group_bounds"]:
  print(f"  {b['group']} n={b['n']} 必录{b['above_cut']} 边界同分{b['at_cut']} "
        f"入选人数[{b['selected_min']},{b['selected_max']}] "
        f"入选率[{b['selection_rate_min']:.4f},{b['selection_rate_max']:.4f}]")
 for key,name in (("gap_min","最小"),("gap_max","最大")):
  node=res[key]
  print(f"  可达{name}差距={node['value']:.4f} 见证分组人数={node['selected']} "
        f"合计={sum(node['selected'].values())}")
 assert sum(res["gap_min"]["selected"].values())==quota
 assert sum(res["gap_max"]["selected"].values())==quota
 print("test_three_group_tie_sample OK")

def test_deterministic_cases():
 rows=[{"candidate_id":f"A{i}","group":"G1" if i%2 else "G2","score":100-i,"qualified":0} for i in range(20)]
 r=quota_boundary(rows,5)
 # 边界仅 1 人且必录（r_tie=t_total），区间退化为单点
 assert r["deterministic"] and r["tie_to_pick"]==r["tie_total"]
 assert all(b["selected_min"]==b["selected_max"] for b in r["group_bounds"])
 assert r["gap_min"]["value"]==r["gap_max"]["value"]
 # 名额等于样本量：全部录取，差距为 0
 r2=quota_boundary(rows,20)
 assert r2["gap_max"]["value"]==0 and all(b["selected_min"]==b["n"] for b in r2["group_bounds"])
 print("test_deterministic_cases OK")

def test_random_against_bruteforce():
 rng=random.Random(20261112)
 for trial in range(300):
  g=rng.randint(2,4)
  groups=[f"G{i}" for i in range(g)]
  rows=[];cid=0
  # 制造大量同分：分数只取少数几个离散值
  levels=[40,55,70,85,100]
  for gi in range(g):
   size=rng.randint(3,7)
   for _ in range(size):
    cid+=1
    rows.append({"candidate_id":f"T{trial}-{cid}","group":groups[gi],
                 "score":levels[rng.randrange(len(levels))],"qualified":rng.randint(0,1)})
  quota=rng.randint(1,len(rows))
  check_instance(rows,quota,f"random-{trial}")
 print("test_random_against_bruteforce OK (300 例全枚举一致)")

def test_tp_range():
 # 边界同分时入选人数固定，TP 仍有可达区间（优先选合格/不合格者给出上下界）
 import random
 from src.services.metrics import group_metrics_for_counts
 rng=random.Random(99)
 for _ in range(200):
  g=[rng.randint(0,1) for _ in range(rng.randint(2,10))]
  tie=[rng.randint(0,1) for _ in range(rng.randint(1,10))]
  rows=[{"candidate_id":f"a{k}","group":"X","score":80,"qualified":q} for k,q in enumerate(g)]
  rows+=[{"candidate_id":f"t{k}","group":"X","score":70,"qualified":q} for k,q in enumerate(tie)]
  rows.append({"candidate_id":"z","group":"Y","score":10,"qualified":0})
  above_q=sum(g);picked=rng.randint(0,len(tie));sel=len(g)+picked
  mm=group_metrics_for_counts(rows,70,{"X":sel,"Y":0})[0]
  tps=[above_q+sum(c) for c in itertools.combinations(tie,picked)]
  assert mm["tp_min"]==min(tps) and mm["tp_max"]==max(tps)
 print("test_tp_range OK (200 例组合枚举一致)")

if __name__=="__main__":
 test_three_group_tie_sample()
 test_deterministic_cases()
 test_random_against_bruteforce()
 test_tp_range()
 print("全部验证通过")
