<script setup lang="ts">
import type { AppOrder } from '@/api/module_app/order'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppOrderAPI from '@/api/module_app/order'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'orders', style: { navigationBarTitleText: '我的订单' } })
useI18nNavTitle('order.navTitle')

const { t } = useI18n()
const toast = useToast()
const orders = ref<AppOrder[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const pageNo = ref(1)
const hasNext = ref(false)
const loadError = ref(false)
const busyId = ref<number | null>(null)

function statusText(status: AppOrder['status']) {
  if (status === 'PAID') {
    return t('order.status.paid')
  }
  if (status === 'CANCELLED') {
    return t('order.status.cancelled')
  }
  return t('order.status.pending')
}

function statusType(status: AppOrder['status']) {
  if (status === 'PAID') {
    return 'success'
  }
  if (status === 'CANCELLED') {
    return 'info'
  }
  return 'warning'
}

function openDetail(order: AppOrder) {
  uni.navigateTo({ url: `/subPages/module_app/order/detail?id=${encodeURIComponent(String(order.id))}` })
}

async function loadOrders(reset = true) {
  if (reset) {
    loading.value = true
    pageNo.value = 1
    loadError.value = false
  }
  else {
    if (loadingMore.value || !hasNext.value)
      return
    loadingMore.value = true
  }

  const targetPage = reset ? 1 : pageNo.value + 1
  try {
    const result = await AppOrderAPI.list({ page_no: targetPage, page_size: 10 })
    const items = Array.isArray(result?.items) ? result.items : []
    if (reset)
      orders.value = items
    else
      orders.value.push(...items)
    pageNo.value = targetPage
    hasNext.value = Boolean(result?.has_next)
  }
  catch {
    if (reset) {
      orders.value = []
      loadError.value = true
    }
  }
  finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function pay(order: AppOrder) {
  if (busyId.value !== null)
    return
  busyId.value = order.id
  try {
    await AppOrderAPI.pay(order.id)
    toast.success(t('order.paySuccess'))
    await loadOrders(true)
  }
  catch {
    // http 层已统一提示
  }
  finally {
    busyId.value = null
  }
}

async function cancel(order: AppOrder) {
  if (busyId.value !== null)
    return
  busyId.value = order.id
  try {
    await AppOrderAPI.cancel(order.id)
    toast.success(t('order.cancelSuccess'))
    await loadOrders(true)
  }
  catch {
    // http 层已统一提示
  }
  finally {
    busyId.value = null
  }
}

onShow(() => loadOrders(true))
onPullDownRefresh(async () => {
  try {
    await loadOrders(true)
  }
  finally {
    uni.stopPullDownRefresh()
  }
})
onReachBottom(() => loadOrders(false))
</script>

<template>
  <view class="page-wraper py-3">
    <wd-loading v-if="loading && orders.length === 0" class="mx-auto my-8 block" />
    <template v-else-if="loadError">
      <wd-empty :tip="t('common.loadFailed')" />
      <view class="mt-3 flex justify-center"><wd-button size="small" plain @click="loadOrders(true)">{{ t('common.retry') }}</wd-button></view>
    </template>
    <wd-empty v-else-if="orders.length === 0" :tip="t('order.empty')" />
    <view v-else class="mx-3 flex flex-col gap-3">
      <view v-for="order in orders" :key="order.id" class="order-card wot-bg-filled-oppo rounded-3 p-4" @click="openDetail(order)">
        <view class="flex items-center justify-between gap-2">
          <wd-text class="wot-text-text-secondary truncate text-2.5" :text="order.order_no" />
          <wd-tag size="small" round plain :type="statusType(order.status)">{{ statusText(order.status) }}</wd-tag>
        </view>
        <view v-if="order.items[0]" class="mt-3 flex items-center gap-3">
          <view class="order-card__thumb flex shrink-0 items-center justify-center overflow-hidden rounded-2">
            <image v-if="order.items[0].product_cover" class="h-full w-full" :src="order.items[0].product_cover" mode="aspectFill" />
            <wd-icon v-else name="shopping-bag" size="24px" color="var(--wot-text-color-secondary)" />
          </view>
          <view class="min-w-0 flex-1">
            <view class="wot-text-text-main truncate text-3.5">{{ order.items[0].product_name }}</view>
            <view class="wot-text-text-secondary mt-1 text-2.5">×{{ order.items[0].quantity }} · ¥{{ order.items[0].unit_price }}</view>
          </view>
          <wd-text class="wot-text-price text-4 font-bold" :text="`¥${order.total_amount}`" />
        </view>
        <view class="mt-3 flex items-center justify-between gap-2">
          <wd-text class="wot-text-text-auxiliary text-2.5" :text="order.created_time || ''" />
          <view v-if="order.status === 'PENDING_PAYMENT'" class="flex gap-2" @click.stop>
            <wd-button size="small" plain :loading="busyId === order.id" @click="cancel(order)">{{ t('order.cancel') }}</wd-button>
            <wd-button size="small" type="primary" :loading="busyId === order.id" @click="pay(order)">{{ t('order.developmentPayment') }}</wd-button>
          </view>
        </view>
      </view>
      <view v-if="loadingMore" class="py-4 text-center"><wd-loading /></view>
      <wd-text v-else-if="!hasNext" class="wot-text-text-auxiliary block py-3 text-center text-2.5" :text="t('mall.noMore')" />
    </view>
    <wd-gap height="100rpx" safe-area-bottom />
  </view>
</template>

<style lang="scss" scoped>
.order-card {
  box-shadow: 0 4rpx 18rpx rgba(0, 0, 0, 0.04);

  &__thumb {
    width: 112rpx;
    height: 112rpx;
    background: var(--wot-color-bg);
  }
}
</style>
