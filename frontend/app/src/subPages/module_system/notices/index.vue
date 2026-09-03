<script setup lang="ts">
import type { AppNoticeDetail, AppNoticeListItem } from '@/api/module_app/notice'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppNoticeAPI from '@/api/module_app/notice'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'notices', style: { navigationBarTitleText: '通知公告', enablePullDownRefresh: true } })
useI18nNavTitle('notices.title')

const { t } = useI18n()
const list = ref<AppNoticeListItem[]>([])
const loading = ref(false)
const loadError = ref(false)
const loadingMore = ref(false)
const pageNo = ref(1)
const total = ref(0)
const hasNext = ref(false)
const selectedNotice = ref<AppNoticeDetail | null>(null)
const showDetail = ref(false)
const detailLoading = ref(false)

function noticeTypeLabel(type?: string) {
  return type === '2' ? t('notices.announce') : t('notices.notice')
}

async function loadData(reset = true) {
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
    const result = await AppNoticeAPI.list({ page_no: targetPage, page_size: 10 })
    const items = Array.isArray(result?.items) ? result.items : []
    if (reset)
      list.value = items
    else
      list.value.push(...items)
    pageNo.value = targetPage
    total.value = result?.total ?? list.value.length
    hasNext.value = Boolean(result?.has_next)
  }
  catch {
    if (reset) {
      list.value = []
      total.value = 0
      hasNext.value = false
      loadError.value = true
    }
    uni.showToast({ title: t('common.loadFailed'), icon: 'none' })
  }
  finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function openDetail(item: AppNoticeListItem) {
  selectedNotice.value = null
  showDetail.value = true
  detailLoading.value = true
  try {
    selectedNotice.value = await AppNoticeAPI.detail(item.id)
  }
  catch {
    showDetail.value = false
    uni.showToast({ title: t('notices.detailFailed'), icon: 'none' })
  }
  finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  showDetail.value = false
  selectedNotice.value = null
}

onLoad(() => loadData(true))
onPullDownRefresh(async () => {
  try {
    await loadData(true)
  }
  finally {
    uni.stopPullDownRefresh()
  }
})
onReachBottom(() => loadData(false))
</script>

<template>
  <view class="page-wraper">
    <view class="mx-3 mb-2 mt-3 flex items-center justify-between px-1">
      <wd-text class="wot-text-text-secondary text-3" :text="t('notices.count', { count: total })" />
    </view>

    <wd-loading v-if="loading && list.length === 0" class="mx-auto my-5 block" />
    <template v-else-if="loadError">
      <wd-empty :tip="t('common.loadFailed')" />
      <view class="mt-3 flex justify-center">
        <wd-button size="small" plain @click="loadData(true)">
          {{ t('common.retry') }}
        </wd-button>
      </view>
    </template>
    <wd-empty v-else-if="list.length === 0" :tip="t('notices.empty')" />
    <view v-else class="mx-3">
      <wd-cell-group border custom-class="rounded-2! overflow-hidden">
        <wd-cell
          v-for="item in list"
          :key="item.id"
          center
          is-link
          @click="openDetail(item)"
        >
          <template #title>
            <view class="min-w-0 flex-1">
              <view class="flex items-center justify-between gap-2">
                <wd-text class="wot-text-text-main truncate text-3.5 font-medium" :text="item.notice_title || ''" />
                <wd-tag size="small" round plain type="primary">
                  {{ noticeTypeLabel(item.notice_type) }}
                </wd-tag>
              </view>
              <view class="mt-1 flex items-center justify-between gap-2">
                <wd-text class="wot-text-text-auxiliary truncate text-2.5" :text="item.description || ''" />
                <wd-text class="wot-text-text-auxiliary shrink-0 text-2.5" :text="(item.created_time || '').slice(0, 10)" />
              </view>
            </view>
          </template>
        </wd-cell>
      </wd-cell-group>
      <view v-if="loadingMore" class="py-4 text-center">
        <wd-loading />
      </view>
      <wd-text
        v-else-if="!hasNext"
        class="wot-text-text-auxiliary block py-4 text-center text-2.5"
        :text="t('notices.noMore')"
      />
      <wd-gap height="100rpx" safe-area-bottom />
    </view>

    <wd-popup v-model="showDetail" position="bottom" round custom-style="height: 70vh;" @close="closeDetail">
      <view class="notice-detail">
        <wd-navbar :title="selectedNotice?.notice_title || ''" left-arrow @click-left="closeDetail" />
        <wd-loading v-if="detailLoading" class="mx-auto my-8 block" />
        <template v-else-if="selectedNotice">
          <view class="px-4 pb-2 pt-3">
            <view class="flex items-center gap-2">
              <wd-tag size="small" round plain type="primary">
                {{ noticeTypeLabel(selectedNotice.notice_type) }}
              </wd-tag>
              <wd-text class="wot-text-text-auxiliary text-2.5" :text="selectedNotice.created_time || ''" />
            </view>
          </view>
          <scroll-view scroll-y class="notice-detail__body">
            <mp-html
              v-if="selectedNotice.notice_content"
              :content="selectedNotice.notice_content"
              :selectable="true"
              container-style="padding: 32rpx;"
            />
            <wd-text v-else class="wot-text-text-secondary block p-8 text-3 leading-relaxed" :text="t('notices.noContent')" />
          </scroll-view>
        </template>
      </view>
    </wd-popup>
  </view>
</template>

<style lang="scss" scoped>
.notice-detail {
  height: 70vh;
  display: flex;
  flex-direction: column;

  &__body {
    flex: 1;
    min-height: 0;
  }
}
</style>
