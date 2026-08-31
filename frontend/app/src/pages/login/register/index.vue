<script setup lang="ts">
import type { FormSchema } from '@wot-ui/ui/components/wd-form/types'
import type { AppRegisterForm } from '@/api/module_app/auth'
import { onLoad } from '@dcloudio/uni-app'
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppAuthAPI from '@/api/module_app/auth'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { REMEMBER_ME_KEY } from '@/constants'
import { useConfigStore } from '@/store/configStore'
import { useUserStore } from '@/store/userStore'
import { Storage } from '@/utils/storage'

definePage({ name: 'register', style: { navigationBarTitleText: '注册' } })
useI18nNavTitle('register.navTitle')

const { t } = useI18n()
const toast = useToast()
const userStore = useUserStore()
const configStore = useConfigStore()

const submitting = ref(false)
const codeSending = ref(false)
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null
const agreeRead = ref(false)
const registerFormRef = ref()
const registerForm = reactive({
  mobile: '',
  code: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  referral_code: '',
})

const MOBILE_REG = /^\+?[1-9]\d{6,14}$/

/** 表单验证 schema — 字段级错误提示（与登录页 wd-form 一致） */
const registerSchema: FormSchema = {
  validate: (model) => {
    const errors: Array<{ path: Array<string | number>, message: string }> = []
    const mobile = String(model.mobile ?? '').replace(/[\s-]+/g, '')
    const code = String(model.code ?? '')
    const password = String(model.password ?? '')
    const confirmPassword = String(model.confirmPassword ?? '')
    if (!mobile)
      errors.push({ path: ['mobile'], message: t('register.mobileRequired') })
    else if (!MOBILE_REG.test(mobile))
      errors.push({ path: ['mobile'], message: t('register.mobileInvalid') })
    if (!/^\d{6}$/.test(code))
      errors.push({ path: ['code'], message: t('register.codeRequired') })
    if (!password)
      errors.push({ path: ['password'], message: t('common.form.passwordRequired') })
    else if (password.length < 6 || password.length > 128)
      errors.push({ path: ['password'], message: t('common.form.passwordLength') })
    if (!confirmPassword)
      errors.push({ path: ['confirmPassword'], message: t('common.form.confirmRequired') })
    else if (confirmPassword !== password)
      errors.push({ path: ['confirmPassword'], message: t('common.form.mismatch') })
    return errors
  },
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

async function sendRegisterCode() {
  const mobile = registerForm.mobile.replace(/[\s-]+/g, '')
  if (!MOBILE_REG.test(mobile)) {
    toast.warning(t('register.mobileInvalid'))
    return
  }
  if (codeSending.value || countdown.value > 0)
    return

  codeSending.value = true
  try {
    const result = await AppAuthAPI.sendCode({ mobile, scene: 'register_code' })
    startCountdown(result.resend_after || 60)
    toast.success(t('register.codeSent'))
  }
  catch {
    // http 层已统一展示后端错误
  }
  finally {
    codeSending.value = false
  }
}

/** 打开用户协议：H5 新窗口，其他端复制链接（与设置页链接行为一致） */
function handleAgreementOpen() {
  const url = configStore.configData?.clause?.config_value?.trim() || ''
  if (!url) {
    toast.info(t('register.userAgreement'))
    return
  }
  // #ifdef H5
  window.open(url, '_blank')
  // #endif
  // #ifndef H5
  uni.setClipboardData({
    data: url,
    showToast: false,
    success: () => {
      uni.hideToast()
      toast.success({ msg: url })
    },
  })
  // #endif
}

/** 注册成功后直接使用独立 App 认证登录。 */
async function autoLoginAfterRegister(mobile: string, password: string) {
  try {
    await userStore.loginByPassword({ mobile, password, remember: true })
    uni.reLaunch({ url: '/pages/index/index' })
  }
  catch {
    Storage.set(REMEMBER_ME_KEY, { mobile, remember: true })
    uni.reLaunch({ url: '/pages/login/index' })
  }
}

async function handleSubmit() {
  if (submitting.value)
    return
  if (!agreeRead.value) {
    toast.warning(t('register.agreeRequired'))
    return
  }
  const { valid } = await registerFormRef.value.validate()
  if (!valid)
    return

  const mobile = registerForm.mobile.replace(/[\s-]+/g, '')
  submitting.value = true
  try {
    const body: AppRegisterForm = {
      mobile,
      code: registerForm.code,
      password: registerForm.password,
    }
    if (registerForm.nickname.trim())
      body.nickname = registerForm.nickname.trim()
    if (registerForm.referral_code.trim())
      body.referral_code = registerForm.referral_code.trim()
    await AppAuthAPI.register(body)
    toast.success(t('register.success'))
    await autoLoginAfterRegister(mobile, registerForm.password)
  }
  catch {
    // http 层已统一错误提示（如用户名已存在）
  }
  finally {
    submitting.value = false
  }
}

onLoad(() => {
  // 拉取系统参数（用户协议链接 clause），幂等 + 本地持久化缓存
  configStore.getConfig()
})

function goLogin() {
  uni.reLaunch({ url: '/pages/login/index' })
}

onBeforeUnmount(stopCountdown)
</script>

<template>
  <view class="register-page">
    <view class="register-card">
      <text class="register-card__title">
        {{ t('register.title') }}
      </text>

      <view class="register-form">
        <wd-form ref="registerFormRef" :model="registerForm" :schema="registerSchema">
          <wd-form-item prop="mobile" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input
              v-model="registerForm.mobile"
              :placeholder="t('common.form.mobilePlaceholder')"
              clearable
              type="tel"
              :compact="false"
              prefix-icon="phone"
            />
          </wd-form-item>
          <view class="register-code-row">
            <view class="register-code-input">
              <wd-form-item prop="code" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
                <wd-input
                  v-model="registerForm.code"
                  :placeholder="t('common.form.codePlaceholder')"
                  clearable
                  type="number"
                  :compact="false"
                  prefix-icon="lock"
                />
              </wd-form-item>
            </view>
            <wd-button
              class="register-code-button"
              size="small"
              plain
              :loading="codeSending"
              :disabled="codeSending || countdown > 0"
              @click="sendRegisterCode"
            >
              {{ countdown > 0 ? t('register.countdown', { seconds: countdown }) : t('register.getCode') }}
            </wd-button>
          </view>
          <wd-form-item prop="nickname" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input
              v-model="registerForm.nickname"
              :placeholder="t('common.form.nicknameOptionalPlaceholder')"
              clearable
              :compact="false"
              prefix-icon="user"
            />
          </wd-form-item>
          <wd-form-item prop="password" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input
              v-model="registerForm.password"
              :placeholder="t('common.form.passwordPlaceholder')"
              show-password
              clearable
              :compact="false"
              prefix-icon="lock"
            />
          </wd-form-item>
          <wd-form-item prop="confirmPassword" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input
              v-model="registerForm.confirmPassword"
              :placeholder="t('common.form.confirmPlaceholder')"
              show-password
              clearable
              :compact="false"
              prefix-icon="lock"
            />
          </wd-form-item>
          <wd-form-item prop="referral_code" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input
              v-model="registerForm.referral_code"
              :placeholder="t('register.referralCodeOptional')"
              clearable
              :compact="false"
              prefix-icon="share"
            />
          </wd-form-item>
        </wd-form>

        <!-- 用户协议勾选（与 web 端一致，注册前必须同意） -->
        <view class="register-agreement">
          <wd-checkbox v-model="agreeRead" size="18px">
            {{ t('register.agree') }}
          </wd-checkbox>
          <wd-text class="register-agreement__link" :text="t('register.userAgreement')" type="primary" @click="handleAgreementOpen" />
        </view>

        <wd-button type="primary" round block :loading="submitting" @click="handleSubmit">
          {{ submitting ? t('register.submitting') : t('register.submit') }}
        </wd-button>
      </view>

      <view class="register-footer">
        <wd-text class="register-footer__text" :text="t('register.hasAccount')" />
        <wd-text class="register-footer__link" :text="t('register.toLogin')" type="primary" @click="goLogin" />
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.register-page {
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
  padding: 0 64rpx;
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
  /* 接入全局水滴渐变（--drop-bg 由 App.vue 按主题色定义，暗色回退纯色由下方规则接管） */
  background: var(--drop-bg, #F9F9F9);
  overflow: hidden;
  box-sizing: border-box;
}

/* 暗黑模式下整页背景变深，消除白色断层（wot 根类为 wot-theme-dark） */
.wot-theme-dark .register-page {
  @apply wot-bg-filled-bottom;
}

.register-card {
  width: 100%;
  margin-top: 120rpx;
  /* 亮色下默认带主题色最浅阶，避免一片纯白；--card-bg-color 可被外部覆盖 */
  background: var(--card-bg-color, var(--wot-primary-1, #FFFFFF));
  border-radius: var(--radius-xl, 32rpx);
  padding: 40rpx 36rpx;
  /* 边框跟随主题色浅阶，替代中性灰，让卡片更有主题感 */
  border: 2rpx solid var(--border-color, var(--wot-primary-2, #EAECF0));
  box-shadow: var(--shadow-md, 0 8rpx 32rpx rgba(15, 23, 42, 0.04));

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
    margin-bottom: 28rpx;

    /* 暗黑模式下使用纯白，提升卡片标题醒目度 */
    .wot-theme-dark & {
      color: #FFFFFF;
    }
  }
}

.register-form {
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

  /* 去掉 wd-cell 自带左右内边距，使输入框与登录按钮同宽（与登录页一致） */
  :deep(.wd-form-item) {
    margin-bottom: 14rpx;
    padding-left: 0;
    padding-right: 0;
  }
}

.register-code-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.register-code-input {
  flex: 1;
  min-width: 0;
}

.register-code-button {
  flex-shrink: 0;
  height: 80rpx;
}

/* cell 容器回归透明：亮色下消除输入框外围的白色方形区域，暗色下消除纯黑块，
   让自带圆角+边框的输入框直接显示在卡片上 */
:deep(.wd-cell) {
  --wot-cell-bg: transparent;
}

.wot-theme-dark .register-page :deep(.wd-input) {
  /* 比卡片背景（filled-content）亮一档，输入框在暗色卡片上凸起有层次 */
  --wot-input-bg: var(--wot-coolgrey-8, var(--wot-filled-content));
  border-color: var(--wot-border-main, #2C2C2E);
  box-shadow: none;
}

.register-agreement {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;

  :deep(.wd-checkbox__label) {
    font-size: var(--font-md, 28rpx);
    @apply wot-text-text-auxiliary;
  }

  &__link {
    font-size: var(--font-md, 28rpx);
  }
}

.register-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8rpx;
  margin-top: 32rpx;

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
.register-card .wd-form-item .wd-cell__left {
  display: none;
}
</style>
