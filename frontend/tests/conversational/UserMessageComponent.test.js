import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import UserMessageComponent from '@/conversational/UserMessageComponent.vue'

const globalStubs = {
  VContainer: {
    template: '<div><slot /></div>'
  }
}

describe('UserMessageComponent.vue', () => {
  it('renders markdown content correctly', () => {
    const message = '*Italic* text'
    const wrapper = mount(UserMessageComponent, {
      props: {
        message
      },
      global: {
        stubs: globalStubs
      }
    })

    const bubble = wrapper.find('.user-bubble')
    expect(bubble.exists()).toBe(true)
    expect(bubble.element.innerHTML).toContain('<em>Italic</em>')
    expect(bubble.text()).toContain('Italic text')
  })

  it('handles undefined message safely', () => {
    const wrapper = mount(UserMessageComponent, {
      global: {
        stubs: globalStubs
      }
    })

    const bubble = wrapper.find('.user-bubble')
    expect(bubble.exists()).toBe(true)
    expect(bubble.text()).toBe('')
  })
})
