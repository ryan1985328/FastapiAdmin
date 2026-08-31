<script lang="ts" setup>
import type { FormSchema } from '@wot-ui/ui/components/wd-form/types'
import type { AppMobilePasswordLoginForm } from '@/api/module_app/auth'
import { onLoad } from '@dcloudio/uni-app'
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppAuthAPI from '@/api/module_app/auth'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { REMEMBER_ME_KEY } from '@/constants'
import { useConfigStore } from '@/store/configStore'
import { useUserStore } from '@/store/userStore'
import { Storage } from '@/utils/storage'

definePage({ name: 'login', style: { navigationBarTitleText: '登录' } })
useI18nNavTitle('login.navTitle')

const { t } = useI18n()
const loginFormRef = ref()
const loading = ref(false)
const userStore = useUserStore()
const configStore = useConfigStore()
const redirect = ref('/pages/index/index')
const loginMode = ref<'password' | 'sms'>('password')
const codeSending = ref(false)
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

/** 规范化 BASE_URL（保证以 / 结尾），用于拼接静态资源路径 */
const BASE_PATH = import.meta.env.BASE_URL.endsWith('/') ? import.meta.env.BASE_URL : `${import.meta.env.BASE_URL}/`

/** 品牌区参数来自现有系统参数，继续复用 App 壳配置 */
const brandLogo = computed(() => configStore.configData?.logo_url?.config_value?.trim() || `${BASE_PATH}static/logo.png`)
const brandTitle = computed(() => configStore.configData?.sys_name?.config_value?.trim() || 'FastAPI Admin Starter')
const brandSubtitle = computed(() => configStore.configData?.login_title?.config_value?.trim() || t('login.brandSubtitle'))

const loginSchema: FormSchema = {
  validate: (model) => {
    const errors: Array<{ path: Array<string | number>, message: string }> = []
    const mobile = String(model.mobile ?? '').replace(/[\s-]+/g, '')
    const password = String(model.password ?? '')
    const code = String(model.code ?? '')
    if (!mobile)
      errors.push({ path: ['mobile'], message: t('login.mobileRequired') })
    else if (!/^\+?[1-9]\d{6,14}$/.test(mobile))
      errors.push({ path: ['mobile'], message: t('login.mobileInvalid') })
    if (loginMode.value === 'password' && !password)
      errors.push({ path: ['password'], message: t('common.form.passwordRequired') })
    else if (loginMode.value === 'password' && (password.length < 6 || password.length > 128))
      errors.push({ path: ['password'], message: t('login.passwordLength') })
    if (loginMode.value === 'sms' && !/^\d{6}$/.test(code))
      errors.push({ path: ['code'], message: t('login.codeRequired') })
    return errors
  },
}

const loginFormData = reactive<AppMobilePasswordLoginForm & { code: string }>({
  mobile: '',
  password: '',
  code: '',
  remember: true,
})

/** 从本地存储恢复记住的手机号（不存储密码或验证码） */
function restoreRememberedUser() {
  const remembered = Storage.get<{ mobile?: string, username?: string, remember: boolean }>(REMEMBER_ME_KEY)
  if (remembered) {
    loginFormData.mobile = remembered.mobile || ''
    loginFormData.remember = remembered.remember ?? true
  }
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function startCountdown(seconds: number) {
  stopCountdown()
  countdown.value = seconds
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0)
      stopCountdown()
  }, 1000)
}

async function sendLoginCode() {
  const mobile = loginFormData.mobile.replace(/[\s-]+/g, '')
  if (!/^\+?[1-9]\d{6,14}$/.test(mobile)) {
    uni.showToast({ title: t('login.mobileInvalid'), icon: 'none' })
    return
  }
  if (codeSending.value || countdown.value > 0)
    return

  codeSending.value = true
  try {
    const result = await AppAuthAPI.sendCode({ mobile, scene: 'login_code' })
    startCountdown(result.resend_after || 60)
    uni.showToast({ title: t('login.codeSent'), icon: 'success' })
  }
  catch {
    // http 层已统一展示后端错误
  }
  finally {
    codeSending.value = false
  }
}

onLoad((options) => {
  const from = options?.redirect ? decodeURIComponent(options.redirect) : ''
  if (from && from !== '/pages/login/index' && from.startsWith('/pages/'))
    redirect.value = from
  restoreRememberedUser()
  configStore.getConfig()
})

async function handleSubmit() {
  if (loading.value)
    return

  loading.value = true
  try {
    const { valid } = await loginFormRef.value.validate()
    if (!valid)
      return
    loginFormData.mobile = loginFormData.mobile.replace(/[\s-]+/g, '')
    if (loginMode.value === 'password')
      await userStore.loginByPassword(loginFormData)
    else
      await userStore.loginBySms({ mobile: loginFormData.mobile, code: loginFormData.code })
    if (loginFormData.remember)
      Storage.set(REMEMBER_ME_KEY, { mobile: loginFormData.mobile, remember: true })
    else
      Storage.remove(REMEMBER_ME_KEY)
    uni.reLaunch({ url: redirect.value })
  }
  catch {
    uni.showToast({ title: t('login.loginFailed'), icon: 'none', duration: 2500 })
  }
  finally {
    loading.value = false
  }
}

function goForgot() {
  uni.navigateTo({ url: '/pages/login/forget/index' })
}

function goRegister() {
  uni.navigateTo({ url: '/pages/login/register/index' })
}

onBeforeUnmount(stopCountdown)
</script>

<template>
  <view class="login-page">
    <!-- Brand area -->
    <view class="login-brand">
      <image class="brand-logo" :src="brandLogo" mode="aspectFit" />
      <text class="brand-title">
        {{ brandTitle }}
      </text>
      <wd-text class="brand-subtitle" :text="brandSubtitle" />
    </view>

    <!-- Form card -->
    <view class="login-card">
      <text class="login-card__title">
        {{ t('login.cardTitle') }}
      </text>

      <view class="login-modes">
        <wd-text
          class="login-mode"
          :class="{ 'login-mode--active': loginMode === 'password' }"
          :text="t('login.passwordMode')"
          @click="loginMode = 'password'"
        />
        <wd-text
          class="login-mode"
          :class="{ 'login-mode--active': loginMode === 'sms' }"
          :text="t('login.smsMode')"
          @click="loginMode = 'sms'"
        />
      </view>

      <wd-form ref="loginFormRef" :model="loginFormData" :schema="loginSchema">
        <wd-form-item prop="mobile" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input
            v-model="loginFormData.mobile"
            :placeholder="t('common.form.mobilePlaceholder')"
            clearable
            confirm-type="next"
            type="tel"
            :compact="false"
            prefix-icon="phone"
          />
        </wd-form-item>

        <template v-if="loginMode === 'password'">
          <wd-form-item prop="password" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input
              v-model="loginFormData.password"
              :placeholder="t('common.form.passwordPlaceholder')"
              clearable
              show-password
              confirm-type="go"
              :compact="false"
              prefix-icon="lock"
              @confirm="handleSubmit"
            />
          </wd-form-item>
        </template>

        <template v-else>
          <view class="code-row">
            <view class="code-input">
              <wd-form-item prop="code" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
                <wd-input
                  v-model="loginFormData.code"
                  :placeholder="t('common.form.codePlaceholder')"
                  clearable
                  type="number"
                  confirm-type="go"
                  :compact="false"
                  prefix-icon="lock"
                  @confirm="handleSubmit"
                />
              </wd-form-item>
            </view>
            <wd-button
              class="code-button"
              size="small"
              plain
              :loading="codeSending"
              :disabled="codeSending || countdown > 0"
              @click="sendLoginCode"
            >
              {{ countdown > 0 ? t('login.countdown', { seconds: countdown }) : t('login.getCode') }}
            </wd-button>
          </view>
        </template>

        <!-- 记住手机号（不保存密码/验证码） -->
        <view class="login-options">
          <wd-checkbox v-model="loginFormData.remember" size="18px">
            {{ t('login.remember') }}
          </wd-checkbox>
          <wd-text class="forgot-link" :text="t('login.forgot')" type="primary" @click="goForgot" />
        </view>

        <!-- Submit -->
        <wd-button
          type="primary"
          :loading="loading"
          round
          block
          @click="handleSubmit"
        >
          {{ loading ? t('login.submitting') : t('login.submit') }}
        </wd-button>
      </wd-form>
    </view>

    <!-- Footer -->
    <view class="login-footer">
      <wd-text class="login-footer__text" :text="t('login.noAccount')" />
      <wd-text class="login-footer__link" :text="t('login.toRegister')" type="primary" @click="goRegister" />
    </view>
  </view>
</template>

<style lang="scss" scoped>
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* H5 下 100vh 包含导航栏，使用uni-app的可用视口高度变量避免溢出 */
  /* #ifdef H5 */
  height: calc(100vh - 44px);
  /* #endif */
  /* #ifndef H5 */
  height: 100vh;
  /* #endif */
  padding: 40rpx 64rpx 0;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
  /* 接入全局水滴渐变（--drop-bg 由 App.vue 按主题色定义，暗色回退纯色由下方规则接管） */
  background: var(--drop-bg, #F9F9F9);
  overflow: hidden;
  box-sizing: border-box;
}

/* 暗黑模式下整页背景变深，消除白色断层（wot 根类为 wot-theme-dark） */
.wot-theme-dark .login-page {
  @apply wot-bg-filled-bottom;
}

/* ===== Brand ===== */
.login-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 48rpx;
  padding-bottom: 32rpx;
  gap: 10rpx;
  flex-shrink: 0;

  .brand-logo {
    width: 104rpx;
    height: 104rpx;
  }

  .brand-title {
    font-size: var(--font-3xl, 48rpx);
    font-weight: 700;
    /* 亮色下使用主题色渐变文字，品牌识别度更高（background-clip 不生效时回退主题主色） */
    background: linear-gradient(135deg, var(--wot-primary-5, #4480FF) 0%, var(--wot-primary-7, #164ED1) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: var(--wot-primary-6, #1C64FD);

    /* 暗黑模式下使用纯白，提升品牌标题醒目度 */
    .wot-theme-dark & {
      background: none;
      -webkit-background-clip: initial;
      background-clip: initial;
      -webkit-text-fill-color: initial;
      color: #FFFFFF;
    }
  }

  .brand-subtitle {
    font-size: var(--font-md, 28rpx);
    @apply wot-text-text-auxiliary;

    /* 暗黑下提亮到 --text-color-2，避免 #9CA3AF 在深底上偏暗 */
    .wot-theme-dark & {
      @apply wot-text-text-secondary;
    }
  }
}

/* ===== Card（不再是毛玻璃，使用纯色背景 + 与页面背景形成层级差） ===== */
.login-card {
  width: 100%;
  /* 亮色下默认带主题色最浅阶，避免一片纯白；--card-bg-color 可被外部覆盖 */
  background: var(--card-bg-color, var(--wot-primary-1, #FFFFFF));
  border-radius: var(--radius-xl, 32rpx);
  padding: 28rpx 36rpx;
  /* 边框跟随主题色浅阶，替代中性灰，让卡片更有主题感 */
  border: 2rpx solid var(--border-color, var(--wot-primary-2, #EAECF0));
  box-shadow: var(--shadow-md, 0 8rpx 32rpx rgba(15, 23, 42, 0.04));
  margin-bottom: 12rpx;
  flex-shrink: 0;

  /* 暗黑模式：卡片用深色 2 级，页面背景用深色 1 级，形成细微层级差 */
  .wot-theme-dark & {
    @apply wot-bg-filled-content;
    border-color: var(--border-color, #2C2C2E);
    box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.2);
  }

  &__title {
    display: block;
    font-size: var(--font-xl, 36rpx);
    font-weight: 600;
    @apply wot-text-text-main;
    margin-bottom: 18rpx;

    /* 暗黑模式下使用纯白，提升卡片标题醒目度 */
    .wot-theme-dark & {
      color: #FFFFFF;
    }
  }
}

.login-modes {
  display: flex;
  gap: 36rpx;
  margin-bottom: 18rpx;
}

.login-mode {
  padding-bottom: 8rpx;
  font-size: var(--font-md, 28rpx);
  @apply wot-text-text-auxiliary;

  &--active {
    font-weight: 600;
    @apply wot-text-primary;
    border-bottom: 4rpx solid var(--wot-primary-6, #1C64FD);
  }
}

/* 输入框微调 — 圆角加大 + 主题色边框 + 轻阴影，从"方方正正"变"圆润悬浮" */
:deep(.wd-input) {
  border-radius: 24rpx;
  /* 亮色下主题色浅阶边框与卡片边框呼应，白色底在淡色卡片上形成浮层 */
  border: 2rpx solid var(--wot-primary-2, var(--wot-border-main, #EAECF0));
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.05);
}

/* H5 聚焦态：主题色描边 + 淡色光晕（MP 端不支持 :focus-within，跳过） */
/* #ifdef H5 */
:deep(.wd-input:focus-within) {
  border-color: var(--wot-primary-6, #1C64FD);
  box-shadow: 0 0 0 4rpx var(--wot-primary-1, #F5F8FF);
}
/* #endif */

/* cell 容器回归透明：亮色下消除输入框外围的白色方形区域，暗色下消除纯黑块，
   让自带圆角+边框的输入框直接显示在卡片上 */
:deep(.wd-cell) {
  --wot-cell-bg: transparent;
}

/* 滑块验证 — 滑块按钮默认纯白（filled-oppo）在浅灰轨道上不明显；同时整个滑块行
   默认浅灰底在淡主题色卡片上也几乎隐形，只有拖动时才变色。
   统一改为与输入框一致的"白底 + 主题色边框 + 轻阴影"浮层语言，静态即可见 */
:deep(.wd-slide-verify) {
  /* 整行容器：白底替代浅灰轨道，静态可见 */
  --wot-slide-verify-bg: #FFFFFF;
  /* 滑块按钮：主题色描边 + 图标，白底保留 */
  --wot-slide-verify-button-bg: #FFFFFF;
  --wot-slide-verify-button-border-color: var(--wot-primary-6, #1C64FD);
  --wot-slide-verify-button-color: var(--wot-primary-6, #1C64FD);
  --wot-slide-verify-button-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.12);
  /* 与输入框呼应的边框 + 浮层阴影 */
  border: 2rpx solid var(--wot-primary-2, var(--wot-border-main, #EAECF0));
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.05);
}

.wot-theme-dark .login-page :deep(.wd-input) {
  /* 比卡片背景（filled-content）亮一档，输入框在暗色卡片上凸起有层次 */
  --wot-input-bg: var(--wot-coolgrey-8, var(--wot-filled-content));
  border-color: var(--wot-border-main, #2C2C2E);
  box-shadow: none;
}

.wot-theme-dark .login-page :deep(.wd-slide-verify) {
  /* 滑块行与按钮：默认纯黑（filled-oppo）/纯黑轨道在暗色下均不可见，
     统一改亮一档底色 + 主题色描边/图标，与输入框的暗色浮层语言一致 */
  --wot-slide-verify-bg: var(--wot-coolgrey-8, var(--wot-filled-content));
  --wot-slide-verify-button-bg: var(--wot-coolgrey-8, var(--wot-filled-content));
  --wot-slide-verify-button-border-color: var(--wot-primary-5, #4480FF);
  --wot-slide-verify-button-color: var(--wot-primary-5, #4480FF);
  --wot-slide-verify-button-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.4);
  border-color: var(--wot-border-main, #2C2C2E);
  box-shadow: none;
}

:deep(.wd-form-item) {
  margin-bottom: 14rpx;
  /* 去掉 wd-cell 自带左右内边距，使输入框/滑块与登录按钮同宽 */
  padding-left: 0;
  padding-right: 0;
}

/* ===== 记住密码 + 忘记密码 ===== */
.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.code-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.code-input {
  flex: 1;
  min-width: 0;
}

.code-button {
  flex-shrink: 0;
  height: 80rpx;
  margin-top: 0;
}

.forgot-link {
  font-size: var(--font-md, 28rpx);
}

/* ===== OAuth Section ===== */
.oauth-section {
  width: 100%;
  margin-top: 8rpx;
  flex-shrink: 0;

  /* 去掉宫格项默认填充背景，仅保留图标/文字与轻量点击反馈 */
  :deep(.wd-grid-item) {
    --wot-grid-item-bg: transparent;
  }
}

/* ===== 微信一键登录区域 ===== */
.wx-login-section {
  margin-bottom: 16rpx;

  :deep(.wd-button) {
    height: 88rpx;
    font-size: 30rpx;
  }
}

.oauth-btn__icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.oauth-btn__iconify {
  width: 40rpx;
  height: 40rpx;
}

.oauth-btn__label {
  font-size: var(--font-xs, 20rpx);
  @apply wot-text-text-auxiliary;
}

/* ===== Footer ===== */
.login-footer {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 12rpx 0 0;
  flex-shrink: 0;

  &__text {
    font-size: var(--font-md, 28rpx);
    @apply wot-text-text-auxiliary;
  }

  &__link {
    font-size: var(--font-md, 28rpx);
  }
}

/* MP 端兼容：wd-form-item 内部 wd-cell 因 uni-app 插槽静态声明（u-s）误判 label/title 插槽被使用，
   showLeft=true 渲染空 left 区域（flex:1 占半宽），H5 端运行时插槽判定无此问题。
   本页 form-item 无 title/label/prefix 内容，隐藏 left 安全，保证输入框与登录按钮同宽 */
.login-card .wd-form-item .wd-cell__left {
  display: none;
}
</style>
