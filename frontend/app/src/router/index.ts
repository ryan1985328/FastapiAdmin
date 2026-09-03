/// <reference types="@uni-helper/vite-plugin-uni-pages/client" />
import { createRouter } from '@wot-ui/router'
import { pages, subPackages } from 'virtual:uni-pages'
import { useUserStore } from '@/store/userStore'
import { AUTH_ROUTE_NAMES, isAuthRoute, isProtectedRoute, normalizeInternalRedirect } from './access'

function generateRoutes() {
  const routes = pages.map((page) => {
    const newPath = `/${page.path}`
    return { ...page, path: newPath }
  })
  if (subPackages && subPackages.length > 0) {
    subPackages.forEach((subPackage) => {
      const subRoutes = subPackage.pages.map((page: (typeof pages)[number]) => {
        const newPath = `/${subPackage.root}/${page.path}`
        return { ...page, path: newPath }
      })
      routes.push(...subRoutes)
    })
  }
  return routes
}

const router = createRouter({
  routes: generateRoutes(),
})

function loginLocation(redirect?: string) {
  const safeTarget = normalizeInternalRedirect(redirect)
  if (safeTarget) {
    return {
      path: '/pages/login/index',
      navType: 'replace' as const,
      query: { redirect: safeTarget },
    }
  }
  return {
    path: '/pages/login/index',
    navType: 'replace' as const,
  }
}

// App 采用公共访问优先：只有明确标记为用户私有的页面才要求登录。
// 使用 promise guard 统一等待会话恢复，避免只在点击时保护页面。
router.beforeEach(async (to) => {
  const userStore = useUserStore()
  const authenticated = await userStore.restoreSession()
  if (isProtectedRoute(to) && !authenticated)
    return loginLocation(to.fullPath)
  // 已登录访问登录/注册页 → 回到首页
  if (AUTH_ROUTE_NAMES.has(String(to.name)) && authenticated)
    return { path: '/pages/index/index', navType: 'pushTab' as const }
  return true
})

let initialRouteChecking = false

/**
 * @wot-ui/router 的页面 onLoad 同步只更新 currentRoute，不执行 beforeEach。
 * afterEach 作为初始直达/刷新页面的兜底，配合 App 根部的恢复遮罩防止私有页面先可用。
 */
async function enforceLoadedRoute(to: typeof router.currentRoute.value) {
  if (initialRouteChecking)
    return
  if (to.name === 'not-found')
    return

  initialRouteChecking = true
  try {
    if (!to.name) {
      await router.replace({ path: '/pages/error/index', navType: 'replace' })
      return
    }

    const userStore = useUserStore()
    const authenticated = await userStore.restoreSession()
    if (isProtectedRoute(to) && !authenticated) {
      if (router.currentRoute.value.name !== 'login')
        await router.replace(loginLocation(to.fullPath))
      return
    }
    if (isAuthRoute(to) && authenticated)
      await router.replace({ path: '/pages/index/index', navType: 'pushTab' })
  }
  catch (error) {
    // @wot-ui/router rejects a redirect that has already been superseded by
    // the guard's replacement navigation. That is an expected deep-link
    // outcome, not an application error worth surfacing in the console.
    const message = typeof error === 'object' && error !== null && 'message' in error
      ? String((error as { message?: unknown }).message)
      : String(error)
    if (!/Navigation (?:cancelled|aborted)|redirectTo:fail/.test(message))
      console.error('App 路由访问校验失败', error)
  }
  finally {
    initialRouteChecking = false
  }
}

// 导航完成钩子：同步路由状态，并兜底检查初始直达页面。
router.afterEach((to, from) => {
  if (to.path && from.path && to.path !== from.path) {
    console.log(`📍 页面切换: ${from.path} → ${to.path}`)
  }
  if (!to.name || isProtectedRoute(to) || isAuthRoute(to))
    void enforceLoadedRoute(to)
})

export { isAuthRoute, isProtectedRoute }
export default router
