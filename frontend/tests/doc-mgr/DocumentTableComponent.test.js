import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import DocumentTableComponent from '@/doc-mgr/DocumentTableComponent.vue'
import { useDocumentStore } from '@/doc-mgr/DocStore'

// Mock CommonDataTable and other components to avoid rendering full children
const globalStubs = {
    CommonDataTable: {
        name: 'CommonDataTable',
        template: `
      <div>
        <slot name="more-action-icons" :item="{ id: '1', name: 'Doc 1' }" :index="0"></slot>
        <slot name="more-selected-items-buttons" :selectedItemCount="1"></slot>
        <slot name="more-action-dialogs" :selectedItemCount="1"></slot>
      </div>
    `,
        props: ['deleteSingleItem', 'deleteMultipleItems', 'loadItems', 'loadTableStats']
    },
    ConfirmationDialog: {
        template: '<div class="confirmation-dialog-stub" @click="$emit(\'confirmed\')"></div>',
        props: ['active']
    },
    EditDocDialog: {
        template: '<div class="edit-doc-dialog-stub" @click="$emit(\'confirmed\')"></div>',
        props: ['active', 'modelValue']
    },
    VIcon: { template: '<span class="v-icon-stub" @click="$emit(\'click\')"><slot /></span>' },
    VBtn: { template: '<button class="v-btn-stub" @click="$emit(\'click\')"><slot /></button>' }
}

// Mock AuthUtils
vi.mock('@/common/AuthUtils.js', () => ({
    getAuthorization: vi.fn().mockResolvedValue('Bearer token')
}))

// Mock Logger
vi.mock('@/common/Logger.js', () => ({
    default: {
        apiSuccess: vi.fn(),
        apiError: vi.fn()
    }
}))

// Mock Fetch
global.fetch = vi.fn(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({})
}))

describe('DocumentTableComponent.vue', () => {
    let wrapper
    let store

    beforeEach(() => {
        vi.clearAllMocks()

        wrapper = mount(DocumentTableComponent, {
            global: {
                plugins: [
                    createTestingPinia({
                        createSpy: vi.fn,
                        initialState: {
                            documentStore: {
                                page: 1,
                                itemsPerPage: 10,
                                totalItems: 0,
                                items: [],
                                selectedItems: [],
                                documentSetFilter: null,
                                contentTypeFilter: null,
                                sourceUrlFilter: null
                            }
                        }
                    })
                ],
                stubs: globalStubs
            }
        })
        store = useDocumentStore()
    })

    it('renders CommonDataTable', () => {
        expect(wrapper.findComponent({ name: 'CommonDataTable' }).exists()).toBe(true)
    })

    it('calls ingest API when ingest single item is confirmed', async () => {
        // 1. Trigger ingest icon click (in slot)
        const ingestIcon = wrapper.findAll('.v-icon-stub').find(icon => icon.text() === 'mdi-database-import')
        await ingestIcon.trigger('click')

        // 2. Expect confirmation dialog to be active (checking logic, triggering confirm)
        // In our stub, clicking the dialog emits 'confirmed'
        const confirmDialog = wrapper.find('.confirmation-dialog-stub')
        await confirmDialog.trigger('click')

        // 3. Verify fetch called
        expect(global.fetch).toHaveBeenCalledWith('/api/documents/ingest', expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ docUuids: ['1'] }, null, 2)
        }))
    })

    it('calls ingest all uploaded API when button clicked', async () => {
        const ingestAllButton = wrapper.findAll('button').find(b => b.text() === 'Ingest All Uploaded')
        await ingestAllButton.trigger('click')

        // Find the SECOND confirmation dialog (index based on template order)
        // 1. Ingest Item, 2. Ingest All Uploaded, 3. Ingest Selected
        const confirmDialogs = wrapper.findAll('.confirmation-dialog-stub')
        await confirmDialogs[1].trigger('click')

        expect(global.fetch).toHaveBeenCalledWith('/api/documents/ingest', expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ allUploaded: true }, null, 2)
        }))
    })

    it('calls ingest selected API when button clicked', async () => {
        // Set selected items in store or via v-model if 2-way binding works with stub
        store.selectedItems = [{ id: '100', name: 'Selected Doc' }]

        const ingestSelectedButton = wrapper.findAll('button').find(b => b.text() === 'Ingest Selected')
        await ingestSelectedButton.trigger('click')

        // 3rd dialog
        const confirmDialogs = wrapper.findAll('.confirmation-dialog-stub')
        await confirmDialogs[2].trigger('click')

        expect(global.fetch).toHaveBeenCalledWith('/api/documents/ingest', expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ docUuids: ['100'] }, null, 2)
        }))
    })

})
