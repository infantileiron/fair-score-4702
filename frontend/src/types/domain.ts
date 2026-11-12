export interface Candidate {candidate_id:string; group:string; score:number; qualified:number}
export interface Dataset {id:string;name:string;source:string;rows:Candidate[];created_at:string}
export interface Policy {id:string;name:string;dataset_id:string;threshold:number;max_gap:number;quota:number|null;created_at:string}
export interface GroupMetric {
 group:string;n:number;selected:number;qualified:number;tp:number;fp:number;fn:number;tn:number;
 selection_rate:number;selection_ci:[number,number];tpr:number|null;fpr:number|null;small_sample:boolean;
 // 固定名额口径的可达区间（分数线模式下为 undefined）
 selected_min?:number;selected_max?:number;selection_rate_min?:number;selection_rate_max?:number;
 above_cut?:number;at_cut?:number;tp_min?:number;tp_max?:number;
}
export interface GapEndpoint {value:number;selected:Record<string,number>;selection_rates:Record<string,number>}
export interface QuotaBoundary {
 mode:'quota';quota:number;cutoff_score:number;tie_total:number;tie_to_pick:number;deterministic:boolean;
 group_bounds:{group:string;n:number;above_cut:number;at_cut:number;selected_min:number;selected_max:number;selection_rate_min:number;selection_rate_max:number}[];
 gap_min:GapEndpoint;gap_max:GapEndpoint;
}
export interface Frontier {threshold:number;accuracy:number;selection_gap:number;pareto:boolean}
export interface Result {
 mode?:'threshold'|'quota';n:number;threshold:number;groups:GroupMetric[];
 selection_gap:number;tpr_gap:number|null;fpr_gap:number|null;accuracy:number|null;
 max_gap:number;exceeds_gap:boolean;frontier:Frontier[];warnings:string[];checksum:string;
 // 固定名额口径
 quota?:number;cutoff_score?:number;quota_boundary?:QuotaBoundary;
 selection_gap_min?:number;selection_gap_max?:number;exceeds_gap_any?:boolean;
 endpoint_metrics?:Record<string,GroupMetric[]>;
}
export interface Run {id:string;policy_id:string;status:string;result:Result;error:string;created_at:string}
export interface Review {id:string;run_id:string;note:string;decision:string;author:string;created_at:string}
export interface Report {id:string;run_id:string;title:string;published_by:string;created_at:string}
export interface Audit {id:string;actor:string;action:string;status:number;created_at:string}
export interface User {email:string;role:string}
