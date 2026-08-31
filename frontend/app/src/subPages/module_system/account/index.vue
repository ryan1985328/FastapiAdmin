<script setup lang="ts">
import type { FormSchema } from '@wot-ui/ui/components/wd-form/types'
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppAuthAPI from '@/api/module_app/auth'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useUserStore } from '@/store/userStore'

definePage({
  name: 'account',
  layout: 'default',
  style: { navigationBarTitleText: '安全设置' },
})
useI18nNavTitle('account.navTitle')

const { t } = useI18n()
const toast = useToast()
const userStore = useUserStore()
const formRef = ref()
const submitting = ref(false)

const form = reactive({
  current_password: '',
  new_password: '',
  confirmPassword: '',
})

const passwordSchema: FormSchema = {
  validate: (model) => {
    const errors: Array<{ path: Array<string | number>, message: string }> = []
    const currentPassword = String(model.current_password ?? '')
    const newPassword = String(model.new_password ?? '')
    const confirmPassword = String(model.confirmPassword ?? '')
    if (!currentPassword)
      errors.push({ path: ['current_password'], message: t('account.oldRequired') })
    if (!newPassword)
      errors.push({ path: ['new_password'], message: t('common.form.newPasswordRequired') })
    else if (newPassword.length < 6 || newPassword.length > 128)
      errors.push({ path: ['new_password'], message: t('common.form.passwordLength') })
    if (!confirmPassword)
      errors.push({ path: ['confirmPassword'], message: t('common.form.confirmNewRequired') })
    else if (confirmPassword !== newPassword)
      errors.push({ path: ['confirmPassword'], message: t('common.form.mismatch') })
    return errors
  },
}

async function handleSubmit() {
  if (submitting.value)
    return
  const { valid } = await formRef.value.validate()
  if (!valid)
    return

  submitting.value = true
  try {
    await AppAuthAPI.changePassword({
      current_password: form.current_password,
      new_password: form.new_password,
    })
    toast.success(t('account.success'))
    // 密码修改会撤销服务端全部会话，直接清理本地凭证并回到登录页。
    userStore.clearAll()
    uni.reLaunch({ url: '/pages/login/index' })
  }
  catch {
    // http 层已统一提示后端错误
  }
  finally {
    submitting.value = false
  }
}

function goForgotPassword() {
  uni.navigateTo({ url: '/pages/login/forget/index' })
}
</script>

<template>
  <view class="page-wraper py-3">
    <view class="wot-bg-filled-oppo mx-3 mb-3 rounded-2 p-4">
      <wd-text class="wot-text-text-main text-4 font-medium" :text="t('account.password')" />
      <wd-text class="wot-text-text-secondary mt-2 block text-3" :text="t('account.passwordTip')" />
    </view>

    <view class="wot-bg-filled-oppo mx-3 mb-3 rounded-2 p-4">
      <wd-form ref="formRef" :model="form" :schema="passwordSchema">
        <wd-form-item prop="current_password" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input
            v-model="form.current_password"
            :placeholder="t('account.oldPlaceholder')"
            clearable
            show-password
            :compact="false"
            prefix-icon="lock"
          />
        </wd-form-item>
        <wd-form-item prop="new_password" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input
            v-model="form.new_password"
            :placeholder="t('common.form.newPasswordPlaceholder')"
            clearable
            show-password
            :compact="false"
            prefix-icon="lock"
          />
        </wd-form-item>
        <wd-form-item prop="confirmPassword" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input
            v-model="form.confirmPassword"
            :placeholder="t('common.form.confirmNewPlaceholder')"
            clearable
            show-password
            :compact="false"
            prefix-icon="lock"
          />
        </wd-form-item>
      </wd-form>
      <wd-button type="primary" round block :loading="submitting" @click="handleSubmit">
        {{ submitting ? t('account.submitting') : t('account.submit') }}
      </wd-button>
    </view>

    <view class="mx-3">
      <wd-cell-group border custom-class="rounded-2! overflow-hidden">
        <wd-cell :title="t('account.forgotPassword')" :label="t('account.forgotPasswordTip')" is-link @click="goForgotPassword" />
      </wd-cell-group>
    </view>
  </view>
</template>
