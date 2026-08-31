import { request } from "@utils";

const API_PATH = "/system/sms_channel";

const SmsChannelAPI = {
  getSmsChannelList(query: SmsChannelPageQuery) {
    return request<ApiResponse<PageResult<SmsChannelTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getSmsChannelDetail(query: number) {
    return request<ApiResponse<SmsChannelTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  createSmsChannel(body: SmsChannelForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateSmsChannel(id: number, body: SmsChannelForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  batchSmsChannel(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  setDefaultSmsChannel(id: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/default/${id}`,
      method: "patch",
    });
  },

  testSendSmsChannel(id: number, body: SmsTestSendForm) {
    return request<ApiResponse<SmsTestSendResult>>({
      url: `${API_PATH}/test-send/${id}`,
      method: "post",
      data: body,
    });
  },
};

export default SmsChannelAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

/** 列表查询参数 */
export interface SmsChannelPageQuery extends PageQuery, UserByQueryParams {
  name?: string;
  provider?: "aliyun";
  status?: number;
}

/** 列表展示项 */
export interface SmsChannelTable extends BaseType {
  name?: string;
  provider?: "aliyun";
  access_key_id?: string;
  sign_name?: string;
  status?: number;
  is_default?: boolean;
  has_secret?: boolean;
}

/** 新增/修改表单参数 */
export interface SmsChannelForm extends BaseFormType {
  name?: string;
  provider?: "aliyun";
  access_key_id?: string;
  access_key_secret?: string;
  sign_name?: string;
  status?: number;
  is_default?: boolean;
}

export interface SmsTestSendForm {
  mobile: string;
  scene: "register_code" | "login_code" | "reset_password_code";
  params: Record<string, string | number | boolean>;
}

export interface SmsTestSendResult {
  provider?: string;
  success?: boolean;
  code?: string;
  message?: string;
  request_id?: string;
}
