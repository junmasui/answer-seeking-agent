import { Comment, Text, Fragment } from 'vue'

function _isVnodesEmpty(vnodes) {
  return vnodes.every((node) => {
    if (node.type === Comment) return true
    if (node.type === Text && !node.children.trim()) return true
    if (node.type === Fragment && _isVnodesEmpty(node.children)) return true
    return false
  })
}

export function isSlotEmpty(slot) {
  if (!slot) return true
  const vnodes = slot()
  return _isVnodesEmpty(vnodes)
}
