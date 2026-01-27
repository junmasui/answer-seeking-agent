import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MermaidDiagram from '@/common/MermaidDiagram.vue'
import mermaid from 'mermaid'

// Mock mermaid module
vi.mock('mermaid', () => ({
    default: {
        initialize: vi.fn(),
        render: vi.fn()
    }
}))

describe('MermaidDiagram.vue', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Reset render mock
        mermaid.render.mockResolvedValue({ svg: '<svg>Mocked Diagram</svg>' })
    })

    it('renders placeholder when no definition is provided', () => {
        const wrapper = mount(MermaidDiagram, {
            props: {
                definition: ''
            }
        })

        expect(wrapper.find('.mermaid-placeholder').exists()).toBe(true)
        expect(wrapper.text()).toContain('No diagram available')
    })

    it('initializes mermaid and renders diagram when definition is provided', async () => {
        // We need to wait for the async watcher to fire and complete
        const definition = 'graph TD; A-->B;'
        const wrapper = mount(MermaidDiagram, {
            props: {
                definition
            }
        })

        // Wait for promises to resolve (watch callback is async)
        await new Promise(resolve => setTimeout(resolve, 10))
        await wrapper.vm.$nextTick()

        // Check initialization
        expect(mermaid.initialize).toHaveBeenCalled()
        expect(mermaid.initialize).toHaveBeenCalledWith(expect.objectContaining({
            startOnLoad: false,
            theme: 'neutral'
        }))

        // Check rendering
        expect(mermaid.render).toHaveBeenCalled()
        expect(mermaid.render).toHaveBeenCalledWith(
            expect.stringMatching(/^mermaid-diagram-/),
            definition
        )

        // Check output
        expect(wrapper.find('.mermaid-diagram').exists()).toBe(true)
        expect(wrapper.vm.svg).toBe('<svg>Mocked Diagram</svg>')
    })

    it('handles render errors gracefully', async () => {
        // Mock console.error to prevent test output noise
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { })
        mermaid.render.mockRejectedValue(new Error('Syntax error'))

        const wrapper = mount(MermaidDiagram, {
            props: {
                definition: 'invalid graph'
            }
        })

        // Wait for async operations
        await new Promise(resolve => setTimeout(resolve, 10))
        await wrapper.vm.$nextTick()

        expect(wrapper.find('.mermaid-error').exists()).toBe(true)
        expect(wrapper.text()).toContain('Syntax error')
        expect(wrapper.find('.mermaid-diagram').exists()).toBe(false)

        // Restore console.error
        consoleSpy.mockRestore()
    })

    it('updates diagram when props change', async () => {
        const wrapper = mount(MermaidDiagram, {
            props: {
                definition: 'graph A'
            }
        })

        await new Promise(resolve => setTimeout(resolve, 10))
        expect(mermaid.render).toHaveBeenCalledTimes(1)

        // Change definition
        await wrapper.setProps({ definition: 'graph B' })
        await new Promise(resolve => setTimeout(resolve, 10))

        expect(mermaid.render).toHaveBeenCalledTimes(2)
        expect(mermaid.render.mock.calls[1][1]).toBe('graph B')
    })
})
