import math
def wilson(k,n,z=1.959963984540054):
 if n==0: return None
 p=k/n;d=1+z*z/n
 center=(p+z*z/(2*n))/d
 half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [0.0 if k==0 else max(0,center-half),1.0 if k==n else min(1,center+half)]
def group_metrics(rows,threshold):
 result=[]
 for name in sorted({r["group"] for r in rows}):
  subset=[r for r in rows if r["group"]==name]
  tp=sum(r["score"]>=threshold and r["qualified"]==1 for r in subset)
  fp=sum(r["score"]>=threshold and r["qualified"]==0 for r in subset)
  positives=sum(r["qualified"] for r in subset);n=len(subset);negatives=n-positives
  result.append({"group":name,"n":n,"selected":tp+fp,"qualified":positives,"tp":tp,"fp":fp,"fn":positives-tp,"tn":negatives-fp,"selection_rate":(tp+fp)/n,"selection_ci":wilson(tp+fp,n),"tpr":tp/positives if positives else None,"fpr":fp/negatives if negatives else None,"tpr_ci":wilson(tp,positives),"fpr_ci":wilson(fp,negatives),"small_sample":n<30})
 return result
def group_metrics_for_counts(rows,cutoff,selected_by_group):
 """给定每组入选人数（固定名额口径），计算该组标签口径指标。

 严格高于边界分者必录，边界同分者任选。因此入选人数固定时，TP 也有
 可达区间：在边界同分时优先选合格/不合格者分别给出 TP 上界/下界。
 历史数据升级后仍可凭同一 cutoff 按原分数线复核标签结构。
 """
 result=[]
 for name in sorted({r["group"] for r in rows}):
  subset=[r for r in rows if r["group"]==name]
  n=len(subset);positives=sum(r["qualified"] for r in subset);negatives=n-positives
  selected=selected_by_group[name]
  above=[r for r in subset if r["score"]>cutoff]
  tied=[r for r in subset if r["score"]==cutoff]
  tp_above=sum(r["qualified"]==1 for r in above)
  q_tie=sum(r["qualified"]==1 for r in tied)
  tie_picked=selected-len(above)
  tp_min=tp_above+max(0,tie_picked-(len(tied)-q_tie))
  tp_max=tp_above+min(q_tie,tie_picked)
  tp=tp_min  # 保守取下界；区间由 tp_min/tp_max 同时保留
  fp=selected-tp
  result.append({"group":name,"n":n,"selected":selected,"qualified":positives,
   "tp":tp,"fp":fp,"fn":positives-tp,"tn":negatives-fp,
   "tp_min":tp_min,"tp_max":tp_max,
   "selection_rate":selected/n,"selection_ci":wilson(selected,n),
   "tpr":tp/positives if positives else None,"fpr":fp/negatives if negatives else None,
   "tpr_ci":wilson(tp,positives),"fpr_ci":wilson(fp,negatives),"small_sample":n<30})
 return result
def gap(values):
 valid=[v for v in values if v is not None]
 return max(valid)-min(valid) if len(valid)>1 else None
