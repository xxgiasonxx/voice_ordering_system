import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { router } from './router/router'
import { TokenProvider } from './contexts/TokenContext'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TokenProvider>
        <RouterProvider router={router} />
    </TokenProvider>
  </StrictMode>,
)
