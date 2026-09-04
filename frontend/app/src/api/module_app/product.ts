import { http } from '@/http'

const APP_PRODUCT_BASE_URL = '/app/product'

export const AppProductAPI = {
  list(params?: AppProductPageParams): Promise<AppProductPage> {
    return http.Get(`${APP_PRODUCT_BASE_URL}/list`, {
      params: params ?? {},
      meta: { ignoreAuth: true, authRole: 'visitor' },
    })
  },

  detail(id: number): Promise<AppProductDetail> {
    return http.Get(`${APP_PRODUCT_BASE_URL}/${id}`, {
      meta: { ignoreAuth: true, authRole: 'visitor' },
    })
  },
}

export interface AppProductPageParams {
  page_no?: number
  page_size?: number
  keyword?: string
}

export interface AppProductListItem {
  id: number
  name: string
  cover_url?: string | null
  price: string
  stock: number
  sold_out: boolean
}

export interface AppProductDetail extends AppProductListItem {
  description?: string | null
}

export interface AppProductPage {
  page_no: number
  page_size: number
  total: number
  has_next: boolean
  items: AppProductListItem[]
}

export default AppProductAPI
