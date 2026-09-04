<script setup lang="ts">
import type { AppProductDetail, AppProductImage } from '@/api/module_app/product'
import { onLoad } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppOrderAPI from '@/api/module_app/order'
import AppProductAPI from '@/api/module_app/product'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useUserStore } from '@/store/userStore'
import { toLoginPage } from '@/utils/toLoginPage'
import { MARKDOWN_TAG_STYLE } from '@/constants/markdown.constant'

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
const purchaseVisible = ref(false)
const currentImageIndex = ref(0)

const displayImages = computed<AppProductImage[]>(() => {
  if (product.value?.images?.length) return product.value.images
  if (product.value?.cover_url) return [{ url: product.value.cover_url, sort: 0 }]
  return []
})
const maxQuantity = computed(() => Math.max(1, Math.min(999, product.value?.stock ?? 1)))
const canBuy = computed(() => Boolean(product.value && product.value.stock > 0))

function moneyToCents(value: unknown): number {
  const [wholePart = '0', fractionPart = ''] = String(value ?? '0').trim().split('.')
  const whole = Number(wholePart.replace(/[^\d]/g, '')) || 0
  const fraction = Number(fractionPart.replace(/[^\d]/g, '').slice(0, 2).padEnd(2, '0')) || 0
  return whole * 100 + fraction
}

function formatCents(cents: number): string {
  const safeCents = Math.max(0, Math.trunc(cents))
  return `¥${Math.floor(safeCents / 100)}.${String(safeCents % 100).padStart(2, '0')}`
}

const amountPreview = computed(() => formatCents(moneyToCents(product.value?.price) * quantity.value))

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
    currentImageIndex.value = 0
  }
  catch {
    product.value = null
    loadError.value = true
  }
  finally {
    loading.value = false
  }
}

function openPurchaseSheet() {
  if (!product.value || !canBuy.value || buying.value) return
  normalizeQuantity()
  if (!userStore.isLoggedIn()) {
    toLoginPage({ redirect: route.fullPath })
    return
  }
  purchaseVisible.value = true
}

function closePurchaseSheet() {
  if (!buying.value) purchaseVisible.value = false
}

function handleSwiperChange(event: { detail?: { current?: number } }) {
  const next = Number(event.detail?.current)
  if (Number.isInteger(next) && next >= 0) currentImageIndex.value = next
}

async function confirmPurchase() {
  if (!product.value || !canBuy.value || buying.value) return
  normalizeQuantity()
  buying.value = true
  try {
    const order = await AppOrderAPI.create({ product_id: product.value.id, quantity: quantity.value })
    purchaseVisible.value = false
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
  if (Number.isInteger(id) && id > 0) void loadProduct(id)
  else loadError.value = true
})
</script>

<template>
  <view class="page-wraper product-detail-page py-3">
    <wd-loading v-if="loading" class="mx-auto my-8 block" />
    <template v-else-if="loadError || !product">
      <wd-empty :tip="t('mall.detailLoadFailed')" />
    </template>
    <template v-else>
      <view class="mx-3 overflow-hidden rounded-3 wot-bg-filled-oppo">
        <view v-if="displayImages.length" class="product-gallery">
          <swiper
            class="product-gallery__swiper"
            :current="currentImageIndex"
            :duration="260"
            :circular="displayImages.length > 1"
            @change="handleSwiperChange"
          >
            <swiper-item v-for="(image, index) in displayImages" :key="`${image.url}-${index}`">
              <image class="product-gallery__image" :src="image.url" mode="aspectFit" :alt="`${product.name} ${index + 1}`" />
            </swiper-item>
          </swiper>
          <view v-if="displayImages.length > 1" class="product-gallery__indicator" aria-label="商品图片指示器">
            <view
              v-for="(_image, index) in displayImages"
              :key="index"
              class="product-gallery__dot"
              :class="{ 'product-gallery__dot--active': index === currentImageIndex }"
            />
            <view class="product-gallery__count">{{ currentImageIndex + 1 }}/{{ displayImages.length }}</view>
          </view>
        </view>
        <view v-else class="product-gallery product-gallery--empty flex items-center justify-center">
          <wd-icon name="shopping-bag" size="48px" color="var(--wot-text-color-secondary)" />
        </view>
        <view class="p-4">
          <view class="wot-text-text-main text-5 font-bold">{{ product.name }}</view>
          <view class="mt-2 flex items-center justify-between gap-3">
            <wd-text class="wot-text-price text-6 font-bold" :text="formatCents(moneyToCents(product.price))" />
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
          <mp-html
            v-if="product.description"
            :content="product.description"
            :tag-style="MARKDOWN_TAG_STYLE"
            :selectable="true"
            :preview-img="true"
            :scroll-table="true"
            :set-title="false"
            container-style="width: 100%; overflow-wrap: anywhere;"
          />
          <view v-else>{{ t('mall.noDescription') }}</view>
        </view>
      </view>

      <view class="product-detail-page__bottom-spacer" aria-hidden="true" />

      <view class="product-purchase-bar" style="padding-bottom: env(safe-area-inset-bottom);">
        <view class="product-purchase-bar__amount">
          <view class="wot-text-text-secondary text-2.5">{{ t('mall.totalPreview') }}</view>
          <view class="wot-text-price mt-1 text-5 font-bold">{{ formatCents(moneyToCents(product.price)) }}</view>
        </view>
        <wd-button
          class="product-purchase-bar__button"
          type="primary"
          round
          :disabled="!canBuy"
          :loading="buying"
          @click="openPurchaseSheet"
        >
          {{ canBuy ? t('mall.buyNow') : t('mall.soldOut') }}
        </wd-button>
      </view>

      <view v-if="purchaseVisible" class="purchase-overlay" @click.self="closePurchaseSheet">
        <view class="purchase-sheet wot-bg-filled-oppo" @click.stop>
          <view class="flex items-center justify-between">
            <view class="wot-text-text-main text-4 font-bold">{{ t('mall.confirmPurchase') }}</view>
            <wd-icon name="close" size="20px" color="var(--wot-text-color-secondary)" @click="closePurchaseSheet" />
          </view>
          <view class="purchase-sheet__product mt-4 flex items-center gap-3">
            <image v-if="displayImages[0]" class="purchase-sheet__image" :src="displayImages[0].url" mode="aspectFill" />
            <view class="min-w-0 flex-1">
              <view class="wot-text-text-main truncate text-3.5 font-medium">{{ product.name }}</view>
              <view class="wot-text-price mt-1 text-3.5">{{ formatCents(moneyToCents(product.price)) }}</view>
            </view>
          </view>
          <view class="purchase-sheet__row mt-5 flex items-center justify-between">
            <wd-text class="wot-text-text-secondary text-3.5" :text="t('mall.quantity')" />
            <view class="flex items-center gap-2">
              <wd-button size="small" plain :disabled="quantity <= 1" @click="quantity = Math.max(1, quantity - 1)">−</wd-button>
              <input v-model.number="quantity" class="qty-input" type="number" min="1" :max="maxQuantity" @blur="normalizeQuantity">
              <wd-button size="small" plain :disabled="quantity >= maxQuantity" @click="quantity = Math.min(maxQuantity, quantity + 1)">+</wd-button>
            </view>
          </view>
          <view class="mt-5 flex items-center justify-between">
            <wd-text class="wot-text-text-secondary text-3.5" :text="t('mall.amountPreview')" />
            <view class="wot-text-price text-5 font-bold">{{ amountPreview }}</view>
          </view>
          <wd-button class="mt-5" type="primary" block round :loading="buying" @click="confirmPurchase">
            {{ t('mall.confirmBuy') }}
          </wd-button>
        </view>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.product-detail-page {
  min-height: 100%;
}

.product-detail-page__bottom-spacer {
  height: calc(180rpx + env(safe-area-inset-bottom));
}

.product-gallery {
  position: relative;
  background: var(--wot-color-bg);

  &__swiper,
  &__image {
    display: block;
    width: 100%;
    height: 520rpx;
  }

  &__image {
    background: var(--wot-color-bg);
  }

  &--empty {
    height: 520rpx;
  }

  &__indicator {
    position: absolute;
    right: 20rpx;
    bottom: 18rpx;
    left: 20rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8rpx;
  }

  &__dot {
    width: 10rpx;
    height: 10rpx;
    border-radius: 50%;
    background: rgb(0 0 0 / 25%);

    &--active {
      width: 24rpx;
      border-radius: 99rpx;
      background: var(--wot-primary-color);
    }
  }

  &__count {
    position: absolute;
    right: 0;
    padding: 4rpx 12rpx;
    border-radius: 99rpx;
    color: #fff;
    background: rgb(0 0 0 / 48%);
    font-size: 22rpx;
  }
}

.product-description {
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;

  :deep(img) {
    max-width: 100% !important;
    height: auto !important;
  }
}

.product-purchase-bar {
  position: fixed;
  z-index: 20;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 18rpx 24rpx;
  border-top: 1px solid var(--wot-border-color);
  background: var(--wot-bg-color-page, var(--wot-color-bg));
  box-shadow: 0 -6rpx 24rpx rgb(0 0 0 / 6%);

  &__amount {
    min-width: 0;
  }

  &__button {
    min-width: 240rpx;
  }
}

.purchase-overlay {
  position: fixed;
  z-index: 30;
  inset: 0;
  display: flex;
  align-items: flex-end;
  background: rgb(0 0 0 / 45%);
}

.purchase-sheet {
  width: 100%;
  padding: 28rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
  border-radius: 28rpx 28rpx 0 0;
}

.purchase-sheet__image {
  width: 120rpx;
  height: 120rpx;
  border-radius: 16rpx;
  background: var(--wot-color-bg);
}

.qty-input {
  width: 80rpx;
  height: 64rpx;
  border: 1px solid var(--wot-border-color);
  border-radius: 12rpx;
  color: var(--wot-text-color-primary);
  text-align: center;
}
</style>
