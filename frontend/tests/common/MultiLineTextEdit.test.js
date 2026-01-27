import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MultiLineTextEdit from '@/common/MultiLineTextEdit.vue'

// Stub VTextarea to mimic its v-model behavior
// In Vuetify, v-textarea uses 'modelValue' prop and emits 'update:modelValue'
const globalStubs = {
    VTextarea: {
        props: ['modelValue', 'label'],
        template: `
      <div class="v-textarea-stub">
        <textarea 
          :value="modelValue" 
          @input="$emit('update:modelValue', $event.target.value)"
        ></textarea>
        <label>{{ label }}</label>
      </div>
    `
    }
}

describe('MultiLineTextEdit.vue', () => {
    it('renders correctly with label', () => {
        const wrapper = mount(MultiLineTextEdit, {
            props: {
                label: 'My Label',
                modelValue: 'Initial text'
            },
            global: {
                stubs: globalStubs
            }
        })

        expect(wrapper.find('label').text()).toBe('My Label')
        expect(wrapper.find('textarea').element.value).toBe('Initial text')
    })

    it('emits update:modelValue when input changes', async () => {
        const wrapper = mount(MultiLineTextEdit, {
            props: {
                modelValue: ''
            },
            global: {
                stubs: globalStubs
            }
        })

        const textarea = wrapper.find('textarea')
        await textarea.setValue('New text')

        expect(wrapper.emitted('update:modelValue')).toBeTruthy()
        expect(wrapper.emitted('update:modelValue')[0]).toEqual(['New text'])
    })
})
