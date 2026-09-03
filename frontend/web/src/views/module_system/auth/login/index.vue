<!-- 登录页：全屏技术视觉 + Admin 登录工作区；认证流程由现有逻辑负责。 -->
<template>
  <div class="login-page-root" :style="loginPageStyle">
    <FaAuthTopBar />

    <div class="login-auth-split">
      <section class="login-auth-split__col login-auth-split__col--illustration">
        <FaLoginLeftView />
      </section>

      <main class="login-auth-split__col login-auth-split__col--form login-workspace">
        <div class="login-workspace__scroll">
          <div class="login-workspace__content">
            <div class="auth-right-wrap">
              <div class="form">
                <div class="form-intro">
                  <h1 class="title">{{ panelTitle }}</h1>
                  <p class="sub-title">{{ panelSubTitle }}</p>
                </div>

                <FaLoginAccountForm
                  ref="accountFormRef"
                  v-model:is-passing="isPassing"
                  v-model:is-click-pass="isClickPass"
                  v-model:login-form="loginForm"
                  :rules="rules"
                  :form-key="formKey"
                  :is-dark="isDark"
                  :captcha-enabled="captchaEnabled"
                  :drag-verify-text-color="dragVerifyTextColor"
                  :loading="loading"
                  @submit="handleSubmit"
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { LocationQuery, RouteLocationRaw } from "vue-router";
import AuthAPI, { type LoginFormData } from "@/api/module_system/auth";
import { CANONICAL_HOME_PATH } from "@/router/constants";

import { useConfigStore, useAppStore, useSettingsStore, useUserStore } from "@stores";
import { Auth, HttpError } from "@utils";
import { ElMessage, ElNotification } from "element-plus";
import type { FormRules } from "element-plus";
import type FaLoginAccountForm from "./components/forms/FaLoginAccountForm.vue";

defineOptions({ name: "Login" });

const configStore = useConfigStore();
const settingStore = useSettingsStore();
const appStore = useAppStore();
const { isDark } = storeToRefs(settingStore);
const { t, locale } = useI18n();

const panelTitle = computed(() => t("login.title"));
const panelSubTitle = computed(() => t("login.subTitle"));

async function tryConsumeOAuthCallback() {
  const q = route.query;
  const oauthError = q.oauth_error as string | undefined;
  const access = q.access_token as string | undefined;
  const refresh = q.refresh_token as string | undefined;

  if (!oauthError && !(access && refresh)) return;

  const rest: Record<string, unknown> = { ...q };
  delete rest.oauth_error;
  delete rest.access_token;
  delete rest.refresh_token;
  delete rest.token_type;

  if (oauthError) {
    ElMessage.error(decodeURIComponent(oauthError));
    await router.replace({ path: route.path, query: rest as LocationQuery });
    return;
  }

  if (access && refresh) {
    try {
      Auth.setTokens(access, refresh, true);
      userStore.setToken(access, refresh);
      userStore.setLoginStatus(true);
      ElNotification({
        title: t("login.oauthNoticeTitle"),
        message: t("login.oauthLoginSuccess"),
        type: "success",
      });
      await router.replace(resolveRedirectTarget(rest as LocationQuery));
      if (settingStore.showGuide) {
        appStore.showGuide(true);
      }
    } catch (error) {
      console.error("[Login] OAuth callback:", error);
      ElMessage.error(t("login.oauthLoginFailed"));
      await router.replace({ path: route.path, query: rest as LocationQuery });
    }
  }
}

const dragVerifyTextColor = "var(--login-captcha-text-color)";
const formKey = ref(0);

watch(locale, () => {
  formKey.value++;
});

const userStore = useUserStore();
const router = useRouter();
const route = useRoute();
const isPassing = ref(false);
const isClickPass = ref(false);

// 开发构建先隐藏滑块，最终仍以后端验证码开关返回值为准。
const captchaEnabled = ref(!import.meta.env.DEV);
const accountFormRef = ref<InstanceType<typeof FaLoginAccountForm> | null>(null);

const loading = ref(false);

const loginForm = reactive<LoginFormData>({
  username: "",
  password: "",
  captcha_key: "",
  remember: true,
  login_type: "PC端",
});

// —— 登录页背景 ——
const loginPageStyle = computed<Record<string, string>>(() => {
  const bg = configStore.configData?.login_bg?.config_value?.trim();
  return { "--login-configured-background": bg ? `url("${bg}")` : "none" };
});

const rules = computed<FormRules>(() => {
  const base: FormRules = {
    username: [
      {
        required: true,
        trigger: "blur",
        message: t("login.message.username.required"),
      },
    ],
    password: [
      {
        required: true,
        trigger: "blur",
        message: t("login.message.password.required"),
      },
      {
        min: 6,
        message: t("login.message.password.min"),
        trigger: "blur",
      },
    ],
  };
  return base;
});

async function getCaptcha() {
  try {
    const response = await AuthAPI.getCaptcha();
    const data = response.data.data;
    captchaEnabled.value = data.enable;
    loginForm.captcha_key = data.key;
    // 重置滑块状态
    isPassing.value = !data.enable;
    isClickPass.value = false;
  } catch {
    // 获取配置失败时保持安全默认值，避免错误地绕过生产环境验证码。
    captchaEnabled.value = true;
    isPassing.value = false;
    loginForm.captcha_key = "";
  }
}

/** 滑块验证完成后通知后端标记 */
async function handleSliderPass(passed: boolean) {
  if (!captchaEnabled.value || !passed || !loginForm.captcha_key) return;
  try {
    await AuthAPI.sliderComplete(loginForm.captcha_key);
  } catch {
    isPassing.value = false;
    await getCaptcha();
  }
}

/** 监听滑块通过状态 */
watch(isPassing, (val) => {
  handleSliderPass(val);
});

function resolveRedirectTarget(query: LocationQuery): RouteLocationRaw {
  const defaultPath = CANONICAL_HOME_PATH;
  const rawRedirect = (query.redirect as string) || defaultPath;
  try {
    const resolved = router.resolve(rawRedirect);
    return {
      path: resolved.path,
      query: resolved.query,
    };
  } catch {
    return { path: defaultPath };
  }
}

onMounted(async () => {
  await configStore.getConfig(true);
  await tryConsumeOAuthCallback();
  if (userStore.isLogin) {
    await router.replace(resolveRedirectTarget(route.query));
    return;
  }
  getCaptcha();
});

onActivated(() => {
  getCaptcha();
});

watch(
  () => route.fullPath,
  () => getCaptcha()
);

const handleSubmit = async () => {
  if (!accountFormRef.value) return;

  try {
    const valid = await accountFormRef.value.validate?.();
    if (!valid) return;

    if (captchaEnabled.value && !isPassing.value) {
      isClickPass.value = true;
      return;
    }

    loading.value = true;

    await userStore.login(loginForm);
    await router.replace(resolveRedirectTarget(route.query));

    if (settingStore.showGuide) {
      appStore.showGuide(true);
    }
  } catch (error) {
    // 自增 formKey 强制重新挂载表单（滑块自动重置为初始状态）
    formKey.value++;
    await getCaptcha();
    if (!(error instanceof HttpError)) {
      console.error("[Login] Unexpected error:", error);
      ElNotification({
        title: "提示",
        message: error instanceof Error ? error.message : String(error),
        type: "error",
      });
    }
  } finally {
    loading.value = false;
  }
};
</script>
