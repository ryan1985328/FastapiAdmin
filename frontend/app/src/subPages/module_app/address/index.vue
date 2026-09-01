<script setup lang="ts">
import type { AppUserAddress } from '@/api/module_app/address'
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppUserAddressAPI from '@/api/module_app/address'
import { useGlobalDialog } from '@/composables/useGlobalDialog'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'addresses', style: { navigationBarTitleText: '我的地址' } })
useI18nNavTitle('address.navTitle')

const { t } = useI18n()
const toast = useToast()
const globalDialog = useGlobalDialog()
const addresses = ref<AppUserAddress[]>([])
const loading = ref(false)

function maskMobile(value: string) {
  const mobile = String(value || '')
  if (mobile.length <= 7)
    return mobile.replace(/\d/g, '*')
  return `${mobile.slice(0, 3)}${'*'.repeat(mobile.length - 7)}${mobile.slice(-4)}`
}

function formatRegion(address: AppUserAddress) {
  return [address.province, address.city, address.district].filter(Boolean).join(' ')
}

function openForm(id?: number) {
  const query = id ? `?id=${encodeURIComponent(String(id))}` : ''
  uni.navigateTo({ url: `/subPages/module_app/address/form${query}` })
}

async function loadAddresses() {
  loading.value = true
  try {
    addresses.value = await AppUserAddressAPI.list()
  }
  catch {
    addresses.value = []
    toast.error(t('address.loadFailed'))
  }
  finally {
    loading.value = false
  }
}

async function setDefault(address: AppUserAddress) {
  if (address.is_default)
    return
  try {
    await AppUserAddressAPI.setDefault(address.id)
    toast.success(t('address.setDefaultSuccess'))
    await loadAddresses()
  }
  catch {
    // http 层已统一提示
  }
}

async function deleteAddress(address: AppUserAddress) {
  try {
    await AppUserAddressAPI.remove(address.id)
    toast.success(t('address.deleteSuccess'))
    await loadAddresses()
  }
  catch {
    // http 层已统一提示
  }
}

function confirmDelete(address: AppUserAddress) {
  globalDialog.confirm({
    title: t('address.deleteTitle'),
    msg: t('address.deleteMsg'),
    confirmButtonText: t('common.delete'),
    success: (result) => {
      if (result.action === 'confirm')
        void deleteAddress(address)
    },
  })
}

onShow(loadAddresses)
</script>

<template>
  <view class="page-wraper py-3">
    <view class="mx-3 mb-3 flex items-center justify-between gap-3">
      <wd-text class="wot-text-text-main text-5 font-medium" :text="t('address.title')" />
      <wd-button type="primary" size="small" round @click="openForm()">
        {{ t('address.add') }}
      </wd-button>
    </view>

    <wd-loading v-if="loading && addresses.length === 0" class="mx-auto my-8 block" />
    <wd-empty v-else-if="addresses.length === 0" :tip="t('address.empty')" />

    <view v-else class="mx-3 flex flex-col gap-3">
      <view v-for="address in addresses" :key="address.id" class="address-card wot-bg-filled-oppo rounded-2 p-4">
        <view class="flex items-center gap-2">
          <wd-text class="wot-text-text-main text-4 font-medium" :text="address.receiver_name" />
          <wd-text class="wot-text-text-secondary text-3.5" :text="maskMobile(address.receiver_mobile)" />
          <wd-tag v-if="address.is_default" type="primary" size="small" round>
            {{ t('address.default') }}
          </wd-tag>
        </view>
        <wd-text class="wot-text-text-secondary mt-3 block text-3.5" :text="formatRegion(address)" />
        <wd-text class="wot-text-text-main mt-1 block text-3.5 leading-6" :text="address.detail_address" />

        <view class="mt-3 flex items-center justify-end gap-2 border-t border-gray-100 pt-3">
          <wd-button v-if="!address.is_default" size="small" plain @click="setDefault(address)">
            {{ t('address.setDefault') }}
          </wd-button>
          <wd-button size="small" plain @click="openForm(address.id)">
            {{ t('address.edit') }}
          </wd-button>
          <wd-button type="danger" size="small" plain @click="confirmDelete(address)">
            {{ t('common.delete') }}
          </wd-button>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.address-card {
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
</style>
