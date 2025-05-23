// eslint.config.cjs

const eslint = require('@eslint/js');
const pluginVue = require('eslint-plugin-vue');
const globals = require('globals');
const eslintConfigPrettier = require('eslint-config-prettier/flat');
const prettierPlugin = require('eslint-plugin-prettier');

module.exports = [
  // Global ignore patterns
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      '**/*.config.js'
    ]
  },

  // Core ESLint recommendations
  eslint.configs.recommended,

  // Vue 3 essential rules
  ...pluginVue.configs['flat/recommended'],

  // Prettier conflict resolution (MUST come after other configs)
  eslintConfigPrettier,

  // Project-specific configuration
  {
    files: ['**/*.js', '**/*.vue'],
    plugins: {
      prettier: prettierPlugin
    },
    rules: {
      // Prettier formatting rules
      'prettier/prettier': [
        'error',
        {
          semi: false,
          singleQuote: true,
          trailingComma: 'none',
          printWidth: 100,
          endOfLine: 'auto'
        }
      ],
      
      // Vue-specific rules
      'vue/multi-word-component-names': 'warn',
      'vue/attribute-hyphenation': ['error', 'always']
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021
      }
    }
  }
];
