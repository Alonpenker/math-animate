import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/patrick-hand/400.css'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import './index.css'
import App from './App.tsx'

document.cookie = `x-api-key=${import.meta.env.VITE_X_API_KEY ?? ''}; path=/; SameSite=Strict`;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
