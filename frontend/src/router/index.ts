import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'workbench',
      component: () => import('@/views/WorkbenchView.vue'),
      meta: { title: '工作台' },
    },
    {
      path: '/archive',
      name: 'archive',
      component: () => import('@/views/ArchiveView.vue'),
      meta: { title: '档案' },
    },
    {
      path: '/reports/:id',
      name: 'report',
      component: () => import('@/views/ReportView.vue'),
      meta: { title: '报告' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: '设置' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => {
  const title = (to.meta.title as string | undefined) ?? ''
  document.title = title ? `${title} · AI 测试报告助手` : 'AI 测试报告助手'
})

export default router
