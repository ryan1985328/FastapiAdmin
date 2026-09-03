function safeRedirect(value?: string): string {
  if (!value)
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

// 跳转到登录页
export function toLoginPage(
  options: { mode?: 'navigateTo' | 'reLaunch', redirect?: string } = {},
) {
  const { mode = 'navigateTo' } = options
  const redirect = safeRedirect(options.redirect)
  const url = `/pages/login/index${redirect ? `?redirect=${encodeURIComponent(redirect)}` : ''}`

  if (mode === 'reLaunch') {
    uni.reLaunch({
      url,
    })
  }
  else {
    uni.navigateTo({
      url,
    })
  }
}
