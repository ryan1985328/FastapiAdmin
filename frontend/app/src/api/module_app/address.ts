import { http } from '@/http'

const ADDRESS_BASE_URL = '/app/user/addresses'

export interface AppUserAddress {
  id: number
  receiver_name: string
  receiver_mobile: string
  province: string
  city: string
  district: string
  detail_address: string
  postal_code?: string | null
  is_default: boolean
}

export interface AppUserAddressForm {
  receiver_name: string
  receiver_mobile: string
  province: string
  city: string
  district: string
  detail_address: string
  postal_code?: string
  is_default: boolean
}

const AppUserAddressAPI = {
  list(): Promise<AppUserAddress[]> {
    // 地址由用户随时增删改，不能命中 Alova 默认的 GET 缓存。
    return http.Get(ADDRESS_BASE_URL, { cacheFor: 0 })
  },

  detail(id: number): Promise<AppUserAddress> {
    return http.Get(`${ADDRESS_BASE_URL}/${id}`, { cacheFor: 0 })
  },

  create(body: AppUserAddressForm): Promise<AppUserAddress> {
    return http.Post(ADDRESS_BASE_URL, body)
  },

  update(id: number, body: Partial<AppUserAddressForm>): Promise<AppUserAddress> {
    return http.Put(`${ADDRESS_BASE_URL}/${id}`, body)
  },

  remove(id: number): Promise<void> {
    return http.Delete(`${ADDRESS_BASE_URL}/${id}`)
  },

  setDefault(id: number): Promise<AppUserAddress> {
    return http.Put(`${ADDRESS_BASE_URL}/${id}/default`, {})
  },
}

export default AppUserAddressAPI
