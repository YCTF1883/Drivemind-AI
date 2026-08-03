/**
 * 初始化加载效果的 DriveMind Logo
 * @param {string} id - 元素id
 */
function initSvgLogo(id) {
  const appEl = document.querySelector(id)
  if (!appEl) return

  const img = document.createElement('img')
  img.src = '/resource/drivemind/logo.png'
  img.alt = 'DriveMind AI'
  img.style.width = '88px'
  img.style.height = '88px'
  img.style.objectFit = 'contain'
  appEl.appendChild(img)
}

function addThemeColorCssVars() {
  const key = '__THEME_COLOR__'
  const defaultColor = '#4F46E5'
  const themeColor = window.localStorage.getItem(key) || defaultColor
  const cssVars = `--primary-color: ${themeColor}`
  document.documentElement.style.cssText = cssVars
}

addThemeColorCssVars()

initSvgLogo('#loadingLogo')
