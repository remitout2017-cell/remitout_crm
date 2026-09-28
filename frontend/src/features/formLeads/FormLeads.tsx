import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { FiCheckCircle, FiChevronLeft, FiChevronRight, FiCircle, FiDownload, FiSearch, FiTrash2 } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { errorMessage } from '../../store/baseApi'
import { PURPOSE_OPTIONS, type FormLead } from '../../types'
import { fmtDate } from '../../utils/cn'
import { openFormLeadDocument, useDeleteFormLeadMutation, useGetFormLeadsQuery, useUpdateFormLeadStatusMutation } from './api'

const fmtSize = (b: number) => (b < 1024 ? `${b} B` : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`)
const purposeLabel = (p: string) => PURPOSE_OPTIONS.find((o) => o.value === p)?.label ?? p

/** Estimates how many cards fit the visible viewport, so the backend only ever sends one screen's worth. */
function useScreenPageSize() {
  const [size, setSize] = useState(12)
  useEffect(() => {
    const CARD_W = 300
    const CARD_H = 200
    const calc = () => {
      const cols = Math.max(1, Math.floor((window.innerWidth - 120) / CARD_W))
      const rows = Math.max(2, Math.floor((window.innerHeight - 320) / CARD_H))
      setSize(Math.max(6, Math.min(24, cols * rows)))
    }
    calc()
    window.addEventListener('resize', calc)
    return () => window.removeEventListener('resize', calc)
  }, [])
  return size
}

/** Debounces a fast-changing value (the search box) so we don't hit the backend on every keystroke. */
function useDebounced<T>(value: T, delayMs: number) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(t)
  }, [value, delayMs])
  return debounced
}

function DocChip({ lead, docId, fileName, label, size }: { lead: number; docId: number; fileName: string; label: string; size: number }) {
  const open = async () => {
    try {
      await openFormLeadDocument(lead, docId, fileName)
    } catch {
      toast.error('Could not open document')
    }
  }
  return (
    <button type="button" onClick={open}
      className="flex items-center gap-1.5 rounded-full border border-white/50 bg-white/30 px-2.5 py-1 text-xs font-medium text-ink hover:bg-white/50">
      <FiDownload className="h-3 w-3 shrink-0" />
      <span className="truncate">{label}</span>
      <span className="text-muted">· {fmtSize(size)}</span>
    </button>
  )
}

function LeadCard({ lead, onOpen }: { lead: FormLead; onOpen: () => void }) {
  return (
    <button type="button" onClick={onOpen} className="text-left">
      <Card className="h-full cursor-pointer transition-transform hover:-translate-y-0.5 hover:shadow-lg">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate font-bold">{lead.full_name}</p>
            <p className="truncate text-xs text-muted">{lead.email}</p>
          </div>
          <Badge tone={lead.edubao_account_opened ? 'green' : 'gray'}>
            {lead.edubao_account_opened ? 'Edubao done' : 'Edubao pending'}
          </Badge>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Badge tone="brand">{purposeLabel(lead.purpose)}</Badge>
          <span className="text-xs text-muted">{lead.phone_number}</span>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs text-muted">
          <span>{lead.documents.length} document{lead.documents.length === 1 ? '' : 's'}</span>
          <span>{fmtDate(lead.created_at)}</span>
        </div>
      </Card>
    </button>
  )
}

function LeadDetail({ lead, onClose }: { lead: FormLead; onClose: () => void }) {
  const [updateStatus, { isLoading: updating }] = useUpdateFormLeadStatusMutation()
  const [deleteLead, { isLoading: deleting }] = useDeleteFormLeadMutation()

  const toggleDone = async () => {
    try {
      await updateStatus({ id: lead.id, edubao_account_opened: !lead.edubao_account_opened }).unwrap()
      toast.success(lead.edubao_account_opened ? 'Marked Edubao account as pending' : 'Marked Edubao account opening as done')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const remove = async () => {
    if (!window.confirm(`Delete the submission from ${lead.full_name}? This cannot be undone.`)) return
    try {
      await deleteLead(lead.id).unwrap()
      toast.success('Submission deleted')
      onClose()
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div><p className="text-xs font-semibold uppercase text-muted">Full name</p><p className="font-semibold">{lead.full_name}</p></div>
        <div><p className="text-xs font-semibold uppercase text-muted">Purpose</p><Badge tone="brand">{purposeLabel(lead.purpose)}</Badge></div>
        <div><p className="text-xs font-semibold uppercase text-muted">Email</p><p>{lead.email}</p></div>
        <div><p className="text-xs font-semibold uppercase text-muted">Phone</p><p>{lead.phone_number}</p></div>
        <div><p className="text-xs font-semibold uppercase text-muted">Submitted</p><p>{fmtDate(lead.created_at)}</p></div>
        <div>
          <p className="text-xs font-semibold uppercase text-muted">Edubao account</p>
          <Badge tone={lead.edubao_account_opened ? 'green' : 'gray'}>{lead.edubao_account_opened ? 'Opened' : 'Pending'}</Badge>
        </div>
      </div>
      <div>
        <p className="mb-2 text-xs font-semibold uppercase text-muted">Documents</p>
        <div className="flex flex-wrap gap-2">
          {lead.documents.map((d) => (
            <DocChip key={d.id} lead={lead.id} docId={d.id} fileName={d.original_file_name} label={d.label} size={d.size} />
          ))}
        </div>
      </div>
      <div className="flex flex-wrap justify-end gap-2 border-t border-white/40 pt-4">
        <Button variant="danger" icon={<FiTrash2 />} loading={deleting} onClick={remove}>
          Delete
        </Button>
        <Button icon={lead.edubao_account_opened ? <FiCircle /> : <FiCheckCircle />} loading={updating} onClick={toggleDone}>
          {lead.edubao_account_opened ? 'Mark as pending' : 'Mark Edubao account opening as done'}
        </Button>
      </div>
    </div>
  )
}

export default function FormLeads() {
  const [searchInput, setSearchInput] = useState('')
  const search = useDebounced(searchInput, 300)
  const [page, setPage] = useState(1)
  const pageSize = useScreenPageSize()
  const [selected, setSelected] = useState<FormLead | null>(null)

  // Any change to the search term or the computed screen size starts back at page 1.
  // (Adjusted during render, per React's guidance, rather than in an effect — no extra render pass.)
  const filterKey = `${search}|${pageSize}`
  const [prevFilterKey, setPrevFilterKey] = useState(filterKey)
  if (filterKey !== prevFilterKey) {
    setPrevFilterKey(filterKey)
    setPage(1)
  }

  const { data, isLoading, isFetching } = useGetFormLeadsQuery({ search, page, page_size: pageSize })
  const items = data?.items ?? []
  const pages = data?.pages ?? 0

  // Keep the open modal's data in sync after a mark-done/delete mutation refetches the list.
  const selectedLive = selected ? items.find((i) => i.id === selected.id) ?? null : null

  return (
    <>
      <PageHeader title="Form Leads" subtitle="Documents submitted by students, job seekers and other applicants through the public upload form"
        action={
          <div className="relative">
            <FiSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <Input placeholder="Search by name, phone or email…" value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)} className="w-72 pl-9" />
          </div>
        } />

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: pageSize }, (_, i) => <div key={i} className="h-40 animate-pulse rounded-2xl bg-white/40" />)}
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <Card><p className="py-8 text-center text-sm text-muted">{search ? 'No matching submissions.' : 'No submissions yet.'}</p></Card>
      )}

      {!isLoading && items.length > 0 && (
        <div className={`grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 ${isFetching ? 'opacity-60' : ''}`}>
          {items.map((lead) => <LeadCard key={lead.id} lead={lead} onOpen={() => setSelected(lead)} />)}
        </div>
      )}

      {pages > 1 && (
        <div className="mt-5 flex items-center justify-center gap-3">
          <Button variant="secondary" icon={<FiChevronLeft />} disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</Button>
          <span className="text-sm text-muted">Page {page} of {pages} · {data?.total} total</span>
          <Button variant="secondary" icon={<FiChevronRight />} disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Next</Button>
        </div>
      )}

      <Modal open={!!selected} title="Submission details" onClose={() => setSelected(null)}>
        {(selectedLive ?? selected) && <LeadDetail lead={(selectedLive ?? selected)!} onClose={() => setSelected(null)} />}
      </Modal>
    </>
  )
}
