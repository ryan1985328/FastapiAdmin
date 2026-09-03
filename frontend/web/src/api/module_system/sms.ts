import { request } from "@utils";

const API_PATH = "/system/sms";

const SmsSettingsAPI = {
  getSettings() {
    return request<ApiResponse<SmsSettings>>({
      url: `${API_PATH}/settings`,
      method: "get",
    });
  },

  updateSettings(body: SmsSettingsUpdate) {
    return request<ApiResponse<SmsSettings>>({
      url: `${API_PATH}/settings`,
      method: "put",
      data: body,
    });
  },

  testSend(body: SmsSettingsTestSend) {
    return request<ApiResponse<SmsSettingsTestSendResult>>({
      url: `${API_PATH}/settings/test-send`,
      method: "post",
      data: body,
    });
  },
};

export default SmsSettingsAPI;

export type SmsProvider = "aliyun" | "tencent";
export type SmsScene = "register_code" | "login_code" | "reset_password_code";

export interface SmsTemplateSettings {
  register_code: string;
  login_code: string;
  reset_password_code: string;
}

export interface SmsProviderSettings {
  enabled: boolean;
  access_key_id: string;
  has_secret: boolean;
  sms_sdk_app_id?: string | null;
  sign_name: string;
  templates: SmsTemplateSettings;
}

export interface SmsSettings {
  sms_enabled: boolean;
  active_provider: SmsProvider;
  aliyun: SmsProviderSettings;
  tencent: SmsProviderSettings;
}

export interface SmsProviderSettingsUpdate {
  enabled: boolean;
  access_key_id: string;
  access_key_secret: string;
  sms_sdk_app_id?: string | null;
  sign_name: string;
  templates: SmsTemplateSettings;
}

export interface SmsSettingsUpdate {
  sms_enabled: boolean;
  active_provider: SmsProvider;
  aliyun: SmsProviderSettingsUpdate;
  tencent: SmsProviderSettingsUpdate;
}

export interface SmsSettingsTestSend {
  provider: SmsProvider;
  mobile: string;
  scene: SmsScene;
  code: string;
}

export interface SmsSettingsTestSendResult {
  provider?: string;
  success?: boolean;
  code?: string;
  message?: string;
  request_id?: string;
}
