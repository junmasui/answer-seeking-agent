import { Comment, Text, Fragment } from 'vue'

function _isVnodesEmpty(vnodes) {
  return vnodes.every((node) => {
    return (
      node.type === Comment ||
      (node.type === Text && !node.children.trim()) ||
      (node.type === Fragment && _isVnodesEmpty(node.children))
    )
  })
}

export function isSlotEmpty(slot) {
  if (!slot) return true
  const vnodes = slot()
  return _isVnodesEmpty(vnodes)
}
