<script setup lang="ts">
import type { FormSchema } from '@wot-ui/ui/components/wd-form/types'
import type { AppUserAddressForm } from '@/api/module_app/address'
import { onLoad } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppUserAddressAPI from '@/api/module_app/address'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'address-form', style: { navigationBarTitleText: '地址' } })
useI18nNavTitle('address.navTitle')

const { t } = useI18n()
const toast = useToast()
const formRef = ref()
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(0)

function createForm(): AppUserAddressForm {
  return {
    receiver_name: '',
    receiver_mobile: '',
    province: '',
    city: '',
    district: '',
    detail_address: '',
    postal_code: '',
    is_default: false,
  }
}

const form = reactive<AppUserAddressForm>(createForm())

const addressSchema: FormSchema = {
  validate: (model) => {
    const errors: Array<{ path: Array<string | number>, message: string }> = []
    const requiredFields: Array<[keyof AppUserAddressForm, string]> = [
      ['receiver_name', 'address.receiverNameRequired'],
      ['province', 'address.provinceRequired'],
      ['city', 'address.cityRequired'],
      ['district', 'address.districtRequired'],
      ['detail_address', 'address.detailAddressRequired'],
    ]
    requiredFields.forEach(([field, message]) => {
      if (!String(model[field] ?? '').trim())
        errors.push({ path: [field], message: t(message) })
    })

    const mobile = String(model.receiver_mobile ?? '').replace(/[\s-]+/g, '')
    if (!mobile)
      errors.push({ path: ['receiver_mobile'], message: t('address.receiverMobileRequired') })
    else if (!/^\+?[1-9]\d{6,14}$/.test(mobile))
      errors.push({ path: ['receiver_mobile'], message: t('address.receiverMobileInvalid') })
    return errors
  },
}

function resetForm() {
  Object.assign(form, createForm())
}

async function loadAddress(id: number) {
  loading.value = true
  try {
    const address = await AppUserAddressAPI.detail(id)
    Object.assign(form, {
      receiver_name: address.receiver_name,
      receiver_mobile: address.receiver_mobile,
      province: address.province,
      city: address.city,
      district: address.district,
      detail_address: address.detail_address,
      postal_code: address.postal_code || '',
      is_default: address.is_default,
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

  const payload: AppUserAddressForm = {
    receiver_name: form.receiver_name.trim(),
    receiver_mobile: form.receiver_mobile.replace(/[\s-]+/g, ''),
    province: form.province.trim(),
    city: form.city.trim(),
    district: form.district.trim(),
    detail_address: form.detail_address.trim(),
    postal_code: form.postal_code?.trim() || undefined,
    is_default: Boolean(form.is_default),
  }

  submitting.value = true
  try {
    if (editingId.value)
      await AppUserAddressAPI.update(editingId.value, payload)
    else
      await AppUserAddressAPI.create(payload)
    toast.success(t('address.saveSuccess'))
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
    void loadAddress(editingId.value)
  else
    resetForm()
})
</script>

<template>
  <view class="page-wraper py-3">
    <wd-loading v-if="loading" class="mx-auto my-8 block" />
    <view v-else class="address-form-card mx-3 rounded-2 p-4">
      <wd-form ref="formRef" :model="form" :schema="addressSchema">
        <wd-form-item prop="receiver_name" :label="t('address.receiverName')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.receiver_name" :placeholder="t('address.receiverNamePlaceholder')" clearable :compact="false" prefix-icon="user" />
        </wd-form-item>
        <wd-form-item prop="receiver_mobile" :label="t('address.receiverMobile')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.receiver_mobile" type="number" :placeholder="t('address.receiverMobilePlaceholder')" clearable :compact="false" prefix-icon="phone" />
        </wd-form-item>
        <wd-form-item prop="province" :label="t('address.province')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.province" :placeholder="t('address.provincePlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="city" :label="t('address.city')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.city" :placeholder="t('address.cityPlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="district" :label="t('address.district')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.district" :placeholder="t('address.districtPlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="detail_address" :label="t('address.detailAddress')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.detail_address" type="textarea" :rows="3" :placeholder="t('address.detailAddressPlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="postal_code" :label="t('address.postalCode')" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
          <wd-input v-model="form.postal_code" type="number" :placeholder="t('address.postalCodePlaceholder')" clearable :compact="false" />
        </wd-form-item>
        <wd-form-item prop="is_default" :label="t('address.isDefault')" custom-style="margin-bottom: 18rpx; padding-left: 0; padding-right: 0;">
          <wd-switch v-model="form.is_default" size="18px" />
        </wd-form-item>
      </wd-form>
      <wd-button type="primary" round block :loading="submitting" @click="handleSubmit">
        {{ submitting ? t('address.submitting') : t('address.submit') }}
      </wd-button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.address-form-card {
  background: var(--wot-color-white, #fff);
}
</style>
