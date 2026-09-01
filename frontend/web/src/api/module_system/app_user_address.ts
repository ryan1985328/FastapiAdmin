import { request } from "@utils";

const API_PATH = "/system/app_user_address";

const AppUserAddressAPI = {
  getAppUserAddressList(query: AppUserAddressPageQuery) {
    return request<ApiResponse<PageResult<AppUserAddressTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getAppUserAddressDetail(id: number) {
    return request<ApiResponse<AppUserAddressTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },
};

export default AppUserAddressAPI;

export interface AppUserAddressPageQuery extends PageQuery {
  keyword?: string;
  is_default?: boolean;
  user_id?: number;
  province?: string;
  city?: string;
  district?: string;
  created_time?: string[];
  order_by?: string;
}

export interface AppUserAddressUserSummary {
  id: number;
  username: string;
  nickname: string;
  mobile?: string | null;
}

export interface AppUserAddressTable extends BaseType {
  user_id?: number;
  app_user?: AppUserAddressUserSummary | null;
  receiver_name?: string;
  receiver_mobile?: string;
  province?: string;
  city?: string;
  district?: string;
  detail_address?: string;
  postal_code?: string | null;
  is_default?: boolean;
  created_time?: string;
  updated_time?: string;
}
