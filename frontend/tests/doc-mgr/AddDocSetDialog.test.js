import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AddDocSetDialog from '@/doc-mgr/AddDocSetDialog.vue'

const globalStubs = {
  VDialog: { template: '<div><slot /></div>', props: ['modelValue'] },
  VCard: { template: '<div><slot /></div>' },
  VCardTitle: { template: '<div><slot /></div>' },
  VCardText: { template: '<div><slot /></div>' },
  VCardActions: { template: '<div><slot /></div>' },
  VSpacer: { template: '<div />' },
  VBtn: { template: '<button @click="$emit(\'click\')"><slot /></button>' },
  VTextField: {
    template:
      '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'label']
  },
  VSelect: {
    template:
      '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"></select>',
    props: ['modelValue', 'items', 'label']
  },
  VCheckbox: {
    template:
      '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
    props: ['modelValue', 'label']
  }
}

describe('AddDocSetDialog.vue', () => {
  it('renders correctly with default values', () => {
    const wrapper = mount(AddDocSetDialog, {
      props: {
        active: true
      },
      global: { stubs: globalStubs }
    })

    expect(wrapper.text()).toContain('New Document Set')

    // Check default values if inputs are connected
    // checkbox for isPublicViewable defaults to true
    // checkbox for isNewDocDefault defaults to false
  })

  it('emits confirmed event with data', async () => {
    const wrapper = mount(AddDocSetDialog, {
      props: {
        active: true
      },
      global: { stubs: globalStubs }
    })

    // Simulate user input
    const inputs = wrapper.findAll('input')
    // Assumes order: text-field (name), checkbox (public), checkbox (default)
    await inputs[0].setValue('New Set')

    const okBtn = wrapper.findAll('button').find((b) => b.text() === 'OK')
    await okBtn.trigger('click')

    expect(wrapper.emitted('confirmed')).toBeTruthy()
    expect(wrapper.emitted('update:active')[0]).toEqual([false])

    // Check model update
    expect(wrapper.props('modelValue').name).toBe('New Set')
  })
})
