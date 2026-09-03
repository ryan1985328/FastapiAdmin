<script setup lang="ts">
import type { AppNoticeListItem } from '@/api/module_app/notice'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { AppNoticeAPI } from '@/api/module_app/notice'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useShare } from '@/composables/useShare'
import { useTabbarActive } from '@/composables/useTabbarActive'
import { useUserStore } from '@/store/userStore'

const { t, locale } = useI18n()
const userStore = useUserStore()
const router = useRouter()

definePage({
  name: 'home',
  layout: 'tabbar',
  style: { navigationBarTitleText: '首页' },
})
useI18nNavTitle('index.navTitle')

const displayName = computed(() => (userStore.isLoggedIn() ? userStore.userInfo?.nickname : '') || t('index.guestName'))
const loading = ref(false)
const noticeLoadError = ref(false)
const recentNotices = ref<AppNoticeListItem[]>([])
const scrollTop = ref(0)
const latestNotice = computed(() => recentNotices.value[0])

useShare(() => ({
  title: t('index.shareTitle', { name: displayName.value }),
  path: '/pages/index/index',
}))

const NAV_LIST = [
  {
    icon: 'notification',
    titleKey: 'common.nav.notices',
    descriptionKey: 'index.noticeEntryDescription',
    name: 'notices',
    color: 'var(--wot-green-6)',
    soft: 'wot-bg-green-1',
  },
  {
    icon: 'info',
    titleKey: 'common.aboutUs',
    descriptionKey: 'index.aboutEntryDescription',
    name: 'about',
    color: 'var(--wot-purple-6)',
    soft: 'wot-bg-purple-1',
  },
]

function navigateTo(name: string) {
  router.push({ name })
}

async function loadNotices() {
  loading.value = true
  noticeLoadError.value = false
  try {
    const result = await AppNoticeAPI.list({ page_no: 1, page_size: 3 })
    recentNotices.value = Array.isArray(result?.items) ? result.items.slice(0, 3) : []
  }
  catch {
    recentNotices.value = []
    noticeLoadError.value = true
  }
  finally {
    loading.value = false
  }
}

onShow(loadNotices)
onPullDownRefresh(async () => {
  try {
    await loadNotices()
  }
  finally {
    uni.stopPullDownRefresh()
  }
})

useTabbarActive('pages/index/index', 'home')

onPageScroll((event) => {
  scrollTop.value = event.scrollTop
})

const WEEK_ZH = ['日', '一', '二', '三', '四', '五', '六']
const WEEK_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function getDateString() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const day = now.getDate()
  return locale.value.startsWith('zh')
    ? `${year}年${month}月${day}日 星期${WEEK_ZH[now.getDay()]}`
    : `${WEEK_EN[now.getDay()]}, ${month}/${day}/${year}`
}
</script>

<template>
  <view class="tabbar-wraper py-3">
    <view class="home-header wot-bg-filled-oppo mx-3 mb-3 rounded-3 px-5 py-5">
      <view class="wot-text-text-secondary text-3">
        {{ t('index.navTitle') }}
      </view>
      <view class="wot-text-text-main mt-2 text-6 font-bold">
        {{ t('index.welcomeTitle', { name: displayName }) }}
      </view>
      <view class="wot-text-text-secondary mt-2 text-3">
        {{ getDateString() }}
      </view>
    </view>

    <wd-notice-bar
      v-if="latestNotice"
      :text="latestNotice.notice_title"
      type="info"
      prefix="notification"
      custom-class="home-notice"
      class="mx-3 mb-3"
      @click="navigateTo('notices')"
    />

    <view class="mx-3 mb-3">
      <wd-cell-group border custom-class="rounded-2! overflow-hidden">
        <wd-cell
          v-for="item in NAV_LIST"
          :key="item.name"
          center
          is-link
          :title="t(item.titleKey)"
          :label="t(item.descriptionKey)"
          @click="navigateTo(item.name)"
        >
          <template #icon>
            <view class="mr-3 h-9 w-9 flex shrink-0 items-center justify-center rounded-xl" :class="item.soft">
              <wd-icon :name="item.icon" size="18px" :color="item.color" />
            </view>
          </template>
        </wd-cell>
      </wd-cell-group>
    </view>

    <view class="mb-2 mt-4 flex items-center justify-between px-3">
      <view class="flex items-center gap-2">
        <view class="wot-bg-success-main h-3.5 w-1 rounded-full" />
        <wd-text class="wot-text-text-main text-3.5" :text="t('index.latestNotice')" bold />
      </view>
      <wd-text class="text-3" :text="t('common.all')" type="primary" @click="navigateTo('notices')" />
    </view>

    <wd-loading v-if="loading && recentNotices.length === 0" class="mx-auto my-5 block" />
    <template v-else-if="noticeLoadError">
      <wd-empty :tip="t('common.loadFailed')" />
      <view class="mt-3 flex justify-center">
        <wd-button size="small" plain @click="loadNotices">
          {{ t('common.retry') }}
        </wd-button>
      </view>
    </template>
    <wd-empty v-else-if="recentNotices.length === 0" :tip="t('notices.empty')" />
    <view v-else class="mx-3">
      <wd-cell-group border custom-class="rounded-2! overflow-hidden">
        <wd-cell
          v-for="item in recentNotices"
          :key="item.id"
          :title="item.notice_title"
          is-link
          @click="navigateTo('notices')"
        >
          <template #label>
            <wd-text class="wot-text-text-auxiliary text-2.5" :text="item.created_time || ''" />
          </template>
        </wd-cell>
      </wd-cell-group>
    </view>

    <wd-backtop :scroll-top="scrollTop" :top="80" />
  </view>
</template>

<style lang="scss" scoped>
.home-header {
  border: 2rpx solid var(--wot-border-main);
}
</style>
