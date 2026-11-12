import type {GroupMetric} from '../types/domain';import {percent} from '../utils/format';
export function GroupTable({groups}:{groups:GroupMetric[]}){
 const quota=groups.some(g=>g.selected_min!==undefined);
 return <div className="table-scroll"><table><thead><tr>
 <th>复核组 / 样本</th><th>{quota?'入选率可达范围 · 区间':'入选率 · 95%区间'}</th><th>真阳性率</th><th>假阳性率</th>{quota&&<th>TP可达 / FP / FN / TN</th>}{!quota&&<th>TP / FP / FN / TN</th>}
 </tr></thead><tbody>{groups.map(g=><tr key={g.group}><td><b>{g.group}</b><small>n = {g.n}{g.small_sample?' · 小样本':''}</small></td>
 {quota
  ?<td>{percent(g.selection_rate_min)} — {percent(g.selection_rate_max)}<small>入选 {g.selected_min}—{g.selected_max} 人{g.tp_min!==g.tp_max?` · TP ${g.tp_min}—${g.tp_max}`:''}</small></td>
  :<td>{percent(g.selection_rate)}<small>{percent(g.selection_ci[0])} — {percent(g.selection_ci[1])}</small></td>}
 <td>{percent(g.tpr)}</td><td>{percent(g.fpr)}</td>
 {quota?<td>{g.tp_min}{g.tp_min!==g.tp_max?`—${g.tp_max}`:''} / {g.fp} / {g.fn} / {g.tn}</td>:<td>{g.tp} / {g.fp} / {g.fn} / {g.tn}</td>}
 </tr>)}</tbody></table></div>}
