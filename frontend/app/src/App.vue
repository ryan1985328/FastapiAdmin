<script setup lang="ts">
import router from '@/router'
import { useUserStore } from '@/store/userStore'

const userStore = useUserStore()
let fallbackRedirecting = false

// 立即开始启动会话恢复；App 页面渲染前由 App.ku 的遮罩等待结果。
void userStore.restoreSession()

// H5 对未知 hash 不会进入 uni 页面生命周期，补一个最小 404 兜底。
// 已知路由仍交给 uni / @wot-ui/router 处理，不改变正常导航。
// #ifdef H5
function checkH5Route() {
  const rawPath = window.location.hash.replace(/^#/, '').split('?')[0]
  const path = rawPath || '/pages/index/index'
  if (path === '/' || path === '/pages/error/index' || router.routes.some(route => route.path === path || route.aliasPath === path))
    return
  if (fallbackRedirecting)
    return

  fallbackRedirecting = true
  uni.reLaunch({
    url: '/pages/error/index',
    complete: () => {
      fallbackRedirecting = false
    },
  })
}
// #endif

onLaunch(() => {
  void userStore.restoreSession()
  // #ifdef H5
  window.addEventListener('hashchange', checkH5Route)
  setTimeout(checkH5Route, 0)
  // #endif
})
</script>

<style lang="scss">
/* 全局样式按职责拆分：
   - theme.scss：玻璃水滴渐变主题变量（6 套主题色）
   - base.scss：页面容器 / 暗色背景等基础全局样式
   页面级样式（登录表单输入框、滑块等）保留在各页面 scoped 内 */
@import './styles/theme.scss';
@import './styles/base.scss';
</style>
