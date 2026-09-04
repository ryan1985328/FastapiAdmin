<script setup lang="ts">
import type { AppProductDetail } from '@/api/module_app/product'
import { onLoad } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppOrderAPI from '@/api/module_app/order'
import AppProductAPI from '@/api/module_app/product'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useUserStore } from '@/store/userStore'
import { toLoginPage } from '@/utils/toLoginPage'

definePage({ name: 'product-detail', style: { navigationBarTitleText: '商品详情' } })
useI18nNavTitle('mall.detailTitle')

const { t } = useI18n()
const route = useRoute()
const userStore = useUserStore()
const toast = useToast()
const product = ref<AppProductDetail | null>(null)
const loading = ref(false)
const loadError = ref(false)
const quantity = ref(1)
const buying = ref(false)

const maxQuantity = computed(() => Math.max(1, Math.min(999, product.value?.stock ?? 1)))
const canBuy = computed(() => Boolean(product.value && product.value.stock > 0))

function normalizeQuantity() {
  const value = Number(quantity.value)
  quantity.value = Number.isFinite(value) ? Math.min(maxQuantity.value, Math.max(1, Math.floor(value))) : 1
}

async function loadProduct(id: number) {
  loading.value = true
  loadError.value = false
  try {
    product.value = await AppProductAPI.detail(id)
    quantity.value = 1
  }
  catch {
    product.value = null
    loadError.value = true
  }
  finally {
    loading.value = false
  }
}

async function buyNow() {
  if (!product.value || !canBuy.value || buying.value)
    return
  normalizeQuantity()
  if (!userStore.isLoggedIn()) {
    toLoginPage({ redirect: route.fullPath })
    return
  }

  buying.value = true
  try {
    const order = await AppOrderAPI.create({ product_id: product.value.id, quantity: quantity.value })
    toast.success(t('mall.orderCreated'))
    uni.navigateTo({ url: `/subPages/module_app/order/detail?id=${encodeURIComponent(String(order.id))}` })
  }
  catch {
    // http 层已统一提示
  }
  finally {
    buying.value = false
  }
}

onLoad((options) => {
  const id = Number(options?.id)
  if (Number.isInteger(id) && id > 0)
    void loadProduct(id)
  else
    loadError.value = true
})
</script>

<template>
  <view class="page-wraper py-3">
    <wd-loading v-if="loading" class="mx-auto my-8 block" />
    <template v-else-if="loadError || !product">
      <wd-empty :tip="t('mall.detailLoadFailed')" />
    </template>
    <template v-else>
      <view class="mx-3 overflow-hidden rounded-3 wot-bg-filled-oppo">
        <image v-if="product.cover_url" class="product-cover" :src="product.cover_url" mode="aspectFit" />
        <view v-else class="product-cover product-cover--empty flex items-center justify-center">
          <wd-icon name="shopping-bag" size="48px" color="var(--wot-text-color-secondary)" />
        </view>
        <view class="p-4">
          <view class="wot-text-text-main text-5 font-bold">{{ product.name }}</view>
          <view class="mt-2 flex items-center justify-between gap-3">
            <wd-text class="wot-text-price text-6 font-bold" :text="`¥${product.price}`" />
            <wd-text
              v-if="!product.sold_out"
              class="wot-text-text-secondary text-3"
              :text="t('mall.stock', { count: product.stock })"
            />
            <wd-tag v-else type="danger" round plain>{{ t('mall.soldOut') }}</wd-tag>
          </view>
        </view>
      </view>

      <view class="mx-3 mt-3 rounded-3 wot-bg-filled-oppo p-4">
        <view class="wot-text-text-main text-4 font-medium">{{ t('mall.description') }}</view>
        <view class="wot-text-text-secondary product-description mt-3 text-3.5 leading-relaxed">
          {{ product.description || t('mall.noDescription') }}
        </view>
      </view>

      <view class="mx-3 mt-3 flex items-center justify-between rounded-3 wot-bg-filled-oppo p-4">
        <wd-text class="wot-text-text-main text-3.5" :text="t('mall.quantity')" />
        <view class="flex items-center gap-2">
          <wd-button size="small" plain :disabled="quantity <= 1" @click="quantity = Math.max(1, quantity - 1)">−</wd-button>
          <input v-model.number="quantity" class="qty-input" type="number" min="1" :max="maxQuantity" @blur="normalizeQuantity">
          <wd-button size="small" plain :disabled="quantity >= maxQuantity" @click="quantity = Math.min(maxQuantity, quantity + 1)">+</wd-button>
        </view>
      </view>

      <view class="mx-3 mt-4">
        <wd-button type="primary" block round :disabled="!canBuy" :loading="buying" @click="buyNow">
          {{ canBuy ? t('mall.buyNow') : t('mall.soldOut') }}
        </wd-button>
      </view>
    </template>
    <wd-gap height="100rpx" safe-area-bottom />
  </view>
</template>

<style lang="scss" scoped>
.product-cover {
  display: block;
  width: 100%;
  height: 520rpx;
  background: var(--wot-color-bg);

  &--empty {
    background: var(--wot-color-bg);
  }
}

.product-description {
  white-space: pre-wrap;
  word-break: break-word;
}

.qty-input {
  width: 80rpx;
  height: 64rpx;
  border: 1px solid var(--wot-color-border);
  border-radius: 12rpx;
  color: var(--wot-text-color-primary);
  text-align: center;
}
</style>
