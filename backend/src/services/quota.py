"""固定名额复核：按分数从高到低录满指定名额。

边界分数上存在同分候选时，不按编号等顺序强行定人：严格高于边界分的候选
必然入选，边界同分候选只需从中任选 r 人即可恰好录满。因此每个组的入选
人数存在一个可达区间，组间入选率差距也存在可达最小值与最大值。

两个差距端点均返回一组**能恰好录满名额**的分组入选人数（witness），
避免把互不相容的单组极值拼接成不可实现的差距。
"""
import math
EPS=1e-12

def _ceil_rate(rate,n):
 # 最小整数 x 使 x/n >= rate（浮点容差，最小比例差远大于 EPS）
 return max(0,math.ceil(rate*n-EPS))

def _floor_rate(rate,n):
 return math.floor(rate*n+EPS)

def quota_boundary(rows,quota):
 """返回固定名额复核的完整可达性结构（不含标签口径指标）。"""
 groups=sorted({r["group"] for r in rows})
 if quota<1 or quota>len(rows):
  raise ValueError("名额须在1至样本量之间")
 ordered=sorted(rows,key=lambda r:(-r["score"],r["candidate_id"]))
 cutoff=ordered[quota-1]["score"]
 # 严格高于边界分（必录）与边界同分（任选）
 above={g:0 for g in groups}; tie={g:0 for g in groups}
 for r in rows:
  if r["score"]>cutoff: above[r["group"]]+=1
  elif r["score"]==cutoff: tie[r["group"]]+=1
 a_total=sum(above.values()); t_total=sum(tie.values())
 r_tie=quota-a_total            # 边界同分中还需录取的人数
 if not 0<=r_tie<=t_total: raise RuntimeError("边界名额计算异常")
 n={g:sum(1 for r in rows if r["group"]==g) for g in groups}
 # 每组在“恰好录满”约束下可录取的人数区间 [lo,hi]
 lo={g:above[g]+max(0,r_tie-(t_total-tie[g])) for g in groups}
 hi={g:above[g]+min(tie[g],r_tie) for g in groups}
 group_bounds=[{"group":g,"n":n[g],"above_cut":above[g],"at_cut":tie[g],
  "selected_min":lo[g],"selected_max":hi[g],
  "selection_rate_min":lo[g]/n[g],"selection_rate_max":hi[g]/n[g]} for g in groups]
 min_gap,min_witness=_min_gap(groups,n,lo,hi,quota)
 max_gap,max_witness=_max_gap(groups,n,lo,hi,quota)
 return {"mode":"quota","quota":quota,"cutoff_score":cutoff,
  "tie_total":t_total,"tie_to_pick":r_tie,"deterministic":r_tie in (0,t_total),
  "group_bounds":group_bounds,
  "gap_min":{"value":min_gap,"selected":min_witness,
   "selection_rates":{g:min_witness[g]/n[g] for g in groups}},
  "gap_max":{"value":max_gap,"selected":max_witness,
   "selection_rates":{g:max_witness[g]/n[g] for g in groups}}}

def _feasible(groups,n,lo,hi,quota,d,anchor):
 """以 anchor 组为入选率最低组，检查是否存在 max-min<=d 的恰好录满分配。"""
 # anchor 至少要达到“其余组最低入选率 - d”，否则差距必然超过 d
 other_floor=max(lo[g]/n[g] for g in groups if g!=anchor)
 a_lo=max(lo[anchor],_ceil_rate(other_floor-d,n[anchor]))
 if a_lo>hi[anchor]: return None
 for x_anchor in range(a_lo,hi[anchor]+1):
  floors={anchor:x_anchor};caps={anchor:x_anchor};ok=True
  anchor_rate=x_anchor/n[anchor]
  for g in groups:
   if g==anchor: continue
   # anchor 为最低组：anchor_rate <= x_g/n_g <= anchor_rate + d
   floor=max(lo[g],_ceil_rate(anchor_rate,n[g]))
   cap=min(hi[g],_floor_rate(anchor_rate+d,n[g]))
   floors[g]=floor;caps[g]=cap
   if floor>cap: ok=False;break
  if not ok: continue
  total_lo=sum(floors.values());total_hi=sum(caps.values())
  if total_lo<=quota<=total_hi:
   witness=dict(floors);remain=quota-total_lo
   for g in groups:
    take=min(remain,caps[g]-witness[g]);witness[g]+=take;remain-=take
   if remain==0: return witness
 return None

def _min_gap(groups,n,lo,hi,quota):
 """二分最小可达差距，并返回达到该差距的恰好录满分组人数。"""
 rates=[x/n[g] for g in groups for x in range(lo[g],hi[g]+1)]
 lo_d,hi_d=0.0,max(rates)-min(rates);best=None
 for _ in range(48):
  mid=(lo_d+hi_d)/2
  witness=next((w for anchor in groups if (w:=_feasible(groups,n,lo,hi,quota,mid,anchor)) is not None),None)
  if witness is not None: hi_d=mid;best=witness
  else: lo_d=mid
 for anchor in groups:
  witness=_feasible(groups,n,lo,hi,quota,hi_d,anchor)
  if witness is not None:
   best=witness;break
 value=max(best[g]/n[g] for g in groups)-min(best[g]/n[g] for g in groups)
 return value,best

def _max_gap(groups,n,lo,hi,quota):
 """最大可达差距。

 对每个有序组对 (i 最高, j 最低)，把 i 顶到上界 hi_i、j 压到下界 lo_j，
 剩余名额交给其余组在其区间内补足（区间总和恒覆盖名额，故必可构造）。
 该分配同时最大化 r_i、最小化 r_j，即为该组对最优；再取所有组对最大者。
 """
 best_gap=-1.0;best_witness=None
 for i in groups:
  for j in groups:
   if i==j: continue
   x={i:hi[i],j:lo[j]}
   others=[o for o in groups if o not in (i,j)]
   remain=quota-x[i]-x[j]
   # 两阶段可行填充：先全部压到下界，再把剩余名额逐组加到上界
   for o in others: x[o]=lo[o]
   remain-=sum(lo[o] for o in others)
   for o in others:
    take=min(remain,hi[o]-x[o]);x[o]+=take;remain-=take
   if remain!=0 or any(x[k]<lo[k] or x[k]>hi[k] for k in groups): continue
   rates={k:x[k]/n[k] for k in groups}
   gap=max(rates.values())-min(rates.values())
   if gap>best_gap+EPS: best_gap,best_witness=gap,dict(x)
 return best_gap,best_witness
