import { Moon, Sun } from 'lucide-react'
import { useDark } from '../../context/DarkModeContext.jsx'

export default function DarkToggle() {
  const { dark, setDark } = useDark()
  return (
    <button onClick={() => setDark(!dark)} className="p-1.5 rounded-md hover:bg-accent transition" title={dark ? 'Light mode' : 'Dark mode'}>
      {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  )
}
