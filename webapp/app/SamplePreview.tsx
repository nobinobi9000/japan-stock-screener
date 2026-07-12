const SAMPLE_ROWS = [
  { code: '0001', name: 'サンプル商事', sector: '卸売業', price: 1234, score: 78, buy: [true, true, false, true, false], sell: [false, false] },
  { code: '0002', name: 'サンプル工業', sector: '機械', price: 856, score: 65, buy: [true, false, true, false, true], sell: [false, false] },
  { code: '0003', name: 'サンプル電子工業', sector: '電気機器', price: 3420, score: 54, buy: [false, true, false, true, false], sell: [false, false] },
  { code: '0004', name: 'サンプル食品HD', sector: '食料品', price: 512, score: 41, buy: [true, false, false, false, true], sell: [true, false] },
  { code: '0005', name: 'サンプル物流', sector: '陸運業', price: 987, score: 33, buy: [false, false, true, false, false], sell: [true, true] },
]

const BUY_LABELS = ['GC', 'MA200↑', 'BB', 'OBV↑', '出来高']
const SELL_LABELS = ['DC', 'MA200割れ']

export default function SamplePreview() {
  return (
    <div className="relative overflow-hidden border border-[var(--border2)] rounded-xl bg-[var(--panel)]">
      <div className="absolute top-3 right-3 z-10 font-[family-name:var(--mono)] text-[10px] font-bold tracking-[2px] text-[var(--amber)] border border-[var(--amber)] px-2 py-1 rounded-sm bg-[rgba(245,158,11,0.08)]">
        SAMPLE — 架空データ
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead className="bg-[var(--panel2)] text-[var(--muted)]">
            <tr>
              <th className="px-3 py-2 text-left">コード</th>
              <th className="px-3 py-2 text-left">銘柄名</th>
              <th className="px-3 py-2 text-left">セクター</th>
              <th className="px-3 py-2 text-right">株価</th>
              <th className="px-3 py-2 text-right">総合スコア</th>
              {BUY_LABELS.map((l) => (
                <th key={l} className="px-2 py-2 text-center whitespace-nowrap">{l}</th>
              ))}
              {SELL_LABELS.map((l) => (
                <th key={l} className="px-2 py-2 text-center whitespace-nowrap">{l}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SAMPLE_ROWS.map((s) => (
              <tr key={s.code} className="border-t border-[var(--border2)]">
                <td className="px-3 py-2 font-[family-name:var(--mono)] text-[var(--head)]">{s.code}</td>
                <td className="px-3 py-2 text-[var(--text)]">{s.name}</td>
                <td className="px-3 py-2 text-[var(--muted)]">{s.sector}</td>
                <td className="px-3 py-2 text-right text-[var(--text)]">{s.price.toLocaleString()}</td>
                <td className="px-3 py-2 text-right text-[var(--green2)]">{s.score.toFixed(1)}</td>
                {s.buy.map((v, i) => (
                  <td key={i} className="px-2 py-2 text-center">
                    {v ? <span className="text-[var(--green)]">●</span> : ''}
                  </td>
                ))}
                {s.sell.map((v, i) => (
                  <td key={i} className="px-2 py-2 text-center">
                    {v ? <span className="text-[var(--red)]">●</span> : ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="px-4 py-3 text-[11px] text-[var(--muted)] border-t border-[var(--border2)]">
        ※このテーブルは画面イメージのサンプルです。銘柄名・数値はすべて架空のものです。ログイン後、basic・premiumプランでは東証全銘柄の実データ(9指標・JVQM・売りシグナル含む)をご覧いただけます。
      </p>
    </div>
  )
}
