<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'

definePage({
  name: 'not-found',
  layout: 'default',
  style: { navigationBarTitleText: '页面不存在' },
})
useI18nNavTitle('notFound.navTitle')

const { t } = useI18n()
const router = useRouter()

function goHome() {
  router.pushTab({ name: 'home' })
}
</script>

<template>
  <view class="page-wraper not-found-page">
    <wd-icon name="warning" size="56px" color="var(--wot-primary-6)" />
    <wd-text class="wot-text-text-main mt-4 text-5 font-medium" :text="t('notFound.title')" />
    <wd-text class="wot-text-text-secondary mt-2 text-3" :text="t('notFound.description')" />
    <wd-button class="mt-6" type="primary" round @click="goHome">
      {{ t('notFound.home') }}
    </wd-button>
  </view>
</template>

<style lang="scss" scoped>
.not-found-page {
  display: flex;
  min-height: calc(100vh - var(--window-top));
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
  box-sizing: border-box;
  text-align: center;
}
</style>
