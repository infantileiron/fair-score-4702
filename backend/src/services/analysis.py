import hashlib,json,math
from src.services.metrics import group_metrics,group_metrics_for_counts,gap
from src.services.pareto import threshold_frontier
from src.services.quota import quota_boundary
GENERIC_WARNINGS=["模拟数据仅作回顾性统计。差异不能直接解释为歧视或因果。",
 "区间为逐组Wilson区间，未作多重比较校正；样本稀少及标签偏差需要人工复核。",
 "同一口径用于全部组；Pareto前沿供复核讨论，不自动推荐招聘决策。"]
def analyze(rows,threshold,max_gap,quota=None):
 if len(rows)<20: raise ValueError("样本至少20条")
 if len({r["group"] for r in rows})<2: raise ValueError("至少两个复核组")
 checksum=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
 if quota is not None:
  return _analyze_quota(rows,quota,max_gap,checksum)
 if not math.isfinite(threshold) or not 0<=threshold<=100: raise ValueError("阈值应在0至100")
 return _analyze_threshold(rows,threshold,max_gap,checksum)
def _analyze_threshold(rows,threshold,max_gap,checksum):
 groups=group_metrics(rows,threshold)
 selection_gap=gap([g["selection_rate"] for g in groups])
 return {"mode":"threshold","threshold":threshold,"n":len(rows),"groups":groups,
  "selection_gap":selection_gap,
  "tpr_gap":gap([g["tpr"] for g in groups]),"fpr_gap":gap([g["fpr"] for g in groups]),
  "accuracy":sum(g["tp"]+g["tn"] for g in groups)/len(rows),
  "exceeds_gap":selection_gap>max_gap,"max_gap":max_gap,
  "frontier":threshold_frontier(rows),"checksum":checksum,"warnings":list(GENERIC_WARNINGS)}
def _analyze_quota(rows,quota,max_gap,checksum):
 if not isinstance(quota,int) or quota<1 or quota>len(rows):
  raise ValueError("名额须为1至样本量之间的整数")
 boundary=quota_boundary(rows,quota)
 cutoff=boundary["cutoff_score"]
 # 两个差距端点各带一组可恰好录满名额的分组人数，分别计算其指标
 endpoint_metrics={}
 for key in ("gap_min","gap_max"):
  endpoint_metrics[key]=group_metrics_for_counts(rows,cutoff,boundary[key]["selected"])
 # 展示用的分组行：入选率区间来自可达人数区间，标签口径取最小差距见证并附TP区间
 groups=[]
 by_group={g["group"]:g for g in endpoint_metrics["gap_min"]}
 for b in boundary["group_bounds"]:
  m=by_group[b["group"]]
  row=dict(m)
  row.update({"selection_rate_min":b["selection_rate_min"],"selection_rate_max":b["selection_rate_max"],
   "selected_min":b["selected_min"],"selected_max":b["selected_max"],
   "above_cut":b["above_cut"],"at_cut":b["at_cut"]})
  groups.append(row)
 warnings=list(GENERIC_WARNINGS)
 if not boundary["deterministic"]:
  warnings.append(
   f"边界分{cutoff}上有{boundary['tie_total']}名同分候选，只需任选{boundary['tie_to_pick']}人；"
   "不按编号强行定人，各组入选率与组间差距以可达区间及两个带见证人数的端点呈现。")
 else:
  warnings.append(f"边界分{cutoff}无同分争议（同分候选全部入选或无人落选），各端点一致。")
 return {"mode":"quota","threshold":cutoff,"cutoff_score":cutoff,"quota":quota,
  "n":len(rows),"groups":groups,"quota_boundary":boundary,
  "endpoint_metrics":endpoint_metrics,
  "selection_gap":boundary["gap_min"]["value"],
  "selection_gap_min":boundary["gap_min"]["value"],
  "selection_gap_max":boundary["gap_max"]["value"],
  "tpr_gap":None,"fpr_gap":None,
  "accuracy":None,"exceeds_gap":boundary["gap_min"]["value"]>max_gap,
  "exceeds_gap_any":boundary["gap_max"]["value"]>max_gap,"max_gap":max_gap,
  "frontier":threshold_frontier(rows),"checksum":checksum,"warnings":warnings}
