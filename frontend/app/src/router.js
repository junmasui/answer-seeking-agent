import { createWebHistory, createRouter } from 'vue-router'

import HomeView from './core/HomeView.vue'
import AboutView from './core/AboutView.vue'
import ConversationalView from './conversational/ConversationalView.vue'
import DocManagerView from './doc-mgr/DocManagerView.vue'
import DocManagerIngestTab from './doc-mgr/DocManagerIngestTab.vue'
import DocManagerUploadTab from './doc-mgr/DocManagerUploadTab.vue'
import HealthCheckView from './core/HealthCheckView.vue'
import AdminCheckView from './core/AdminView.vue'

const routes = [
  { path: '/', component: HomeView },
  // Reinsert when we have meaningful info: { path: '/about', component: AboutView },
  { path: '/conversational', component: ConversationalView },
  { path: '/doc-mgr', component: DocManagerView,
    children: [
      { name: 'upload', path: '', component: DocManagerUploadTab, alias: 'upload' },
      { name: 'ingest', path: 'ingest', component: DocManagerIngestTab },
    ]
   },
  { path: '/health', component: HealthCheckView },
  { path: '/admin', component: AdminCheckView },
]

// See createWebHistory at: https://router.vuejs.org/guide/essentials/history-mode#HTML5-Mode
const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
