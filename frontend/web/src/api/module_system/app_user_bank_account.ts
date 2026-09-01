import { request } from "@utils";

const API_PATH = "/system/app_user_bank_account";

const AppUserBankAccountAPI = {
  getAppUserBankAccountList(query: AppUserBankAccountPageQuery) {
    return request<ApiResponse<PageResult<AppUserBankAccountTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getAppUserBankAccountDetail(id: number) {
    return request<ApiResponse<AppUserBankAccountTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  changeAppUserBankAccountStatus(id: number, action: AppUserBankAccountStatusAction) {
    return request<ApiResponse<AppUserBankAccountTable>>({
      url: `${API_PATH}/status/${id}`,
      method: "patch",
      data: { action },
    });
  },
};

export default AppUserBankAccountAPI;

export interface AppUserBankAccountPageQuery extends PageQuery {
  keyword?: string;
  user_id?: number;
  bank_name?: string;
  account_name?: string;
  branch_name?: string;
  is_default?: boolean;
  status?: AppUserBankAccountStatus;
  kyc_status?: AppUserKycStatus;
  created_time?: string[];
  updated_time?: string[];
  order_by?: string;
}

export type AppUserBankAccountStatus = 0 | 1;
export type AppUserBankAccountStatusAction = "enable" | "disable";
export type AppUserKycStatus = "unverified" | "pending" | "verified" | "rejected";

export interface AppUserBankAccountUserSummary {
  id: number;
  username: string;
  nickname: string;
  mobile?: string | null;
  kyc_status?: AppUserKycStatus;
}

export interface AppUserBankAccountTable extends BaseType {
  id?: number;
  user_id?: number;
  app_user?: AppUserBankAccountUserSummary | null;
  bank_name?: string;
  bank_code?: string | null;
  account_name?: string;
  masked_card_number?: string;
  branch_name?: string | null;
  is_default?: boolean;
  status?: AppUserBankAccountStatus;
  created_time?: string;
  updated_time?: string;
}
