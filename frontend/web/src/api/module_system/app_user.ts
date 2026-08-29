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
  username?: string;
  nickname?: string;
  mobile?: string;
  status?: number;
}

export interface AppUserTable extends BaseType {
  username?: string;
  nickname?: string;
  avatar?: string;
  mobile?: string;
  status?: number;
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
