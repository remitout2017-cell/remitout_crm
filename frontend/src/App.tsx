import { Toaster } from 'react-hot-toast'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import Dashboard from './features/dashboard/Dashboard'
import EdubaoLookup from './features/edubaoLookup/EdubaoLookup'
import FormLeads from './features/formLeads/FormLeads'
import PublicForm from './features/formLeads/PublicForm'
import LeadDetail from './features/leads/LeadDetail'
import Leads from './features/leads/Leads'
import Partners from './features/partners/Partners'
import Students from './features/students/Students'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{ style: { border: '1px solid #fee4cc' }, success: { iconTheme: { primary: '#ff5a00', secondary: '#fff' } } }} />
      <Routes>
        {/* Public, unauthenticated intake form — not part of the admin shell. */}
        <Route path="apply" element={<PublicForm />} />
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="students" element={<Students />} />
          <Route path="leads" element={<Leads />} />
          <Route path="leads/:id" element={<LeadDetail />} />
          <Route path="form-leads" element={<FormLeads />} />
          <Route path="partners" element={<Partners />} />
          <Route path="edubao-lookup" element={<EdubaoLookup />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
