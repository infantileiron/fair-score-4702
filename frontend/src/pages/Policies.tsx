import {useState} from 'react';import type {Workspace} from '../stores/workspace';import {PageHeading} from '../components/common/PageHeading';import {Notice} from '../components/common/Notice';import {Status} from '../components/common/Status';import {createPolicies} from '../api/policies';import {createRuns} from '../api/runs';import {useAsync} from '../hooks/useAsync';import {percent,date} from '../utils/format';
export function Policies({data,canWrite,refresh,go}:{data:Workspace;canWrite:boolean;refresh:()=>Promise<void>;go:(s:string)=>void}){
 const [name,setName]=useState('');const [datasetId,setDatasetId]=useState('');
 const [mode,setMode]=useState<'threshold'|'quota'>('threshold');
 const [threshold,setThreshold]=useState(65);const [gap,setGap]=useState(.1);const [quota,setQuota]=useState(10);
 const task=useAsync();
 const dataset=data.datasets.find(d=>d.id===(datasetId||data.datasets[0]?.id));
 const sampleSize=dataset?.rows.length??0;
 return <><PageHeading label="03 / SCORE POLICY" title="每条分数线，都留有来处。">分数线模式对分数≥阈值者计入选；固定名额模式按分数从高到低录满名额，<br/>边界同分不按编号强行定人，而以可达区间呈现取舍。</PageHeading>
 {canWrite&&<section className="paper"><h2>新建回顾性方案</h2><form className="policy-form" onSubmit={e=>{e.preventDefault();task.execute(async()=>{
  const payload=mode==='quota'
   ?{name,dataset_id:datasetId||data.datasets[0]?.id,threshold:0,max_gap:gap,quota}
   :{name,dataset_id:datasetId||data.datasets[0]?.id,threshold,max_gap:gap};
  await createPolicies(payload);setName('');await refresh();})}}>
 <label>方案名称<input aria-label="方案名称" required minLength={2} value={name} onChange={e=>setName(e.target.value)}/></label>
 <label>样本卷宗<select value={datasetId||data.datasets[0]?.id||''} onChange={e=>setDatasetId(e.target.value)}>{data.datasets.map(d=><option key={d.id} value={d.id}>{d.name}（n={d.rows.length}）</option>)}</select></label>
 <label>复核口径<select aria-label="复核口径" value={mode} onChange={e=>setMode(e.target.value as 'threshold'|'quota')}><option value="threshold">统一分数线</option><option value="quota">固定名额（按分数录满）</option></select></label>
 {mode==='threshold'
  ?<label>统一分数线<input aria-label="统一分数线" type="number" min={0} max={100} step={1} value={threshold} onChange={e=>setThreshold(+e.target.value)}/></label>
  :<label>固定名额<input aria-label="固定名额" type="number" min={1} max={sampleSize||undefined} step={1} required value={quota} onChange={e=>setQuota(+e.target.value)}/><small>当前卷宗 {sampleSize} 人；边界同分仅任选，不按编号定人</small></label>}
 <label>差距提示线<input type="number" min={0} max={1} step={.01} value={gap} onChange={e=>setGap(+e.target.value)}/></label>
 <button disabled={task.busy||(mode==='quota'&&(quota<1||quota>sampleSize))}>保存方案</button>
 </form></section>}
 {task.error&&<Notice error>{task.error}</Notice>}
 <section className="paper"><h2>已保存方案</h2>{data.policies.map(p=><article className="policy-row" key={p.id}><div><span className="eyebrow">{p.quota?`固定名额 ${p.quota} 人`:`统一阈值 ${p.threshold}`} / 提示差距 {percent(p.max_gap)}</span><h3>{p.name}</h3><p>{data.datasets.find(d=>d.id===p.dataset_id)?.name}</p></div>{canWrite&&<button className="secondary" disabled={task.busy} onClick={()=>task.execute(async()=>{await createRuns({policy_id:p.id});await refresh();go('results')})}>运行复核　→</button>}</article>)}</section>
 <section className="paper"><h2>计算队列</h2><div className="table-scroll"><table><thead><tr><th>方案</th><th>状态</th><th>提交时间</th></tr></thead><tbody>{data.runs.map(r=><tr key={r.id}><td>{data.policies.find(p=>p.id===r.policy_id)?.name}</td><td><Status value={r.status}/></td><td>{date(r.created_at)}</td></tr>)}</tbody></table></div></section></>}
