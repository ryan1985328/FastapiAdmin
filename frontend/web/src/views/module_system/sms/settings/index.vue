<template>
  <div class="fa-full-height sms-settings-page">
    <ElCard class="fa-card sms-settings-card" shadow="never">
      <template #header>
        <div class="settings-header">
          <div>
            <div class="settings-title">短信配置</div>
            <div class="settings-subtitle">固定管理 Aliyun 与 Tencent Cloud，认证场景模板不可新增或删除。</div>
          </div>
          <ElTag :type="form.sms_enabled ? 'success' : 'info'">
            {{ form.sms_enabled ? "真实发送已开启" : "真实发送已关闭" }}
          </ElTag>
        </div>
      </template>

      <ElForm :model="form" label-position="top" class="sms-form">
        <section class="settings-section global-section">
          <div class="section-heading">
            <div>
              <h2>全局短信设置</h2>
              <p>关闭后不会调用任何真实短信供应商；开发固定验证码仍遵循现有开发/测试约定。</p>
            </div>
          </div>
          <div class="global-grid">
            <ElFormItem label="短信服务">
              <div class="switch-field">
                <ElSwitch v-model="form.sms_enabled" active-text="开启" inactive-text="关闭" />
                <span class="field-hint">{{ form.sms_enabled ? "允许 App 认证短信发送" : "已阻止真实短信发送" }}</span>
              </div>
            </ElFormItem>
            <ElFormItem label="当前供应商">
              <ElRadioGroup v-model="form.active_provider">
                <ElRadio value="aliyun">阿里云</ElRadio>
                <ElRadio value="tencent">腾讯云</ElRadio>
              </ElRadioGroup>
              <div class="field-hint">App 注册、短信登录、重置密码只使用这里选择的供应商。</div>
            </ElFormItem>
          </div>
          <ElAlert
            v-if="form.sms_enabled"
            title="开启后，当前供应商必须已启用并完成凭据、签名和三个认证模板配置。"
            type="warning"
            :closable="false"
            show-icon
          />
        </section>

        <div class="provider-grid">
          <section v-for="provider in PROVIDERS" :key="provider" class="provider-section">
            <div class="provider-heading">
              <div>
                <h2>{{ providerLabel(provider) }}</h2>
                <p>{{ providerDescription(provider) }}</p>
              </div>
              <ElSwitch v-model="form[provider].enabled" active-text="启用" inactive-text="停用" />
            </div>

            <div class="provider-grid-fields">
              <ElFormItem :label="credentialLabel(provider)">
                <ElInput v-model="form[provider].access_key_id" clearable :placeholder="credentialPlaceholder(provider)" />
              </ElFormItem>
              <ElFormItem :label="secretLabel(provider)">
                <ElInput
                  v-model="form[provider].access_key_secret"
                  type="password"
                  show-password
                  clearable
                  :placeholder="secretPlaceholder(provider)"
                />
                <div class="field-hint">
                  <ElTag v-if="configured[provider]" type="success" size="small">密钥已配置（不会回显）</ElTag>
                  <span v-else>未配置密钥</span>
                  <span>留空会保留当前密文。</span>
                </div>
              </ElFormItem>
              <ElFormItem v-if="provider === 'tencent'" label="SMS SDK App ID">
                <ElInput v-model="form[provider].sms_sdk_app_id" clearable placeholder="请输入腾讯云短信 SDK App ID" />
              </ElFormItem>
              <ElFormItem label="短信签名">
                <ElInput v-model="form[provider].sign_name" clearable placeholder="请输入已审核通过的短信签名" />
              </ElFormItem>
            </div>

            <div class="template-section">
              <div class="subsection-heading">认证场景模板</div>
              <div class="template-grid">
                <ElFormItem v-for="template in TEMPLATE_FIELDS" :key="template.key" :label="template.label">
                  <ElInput v-model="form[provider].templates[template.key]" clearable :placeholder="template.placeholder" />
                </ElFormItem>
              </div>
            </div>

            <div class="test-send-panel">
              <div class="subsection-heading">测试发送</div>
              <p class="field-hint">测试发送使用已保存的 {{ providerLabel(provider) }} 配置，请先保存配置。</p>
              <div class="test-send-grid">
                <ElFormItem label="手机号">
                  <ElInput v-model="testForms[provider].mobile" clearable placeholder="请输入接收测试短信的手机号" />
                </ElFormItem>
                <ElFormItem label="场景">
                  <ElSelect v-model="testForms[provider].scene" class="full-width" placeholder="请选择认证场景">
                    <ElOption v-for="scene in SCENE_OPTIONS" :key="scene.key" :label="scene.label" :value="scene.key" />
                  </ElSelect>
                </ElFormItem>
                <ElFormItem label="验证码">
                  <ElInput v-model="testForms[provider].code" maxlength="6" show-word-limit placeholder="6 位数字" />
                </ElFormItem>
                <ElFormItem label=" ">
                  <ElButton v-hasPerm="'module_system:sms_settings:test_send'" type="primary" plain :loading="testLoading[provider]" @click="handleTestSend(provider)">
                    测试发送
                  </ElButton>
                </ElFormItem>
              </div>
            </div>
          </section>
        </div>

        <div class="settings-actions">
          <ElButton v-hasPerm="'module_system:sms_settings:update'" type="primary" :loading="saving" @click="saveSettings">保存配置</ElButton>
        </div>
      </ElForm>
    </ElCard>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import SmsSettingsAPI, {
  type SmsProvider,
  type SmsProviderSettings,
  type SmsProviderSettingsUpdate,
  type SmsScene,
  type SmsSettings,
  type SmsSettingsUpdate,
} from "@/api/module_system/sms";

defineOptions({ name: "SmsSettings", inheritAttrs: false });

const PROVIDERS: SmsProvider[] = ["aliyun", "tencent"];
const TEMPLATE_FIELDS: Array<{ key: keyof SmsProviderSettingsUpdate["templates"]; label: string; placeholder: string }> = [
  { key: "register_code", label: "注册验证码模板", placeholder: "请输入注册验证码模板编码或 ID" },
  { key: "login_code", label: "登录验证码模板", placeholder: "请输入登录验证码模板编码或 ID" },
  { key: "reset_password_code", label: "重置密码模板", placeholder: "请输入重置密码验证码模板编码或 ID" },
];
const SCENE_OPTIONS: Array<{ key: SmsScene; label: string }> = [
  { key: "register_code", label: "注册验证码" },
  { key: "login_code", label: "登录验证码" },
  { key: "reset_password_code", label: "重置密码验证码" },
];

function emptyTemplates() {
  return { register_code: "", login_code: "", reset_password_code: "" };
}

function emptyProvider(): SmsProviderSettingsUpdate {
  return {
    enabled: false,
    access_key_id: "",
    access_key_secret: "",
    sms_sdk_app_id: null,
    sign_name: "",
    templates: emptyTemplates(),
  };
}

const form = reactive<SmsSettingsUpdate>({
  sms_enabled: false,
  active_provider: "aliyun",
  aliyun: emptyProvider(),
  tencent: emptyProvider(),
});
const configured = reactive<Record<SmsProvider, boolean>>({ aliyun: false, tencent: false });
const testLoading = reactive<Record<SmsProvider, boolean>>({ aliyun: false, tencent: false });
const testForms = reactive<Record<SmsProvider, { mobile: string; scene: SmsScene; code: string }>>({
  aliyun: { mobile: "", scene: "register_code", code: "" },
  tencent: { mobile: "", scene: "register_code", code: "" },
});
const saving = ref(false);

function providerLabel(provider: SmsProvider): string {
  return provider === "aliyun" ? "阿里云 Aliyun" : "腾讯云 Tencent Cloud";
}

function providerDescription(provider: SmsProvider): string {
  return provider === "aliyun" ? "Dysmsapi AccessKey 与模板 Code" : "SecretId、SecretKey、SDK App ID 与模板 ID";
}

function credentialLabel(provider: SmsProvider): string {
  return provider === "aliyun" ? "AccessKey ID" : "SecretId";
}

function credentialPlaceholder(provider: SmsProvider): string {
  return provider === "aliyun" ? "请输入 Aliyun AccessKey ID" : "请输入 Tencent SecretId";
}

function secretLabel(provider: SmsProvider): string {
  return provider === "aliyun" ? "AccessKey Secret" : "SecretKey";
}

function secretPlaceholder(provider: SmsProvider): string {
  return configured[provider] ? "留空保留已配置密钥" : `请输入 ${secretLabel(provider)}`;
}

function applyProvider(provider: SmsProvider, value: SmsProviderSettings) {
  form[provider] = {
    enabled: value.enabled,
    access_key_id: value.access_key_id ?? "",
    access_key_secret: "",
    sms_sdk_app_id: value.sms_sdk_app_id ?? null,
    sign_name: value.sign_name ?? "",
    templates: { ...emptyTemplates(), ...(value.templates ?? {}) },
  };
  configured[provider] = Boolean(value.has_secret);
}

function applySettings(value: SmsSettings) {
  form.sms_enabled = value.sms_enabled;
  form.active_provider = value.active_provider;
  applyProvider("aliyun", value.aliyun);
  applyProvider("tencent", value.tencent);
}

async function loadSettings() {
  const response = await SmsSettingsAPI.getSettings();
  const value = response.data.data;
  if (value) applySettings(value);
}

function validateActiveProvider(): boolean {
  const provider = form.active_provider;
  const config = form[provider];
  if (!form.sms_enabled) return true;
  if (!config.enabled) {
    ElMessage.warning(`短信已开启，请先启用当前供应商：${providerLabel(provider)}`);
    return false;
  }
  if (!config.access_key_id || (!config.access_key_secret && !configured[provider])) {
    ElMessage.warning(`${providerLabel(provider)}的凭据尚未配置完整`);
    return false;
  }
  if (!config.sign_name || (provider === "tencent" && !config.sms_sdk_app_id)) {
    ElMessage.warning(`${providerLabel(provider)}的签名或 SDK App ID 尚未配置完整`);
    return false;
  }
  if (TEMPLATE_FIELDS.some((field) => !config.templates[field.key])) {
    ElMessage.warning(`${providerLabel(provider)}的三个认证模板均需配置`);
    return false;
  }
  return true;
}

async function saveSettings() {
  if (!validateActiveProvider() || saving.value) return;
  saving.value = true;
  try {
    const response = await SmsSettingsAPI.updateSettings(form);
    if (response.data.data) applySettings(response.data.data);
    ElMessage.success("短信配置保存成功");
  } finally {
    saving.value = false;
  }
}

async function handleTestSend(provider: SmsProvider) {
  const test = testForms[provider];
  if (!form.sms_enabled) {
    ElMessage.warning("短信服务已关闭，不能发送测试短信");
    return;
  }
  if (!form[provider].enabled) {
    ElMessage.warning(`请先启用${providerLabel(provider)}`);
    return;
  }
  if (!/^\d{6}$/.test(test.code)) {
    ElMessage.warning("测试验证码必须是 6 位数字");
    return;
  }
  testLoading[provider] = true;
  try {
    await SmsSettingsAPI.testSend({ provider, mobile: test.mobile, scene: test.scene, code: test.code });
    ElMessage.success(`${providerLabel(provider)}测试短信发送成功`);
  } finally {
    testLoading[provider] = false;
  }
}

onMounted(() => {
  void loadSettings();
});
</script>

<style scoped>
.sms-settings-page {
  min-height: 0;
  overflow: auto;
}

.sms-settings-card {
  min-height: 100%;
}

.settings-header,
.provider-heading,
.settings-actions,
.switch-field {
  display: flex;
  align-items: center;
}

.settings-header,
.provider-heading {
  gap: 1rem;
  justify-content: space-between;
}

.settings-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.settings-subtitle,
.section-heading p,
.provider-heading p,
.field-hint {
  margin: 0.35rem 0 0;
  font-size: 0.78rem;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.sms-form {
  max-width: 1280px;
}

.settings-section,
.provider-section {
  padding: 1rem;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 0.5rem;
}

.global-section {
  margin-bottom: 1rem;
}

.section-heading h2,
.provider-heading h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.global-grid,
.provider-grid-fields,
.template-grid,
.test-send-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 1rem;
}

.global-grid {
  margin-top: 1rem;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.provider-heading {
  padding-bottom: 0.85rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.provider-grid-fields :deep(.el-form-item),
.template-grid :deep(.el-form-item),
.test-send-grid :deep(.el-form-item) {
  min-width: 0;
}

.switch-field {
  flex-wrap: wrap;
  gap: 0.75rem;
  min-height: 32px;
}

.subsection-heading {
  padding-left: 0.65rem;
  margin: 0 0 0.8rem;
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--el-text-color-primary);
  border-left: 3px solid var(--el-color-primary);
}

.template-section,
.test-send-panel {
  padding-top: 0.85rem;
  margin-top: 0.35rem;
  border-top: 1px solid var(--el-border-color-lighter);
}

.test-send-panel .field-hint {
  margin-top: -0.35rem;
  margin-bottom: 0.8rem;
}

.full-width {
  width: 100%;
}

.settings-actions {
  justify-content: flex-end;
  padding-top: 1rem;
  margin-top: 1rem;
  border-top: 1px solid var(--el-border-color-lighter);
}

@media (width <= 1100px) {
  .provider-grid {
    grid-template-columns: 1fr;
  }
}

@media (width <= 700px) {
  .global-grid,
  .provider-grid-fields,
  .template-grid,
  .test-send-grid {
    grid-template-columns: 1fr;
  }

  .settings-header,
  .provider-heading {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
