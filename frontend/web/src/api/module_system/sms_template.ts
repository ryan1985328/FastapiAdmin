import { request } from "@utils";

const API_PATH = "/system/sms_template";

const SmsTemplateAPI = {
  getSmsTemplateList(query: SmsTemplatePageQuery) {
    return request<ApiResponse<PageResult<SmsTemplateTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getSmsTemplateDetail(query: number) {
    return request<ApiResponse<SmsTemplateTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  createSmsTemplate(body: SmsTemplateForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateSmsTemplate(id: number, body: SmsTemplateForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  batchSmsTemplate(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },
};

export default SmsTemplateAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

/** 列表查询参数 */
export interface SmsTemplatePageQuery extends PageQuery, UserByQueryParams {
  name?: string;
  scene?: string;
  provider?: "aliyun";
  status?: number;
}

/** 列表展示项 */
export interface SmsTemplateTable extends BaseType {
  name?: string;
  scene?: string;
  provider?: "aliyun";
  provider_template_code?: string;
  param_schema?: string[];
  status?: number;
}

/** 新增/修改表单参数 */
export interface SmsTemplateForm extends BaseFormType {
  name?: string;
  scene?: string;
  provider?: "aliyun";
  provider_template_code?: string;
  param_schema?: string[];
  status?: number;
}
