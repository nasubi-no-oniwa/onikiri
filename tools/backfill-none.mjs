// 才能なし（刀の色が変わらない人）のランキング k/none に、これまでの全体ランキング n の記録を写す。
// 何回動かしてもよい：k/none にまだ無い人と、n のほうが遠くまで走っている人だけ書く。
import { token, api } from './fb.mjs';
const tk = await token();
const n = JSON.parse(await api('GET', '/onikiri/n.json', undefined, tk)) || {};
const cur = JSON.parse(await api('GET', '/onikiri/k/none.json', undefined, tk)) || {};
const up = {}; let all = 0;
for (const [h, v] of Object.entries(n)) {
  if (!v || v.k !== 'none' || typeof v.d !== 'number') continue; all++;
  if (!cur[h] || !(cur[h].d >= v.d)) up[h] = v;
}
const keys = Object.keys(up);
for (let i = 0; i < keys.length; i += 400) { const part = {}; for (const h of keys.slice(i, i + 400)) part[h] = up[h]; await api('PATCH', '/onikiri/k/none.json', part, tk); }
console.log(`全体 ${Object.keys(n).length} 件のうち才能なしは ${all} 件。今回写したのは ${keys.length} 件（すでに ${Object.keys(cur).length} 件あり）`);
