<script setup lang="ts">
import type { AppUserBankAccount } from '@/api/module_app/bankAccount'
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppUserBankAccountAPI from '@/api/module_app/bankAccount'
import { useGlobalDialog } from '@/composables/useGlobalDialog'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'bank-accounts', style: { navigationBarTitleText: '我的银行卡' } })
useI18nNavTitle('bankAccount.navTitle')

const { t } = useI18n()
const toast = useToast()
const globalDialog = useGlobalDialog()
const accounts = ref<AppUserBankAccount[]>([])
const loading = ref(false)

function openForm(id?: number) {
  const query = id ? `?id=${encodeURIComponent(String(id))}` : ''
  uni.navigateTo({ url: `/subPages/module_app/bank-account/form${query}` })
}

async function loadAccounts() {
  loading.value = true
  try {
    accounts.value = await AppUserBankAccountAPI.list()
  }
  catch {
    accounts.value = []
    toast.error(t('bankAccount.loadFailed'))
  }
  finally {
    loading.value = false
  }
}

async function setDefault(account: AppUserBankAccount) {
  if (account.is_default || account.status !== 0)
    return
  try {
    await AppUserBankAccountAPI.setDefault(account.id)
    toast.success(t('bankAccount.setDefaultSuccess'))
    await loadAccounts()
  }
  catch {
    // http 层已统一提示
  }
}

async function unbind(account: AppUserBankAccount) {
  try {
    await AppUserBankAccountAPI.remove(account.id)
    toast.success(t('bankAccount.unbindSuccess'))
    await loadAccounts()
  }
  catch {
    // http 层已统一提示
  }
}

function confirmUnbind(account: AppUserBankAccount) {
  globalDialog.confirm({
    title: t('bankAccount.unbindTitle'),
    msg: t('bankAccount.unbindMsg'),
    confirmButtonText: t('bankAccount.unbind'),
    success: (result) => {
      if (result.action === 'confirm')
        void unbind(account)
    },
  })
}

onShow(loadAccounts)
</script>

<template>
  <view class="page-wraper py-3">
    <view class="mx-3 mb-3 flex items-center justify-between gap-3">
      <wd-text class="wot-text-text-main text-5 font-medium" :text="t('bankAccount.title')" />
      <wd-button type="primary" size="small" round @click="openForm()">
        {{ t('bankAccount.add') }}
      </wd-button>
    </view>

    <wd-loading v-if="loading && accounts.length === 0" class="mx-auto my-8 block" />
    <wd-empty v-else-if="accounts.length === 0" :tip="t('bankAccount.empty')" />

    <view v-else class="mx-3 flex flex-col gap-3">
      <view v-for="account in accounts" :key="account.id" class="bank-account-card wot-bg-filled-oppo rounded-2 p-4">
        <view class="flex items-center gap-2">
          <wd-text class="wot-text-text-main text-4 font-medium" :text="account.bank_name" />
          <wd-tag v-if="account.is_default && account.status === 0" type="primary" size="small" round>
            {{ t('bankAccount.default') }}
          </wd-tag>
          <wd-tag v-if="account.status === 1" type="danger" size="small" round>
            {{ t('bankAccount.disabled') }}
          </wd-tag>
        </view>
        <wd-text class="wot-text-text-main mt-3 block text-5 tracking-wide" :text="account.masked_card_number" />
        <wd-text class="wot-text-text-secondary mt-2 block text-3.5" :text="account.account_name" />
        <wd-text v-if="account.branch_name" class="wot-text-text-secondary mt-1 block text-3" :text="account.branch_name" />

        <view class="mt-3 flex items-center justify-end gap-2 border-t border-gray-100 pt-3">
          <wd-button v-if="!account.is_default && account.status === 0" size="small" plain @click="setDefault(account)">
            {{ t('bankAccount.setDefault') }}
          </wd-button>
          <wd-button size="small" plain @click="openForm(account.id)">
            {{ t('bankAccount.edit') }}
          </wd-button>
          <wd-button type="danger" size="small" plain @click="confirmUnbind(account)">
            {{ t('bankAccount.unbind') }}
          </wd-button>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.bank-account-card {
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
</style>
