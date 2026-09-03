import { http } from '@/http'

const APP_NOTICE_BASE_URL = '/app/notices'

export const AppNoticeAPI = {
  list(params?: AppNoticePageParams): Promise<AppNoticePage> {
    return http.Get(APP_NOTICE_BASE_URL, {
      params: params ?? {},
      meta: { ignoreAuth: true, authRole: 'visitor' },
    })
  },

  detail(id: number): Promise<AppNoticeDetail> {
    return http.Get(`${APP_NOTICE_BASE_URL}/${id}`, {
      meta: { ignoreAuth: true, authRole: 'visitor' },
    })
  },
}

export interface AppNoticePageParams {
  page_no?: number
  page_size?: number
}

export interface AppNoticeListItem {
  id: number
  notice_title: string
  notice_type: string
  description?: string | null
  created_time?: string | null
}

export interface AppNoticeDetail extends AppNoticeListItem {
  notice_content?: string | null
}

export interface AppNoticePage {
  page_no: number
  page_size: number
  total: number
  has_next: boolean
  items: AppNoticeListItem[]
}

export default AppNoticeAPI
