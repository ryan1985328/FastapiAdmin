import { http } from '@/http'
import { HttpStatus, ResultEnum } from '@/http/tools/enum'

const KYC_BASE_URL = '/app/kyc'

export const AppKycAPI = {
  getMine(): Promise<AppKycInfo | null> {
    return http.Get(`${KYC_BASE_URL}/mine`)
  },

  async uploadImage(body: { filePath: string, name?: string }): Promise<AppKycUploadResult> {
    const response = await http.Post(`${KYC_BASE_URL}/upload`, body, { requestType: 'upload' }) as UploadResponse
    const raw = typeof response.data === 'string' ? JSON.parse(response.data) as ApiResponse<AppKycUploadResult> : response.data
    if (response.statusCode !== HttpStatus.SUCCESS || raw.code !== ResultEnum.SUCCESS || !raw.data)
      throw new Error(raw.msg || '身份证图片上传失败')
    return raw.data
  },

  submit(body: AppKycSubmission): Promise<AppKycInfo> {
    return http.Post(`${KYC_BASE_URL}/submit`, body)
  },

  resubmit(body: AppKycSubmission): Promise<AppKycInfo> {
    return http.Post(`${KYC_BASE_URL}/resubmit`, body)
  },
}

export interface AppKycSubmission {
  real_name: string
  id_card_no: string
  id_card_front: string
  id_card_back: string
}

export interface AppKycInfo extends BaseType {
  app_user_id: number
  real_name?: string | null
  id_card_no: string
  id_card_front?: string | null
  id_card_back?: string | null
  status: 0 | 1 | 2
  review_remark?: string | null
  reviewed_at?: string | null
}

export interface AppKycUploadResult {
  file_path?: string | null
  file_name?: string | null
  origin_name?: string | null
  file_url?: string | null
}

interface UploadResponse {
  statusCode: number
  data: string | ApiResponse<AppKycUploadResult>
}

interface ApiResponse<T> {
  code: number
  msg: string
  data: T | null
}

export default AppKycAPI
