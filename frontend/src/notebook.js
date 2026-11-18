import {api} from './api.js';
export const book={hives:[],visits:[],care:[],lots:[],issues:[],queens:[],moves:[],insulationLots:[],installs:[],spring:[],merges:[],selectedHive:31,selectedVisit:null,selectedCare:null,planning:false,showAll:false};
export async function openNotebook(){[book.hives,book.visits,book.care,book.lots,book.issues,book.queens,book.moves,book.insulationLots,book.installs,book.spring,book.merges]=await Promise.all([api('/hives'),api('/visits'),api('/care'),api('/feed-lots'),api('/feed-issues'),api('/queen-observations'),api('/moves'),api('/insulation-lots'),api('/insulation-installs'),api('/spring-reviews'),api('/colony-merges')]);}
export function activeMerges(){return book.merges.filter(m=>['requested','approved'].includes(m.state));}
export function frozenHiveIds(){return new Set(activeMerges().flatMap(m=>[m.donor_hive_id,m.recipient_hive_id]));}
export function mergeOfHive(id){return book.merges.find(m=>['requested','approved'].includes(m.state)&&(m.donor_hive_id===id||m.recipient_hive_id===id));}
export function latestVisits(){const found=new Map();for(const visit of book.visits)if(!found.has(visit.hive_id))found.set(visit.hive_id,visit);return [...found.values()];}
