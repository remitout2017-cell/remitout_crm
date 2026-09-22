import { Toaster } from 'react-hot-toast'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import Dashboard from './features/dashboard/Dashboard'
import LeadDetail from './features/leads/LeadDetail'
import Leads from './features/leads/Leads'
import Partners from './features/partners/Partners'
import Students from './features/students/Students'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{ style: { border: '1px solid #fee4cc' }, success: { iconTheme: { primary: '#ff5a00', secondary: '#fff' } } }} />
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="students" element={<Students />} />
          <Route path="leads" element={<Leads />} />
          <Route path="leads/:id" element={<LeadDetail />} />
          <Route path="partners" element={<Partners />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
