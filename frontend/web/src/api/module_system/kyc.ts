import { request } from "@utils";

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

  createAppUserKyc(body: AppUserKycForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateAppUserKyc(id: number, body: AppUserKycForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
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

  deleteAppUserKyc(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchAppUserKyc(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  exportAppUserKyc(body: AppUserKycPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  downloadTemplateAppUserKyc() {
    return request<Blob>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  importAppUserKyc(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

export default AppUserKycAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

/** 列表查询参数 */
export interface AppUserKycPageQuery extends PageQuery, UserByQueryParams {
  app_user_id?: number;
  real_name?: string;
  id_card_no?: string;
  id_card_front?: string;
  id_card_back?: string;
  status?: number;
  review_remark?: string;
  reviewed_at?: string;
}

/** 列表展示项 */
export interface AppUserKycTable extends BaseType {
  app_user_id?: number;
  real_name?: string;
  id_card_no?: string;
  id_card_front?: string;
  id_card_back?: string;
  status?: number;
  review_remark?: string;
  reviewed_at?: string;
}

/** 新增/修改表单参数 */
export interface AppUserKycForm extends BaseFormType {
  app_user_id?: number;
  real_name?: string;
  id_card_no?: string;
  id_card_front?: string;
  id_card_back?: string;
  status?: number;
  review_remark?: string;
  reviewed_at?: string;
}
