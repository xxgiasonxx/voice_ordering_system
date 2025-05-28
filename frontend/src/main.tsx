import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { router } from './router/router'
import { CookiesProvider } from 'react-cookie'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <CookiesProvider>
        <RouterProvider router={router} />
    </CookiesProvider>
  </StrictMode>,
)
