import { Card } from '../ui/Card.jsx'

export default function StatCard({ value, label, color = 'navy' }) {
  const borders = { navy: 'border-l-navy', gold: 'border-l-gold', green: 'border-l-emerald-500', blue: 'border-l-blue-500' }
  const texts = { navy: 'text-navy', gold: 'text-amber-700 dark:text-amber-400', green: 'text-emerald-700 dark:text-emerald-400', blue: 'text-blue-700 dark:text-blue-400' }

  return (
    <Card className={`p-4 border-l-4 ${borders[color] || borders.navy} hover:-translate-y-0.5 transition`}>
      <div className={`text-xl sm:text-2xl font-extrabold ${texts[color] || texts.navy}`}>{value}</div>
      <div className="text-[11px] sm:text-xs text-muted-foreground mt-1">{label}</div>
    </Card>
  )
}
