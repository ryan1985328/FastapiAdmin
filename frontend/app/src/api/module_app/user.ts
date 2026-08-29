import { http } from '@/http'

const USER_BASE_URL = '/app/user'

/** Independent C-end user API. */
const AppUserAPI = {
  /** Fetch the authenticated App user's profile. */
  getProfile(): Promise<AppUserInfo> {
    return http.Get(`${USER_BASE_URL}/profile`)
  },
}

export default AppUserAPI

export interface AppUserInfo {
  id: number
  uuid?: string
  username: string
  nickname: string
  avatar?: string | null
  mobile?: string | null
  status: number
  created_time?: string
  updated_time?: string
}
