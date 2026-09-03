import type { AppLoginForm, AppLoginResult, AppMobilePasswordLoginForm, AppMobileSmsLoginForm } from '@/api/module_app/auth'
import type { AppUserInfo } from '@/api/module_app/user'
import { defineStore } from 'pinia'
import AppAuthAPI from '@/api/module_app/auth'
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/constants'
import { Storage } from '@/utils/storage'

export type AppSessionStatus = 'unknown' | 'restoring' | 'authenticated' | 'guest'

let sessionRestorePromise: Promise<boolean> | null = null
let sessionHasBeenResolved = false

export const useUserStore = defineStore('appUserInfo', {
  state: () => ({
    // userInfo 由 persist 插件自动持久化（存储 key 即 store id：appUserInfo），无需手动读写 Storage
    userInfo: null as AppUserInfo | null,
    isLoggingIn: false,
    // sessionStatus 是运行时会话状态；启动时必须重新通过 /me 确认，不能只相信持久化资料。
    sessionStatus: 'unknown' as AppSessionStatus,
  }),

  getters: {
    /** 是否已登录：只有完成当前运行时会话校验且凭据、用户资料同时存在才算登录。 */
    isLogin: state => state.sessionStatus === 'authenticated' && !!state.userInfo,
  },

  // 统一的登录处理方法
  actions: {
    // 获取访问 token
    getAccessToken(): string | null {
      return Storage.get<string>(ACCESS_TOKEN_KEY) || null
    },

    // 设置访问 token
    setAccessToken(token: string): void {
      Storage.set(ACCESS_TOKEN_KEY, token)
    },

    // 获取刷新 token
    getRefreshToken(): string | null {
      return Storage.get<string>(REFRESH_TOKEN_KEY) || null
    },

    // 设置刷新 token
    setRefreshToken(token: string): void {
      Storage.set(REFRESH_TOKEN_KEY, token)
    },

    // 清除所有 token
    clearTokens(): void {
      Storage.remove(ACCESS_TOKEN_KEY)
      Storage.remove(REFRESH_TOKEN_KEY)
    },

    // 获取用户信息（直接读取响应式 state）
    getUserInfo(): AppUserInfo | null {
      return this.userInfo
    },

    // 设置用户信息（合并更新 state，由 persist 插件自动持久化）
    setUserInfo(userInfo: Partial<AppUserInfo>): void {
      this.userInfo = { ...(this.userInfo ?? {}), ...userInfo } as AppUserInfo
    },

    // 清除用户信息（置空 state，由 persist 插件自动同步存储）
    clearUserInfo(): void {
      this.userInfo = null
    },

    // 清除所有缓存信息
    clearAll(): void {
      this.clearTokens()
      this.clearUserInfo()
      this.sessionStatus = 'guest'
      sessionHasBeenResolved = true
    },

    /** 是否已登录（仅判断，不跳转；跳转由路由守卫与 HTTP 拦截器统一处理） */
    isLoggedIn(): boolean {
      return this.sessionStatus === 'authenticated' && !!(this.getAccessToken() && this.userInfo)
    },

    /** 启动恢复期间隐藏页面，避免在认证结果确定前展示私有内容。 */
    isSessionRestoring(): boolean {
      return this.sessionStatus === 'unknown' || this.sessionStatus === 'restoring'
    },

    /**
     * 恢复 App 会话：
     * - 有效 access token 通过 /me 确认；
     * - access token 失效时由现有 HTTP 刷新队列刷新一次并重试；
     * - 只有 refresh token 而没有 access token 时，直接按既有 refresh 合约补发 token；
     * - 无法恢复时清除 access/refresh/user，禁止残留半登录状态。
     */
    async restoreSession(): Promise<boolean> {
      if (sessionRestorePromise)
        return sessionRestorePromise

      if (sessionHasBeenResolved && this.sessionStatus === 'authenticated' && this.isLoggedIn())
        return true
      if (sessionHasBeenResolved && this.sessionStatus === 'guest' && !this.getAccessToken() && !this.getRefreshToken())
        return false

      this.sessionStatus = 'restoring'
      sessionRestorePromise = (async () => {
        const accessToken = this.getAccessToken()
        const refreshToken = this.getRefreshToken()

        try {
          if (!accessToken && !refreshToken) {
            this.clearUserInfo()
            this.sessionStatus = 'guest'
            sessionHasBeenResolved = true
            return false
          }

          if (!accessToken && refreshToken) {
            const refreshed = await AppAuthAPI.refreshToken({ refresh_token: refreshToken })
            if (!refreshed?.access_token)
              throw new Error('登录已过期')
            this.setAccessToken(refreshed.access_token)
            if (refreshed.refresh_token)
              this.setRefreshToken(refreshed.refresh_token)
          }

          const userInfo = await AppAuthAPI.getCurrentUser()
          this.setUserInfo(userInfo)
          this.sessionStatus = 'authenticated'
          sessionHasBeenResolved = true
          return true
        }
        catch (error) {
          console.error('恢复 App 会话失败', error)
          this.clearTokens()
          this.clearUserInfo()
          this.sessionStatus = 'guest'
          sessionHasBeenResolved = true
          return false
        }
        finally {
          sessionRestorePromise = null
        }
      })()

      return sessionRestorePromise
    },

    async handleLogin(loginFn: () => Promise<AppLoginResult>, loginType: string): Promise<AppLoginResult> {
      if (this.isLoggingIn)
        throw new Error('登录中，请稍后')

      this.isLoggingIn = true
      try {
        const result = await loginFn()
        this.setAccessToken(result.access_token)
        this.setRefreshToken(result.refresh_token)

        // 登录成功后获取用户信息；/me 失败时由 getInfo 清理半登录状态并让调用方展示失败。
        await this.getInfo()
        this.sessionStatus = 'authenticated'
        sessionHasBeenResolved = true

        return result
      }
      catch (error) {
        console.error(`${loginType}登录失败`, error)
        throw error
      }
      finally {
        this.isLoggingIn = false
      }
    },

    // 账号密码登录
    async login(data: AppLoginForm): Promise<AppLoginResult> {
      return this.handleLogin(() => AppAuthAPI.login(data), '账号密码')
    },

    // 手机号密码登录
    async loginByPassword(data: AppMobilePasswordLoginForm): Promise<AppLoginResult> {
      return this.handleLogin(() => AppAuthAPI.loginByPassword(data), '手机号密码')
    },

    // 手机号验证码登录
    async loginBySms(data: AppMobileSmsLoginForm): Promise<AppLoginResult> {
      return this.handleLogin(() => AppAuthAPI.loginBySms(data), '手机号验证码')
    },

    // 获取用户信息
    // 微信登录保留 composable 兼容入口；App 用户 OAuth/微信身份本阶段不接入。
    async wxLogin(_data: { code: string, nickname?: string, avatar?: string }): Promise<never> {
      throw new Error('App 用户微信登录尚未接入')
    },

    async wxPhoneLogin(_data: { code: string }): Promise<never> {
      throw new Error('App 用户手机号登录尚未接入')
    },
    async getInfo(): Promise<AppUserInfo> {
      try {
        const userInfoData = await AppAuthAPI.getCurrentUser()
        this.setUserInfo(userInfoData)
        return userInfoData
      }
      catch (error) {
        console.error('获取用户信息失败', error)
        this.clearAll()
        throw error
      }
    },

    // 登出
    async logout(): Promise<void> {
      try {
        await AppAuthAPI.logout()
      }
      catch (error) {
        console.error('登出失败', error)
      }
      finally {
        this.clearAll() // 清除本地的 token 与用户信息
        // App 是公共访问优先，退出后回到首页而不是强制停留在登录页
        uni.reLaunch({
          url: '/pages/index/index',
        })
      }
    },
  },
})
