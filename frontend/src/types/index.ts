export interface Student {
  id: number
  first_name: string
  last_name: string
  email: string
  mobile_no: string
  title?: string | null
  gender?: string | null
  city?: string | null
  country?: string | null
  status: string
  nationality?: string | null
  passport_num?: string | null
  created_at: string
}
export type StudentInput = Pick<Student, 'first_name' | 'last_name' | 'email' | 'mobile_no'> &
  Partial<Pick<Student, 'title' | 'gender' | 'city' | 'country'>>

export interface Place { location: string; city: string; state: string; country: string; iso: string }
export const emptyPlace: Place = { location: '', city: '', state: '', country: '', iso: '' }

export interface Step2Input {
  diff_maiden_name: string
  nationality: string
  nationality_iso: string
  date_of_birth: string
  place_of_birth: Place
  passport_num: string
  passport_issued_date: string
  passport_valid_upto: string
  passport_issue_place: Place
}
export interface Step3Input { blocked_acc_amt: string; blocked_acc_duration: string; visa_eligibility_doc_type: string }
export interface Step4Input { terms_and_conditions: boolean }

export interface Submission { step: number; success: boolean; created_at: string }
export interface Lead {
  id: number
  student_id: number
  partner_account_id: number
  edubao_lead_id: number | null
  account_id: string | null
  current_step: number
  status: string
  app_type: number | null
  expected_date_arrival: string | null
  blocked_acc_amt: string | null
  blocked_acc_duration: number | null
  terms_accepted: boolean
  created_at: string
  submissions: Submission[]
}
export interface LeadInput { student_id: number; partner_account_id: number; app_type: number; expected_date_arrival: string }

export interface Partner {
  id: number
  name: string
  environment: string
  login_email: string
  partner_key: string | null
  is_active: boolean
  onboarded: boolean
}
export interface PartnerStart { name: string; environment: 'staging' | 'production'; login_email: string; password: string }

export interface LeadDocument {
  id: number
  lead_id: number
  edubao_doc_id: number | null
  doc_key: string
  original_file_name: string
  mimetype: string
  size: number
  url: string | null
  created_at: string
}

export interface Verification {
  id: number
  lead_id: number
  document_id: number | null
  type: 'face' | 'document'
  result: string | null
  created_at: string
}

export interface Payer {
  id: number
  lead_id: number
  edubao_payer_id: number | null
  payer_account_id: string | null
  first_name: string
  last_name: string
  email: string
  relationship_to_student: string | null
  transfer_amt: string | null
  created_at: string
}

export interface PayerInput {
  id?: number
  title: string
  first_name: string
  last_name: string
  email: string
  phone_code: string
  mobile_number: string
  date_of_birth: string
  relationship: string
  nationality: string
  nationality_iso: string
  birth_place: Place
  street_num: string
  additional_address: string
  postal_code: string
  city: string
  state: string
  country: string
  country_iso: string
  transfer_amt: string
}

/** Edubao's form-required-data: app types, titles, document types — shape isn't fixed, so keep it loose. */
export type FormReferenceData = Record<string, unknown>
