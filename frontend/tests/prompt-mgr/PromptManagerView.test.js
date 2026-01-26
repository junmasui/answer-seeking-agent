import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PromptManagerView from '@/prompt-mgr/PromptManagerView.vue'

// Mock vue-router
const pushMock = vi.fn()
vi.mock('vue-router', () => ({
    useRouter: () => ({
        push: pushMock
    })
}))

// Stubs for Vuetify and RouterView
const globalStubs = {
    VTabs: { template: '<div><slot /></div>', props: ['modelValue', 'bgColor'] },
    VTab: { template: '<button @click="$emit(\'click\')"><slot /></button>', props: ['value', 'to'] },
    RouterView: { template: '<div class="router-view-stub"></div>' }
}

describe('PromptManagerView.vue', () => {
    it('renders title and tabs', () => {
        const wrapper = mount(PromptManagerView, {
            global: { stubs: globalStubs }
        })

        expect(wrapper.find('h2').text()).toBe('Prompt Manager')
        expect(wrapper.findAll('button').length).toBe(2)
    })

    it('renders router-view', () => {
        const wrapper = mount(PromptManagerView, {
            global: { stubs: globalStubs }
        })

        expect(wrapper.find('.router-view-stub').exists()).toBe(true)
    })
})
