import type {QuotaBoundary} from '../types/domain';import {percent} from '../utils/format';
function EndpointCard({title,node,quota,tonal}:{title:string;node:QuotaBoundary['gap_min'];quota:number;tonal:'min'|'max'}){
 const total=Object.values(node.selected).reduce((a,b)=>a+b,0);
 return <article className={`gap-endpoint ${tonal}`}><div className="endpoint-head"><small>{title}</small><b>{percent(node.value)}</b></div>
 <table><thead><tr><th>复核组</th><th>见证入选人数</th><th>见证入选率</th></tr></thead><tbody>
 {Object.entries(node.selected).map(([g,count])=><tr key={g}><td>{g}</td><td>{count}</td><td>{percent(node.selection_rates[g])}</td></tr>)}
 </tbody></table>
 <p className={`witness-check ${total===quota?'ok':'bad'}`}>见证合计 {total} 人 {total===quota?`= 名额 ${quota}，可恰好录满`:'≠ 名额，分配不可行'}</p></article>}
export function QuotaEvidence({boundary}:{boundary:QuotaBoundary}){
 return <section className="paper quota-evidence"><div className="section-heading"><h2>固定名额 · 边界同分取舍依据</h2>
 <span>名额 {boundary.quota} / 边界分 {boundary.cutoff_score}</span></div>
 <div className="quota-summary">
  <div><small>边界同分候选</small><b>{boundary.tie_total} 人</b></div>
  <div><small>其中需任选</small><b>{boundary.tie_to_pick} 人</b></div>
  <div><small>是否存在同分争议</small><b className={boundary.deterministic?'':'tie-warn'}>{boundary.deterministic?'否（端点一致）':'是（不按编号定人）'}</b></div>
 </div>
 <p className="quota-note">严格高于边界分者必录；边界同分者只需任选 {boundary.tie_to_pick} 人。下表为各组在“恰好录满 {boundary.quota} 人”约束下的可达入选率范围，两个差距端点各自附带一组能录满名额的分组人数，避免拼接互不相容的极值。</p>
 <div className="table-scroll"><table><thead><tr><th>复核组 / 样本</th><th>必录（高于边界）</th><th>边界同分</th><th>入选人数范围</th><th>入选率可达范围</th></tr></thead><tbody>
 {boundary.group_bounds.map(b=><tr key={b.group}><td><b>{b.group}</b><small>n = {b.n}</small></td><td>{b.above_cut}</td><td>{b.at_cut}</td><td>{b.selected_min} — {b.selected_max} 人</td><td>{percent(b.selection_rate_min)} — {percent(b.selection_rate_max)}</td></tr>)}
 </tbody></table></div>
 <div className="gap-endpoints"><EndpointCard title="全组差距 · 可达最小值" node={boundary.gap_min} quota={boundary.quota} tonal="min"/><EndpointCard title="全组差距 · 可达最大值" node={boundary.gap_max} quota={boundary.quota} tonal="max"/></div>
 </section>}
