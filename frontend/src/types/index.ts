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
