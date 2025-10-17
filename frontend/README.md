# TalkDocs Frontend

A modern, developer-focused AI chat interface built with Next.js and TypeScript.

## Features

- 🎨 **Developer Aesthetic**: Terminal-inspired dark theme with syntax highlighting
- 💬 **GPT-style Chat Interface**: Clean, modern chat bubbles with proper message threading
- 📝 **Code Support**: Syntax highlighting for code blocks with copy functionality
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- ⚡ **Real-time Updates**: Smooth animations and loading states
- 📊 **Chat Management**: Export conversations and clear chat history

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Beautiful icons
- **Custom CSS** - Terminal-inspired animations and effects

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/
│   ├── globals.css      # Global styles and animations
│   ├── layout.tsx      # Root layout component
│   └── page.tsx        # Main page component
└── components/
    ├── ChatContainer.tsx  # Main chat container
    ├── ChatMessage.tsx     # Individual message component
    └── ChatInput.tsx       # Message input component
```

## Customization

The interface uses a terminal-inspired color scheme that can be customized in `tailwind.config.ts`:

- `terminal-bg`: Main background color
- `terminal-text`: Primary text color
- `terminal-green`: Accent color for highlights
- `terminal-border`: Border colors

## API Integration

To connect with your AI backend, modify the `handleSendMessage` function in `ChatContainer.tsx` to make actual API calls instead of the simulated response.

## License

MIT License
