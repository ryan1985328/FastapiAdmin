import { http } from '@/http'

const BANK_ACCOUNT_BASE_URL = '/app/user/bank-accounts'

export type AppUserBankAccountStatus = 0 | 1

export interface AppUserBankAccount {
  id: number
  bank_name: string
  bank_code?: string | null
  account_name: string
  masked_card_number: string
  branch_name?: string | null
  is_default: boolean
  status: AppUserBankAccountStatus
}

export interface AppUserBankAccountForm {
  bank_name: string
  bank_code?: string
  account_name: string
  card_number?: string
  branch_name?: string
  is_default: boolean
}

const AppUserBankAccountAPI = {
  list(): Promise<AppUserBankAccount[]> {
    // 银行卡由用户随时增删改，不能命中 Alova 默认的 GET 缓存。
    return http.Get(BANK_ACCOUNT_BASE_URL, { cacheFor: 0 })
  },

  detail(id: number): Promise<AppUserBankAccount> {
    return http.Get(`${BANK_ACCOUNT_BASE_URL}/${id}`, { cacheFor: 0 })
  },

  create(body: AppUserBankAccountForm & { card_number: string }): Promise<AppUserBankAccount> {
    return http.Post(BANK_ACCOUNT_BASE_URL, body)
  },

  update(id: number, body: Partial<AppUserBankAccountForm>): Promise<AppUserBankAccount> {
    return http.Put(`${BANK_ACCOUNT_BASE_URL}/${id}`, body)
  },

  remove(id: number): Promise<void> {
    return http.Delete(`${BANK_ACCOUNT_BASE_URL}/${id}`)
  },

  setDefault(id: number): Promise<AppUserBankAccount> {
    return http.Put(`${BANK_ACCOUNT_BASE_URL}/${id}/default`, {})
  },
}

export default AppUserBankAccountAPI
