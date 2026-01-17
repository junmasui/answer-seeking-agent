import { createWebHistory, createRouter } from 'vue-router'
import { authService } from './common/AuthService'

import LoginView from './core/LoginView.vue'
import HomeView from './core/HomeView.vue'
// Reinsert when we have meaningful info: import AboutView from './core/AboutView.vue'
import AgentDiagramView from './conversational/AgentDiagramView.vue'
import ConversationalView from './conversational/ConversationalView.vue'
import DocManagerView from './doc-mgr/DocManagerView.vue'
import DocManagerDocSetTab from './doc-mgr/DocManagerDocSetTab.vue'
import DocManagerIngestTab from './doc-mgr/DocManagerIngestTab.vue'
import DocManagerUploadTab from './doc-mgr/DocManagerUploadTab.vue'
import PromptManagerView from './prompt-mgr/PromptManagerView.vue'
import PromptManagerPromptsTab from './prompt-mgr/PromptManagerPromptsTab.vue'
import PromptManagerPromptVersionsTab from './prompt-mgr/PromptManagerPromptVersionsTab.vue'
import StatusCheckView from './core/StatusCheckView.vue'
import AdminCheckView from './core/AdminView.vue'

const routes = [
    { path: '/', component: HomeView },
    // Reinsert when we have meaningful info: { path: '/about', component: AboutView },
    { path: '/conversational', component: ConversationalView },
    {
        path: '/doc-mgr',
        component: DocManagerView,
        meta: { requiresAuth: true },
        children: [
            { name: 'doc-sets', path: '', component: DocManagerDocSetTab, alias: 'doc-sets' },
            { name: 'upload-files', path: 'upload-files', component: DocManagerUploadTab },
            { name: 'docs', path: 'docs', component: DocManagerIngestTab }
        ]
    },
    {
        path: '/prompt-mgr',
        component: PromptManagerView,
        meta: { requiresAuth: true },
        children: [
            { name: 'prompts', path: '', component: PromptManagerPromptsTab, alias: 'prompts' },
            { name: 'prompt-versions', path: 'prompt-versions', component: PromptManagerPromptVersionsTab }
        ]
    },
    { path: '/login', component: LoginView },
    { path: '/status', component: StatusCheckView },
    { path: '/diagram', component: AgentDiagramView },
    { path: '/admin', component: AdminCheckView, meta: { requiresAuth: true } }
]

// See createWebHistory at: https://router.vuejs.org/guide/essentials/history-mode#HTML5-Mode
const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(async (to, from, next) => {
    if (to.meta.requiresAuth) {
        const user = await authService.getUser()
        if (!user || user.expired) {
            // Redirect to explicit login page with return path
            next({ path: '/login', query: { redirect: to.fullPath } })
            return
        }
    }
    next()
})

export default router
