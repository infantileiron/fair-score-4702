import type {GroupMetric} from '../types/domain';import {percent} from '../utils/format';
export function GapChart({groups}:{groups:GroupMetric[]}){
 const quota=groups.some(g=>g.selection_rate_min!==undefined);
 return <div className="gap-chart">{groups.map((g,i)=>{
  const low=quota?g.selection_rate_min!:g.selection_ci[0];
  const high=quota?g.selection_rate_max!:g.selection_ci[1];
  const mid=quota?(low+high)/2:g.selection_rate;
  return <div className="bar-row" key={g.group}><label>{g.group}<small>n={g.n}</small></label>
  <div className="bar-track"><span style={{width:percent(mid),background:i%2?'var(--copper)':'var(--green)'}}/>
  <i style={{left:percent(low),width:percent(high-low)}}/></div>
  <b>{quota?`${percent(low)} — ${percent(high)}`:percent(g.selection_rate)}</b></div>})}
 <div className="axis"><span>0%</span><span>入选比例 · {quota?'括号为可达范围':'黑线为Wilson区间'}</span><span>100%</span></div></div>}
