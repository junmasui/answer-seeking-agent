import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EditDocDialog from '@/doc-mgr/EditDocDialog.vue'

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
  }
}

describe('EditDocDialog.vue', () => {
  const defaultModelValue = {
    name: 'Test Doc',
    documentSetName: 'Set A',
    ocrStrategy: 'fast'
  }

  it('renders correctly with model data', () => {
    const wrapper = mount(EditDocDialog, {
      props: {
        active: true,
        modelValue: defaultModelValue
      },
      global: { stubs: globalStubs }
    })

    const inputs = wrapper.findAll('input')
    expect(inputs[0].element.value).toBe('Test Doc')
    expect(inputs[1].element.value).toBe('Set A')
  })

  it('emits confirmed event when OK is clicked', async () => {
    const wrapper = mount(EditDocDialog, {
      props: {
        active: true,
        modelValue: defaultModelValue
      },
      global: { stubs: globalStubs }
    })

    const okBtn = wrapper.findAll('button').find((b) => b.text() === 'OK')
    await okBtn.trigger('click')

    expect(wrapper.emitted('confirmed')).toBeTruthy()
    expect(wrapper.emitted('update:active')[0]).toEqual([false])
  })

  it('emits canceled event when Cancel is clicked', async () => {
    const wrapper = mount(EditDocDialog, {
      props: {
        active: true,
        modelValue: defaultModelValue
      },
      global: { stubs: globalStubs }
    })

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === 'Cancel')
    await cancelBtn.trigger('click')

    expect(wrapper.emitted('canceled')).toBeTruthy()
    expect(wrapper.emitted('update:active')[0]).toEqual([false])
  })
})
