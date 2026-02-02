// eslint.config.cjs

const eslint = require('@eslint/js');
const pluginVue = require('eslint-plugin-vue');
const globals = require('globals');
const eslintConfigPrettier = require('eslint-config-prettier/flat');
const prettierPlugin = require('eslint-plugin-prettier');

module.exports = [
  // Global ignore patterns (migrated from .eslintignore)
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'dist-ssr/**',
      'coverage/**',
      '**/*.config.js',
      'logs/**',
      '*.log',
      '.vscode/**',
      '.idea/**',
      'cypress/**',
      '.nyc_output/**',
      '.cache/**',
      'build/**'
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
      
      // Allow unused vars prefixed with underscore
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],

      // Vue-specific rules
      'vue/multi-word-component-names': 'warn',
      'vue/component-api-style': ['error', ['script-setup']],
      'vue/attribute-hyphenation': ['error', 'always'],
      'vue/no-v-model-argument': 'off' // Explicitly disable v-model argument rule
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021
      }
    }
  },

  // Configuration for CJS files
  {
    files: ['**/*.cjs'],
    languageOptions: {
      sourceType: 'commonjs',
      globals: {
        ...globals.node
      }
    }
  },

  // Configuration for Node.js scripts
  {
    files: ['scripts/**/*.js'],
    languageOptions: {
      globals: {
        ...globals.node
      }
    }
  },

  // Configuration for test files
  {
    files: ['tests/**/*.js', '**/*.test.js', '**/*.spec.js'],
    languageOptions: {
      globals: {
        ...globals.node,
        global: 'readonly'
      }
    },
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
    }
  }
];
