import { http } from '@/http'

const APP_ORDER_BASE_URL = '/app/order'

export const AppOrderAPI = {
  create(body: AppOrderCreate): Promise<AppOrder> {
    return http.Post(APP_ORDER_BASE_URL, body)
  },

  list(params?: AppOrderPageParams): Promise<AppOrderPage> {
    return http.Get(`${APP_ORDER_BASE_URL}/list`, {
      params: params ?? {},
      cacheFor: 0,
    })
  },

  detail(id: number): Promise<AppOrder> {
    return http.Get(`${APP_ORDER_BASE_URL}/${id}`, { cacheFor: 0 })
  },

  pay(id: number): Promise<AppOrder> {
    return http.Post(`${APP_ORDER_BASE_URL}/${id}/pay`, {})
  },

  cancel(id: number): Promise<AppOrder> {
    return http.Post(`${APP_ORDER_BASE_URL}/${id}/cancel`, {})
  },
}

export interface AppOrderCreate {
  product_id: number
  quantity: number
}

export interface AppOrderPageParams {
  page_no?: number
  page_size?: number
}

export type AppOrderStatus = 'PENDING_PAYMENT' | 'PAID' | 'CANCELLED'

export interface AppOrderItem {
  id: number
  product_id?: number | null
  product_name: string
  product_cover?: string | null
  unit_price: string
  quantity: number
  subtotal: string
}

export interface AppOrder {
  id: number
  order_no: string
  total_amount: string
  status: AppOrderStatus
  created_time?: string | null
  updated_time?: string | null
  paid_time?: string | null
  cancelled_time?: string | null
  items: AppOrderItem[]
}

export interface AppOrderPage {
  page_no: number
  page_size: number
  total: number
  has_next: boolean
  items: AppOrder[]
}

export default AppOrderAPI
