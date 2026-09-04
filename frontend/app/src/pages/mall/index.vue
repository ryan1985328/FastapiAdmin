<script setup lang="ts">
import type { AppProductListItem } from '@/api/module_app/product'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppProductAPI from '@/api/module_app/product'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useTabbarActive } from '@/composables/useTabbarActive'
import { Storage } from '@/utils/storage'

definePage({
  name: 'mall',
  layout: 'tabbar',
  style: { navigationBarTitleText: '商城' },
})
useI18nNavTitle('mall.navTitle')

const { t } = useI18n()
const products = ref<AppProductListItem[]>([])
const keyword = ref('')
const pageNo = ref(1)
const hasNext = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const loadError = ref(false)
const viewMode = ref<'grid' | 'list'>(Storage.get<'grid' | 'list'>('mini-mall-view-mode', 'grid') === 'list' ? 'list' : 'grid')
const LOW_STOCK_THRESHOLD = 5

const isSearchResult = computed(() => Boolean(keyword.value.trim()))

function setViewMode(mode: 'grid' | 'list') {
  viewMode.value = mode
  Storage.set('mini-mall-view-mode', mode)
}

function formatMoney(value: unknown): string {
  const text = String(value ?? '').trim()
  const [wholePart = '0', fractionPart = ''] = text.split('.')
  const whole = wholePart.replace(/[^\d]/g, '').replace(/^0+(?=\d)/, '') || '0'
  return `¥${whole}.${fractionPart.replace(/[^\d]/g, '').slice(0, 2).padEnd(2, '0')}`
}

function availabilityText(product: AppProductListItem): string {
  if (product.sold_out) return t('mall.soldOut')
  if (product.stock <= LOW_STOCK_THRESHOLD) return t('mall.lowStock', { count: product.stock })
  return t('mall.inStock')
}

async function loadProducts(reset = true) {
  if (reset) {
    loading.value = true
    pageNo.value = 1
    loadError.value = false
  }
  else {
    if (loadingMore.value || !hasNext.value) return
    loadingMore.value = true
  }

  const targetPage = reset ? 1 : pageNo.value + 1
  try {
    const result = await AppProductAPI.list({
      page_no: targetPage,
      page_size: 10,
      keyword: keyword.value.trim() || undefined,
    })
    const items = Array.isArray(result?.items) ? result.items : []
    if (reset) products.value = items
    else products.value.push(...items)
    pageNo.value = targetPage
    hasNext.value = Boolean(result?.has_next)
  }
  catch {
    if (reset) {
      products.value = []
      loadError.value = true
    }
  }
  finally {
    loading.value = false
    loadingMore.value = false
  }
}

function openProduct(product: AppProductListItem) {
  uni.navigateTo({ url: `/subPages/module_product/product-detail/index?id=${encodeURIComponent(String(product.id))}` })
}

function search() {
  void loadProducts(true)
}

function clearSearch() {
  keyword.value = ''
  void loadProducts(true)
}

onShow(() => loadProducts(true))
onPullDownRefresh(async () => {
  try {
    await loadProducts(true)
  }
  finally {
    uni.stopPullDownRefresh()
  }
})
onReachBottom(() => loadProducts(false))
useTabbarActive('pages/mall/index', 'mall')
</script>

<template>
  <view class="page-wraper mall-page py-3">
    <view class="mall-header mx-3 mb-3 flex items-center justify-between gap-3">
      <view>
        <view class="wot-text-text-main text-5 font-bold">{{ t('mall.navTitle') }}</view>
        <view class="wot-text-text-secondary mt-1 text-2.5">{{ t('mall.headerSubtitle') }}</view>
      </view>
      <view class="mall-view-toggle flex items-center gap-1 rounded-xl p-1" aria-label="商品视图切换">
        <wd-button
          size="small"
          :type="viewMode === 'grid' ? 'primary' : 'info'"
          :plain="viewMode !== 'grid'"
          aria-label="网格视图"
          @click="setViewMode('grid')"
        >
          <wd-icon name="apps" size="17px" />
        </wd-button>
        <wd-button
          size="small"
          :type="viewMode === 'list' ? 'primary' : 'info'"
          :plain="viewMode !== 'list'"
          aria-label="列表视图"
          @click="setViewMode('list')"
        >
          <wd-icon name="list" size="17px" />
        </wd-button>
      </view>
    </view>

    <view class="mx-3 mb-3 flex gap-2">
      <wd-input
        v-model="keyword"
        class="flex-1"
        :placeholder="t('mall.searchPlaceholder')"
        clearable
        :compact="false"
        prefix-icon="search"
        @confirm="search"
        @clear="search"
      />
      <wd-button type="primary" @click="search">
        {{ t('mall.search') }}
      </wd-button>
    </view>

    <view v-if="loading && products.length === 0" class="mall-skeleton-grid mx-3" aria-label="商品加载中">
      <view v-for="index in 4" :key="index" class="mall-skeleton-card">
        <view class="mall-skeleton-card__image" />
        <view class="mall-skeleton-card__line mall-skeleton-card__line--wide" />
        <view class="mall-skeleton-card__line" />
      </view>
    </view>
    <template v-else-if="loadError">
      <wd-empty :tip="t('common.loadFailed')" />
      <view class="mt-3 flex justify-center">
        <wd-button size="small" plain @click="loadProducts(true)">
          {{ t('common.retry') }}
        </wd-button>
      </view>
    </template>
    <template v-else-if="products.length === 0">
      <wd-empty :tip="isSearchResult ? t('mall.searchEmpty') : t('mall.empty')" />
      <view v-if="isSearchResult" class="mt-3 flex justify-center">
        <wd-button size="small" plain @click="clearSearch">
          {{ t('mall.clearSearch') }}
        </wd-button>
      </view>
    </template>
    <view v-else class="mx-3" :class="viewMode === 'grid' ? 'mall-product-grid' : 'mall-product-list'">
      <view
        v-for="product in products"
        :key="product.id"
        class="mall-card wot-bg-filled-oppo overflow-hidden rounded-2"
        :class="{ 'mall-card--sold-out': product.sold_out }"
        @click="openProduct(product)"
      >
        <image v-if="product.cover_url" class="mall-card__cover" :src="product.cover_url" mode="aspectFill" />
        <view v-else class="mall-card__cover mall-card__placeholder flex items-center justify-center">
          <wd-icon name="shopping-bag" size="34px" color="var(--wot-text-color-secondary)" />
        </view>
        <view class="mall-card__body p-3">
          <view class="wot-text-text-main mall-card__name text-3.5 font-medium">{{ product.name }}</view>
          <view class="mall-card__meta mt-2 flex items-center justify-between gap-2">
            <wd-text class="wot-text-price text-4 font-bold" :text="formatMoney(product.price)" />
            <wd-tag v-if="product.sold_out" type="danger" size="small" round plain>
              {{ t('mall.soldOut') }}
            </wd-tag>
            <wd-text
              v-else
              class="wot-text-text-auxiliary text-2.5"
              :class="{ 'mall-card__availability--low': product.stock <= LOW_STOCK_THRESHOLD }"
              :text="availabilityText(product)"
            />
          </view>
        </view>
      </view>
    </view>

    <view v-if="loadingMore" class="py-4 text-center"><wd-loading /></view>
    <wd-text
      v-else-if="products.length > 0 && !hasNext"
      class="wot-text-text-auxiliary block py-4 text-center text-2.5"
      :text="t('mall.noMore')"
    />
    <wd-gap height="100rpx" safe-area-bottom />
  </view>
</template>

<style lang="scss" scoped>
.mall-page {
  min-height: 100%;
}

.mall-header {
  min-height: 66rpx;
}

.mall-view-toggle {
  background: var(--wot-color-bg);
}

.mall-product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24rpx;
}

.mall-product-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.mall-card {
  min-width: 0;
  box-shadow: 0 4rpx 18rpx rgb(0 0 0 / 4%);

  &__cover {
    display: block;
    width: 100%;
    height: 300rpx;
  }

  &__placeholder {
    background: var(--wot-color-bg);
  }

  &__body {
    min-width: 0;
  }

  &__name {
    display: -webkit-box;
    overflow: hidden;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-height: 1.45;
  }

  &__meta {
    min-width: 0;
  }

  &__availability--low {
    color: var(--wot-orange-6);
  }

  &--sold-out {
    opacity: 0.78;
  }
}

.mall-product-list .mall-card {
  display: flex;
  align-items: stretch;

  &__cover {
    width: 220rpx;
    min-width: 220rpx;
    height: 220rpx;
  }

  &__body {
    display: flex;
    flex: 1;
    flex-direction: column;
    justify-content: center;
  }

  &__meta {
    margin-top: 18rpx;
  }
}

.mall-skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24rpx;
}

.mall-skeleton-card {
  padding-bottom: 22rpx;
  overflow: hidden;
  border-radius: 16rpx;
  background: var(--wot-bg-color-page, var(--wot-color-bg));

  &__image,
  &__line {
    background: linear-gradient(90deg, var(--wot-color-bg) 25%, var(--wot-border-color) 50%, var(--wot-color-bg) 75%);
    background-size: 240% 100%;
    animation: mall-skeleton-shimmer 1.4s infinite;
  }

  &__image {
    height: 300rpx;
  }

  &__line {
    width: 70%;
    height: 22rpx;
    margin: 18rpx 20rpx 0;
    border-radius: 99rpx;

    &--wide {
      width: 84%;
    }
  }
}

@keyframes mall-skeleton-shimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}

@media (max-width: 370px) {
  .mall-product-list .mall-card__cover {
    width: 190rpx;
    min-width: 190rpx;
    height: 190rpx;
  }
}
</style>
