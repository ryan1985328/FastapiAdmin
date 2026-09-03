<script setup lang="ts">
import type { FormSchema } from '@wot-ui/ui/components/wd-form/types'
import type { AppUserBankAccountForm } from '@/api/module_app/bankAccount'
import { onLoad } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppUserBankAccountAPI from '@/api/module_app/bankAccount'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'bank-account-form', style: { navigationBarTitleText: '银行卡' } })
useI18nNavTitle('bankAccount.navTitle')

const { t } = useI18n()
const toast = useToast()
const formRef = ref()
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(0)

function createForm(): AppUserBankAccountForm {
  return {
    bank_name: '',
    bank_code: '',
    account_name: '',
    card_number: '',
    branch_name: '',
    is_default: false,
  }
}

const form = reactive<AppUserBankAccountForm>(createForm())

const bankAccountSchema: FormSchema = {
  validate: (model) => {
    const errors: Array<{ path: Array<string | number>, message: string }> = []
    if (!String(model.account_name ?? '').trim())
      errors.push({ path: ['account_name'], message: t('bankAccount.accountNameRequired') })
    if (!String(model.bank_name ?? '').trim())
      errors.push({ path: ['bank_name'], message: t('bankAccount.bankNameRequired') })

    const cardNumber = String(model.card_number ?? '').replace(/[\s-]+/g, '')
    if (!editingId.value && !cardNumber)
      errors.push({ path: ['card_number'], message: t('bankAccount.cardNumberRequired') })
    else if (cardNumber && !/^\d{12,19}$/.test(cardNumber))
      errors.push({ path: ['card_number'], message: t('bankAccount.cardNumberInvalid') })
    return errors
  },
}

function resetForm() {
  Object.assign(form, createForm())
}

async function loadAccount(id: number) {
  loading.value = true
  try {
    const account = await AppUserBankAccountAPI.detail(id)
    // The detail response intentionally contains only masked_card_number.
    // Never copy it into card_number; an empty value means "keep existing card".
    Object.assign(form, {
      bank_name: account.bank_name,
      bank_code: account.bank_code || '',
      account_name: account.account_name,
      card_number: '',
      branch_name: account.branch_name || '',
      is_default: account.is_default,
    })
  }
  catch {
    uni.navigateBack()
  }
  finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (submitting.value || loading.value)
    return
  const { valid } = await formRef.value.validate()
  if (!valid)
    return

  const cardNumber = String(form.card_number || '').replace(/[\s-]+/g, '')
  const payload: AppUserBankAccountForm = {
    bank_name: form.bank_name.trim(),
    bank_code: form.bank_code?.trim() || undefined,
    account_name: form.account_name.trim(),
    branch_name: form.branch_name?.trim() || undefined,
    is_default: Boolean(form.is_default),
  }
  if (cardNumber)
    payload.card_number = cardNumber

  submitting.value = true
  try {
    if (editingId.value)
      await AppUserBankAccountAPI.update(editingId.value, payload)
    else
      await AppUserBankAccountAPI.create({ ...payload, card_number: cardNumber })
    toast.success(t('bankAccount.saveSuccess'))
    uni.navigateBack()
  }
  catch {
    // http 层已统一提示
  }
  finally {
    submitting.value = false
  }
}

onLoad((options) => {
  editingId.value = Number(options?.id || 0)
  if (editingId.value)
    void loadAccount(editingId.value)
  else
    resetForm()
})
</script>

<template>
  <view class="page-wraper py-3">
    <wd-loading v-if="loading" class="mx-auto my-8 block" />
    <view v-else class="bank-account-form-card wot-bg-filled-oppo mx-3 rounded-2 p-4">
      <wd-form ref="formRef" :model="form" :schema="bankAccountSchema">
        <wd-form-item prop="account_name" :label="t('bankAccount.accountName')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.account_name" :placeholder="t('bankAccount.accountNamePlaceholder')" clearable :compact="false" prefix-icon="user" />
        </wd-form-item>
        <wd-form-item prop="bank_name" :label="t('bankAccount.bankName')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.bank_name" :placeholder="t('bankAccount.bankNamePlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="card_number" :label="editingId ? t('bankAccount.replaceCardNumber') : t('bankAccount.cardNumber')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.card_number" type="number" :placeholder="editingId ? t('bankAccount.replaceCardNumberPlaceholder') : t('bankAccount.cardNumberPlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="branch_name" :label="t('bankAccount.branchName')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.branch_name" :placeholder="t('bankAccount.branchNamePlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="is_default" :label="t('bankAccount.isDefault')" custom-style="margin-bottom: 18rpx; padding-left: 0; padding-right: 0;">
          <wd-switch v-model="form.is_default" size="18px" />
        </wd-form-item>
      </wd-form>
      <wd-text v-if="editingId" class="wot-text-text-secondary mb-4 block text-3" :text="t('bankAccount.replaceCardNumberTip')" />
      <wd-button type="primary" round block :loading="submitting" @click="handleSubmit">
        {{ submitting ? t('bankAccount.submitting') : t('bankAccount.submit') }}
      </wd-button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
</style>
