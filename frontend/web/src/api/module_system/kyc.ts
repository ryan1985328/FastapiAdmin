import { request } from "@utils";
import type { AppUserKycStatus } from "./app_user";

// API 前缀来自分系统包 module_xxx → /xxx
// 对齐 module_custom/item：业务接口固定为 /{prefix}/{module_name}
const API_PATH = "/system/kyc";

const AppUserKycAPI = {
  getAppUserKycList(query: AppUserKycPageQuery) {
    return request<ApiResponse<PageResult<AppUserKycTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getAppUserKycDetail(query: number) {
    return request<ApiResponse<AppUserKycTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  reviewAppUserKyc(id: number, body: { status: 1 | 2; review_remark?: string }) {
    return request<ApiResponse<AppUserKycTable>>({
      url: `${API_PATH}/review/${id}`,
      method: "post",
      data: body,
    });
  },

  downloadKycImage(id: number, side: "front" | "back") {
    return request<Blob>({
      url: `${API_PATH}/file/${id}/${side}`,
      method: "get",
      responseType: "blob",
    });
  },
};

export default AppUserKycAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

/** 列表查询参数 */
export interface AppUserKycPageQuery extends PageQuery {
  keyword?: string;
  kyc_status?: AppUserKycStatus;
  created_time?: string[];
  order_by?: string;
}

export interface AppUserKycUserSummary {
  id: number;
  username: string;
  nickname: string;
  mobile?: string | null;
}

/** 列表展示项 */
export interface AppUserKycTable extends BaseType {
  app_user_id?: number;
  app_user?: AppUserKycUserSummary | null;
  real_name?: string;
  id_card_no?: string;
  id_card_front?: string;
  id_card_back?: string;
  status?: number;
  review_remark?: string;
  reviewed_at?: string;
}
