import { http } from '@/http'

const USER_BASE_URL = '/app/user'

/** Independent C-end user API. */
const AppUserAPI = {
  /** Fetch the authenticated App user's profile. */
  getProfile(): Promise<AppUserInfo> {
    return http.Get(`${USER_BASE_URL}/profile`)
  },

  /** Update the minimal App self-service profile field. */
  updateProfile(body: AppUserProfileUpdateForm): Promise<AppUserInfo> {
    return http.Put(`${USER_BASE_URL}/profile`, body)
  },
}

export default AppUserAPI

export interface AppUserProfileUpdateForm {
  nickname: string
}

export interface AppUserInfo {
  id: number
  uuid?: string
  username: string
  nickname: string
  avatar?: string | null
  mobile?: string | null
  status: number
  referral_code?: string
  referrer_id?: number | null
  referrer_bound_at?: string | null
  referrer?: {
    id: number
    username: string
    nickname: string
    mobile?: string | null
    referral_code: string
  } | null
  has_referrer?: boolean
  kyc_status?: 'unverified' | 'pending' | 'verified' | 'rejected'
  kyc_reviewed_at?: string | null
  created_time?: string
  updated_time?: string
}
