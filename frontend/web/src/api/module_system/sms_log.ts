import { request } from "@utils";

const API_PATH = "/system/sms_log";

const SmsLogAPI = {
  getSmsLogList(query: SmsLogPageQuery) {
    return request<ApiResponse<PageResult<SmsLogTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getSmsLogDetail(query: number) {
    return request<ApiResponse<SmsLogTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

};

export default SmsLogAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

/** 列表查询参数 */
export interface SmsLogPageQuery extends PageQuery, UserByQueryParams {
  mobile?: string;
  scene?: string;
  provider?: string;
  status?: number;
}

/** 列表展示项 */
export interface SmsLogTable extends BaseType {
  mobile?: string;
  scene?: string;
  template_code?: string;
  provider?: string;
  status?: number;
  provider_request_id?: string;
  provider_code?: string;
  provider_message?: string;
  sent_at?: string;
}
