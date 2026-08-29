<script setup lang="ts">
import type { NoticeItem } from '@/api/module_system/notice'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NoticeAPI } from '@/api/module_system/notice'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({ name: 'notices', style: { navigationBarTitleText: '通知公告', enablePullDownRefresh: true } })
useI18nNavTitle('notices.title')

const { t } = useI18n()
const searchTitle = ref('')
const list = ref<NoticeItem[]>([])
const loading = ref(false)
const selectedNotice = ref<NoticeItem | null>(null)
const showDetail = ref(false)

const filteredList = computed(() => {
  const keyword = searchTitle.value.trim().toLowerCase()
  if (!keyword)
    return list.value
  return list.value.filter(item => `${item.notice_title || ''} ${item.description || ''}`.toLowerCase().includes(keyword))
})

async function loadData() {
  loading.value = true
  try {
    const result = await NoticeAPI.getAvailable()
    list.value = Array.isArray(result) ? result : []
  }
  catch {
    list.value = []
    uni.showToast({ title: t('common.loadFailed'), icon: 'none' })
  }
  finally {
    loading.value = false
  }
}

function openDetail(item: NoticeItem) {
  selectedNotice.value = item
  showDetail.value = true
}

function closeDetail() {
  showDetail.value = false
  selectedNotice.value = null
}

onLoad(loadData)
onPullDownRefresh(async () => {
  try {
    await loadData()
  }
  finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page-wraper">
    <wd-search
      v-model="searchTitle"
      :placeholder="t('notices.searchPlaceholder')"
      hide-cancel
    />

    <view class="mx-3 mb-2 mt-3 flex items-center justify-between px-1">
      <wd-text class="wot-text-text-secondary text-3" :text="t('notices.count', { count: filteredList.length })" />
    </view>

    <wd-loading v-if="loading && list.length === 0" class="mx-auto my-5 block" />
    <wd-empty
      v-else-if="filteredList.length === 0"
      :tip="searchTitle ? t('notices.emptyWithFilter') : t('notices.empty')"
    />
    <view v-else class="mx-3">
      <wd-cell-group border custom-class="rounded-2! overflow-hidden">
        <wd-cell
          v-for="item in filteredList"
          :key="item.id"
          center
          is-link
          @click="openDetail(item)"
        >
          <template #title>
            <view class="min-w-0 flex-1">
              <view class="flex items-center justify-between gap-2">
                <wd-text class="wot-text-text-main truncate text-3.5 font-medium" :text="item.notice_title || ''" />
                <wd-text class="wot-text-text-auxiliary shrink-0 text-2.5" :text="(item.created_time || '').slice(0, 10)" />
              </view>
              <wd-text class="wot-text-text-auxiliary mt-1 block truncate text-2.5" :text="item.description || ''" />
            </view>
          </template>
        </wd-cell>
      </wd-cell-group>
      <wd-gap height="100rpx" safe-area-bottom />
    </view>

    <wd-popup v-model="showDetail" position="bottom" round custom-style="height: 70vh;" @close="closeDetail">
      <view class="notice-detail">
        <wd-navbar :title="selectedNotice?.notice_title || ''" left-arrow @click-left="closeDetail" />
        <scroll-view scroll-y class="notice-detail__body">
          <mp-html
            v-if="selectedNotice?.notice_content"
            :content="selectedNotice.notice_content"
            :selectable="true"
            :container-style="'padding: 32rpx;'"
          />
          <wd-text v-else class="wot-text-text-secondary block p-8 text-3 leading-relaxed" :text="t('notices.noContent')" />
        </scroll-view>
      </view>
    </wd-popup>
  </view>
</template>

<style lang="scss" scoped>
.notice-detail {
  height: 70vh;

  &__body {
    height: calc(70vh - 88rpx);
  }
}
</style>
