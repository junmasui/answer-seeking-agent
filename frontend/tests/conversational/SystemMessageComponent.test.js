import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SystemMessageComponent from '@/conversational/SystemMessageComponent.vue'

// Define a stub for v-container since it's a Vuetify component
const globalStubs = {
  VContainer: {
    template: '<div><slot /></div>'
  }
}

describe('SystemMessageComponent.vue', () => {
  it('renders markdown content correctly', () => {
    const message = '**Hello** world'
    const wrapper = mount(SystemMessageComponent, {
      props: {
        message
      },
      global: {
        stubs: globalStubs
      }
    })

    const bubble = wrapper.find('.system-bubble')
    expect(bubble.exists()).toBe(true)
    // marked should convert **Hello** to <strong>Hello</strong> or <b>Hello</b> depending on version/config,
    // but usually it's strong.
    expect(bubble.element.innerHTML).toContain('<strong>Hello</strong>')
    expect(bubble.text()).toContain('Hello world')
  })

  it('handles empty message safely', () => {
    const wrapper = mount(SystemMessageComponent, {
      props: {
        message: null
      },
      global: {
        stubs: globalStubs
      }
    })

    const bubble = wrapper.find('.system-bubble')
    expect(bubble.exists()).toBe(true)
    expect(bubble.text()).toBe('')
  })
})
