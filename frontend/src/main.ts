import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'

// 自托管字体：内网可用，不依赖任何外部 CDN
import '@fontsource/noto-sans-sc/400.css'
import '@fontsource/noto-sans-sc/500.css'
import '@fontsource/noto-sans-sc/700.css'
import '@fontsource/noto-serif-sc/400.css'
import '@fontsource/noto-serif-sc/600.css'
import '@fontsource-variable/jetbrains-mono/wght.css'

import './styles/tokens.css'
import './styles/base.css'
import './styles/element.css'

import App from './App.vue'
import router from './router'

createApp(App).use(router).use(ElementPlus, { locale: zhCn }).mount('#app')
