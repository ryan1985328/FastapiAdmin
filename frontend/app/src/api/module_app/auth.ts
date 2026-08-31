import type { AppUserInfo } from './user'
import { http } from '@/http'

const AUTH_BASE_URL = '/app/auth'

/** Independent C-end account authentication API. */
const AppAuthAPI = {
  sendCode(body: AppSmsSendCodeForm): Promise<AppSmsSendCodeResult> {
    return http.Post('/app/sms/send-code', body, {
      meta: { ignoreAuth: true, authRole: 'visitor' },
    })
  },

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

  loginByPassword(body: AppMobilePasswordLoginForm): Promise<AppLoginResult> {
    return http.Post(`${AUTH_BASE_URL}/login/password`, body, {
      meta: { ignoreAuth: true, authRole: 'login' },
    })
  },

  loginBySms(body: AppMobileSmsLoginForm): Promise<AppLoginResult> {
    return http.Post(`${AUTH_BASE_URL}/login/sms`, body, {
      meta: { ignoreAuth: true, authRole: 'login' },
    })
  },

  resetPassword(body: AppResetPasswordForm): Promise<void> {
    return http.Post(`${AUTH_BASE_URL}/reset-password`, body, {
      meta: { ignoreAuth: true, authRole: 'visitor' },
    })
  },

  changePassword(body: AppChangePasswordForm): Promise<void> {
    return http.Post(`${AUTH_BASE_URL}/change-password`, body)
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
  mobile: string
  code: string
  password: string
  nickname?: string
  referral_code?: string
}

export interface AppLoginForm {
  username: string
  password: string
  remember?: boolean
}

export interface AppMobilePasswordLoginForm {
  mobile: string
  password: string
  remember?: boolean
}

export interface AppMobileSmsLoginForm {
  mobile: string
  code: string
  remember?: boolean
}

export interface AppSmsSendCodeForm {
  mobile: string
  scene: 'register_code' | 'login_code' | 'reset_password_code'
}

export interface AppSmsSendCodeResult {
  expires_in: number
  resend_after: number
  debug_code?: string | null
}

export interface AppResetPasswordForm {
  mobile: string
  code: string
  new_password: string
}

export interface AppChangePasswordForm {
  current_password: string
  new_password: string
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
