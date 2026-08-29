<script setup lang="ts">
import type { AppUserInfo } from '@/api/module_app/user'
import { onLoad } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppUserAPI from '@/api/module_app/user'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useUserStore } from '@/store/userStore'

definePage({
  name: 'profile',
  layout: 'default',
  style: { navigationBarTitleText: '个人资料' },
})
useI18nNavTitle('profile.navTitle')

const { t } = useI18n()
const userStore = useUserStore()
const loading = ref(false)
const userProfile = ref<AppUserInfo>()

const statusText = computed(() => userProfile.value?.status === 0 ? t('common.status.enabled') : t('common.status.disabled'))

async function loadUserProfile() {
  loading.value = true
  try {
    userProfile.value = await AppUserAPI.getProfile()
    userStore.setUserInfo(userProfile.value)
  }
  catch {
    // http 层已统一错误提示
  }
  finally {
    loading.value = false
  }
}

onLoad(loadUserProfile)
</script>

<template>
  <view class="page-wraper py-3">
    <SkeletonPage v-if="loading && !userProfile" :rows="5" />

    <template v-else>
      <view class="mx-3 mb-3 flex flex-col items-center gap-2 py-4">
        <wd-avatar
          size="80px"
          round
          :src="userProfile?.avatar || ''"
          :text="(userProfile?.nickname || userProfile?.username || '?').charAt(0)"
        />
        <wd-text class="wot-text-text-main text-4" :text="userProfile?.nickname || userProfile?.username || '-'" bold />
      </view>

      <view class="mx-3 mb-3">
        <wd-cell-group border custom-class="rounded-2! overflow-hidden">
          <wd-cell :title="t('profile.nickname')" :value="userProfile?.nickname || t('profile.notSet')" />
          <wd-cell :title="t('profile.username')" :value="userProfile?.username || '-'" />
          <wd-cell :title="t('profile.mobile')" :value="userProfile?.mobile || t('profile.notBound')" />
          <wd-cell :title="t('common.field.status')" :value="statusText" />
        </wd-cell-group>
      </view>
    </template>
  </view>
</template>
