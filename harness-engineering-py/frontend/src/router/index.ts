import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/skills',
      name: 'Skills',
      component: () => import('@/views/SkillsView.vue'),
    },
    {
      path: '/agents',
      name: 'Agents',
      component: () => import('@/views/AgentsView.vue'),
    },
    {
      path: '/stock',
      name: 'Stock',
      component: () => import('@/views/StockView.vue'),
    },
  ],
})

export default router
