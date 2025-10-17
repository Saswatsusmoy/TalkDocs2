import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'terminal-green': 'var(--terminal-green)',
        'terminal-bg': 'var(--terminal-bg)',
        'terminal-text': 'var(--terminal-text)',
        'terminal-border': 'var(--terminal-border)',
        'message-bg': 'var(--message-bg)',
        'message-border': 'var(--message-border)',
        'input-bg': 'var(--input-bg)',
        'input-border': 'var(--input-border)',
        'header-bg': 'var(--header-bg)',
        'user-message-bg': 'var(--user-message-bg)',
        'user-message-text': 'var(--user-message-text)',
        'assistant-message-bg': 'var(--assistant-message-bg)',
        'assistant-message-text': 'var(--assistant-message-text)',
        'button-hover': 'var(--button-hover)',
        'button-text': 'var(--button-text)',
        'code-bg': 'var(--code-bg)',
        'code-border': 'var(--code-border)',
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'cursor-blink': 'cursor-blink 1s infinite',
        'typing': 'typing 2s steps(40, end)',
      },
      keyframes: {
        'cursor-blink': {
          '0%, 50%': { opacity: '1' },
          '51%, 100%': { opacity: '0' },
        },
        'typing': {
          'from': { width: '0' },
          'to': { width: '100%' },
        },
      },
    },
  },
  plugins: [],
}
export default config
