export default function StatCard({ value, label, color = 'navy' }) {
  const colors = {
    navy: 'border-l-navy text-navy',
    gold: 'border-l-gold text-amber-700',
    green: 'border-l-emerald-500 text-emerald-700',
    blue: 'border-l-blue-500 text-blue-700',
  }
  return (
    <div className={`bg-white rounded-xl p-4 shadow-sm border-l-4 ${colors[color] || colors.navy} hover:-translate-y-0.5 transition`}>
      <div className="text-xl sm:text-2xl font-extrabold leading-none">{value}</div>
      <div className="text-[11px] sm:text-xs text-slate-500 mt-1">{label}</div>
    </div>
  )
}
