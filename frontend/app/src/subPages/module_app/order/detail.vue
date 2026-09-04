<script setup lang="ts">
import type { AppOrder } from '@/api/module_app/order'
import { onLoad } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppOrderAPI from '@/api/module_app/order'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'order-detail', style: { navigationBarTitleText: '订单详情' } })
useI18nNavTitle('order.detailTitle')

const { t } = useI18n()
const toast = useToast()
const order = ref<AppOrder | null>(null)
const loading = ref(false)
const loadError = ref(false)
const busy = ref(false)

function statusText(status: AppOrder['status']) {
  if (status === 'PAID') {
    return t('order.status.paid')
  }
  if (status === 'CANCELLED') {
    return t('order.status.cancelled')
  }
  return t('order.status.pending')
}

async function loadOrder(id: number) {
  loading.value = true
  loadError.value = false
  try {
    order.value = await AppOrderAPI.detail(id)
  }
  catch {
    order.value = null
    loadError.value = true
  }
  finally {
    loading.value = false
  }
}

async function pay() {
  if (!order.value || busy.value || order.value.status !== 'PENDING_PAYMENT')
    return
  busy.value = true
  try {
    order.value = await AppOrderAPI.pay(order.value.id)
    toast.success(t('order.paySuccess'))
  }
  catch {
    // http 层已统一提示
  }
  finally {
    busy.value = false
  }
}

async function cancel() {
  if (!order.value || busy.value || order.value.status !== 'PENDING_PAYMENT')
    return
  busy.value = true
  try {
    order.value = await AppOrderAPI.cancel(order.value.id)
    toast.success(t('order.cancelSuccess'))
  }
  catch {
    // http 层已统一提示
  }
  finally {
    busy.value = false
  }
}

onLoad((options) => {
  const id = Number(options?.id)
  if (Number.isInteger(id) && id > 0)
    void loadOrder(id)
  else
    loadError.value = true
})
</script>

<template>
  <view class="page-wraper py-3">
    <wd-loading v-if="loading" class="mx-auto my-8 block" />
    <template v-else-if="loadError || !order">
      <wd-empty :tip="t('order.detailLoadFailed')" />
    </template>
    <template v-else>
      <view class="mx-3 rounded-3 wot-bg-filled-oppo p-4">
        <view class="flex items-center justify-between gap-3">
          <wd-text class="wot-text-text-main text-4 font-medium" :text="t('order.statusLabel')" />
          <wd-tag round plain :type="order.status === 'PAID' ? 'success' : order.status === 'CANCELLED' ? 'info' : 'warning'">
            {{ statusText(order.status) }}
          </wd-tag>
        </view>
        <wd-text class="wot-text-text-secondary mt-3 block text-2.5" :text="order.order_no" />
        <wd-text class="wot-text-text-auxiliary mt-1 block text-2.5" :text="order.created_time || ''" />
      </view>

      <view class="mx-3 mt-3 rounded-3 wot-bg-filled-oppo p-4">
        <view v-for="item in order.items" :key="item.id" class="flex items-center gap-3">
          <view class="order-thumb flex shrink-0 items-center justify-center overflow-hidden rounded-2">
            <image v-if="item.product_cover" class="h-full w-full" :src="item.product_cover" mode="aspectFill" />
            <wd-icon v-else name="shopping-bag" size="24px" color="var(--wot-text-color-secondary)" />
          </view>
          <view class="min-w-0 flex-1">
            <view class="wot-text-text-main truncate text-3.5">{{ item.product_name }}</view>
            <view class="wot-text-text-secondary mt-1 text-2.5">¥{{ item.unit_price }} × {{ item.quantity }}</view>
          </view>
          <wd-text class="wot-text-price text-4 font-bold" :text="`¥${item.subtotal}`" />
        </view>
        <view class="mt-4 flex items-center justify-between border-t border-gray-100 pt-3 dark:border-gray-700">
          <wd-text class="wot-text-text-secondary text-3" :text="t('order.total')" />
          <wd-text class="wot-text-price text-5 font-bold" :text="`¥${order.total_amount}`" />
        </view>
      </view>

      <view v-if="order.status === 'PENDING_PAYMENT'" class="mx-3 mt-4 flex gap-3">
        <wd-button class="flex-1" plain :loading="busy" @click="cancel">{{ t('order.cancel') }}</wd-button>
        <wd-button class="flex-1" type="primary" :loading="busy" @click="pay">{{ t('order.developmentPayment') }}</wd-button>
      </view>
      <view v-else-if="order.status === 'PAID'" class="mx-3 mt-4">
        <wd-text class="wot-text-text-secondary block text-center text-3" :text="t('order.developmentPaymentNote')" />
      </view>
    </template>
    <wd-gap height="100rpx" safe-area-bottom />
  </view>
</template>

<style lang="scss" scoped>
.order-thumb {
  width: 128rpx;
  height: 128rpx;
  background: var(--wot-color-bg);
}
</style>
