export interface AppRouteLike {
  name?: unknown
  path?: string
  fullPath?: string
}

export const PROTECTED_ROUTE_NAMES = new Set([
  'profile',
  'kyc',
  'account',
  'setting',
  'addresses',
  'address-form',
  'bank-accounts',
  'bank-account-form',
  'orders',
  'order-detail',
])

export const AUTH_ROUTE_NAMES = new Set(['login', 'register', 'forget'])

export function isProtectedRoute(route: AppRouteLike): boolean {
  return PROTECTED_ROUTE_NAMES.has(String(route.name))
}

export function isAuthRoute(route: AppRouteLike): boolean {
  return AUTH_ROUTE_NAMES.has(String(route.name))
}

/** Keep login return targets internal and prevent auth/fallback redirect loops. */
export function normalizeInternalRedirect(value: unknown): string {
  if (value == null)
    return ''

  let decoded = String(value).trim()
  for (let i = 0; i < 2; i++) {
    try {
      const next = decodeURIComponent(decoded)
      if (next === decoded)
        break
      decoded = next
    }
    catch {
      return ''
    }
  }

  if (!decoded.startsWith('/') || decoded.startsWith('//'))
    return ''
  if (['/pages/login/index', '/pages/login/register/index', '/pages/login/forget/index', '/pages/error/index'].some(path => decoded.startsWith(path)))
    return ''
  return decoded
}
