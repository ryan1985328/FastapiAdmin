import { http } from '@/http'
import type { AppUserInfo } from './user'

const AUTH_BASE_URL = '/app/auth'

/** Independent C-end account authentication API. */
const AppAuthAPI = {
  register(body: AppRegisterForm): Promise<AppUserInfo> {
    return http.Post(`${AUTH_BASE_URL}/register`, body, {
      meta: { ignoreAuth: true, authRole: 'visitor' },
    })
  },

  login(body: AppLoginForm): Promise<AppLoginResult> {
    return http.Post(`${AUTH_BASE_URL}/login`, body, {
      meta: { ignoreAuth: true, authRole: 'login' },
    })
  },

  refreshToken(body: AppRefreshTokenBody): Promise<AppTokenResult> {
    return http.Post(`${AUTH_BASE_URL}/refresh`, body, {
      meta: { ignoreAuth: true, silent: true, authRole: 'refreshToken' },
    })
  },

  getCurrentUser(): Promise<AppUserInfo> {
    return http.Get(`${AUTH_BASE_URL}/me`)
  },

  logout(): Promise<void> {
    return http.Post(`${AUTH_BASE_URL}/logout`, {})
  },
}

export default AppAuthAPI

export interface AppRegisterForm {
  username: string
  password: string
  nickname?: string
  avatar?: string
  mobile?: string
}

export interface AppLoginForm {
  username: string
  password: string
  remember?: boolean
}

export interface AppRefreshTokenBody {
  refresh_token: string
}

export interface AppTokenResult {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AppLoginResult extends AppTokenResult {
  user_info: AppUserInfo
}
