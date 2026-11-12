import {useState} from 'react';import type {Workspace} from '../stores/workspace';import {PageHeading} from '../components/common/PageHeading';import {Notice} from '../components/common/Notice';import {Status} from '../components/common/Status';import {Empty} from '../components/common/Empty';import {GroupTable} from '../components/GroupTable';import {GapChart} from '../components/GapChart';import {FrontierChart} from '../components/FrontierChart';import {QuotaEvidence} from '../components/QuotaEvidence';import {percent} from '../utils/format';
export function Results({data}:{data:Workspace}){
 const [selected,setSelected]=useState('');const run=data.runs.find(r=>r.id===selected)||data.runs[0];
 const isQuota=run?.result?.mode==='quota';
 return <><PageHeading label="04 / EVIDENCE & FRONTIER" title="差异可见，判断有边界。">统一口径下保留样本分母与区间；固定名额复核呈现边界同分的<br/>可达入选率范围，及各带录满见证人数的组间差距最小/最大值。</PageHeading>
 <section className="run-selector"><label>计算记录<select aria-label="选择计算记录" value={run?.id||''} onChange={e=>setSelected(e.target.value)}>{data.runs.map(r=><option key={r.id} value={r.id}>{data.policies.find(p=>p.id===r.policy_id)?.name} · {r.created_at.slice(11,19)}</option>)}</select></label>{run&&<Status value={run.status}/>}</section>
 {!run?<Empty>前往分数线方案，保存一份方案后运行复核。</Empty>:run.status!=='completed'?<Notice error={run.status==='failed'}>{run.status==='failed'?run.error:'计算已进入后台队列，页面会自动刷新。'}</Notice>:<>
 {isQuota&&run.result.quota_boundary&&<QuotaEvidence boundary={run.result.quota_boundary}/>}
 <section className="paper"><div className="section-heading"><h2>组间指标</h2><span>{isQuota?`固定名额 ${run.result.quota} / 边界分 ${run.result.cutoff_score}`:`统一阈值 ${run.result.threshold}`} / n={run.result.n}</span></div>
 <div className="result-metrics">
  {isQuota?<>
   <div><small>入选率差距（最小—最大）</small><b>{percent(run.result.selection_gap_min)} — {percent(run.result.selection_gap_max)}</b></div>
   <div><small>最小差距是否超提示线</small><b className={run.result.exceeds_gap?'tie-warn':''}>{run.result.exceeds_gap?'超出':'未超'}</b></div>
   <div><small>最大差距是否超提示线</small><b className={run.result.exceeds_gap_any?'tie-warn':''}>{run.result.exceeds_gap_any?'超出':'未超'}</b></div>
   <div><small>提示线</small><b>{percent(run.result.max_gap)}</b></div>
  </>:<>
   <div><small>入选率差距</small><b>{percent(run.result.selection_gap)}</b></div>
   <div><small>真阳性率差距</small><b>{percent(run.result.tpr_gap)}</b></div>
   <div><small>假阳性率差距</small><b>{percent(run.result.fpr_gap)}</b></div>
   <div><small>总体准确率</small><b>{percent(run.result.accuracy)}</b></div>
  </>}
 </div>
 <GapChart groups={run.result.groups}/><GroupTable groups={run.result.groups}/></section>
 <div className="results-grid"><section className="paper"><h2>阈值的效用—差距前沿</h2><FrontierChart points={run.result.frontier}/></section>
 <aside className="evidence-note"><span className="eyebrow">REVIEW BOUNDARIES</span><h2>{isQuota?(run.result.exceeds_gap_any?'差距可达值触及提示线':'差距可达范围处于提示线内'):(run.result.exceeds_gap?'差距超过提示线':'差距处于提示线内')}</h2><p>本方案提示线 {percent(run.result.max_gap)}。提示仅用于安排人工复核。</p>{run.result.warnings.map((s,i)=><p key={s}><b>0{i+1}</b>{s}</p>)}<small>样本校验码 {run.result.checksum.slice(0,16)}</small></aside></div>
 </>}</>}
