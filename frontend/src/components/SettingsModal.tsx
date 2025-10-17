'use client'

import { useState } from 'react'
import { X, Save, RotateCcw, BookOpen, Settings, Download } from 'lucide-react'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [settings, setSettings] = useState({
    documentationUrl: '',
    enableDocumentation: true
  })
  const [isCrawling, setIsCrawling] = useState(false)

  const handleSave = () => {
    // TODO: Implement settings save functionality
    console.log('Settings saved:', settings)
    onClose()
  }

  const handleReset = () => {
    setSettings({
      documentationUrl: '',
      enableDocumentation: true
    })
  }

  const handleCrawl = async () => {
    if (!settings.documentationUrl.trim()) {
      alert('Please enter a documentation URL first')
      return
    }

    setIsCrawling(true)
    
    try {
      console.log('Crawling documentation from:', settings.documentationUrl)
      
      const response = await fetch('http://localhost:8000/crawl', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: settings.documentationUrl,
          max_depth: 3,
          max_pages: 100,
          delay: 1.0
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      console.log('Crawl result:', result)
      
      alert(`Documentation crawled successfully!\nPages crawled: ${result.pages_crawled}\nContent length: ${result.total_content_length} characters`)
    } catch (error) {
      console.error('Crawling failed:', error)
      alert('Failed to crawl documentation. Please check the URL and try again.')
    } finally {
      setIsCrawling(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-terminal-bg border border-terminal-border rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-terminal-border">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-terminal-green" />
            <h2 className="text-xl font-bold text-terminal-text">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Settings Content */}
        <div className="p-6 space-y-6">
          {/* Documentation Settings Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-terminal-green" />
              <h3 className="text-lg font-semibold text-terminal-text">Documentation Settings</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-300">Enable Documentation</label>
                  <p className="text-xs text-gray-500">Allow AI to access documentation for better responses</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.enableDocumentation}
                  onChange={(e) => setSettings({...settings, enableDocumentation: e.target.checked})}
                  className="w-4 h-4 text-terminal-green bg-gray-800 border-gray-600 rounded focus:ring-terminal-green"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Documentation URL
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={settings.documentationUrl}
                    onChange={(e) => setSettings({...settings, documentationUrl: e.target.value})}
                    placeholder="https://docs.example.com or https://github.com/user/repo"
                    className="flex-1 px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:border-terminal-green focus:outline-none"
                  />
                  <button
                    onClick={handleCrawl}
                    disabled={!settings.documentationUrl.trim() || isCrawling}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-terminal-green hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors rounded-lg"
                  >
                    {isCrawling ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Crawling...
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4" />
                        Crawl
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Enter a documentation website URL or GitHub repository for the AI to reference
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-terminal-border">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors border border-gray-600 rounded-lg hover:border-gray-500"
          >
            <RotateCcw className="w-4 h-4" />
            Reset to Defaults
          </button>
          
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors border border-gray-600 rounded-lg hover:border-gray-500"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-terminal-green hover:bg-green-600 transition-colors rounded-lg"
            >
              <Save className="w-4 h-4" />
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
