import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/home.vue';
import Perf from '@/views/perf.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/home' },
    { path: '/home', name: 'home', component: Home },
    { path: '/perf', name: 'perf', component: Perf },
  ],
});

export default router;
