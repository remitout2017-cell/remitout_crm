import { baseApi } from '../../store/baseApi'

export interface EdubaoDocument {
  doc_id: string
  name: string
  file_name: string
  url: string
  doc_type: string
  mimetype: string
  size: number
  status: number
  status_name: string
}

export interface EdubaoPayerDocument { doc_id: string; name: string; url: string; doc_type: string }

export interface EdubaoPayer {
  payer_id: number
  name: string
  relationship: string
  transfer_amt: string
  email_id: string
  phone_code: string
  mobile_no: string
  date_of_birth: string
  nationality: string
  country: string
  state: string
  city: string
  documents: EdubaoPayerDocument[]
}

export interface EdubaoBankAccount {
  holder_name: string
  iban_number: string
  bic_swift_code: string
  account_number: string
  bank_name: string
  bank_address: string
  date_of_arrival: string
}

/**
 * Edubao's raw "Get Individual Lead" (5f) response. Several fields use bracket-notation keys
 * (e.g. "country[name]", "nationality[name]") that aren't valid TS identifiers — read those via `field()`.
 * Kept loose (`Record<string, unknown>`) since the manual doesn't guarantee every field is always present.
 */
export type EdubaoLead = Record<string, unknown> & {
  lead_id?: number
  account_id?: string
  first_name?: string
  last_name?: string
  title?: string
  gender?: string
  email_id?: string
  phone_code?: string
  mobile_no?: string
  passport_num?: string
  date_of_birth?: string
  passport_issued_date?: string
  passport_valid_upto?: string
  kyc_result_status?: string | null
  visa_eligibility_doc_type?: string
  blocked_acc_duration?: string
  blocked_acc_amt?: string
  setup_fee?: string
  monthly_fee?: string
  buffer_amount?: string
  total_deposit?: string
  documents?: EdubaoDocument[]
  payers?: EdubaoPayer[]
  bank_accounts?: EdubaoBankAccount[]
}

/** Safe reader for bracket-notation / possibly-missing keys, e.g. field(lead, "country[name]"). */
export const field = (data: EdubaoLead | undefined, key: string): string => {
  const v = data?.[key]
  return v == null || v === '' ? '—' : String(v)
}

export const edubaoLookupApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getEdubaoLead: b.query<EdubaoLead, { accountId: number; leadId?: number; edubaoAccountId?: string }>({
      query: ({ accountId, leadId, edubaoAccountId }) => ({
        url: `/partners/${accountId}/edubao-lead`,
        params: { lead_id: leadId, edubao_account_id: edubaoAccountId || undefined },
      }),
    }),
  }),
})

export const { useLazyGetEdubaoLeadQuery } = edubaoLookupApi
