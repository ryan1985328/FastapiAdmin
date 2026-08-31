import { request } from "@utils";

const API_PATH = "/system/app_user";

const AppUserAPI = {
  getAppUserList(query: AppUserPageQuery) {
    return request<ApiResponse<PageResult<AppUserTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getAppUserDetail(id: number) {
    return request<ApiResponse<AppUserTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  updateAppUser(id: number, body: AppUserForm) {
    return request<ApiResponse<AppUserTable>>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  batchAppUser(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  changeAppUserStatus(id: number, action: AppUserStatusAction) {
    return request<ApiResponse<AppUserTable>>({
      url: `${API_PATH}/status/${id}`,
      method: "patch",
      data: { action },
    });
  },

  bindAppUserReferrer(id: number, referral_code: string) {
    return request<ApiResponse<AppUserTable>>({
      url: `${API_PATH}/referrer/bind/${id}`,
      method: "post",
      data: { referral_code },
    });
  },

  resetAppUserPassword(id: number, body: ResetPasswordForm) {
    return request<ApiResponse<AppUserTable>>({
      url: `${API_PATH}/password/reset/${id}`,
      method: "put",
      data: body,
    });
  },
};

export default AppUserAPI;

export interface AppUserPageQuery extends PageQuery {
  keyword?: string;
  id?: number;
  username?: string;
  nickname?: string;
  mobile?: string;
  status?: AppUserStatus;
  referral_code?: string;
  referrer?: string;
  has_referrer?: boolean;
  kyc_status?: AppUserKycStatus;
  created_time?: string[];
}

export type AppUserStatus = 0 | 1 | 2;
export type AppUserKycStatus = "unverified" | "pending" | "verified" | "rejected";
export type AppUserStatusAction = "enable" | "disable" | "freeze" | "unfreeze";

export interface AppUserReferrerSummary {
  id: number;
  username: string;
  nickname: string;
  mobile?: string;
  referral_code: string;
}

export interface AppUserTable extends BaseType {
  id?: number;
  username?: string;
  nickname?: string;
  avatar?: string;
  mobile?: string;
  status?: AppUserStatus;
  referral_code?: string;
  referrer_id?: number;
  referrer_bound_at?: string;
  referrer?: AppUserReferrerSummary;
  has_referrer?: boolean;
  kyc_status?: AppUserKycStatus;
  kyc_reviewed_at?: string;
  created_time?: string;
  updated_time?: string;
}

export interface AppUserForm extends BaseFormType {
  nickname?: string;
  avatar?: string;
  mobile?: string;
}

export interface ResetPasswordForm {
  password: string;
}
