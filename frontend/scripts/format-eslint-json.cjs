#!/usr/bin/env node
// scripts/format-eslint-json.js
// Lightweight formatter to print ESLint JSON output in a human-friendly, verbose way

const fs = require('fs')
const path = require('path')

function plural(n, s) {
  return `${n} ${s}${n === 1 ? '' : 's'}`
}

const filePath = process.argv[2] || 'eslint-report.json'
if (!fs.existsSync(filePath)) {
  console.error(`ESLint report not found: ${filePath}`)
  process.exit(2)
}

let raw
try {
  raw = fs.readFileSync(filePath, 'utf8')
} catch (err) {
  console.error(`Failed to read ${filePath}:`, err.message)
  process.exit(2)
}

let results
try {
  results = JSON.parse(raw)
} catch (err) {
  console.error(`Invalid JSON in ${filePath}:`, err.message)
  process.exit(2)
}

let totalErrors = 0
let totalWarnings = 0
let totalFixable = 0

results.forEach((file) => {
  const { filePath: fpath, messages } = file
  if (messages.length === 0) return
  console.log(`\nFile: ${path.relative(process.cwd(), fpath)}`)
  messages.forEach((msg) => {
    const severity = msg.severity === 2 ? 'error' : 'warning'
    const rule = msg.ruleId || '<internal>'
    const location = `${msg.line || 0}:${msg.column || 0}`
    const fixable = msg.fix ? '[fixable]' : ''
    console.log(`  ${location}  ${severity.toUpperCase()}  ${rule} ${fixable}`)
    console.log(`    ${msg.message}`)
    if (msg.suggestions && msg.suggestions.length) {
      msg.suggestions.forEach((s, i) => {
        console.log(`    Suggestion ${i + 1}: ${s.desc}`)
      })
    }
    if (msg.fix) {
      totalFixable++
    }
    if (msg.severity === 2) totalErrors++
    else if (msg.severity === 1) totalWarnings++
  })
})

console.log('\nSummary:')
console.log(`  ${plural(totalErrors, 'error')}, ${plural(totalWarnings, 'warning')}`)
if (totalFixable) console.log(`  ${plural(totalFixable, 'fixable problem')}`)

// Exit with non-zero if any errors (so CI can fail)
process.exit(totalErrors > 0 ? 1 : 0)
