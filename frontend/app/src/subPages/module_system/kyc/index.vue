<script setup lang="ts">
import type { FormSchema } from '@wot-ui/ui/components/wd-form/types'
import type { AppKycInfo, AppKycSubmission } from '@/api/module_app/kyc'
import { onShow } from '@dcloudio/uni-app'
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppKycAPI from '@/api/module_app/kyc'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'kyc', style: { navigationBarTitleText: '实名认证' } })
useI18nNavTitle('kyc.navTitle')

const { t } = useI18n()
const toast = useToast()
const formRef = ref()
const loading = ref(false)
const loadError = ref(false)
const submitting = ref(false)
const uploadingSide = ref<'front' | 'back' | null>(null)
const kyc = ref<AppKycInfo | null>(null)
const frontPath = ref('')
const backPath = ref('')
const frontPreview = ref('')
const backPreview = ref('')

const form = reactive({
  real_name: '',
  id_card_no: '',
})

const statusText = computed(() => {
  if (!kyc.value)
    return t('kyc.status.unverified')
  return t(`kyc.status.${kyc.value.status === 0 ? 'pending' : kyc.value.status === 1 ? 'approved' : 'rejected'}`)
})

const isEditable = computed(() => !kyc.value || kyc.value.status === 2)
const isResubmit = computed(() => kyc.value?.status === 2)

function maskIdCard(value: string | null | undefined) {
  const normalized = String(value || '').trim()
  if (!normalized)
    return t('profile.notSet')
  if (normalized.length <= 4)
    return '•'.repeat(normalized.length)
  return `${normalized.slice(0, 2)}${'•'.repeat(Math.max(2, normalized.length - 4))}${normalized.slice(-2)}`
}

const kycSchema: FormSchema = {
  validate: (model) => {
    const errors: Array<{ path: Array<string | number>, message: string }> = []
    if (!String(model.real_name ?? '').trim())
      errors.push({ path: ['real_name'], message: t('kyc.realNameRequired') })
    if (!String(model.id_card_no ?? '').trim())
      errors.push({ path: ['id_card_no'], message: t('kyc.idCardRequired') })
    if (!frontPath.value)
      errors.push({ path: ['id_card_front'], message: t('kyc.frontRequired') })
    if (!backPath.value)
      errors.push({ path: ['id_card_back'], message: t('kyc.backRequired') })
    return errors
  },
}

function resetForm() {
  form.real_name = kyc.value?.real_name || ''
  form.id_card_no = kyc.value?.id_card_no || ''
  frontPath.value = kyc.value?.id_card_front || ''
  backPath.value = kyc.value?.id_card_back || ''
  frontPreview.value = ''
  backPreview.value = ''
}

async function loadKyc() {
  loading.value = true
  loadError.value = false
  try {
    kyc.value = await AppKycAPI.getMine()
    resetForm()
  }
  catch {
    if (!kyc.value)
      loadError.value = true
  }
  finally {
    loading.value = false
  }
}

function chooseImage(side: 'front' | 'back') {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (result) => {
      const filePath = result.tempFilePaths?.[0]
      if (!filePath)
        return
      if (side === 'front')
        frontPreview.value = filePath
      else
        backPreview.value = filePath
      uploadingSide.value = side
      try {
        const uploaded = await AppKycAPI.uploadImage({ filePath, name: 'file' })
        const reference = uploaded.file_path || uploaded.file_url || ''
        if (!reference)
          throw new Error(t('kyc.uploadFailed'))
        if (side === 'front')
          frontPath.value = reference
        else
          backPath.value = reference
        toast.success(t('kyc.uploadSuccess'))
      }
      catch {
        if (side === 'front') {
          frontPath.value = ''
          frontPreview.value = ''
        }
        else {
          backPath.value = ''
          backPreview.value = ''
        }
      }
      finally {
        uploadingSide.value = null
      }
    },
  })
}

async function handleSubmit() {
  if (submitting.value || !isEditable.value)
    return
  const { valid } = await formRef.value.validate()
  if (!valid)
    return

  const payload: AppKycSubmission = {
    real_name: form.real_name.trim(),
    id_card_no: form.id_card_no.trim(),
    id_card_front: frontPath.value,
    id_card_back: backPath.value,
  }
  submitting.value = true
  try {
    kyc.value = isResubmit.value ? await AppKycAPI.resubmit(payload) : await AppKycAPI.submit(payload)
    resetForm()
    toast.success(t('kyc.submitSuccess'))
  }
  catch {
    // http 层已统一提示
  }
  finally {
    submitting.value = false
  }
}

onShow(loadKyc)
</script>

<template>
  <view class="page-wraper py-3">
    <SkeletonPage v-if="loading && !kyc" :rows="5" />
    <template v-else-if="loadError">
      <wd-empty :tip="t('common.loadFailed')" />
      <view class="mt-3 flex justify-center">
        <wd-button size="small" plain @click="loadKyc">
          {{ t('common.retry') }}
        </wd-button>
      </view>
    </template>
    <template v-else>
      <view class="mx-3 mb-3 rounded-2 p-4" :class="kyc?.status === 1 ? 'wot-bg-green-1' : 'wot-bg-filled-oppo'">
        <view class="flex items-center justify-between gap-3">
          <wd-text class="wot-text-text-main text-4 font-medium" :text="t('kyc.title')" />
          <wd-tag :type="kyc?.status === 1 ? 'success' : kyc?.status === 2 ? 'danger' : 'warning'" round>
            {{ statusText }}
          </wd-tag>
        </view>
        <wd-text v-if="kyc?.status === 0" class="wot-text-text-secondary mt-2 block text-3" :text="t('kyc.pendingTip')" />
        <wd-text v-if="kyc?.status === 1" class="wot-text-text-secondary mt-2 block text-3" :text="t('kyc.approvedTip')" />
        <wd-text v-if="kyc?.status === 2" class="mt-2 block text-3 text-red-5" :text="kyc.review_remark || t('kyc.rejectedTip')" />
        <wd-text v-if="!kyc" class="wot-text-text-secondary mt-2 block text-3" :text="t('kyc.unverifiedTip')" />
      </view>

      <view v-if="kyc && !isEditable" class="mx-3 mb-3">
        <wd-cell-group border custom-class="rounded-2! overflow-hidden">
          <wd-cell :title="t('kyc.realName')" :value="kyc.real_name || t('profile.notSet')" />
          <wd-cell :title="t('kyc.idCard')" :value="maskIdCard(kyc.id_card_no)" />
          <wd-cell :title="t('kyc.documents')" :value="t('kyc.documentsUploaded')" />
        </wd-cell-group>
      </view>

      <view v-if="isEditable" class="wot-bg-filled-oppo mx-3 rounded-2 p-4">
        <wd-form ref="formRef" :model="form" :schema="kycSchema">
          <wd-form-item prop="real_name" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input v-model="form.real_name" :placeholder="t('kyc.realNamePlaceholder')" clearable :compact="false" prefix-icon="user" />
          </wd-form-item>
          <wd-form-item prop="id_card_no" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input v-model="form.id_card_no" :placeholder="t('kyc.idCardPlaceholder')" clearable :compact="false" prefix-icon="edit" />
          </wd-form-item>
          <wd-form-item prop="id_card_front" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <view class="upload-card" @click="chooseImage('front')">
              <image v-if="frontPreview" class="upload-card__preview" :src="frontPreview" mode="aspectFill" />
              <view v-else class="upload-card__placeholder">
                <wd-icon name="camera" size="24px" color="var(--wot-primary-6)" />
                <wd-text class="mt-1" :text="t('kyc.front')" />
              </view>
              <wd-loading v-if="uploadingSide === 'front'" class="upload-card__loading" />
            </view>
          </wd-form-item>
          <wd-form-item prop="id_card_back" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <view class="upload-card" @click="chooseImage('back')">
              <image v-if="backPreview" class="upload-card__preview" :src="backPreview" mode="aspectFill" />
              <view v-else class="upload-card__placeholder">
                <wd-icon name="camera" size="24px" color="var(--wot-primary-6)" />
                <wd-text class="mt-1" :text="t('kyc.back')" />
              </view>
              <wd-loading v-if="uploadingSide === 'back'" class="upload-card__loading" />
            </view>
          </wd-form-item>
        </wd-form>
        <wd-button type="primary" round block :loading="submitting" :disabled="!!uploadingSide" @click="handleSubmit">
          {{ isResubmit ? t('kyc.resubmit') : t('kyc.submit') }}
        </wd-button>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.upload-card {
  position: relative;
  min-height: 220rpx;
  overflow: hidden;
  border: 2rpx dashed var(--wot-border-main);
  border-radius: 20rpx;
  background: var(--wot-fill-light, #f7f8fa);

  &__preview {
    display: block;
    width: 100%;
    height: 220rpx;
  }

  &__placeholder {
    display: flex;
    height: 220rpx;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    color: var(--wot-text-secondary);
  }

  &__loading {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgb(255 255 255 / 55%);
  }
}
</style>
