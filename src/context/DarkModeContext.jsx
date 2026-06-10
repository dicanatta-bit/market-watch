import { createContext, useContext } from 'react'
import { useDarkMode } from '../hooks/useDarkMode.js'

const DarkModeContext = createContext(null)

export function DarkModeProvider({ children }) {
  const [dark, setDark] = useDarkMode()
  return <DarkModeContext.Provider value={{ dark, setDark }}>{children}</DarkModeContext.Provider>
}

export function useDark() { return useContext(DarkModeContext) }
