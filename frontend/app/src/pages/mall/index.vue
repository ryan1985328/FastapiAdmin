<script setup lang="ts">
import type { AppProductListItem } from '@/api/module_app/product'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppProductAPI from '@/api/module_app/product'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useTabbarActive } from '@/composables/useTabbarActive'

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

async function loadProducts(reset = true) {
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
    const result = await AppProductAPI.list({
      page_no: targetPage,
      page_size: 10,
      keyword: keyword.value.trim() || undefined,
    })
    const items = Array.isArray(result?.items) ? result.items : []
    if (reset)
      products.value = items
    else
      products.value.push(...items)
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
  <view class="page-wraper py-3">
    <view class="mx-3 mb-3 flex gap-2">
      <wd-input
        v-model="keyword"
        class="flex-1"
        :placeholder="t('mall.searchPlaceholder')"
        clearable
        :compact="false"
        prefix-icon="search"
        @confirm="search"
      />
      <wd-button type="primary" @click="search">
        {{ t('mall.search') }}
      </wd-button>
    </view>

    <wd-loading v-if="loading && products.length === 0" class="mx-auto my-8 block" />
    <template v-else-if="loadError">
      <wd-empty :tip="t('common.loadFailed')" />
      <view class="mt-3 flex justify-center">
        <wd-button size="small" plain @click="loadProducts(true)">
          {{ t('common.retry') }}
        </wd-button>
      </view>
    </template>
    <wd-empty v-else-if="products.length === 0" :tip="t('mall.empty')" />
    <view v-else class="mx-3 grid grid-cols-2 gap-3">
      <view
        v-for="product in products"
        :key="product.id"
        class="mall-card wot-bg-filled-oppo overflow-hidden rounded-2"
        @click="openProduct(product)"
      >
        <image v-if="product.cover_url" class="mall-card__cover" :src="product.cover_url" mode="aspectFill" />
        <view v-else class="mall-card__cover mall-card__placeholder flex items-center justify-center">
          <wd-icon name="shopping-bag" size="34px" color="var(--wot-text-color-secondary)" />
        </view>
        <view class="p-3">
          <view class="wot-text-text-main truncate text-3.5 font-medium">{{ product.name }}</view>
          <view class="mt-2 flex items-center justify-between gap-2">
            <wd-text class="wot-text-price text-4 font-bold" :text="`¥${product.price}`" />
            <wd-tag v-if="product.sold_out" type="danger" size="small" round plain>
              {{ t('mall.soldOut') }}
            </wd-tag>
            <wd-text v-else class="wot-text-text-auxiliary text-2.5" :text="t('mall.stock', { count: product.stock })" />
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
.mall-card {
  box-shadow: 0 4rpx 18rpx rgba(0, 0, 0, 0.04);

  &__cover {
    display: block;
    width: 100%;
    height: 300rpx;
  }

  &__placeholder {
    background: var(--wot-color-bg);
  }
}
</style>
