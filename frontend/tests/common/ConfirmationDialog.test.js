import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ConfirmationDialog from '@/common/ConfirmationDialog.vue'

// Basic stubbing for Vuetify components to avoid dragging in the whole library for unit tests
const globalStubs = {
    VDialog: {
        template: '<div><slot /></div>',
        props: ['modelValue']
    },
    VCard: { template: '<div><slot /></div>' },
    VCardTitle: { template: '<div><slot /></div>' },
    VCardActions: { template: '<div><slot /></div>' },
    VSpacer: { template: '<div />' },
    VBtn: {
        template: '<button @click="$emit(\'click\')"><slot /></button>',
        props: ['color', 'variant']
    }
}

describe('ConfirmationDialog.vue', () => {
    it('renders slot content', () => {
        const wrapper = mount(ConfirmationDialog, {
            props: {
                active: true,
            },
            slots: {
                default: 'Confirm this action?',
            },
            global: {
                stubs: globalStubs
            }
        })

        expect(wrapper.text()).toContain('Confirm this action?')
    })

    it('emits "canceled" and "done" when Cancel is clicked', async () => {
        const wrapper = mount(ConfirmationDialog, {
            props: {
                active: true,
            },
            global: {
                stubs: globalStubs
            }
        })

        const buttons = wrapper.findAll('button')
        const cancelButton = buttons.find(b => b.text() === 'Cancel')

        await cancelButton.trigger('click')

        expect(wrapper.emitted('canceled')).toBeTruthy()
        expect(wrapper.emitted('done')).toBeTruthy()
        // It should also update the model value to false
        expect(wrapper.emitted('update:active')[0]).toEqual([false])
    })

    it('emits "confirmed" and "done" when OK is clicked', async () => {
        const wrapper = mount(ConfirmationDialog, {
            props: {
                active: true,
            },
            global: {
                stubs: globalStubs
            }
        })

        const buttons = wrapper.findAll('button')
        const okButton = buttons.find(b => b.text() === 'OK')

        await okButton.trigger('click')

        expect(wrapper.emitted('confirmed')).toBeTruthy()
        expect(wrapper.emitted('done')).toBeTruthy()
        expect(wrapper.emitted('update:active')[0]).toEqual([false])
    })
})
