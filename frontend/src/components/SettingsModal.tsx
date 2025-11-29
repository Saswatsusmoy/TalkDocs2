'use client'

import { useState, useEffect } from 'react'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

interface Source {
  source_id: string
  collection_name: string
  document_count: number
  created_at: string
  description: string
}

interface ModelProvider {
  provider: string
  model_name: string
  model_type: string
  base_url?: string
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [settings, setSettings] = useState({
    documentationUrl: '',
    enableDocumentation: true,
    activeSourceId: ''
  })
  const [isCrawling, setIsCrawling] = useState(false)
  const [sources, setSources] = useState<Source[]>([])
  const [isLoadingSources, setIsLoadingSources] = useState(false)
  const [deletingSourceId, setDeletingSourceId] = useState<string | null>(null)
  const [modelProvider, setModelProvider] = useState<ModelProvider | null>(null)
  const [isLoadingProvider, setIsLoadingProvider] = useState(false)
  const [isSwitchingProvider, setIsSwitchingProvider] = useState(false)

  const handleSave = () => {
    // TODO: Implement settings save functionality
    console.log('Settings saved:', settings)
    onClose()
  }

  const handleReset = () => {
    setSettings({
      documentationUrl: '',
      enableDocumentation: true,
      activeSourceId: ''
    })
  }

  const loadSources = async () => {
    setIsLoadingSources(true)
    try {
      const response = await fetch('http://localhost:8000/sources')
      if (response.ok) {
        const sourcesData = await response.json()
        setSources(sourcesData)
        setSettings(prev => {
          if (prev.activeSourceId && !sourcesData.some((source: Source) => source.source_id === prev.activeSourceId)) {
            return { ...prev, activeSourceId: '' }
          }
          return prev
        })
      }
    } catch (error) {
      console.error('Failed to load sources:', error)
    } finally {
      setIsLoadingSources(false)
    }
  }

  const loadActiveSource = async () => {
    try {
      const response = await fetch('http://localhost:8000/sources/active')
      if (response.ok) {
        const activeData = await response.json()
        setSettings(prev => ({
          ...prev,
          activeSourceId: activeData.source_id || ''
        }))
      }
    } catch (error) {
      console.error('Failed to load active source:', error)
    }
  }

  const setActiveSource = async (sourceId: string) => {
    try {
      const response = await fetch('http://localhost:8000/sources/active', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source_id: sourceId })
      })
      
      if (response.ok) {
        setSettings(prev => ({ ...prev, activeSourceId: sourceId }))
      }
    } catch (error) {
      console.error('Failed to set active source:', error)
    }
  }

  const handleDeleteSource = async (sourceId: string) => {
    const confirmDelete = window.confirm('Are you sure you want to delete this documentation source? This will remove all associated data.')
    if (!confirmDelete) {
      return
    }

    setDeletingSourceId(sourceId)
    try {
      const response = await fetch(`http://localhost:8000/sources/${sourceId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error(`Failed to delete source: ${response.status}`)
      }

      if (settings.activeSourceId === sourceId) {
        setSettings(prev => ({ ...prev, activeSourceId: '' }))
      }

      await loadSources()
      alert('Source deleted successfully.')
    } catch (error) {
      console.error('Failed to delete source:', error)
      alert('Failed to delete the selected documentation source. Please try again.')
    } finally {
      setDeletingSourceId(null)
    }
  }

  const loadModelProvider = async () => {
    setIsLoadingProvider(true)
    try {
      const response = await fetch('http://localhost:8000/model/provider')
      if (response.ok) {
        const providerData = await response.json()
        setModelProvider(providerData)
      }
    } catch (error) {
      console.error('Failed to load model provider:', error)
    } finally {
      setIsLoadingProvider(false)
    }
  }

  const setProvider = async (provider: string) => {
    setIsSwitchingProvider(true)
    try {
      const response = await fetch('http://localhost:8000/model/provider', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider })
      })
      
      if (response.ok) {
        const providerData = await response.json()
        setModelProvider(providerData)
        alert(`Model provider switched to ${providerData.model_type}`)
      } else {
        const errorData = await response.json()
        alert(`Failed to switch provider: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to set model provider:', error)
      alert('Failed to switch model provider. Please try again.')
    } finally {
      setIsSwitchingProvider(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadSources()
      loadActiveSource()
      loadModelProvider()
    }
  }, [isOpen])

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
      
      alert(`Documentation crawled successfully!\nNew pages crawled: ${result.new_pages_crawled}\nExisting documents retrieved: ${result.existing_documents_retrieved}\nTotal content length: ${result.total_content_length} characters`)
      
      // Refresh sources list after successful crawl
      await loadSources()
    } catch (error) {
      console.error('Crawling failed:', error)
      alert('Failed to crawl documentation. Please check the URL and try again.')
    } finally {
      setIsCrawling(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-black dark:bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-terminal-bg border border-terminal-border w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-terminal-border">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-terminal-text">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-terminal-text dark:text-gray-400 dark:hover:text-white"
          >
            ×
          </button>
        </div>

        {/* Settings Content */}
        <div className="p-6 space-y-6">
          {/* Documentation Settings Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <h3 className="text-lg font-semibold text-terminal-text">Documentation Settings</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Enable Documentation</label>
                  <p className="text-xs text-gray-600 dark:text-gray-500">Allow AI to access documentation for better responses</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.enableDocumentation}
                  onChange={(e) => setSettings({...settings, enableDocumentation: e.target.checked})}
                  className="w-4 h-4 text-terminal-green bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 rounded focus:ring-terminal-green"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Documentation URL
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={settings.documentationUrl}
                    onChange={(e) => setSettings({...settings, documentationUrl: e.target.value})}
                    placeholder="https://docs.example.com or https://github.com/user/repo"
                    className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-terminal-text placeholder-gray-500 dark:placeholder-gray-400 focus:border-terminal-green focus:outline-none"
                  />
                         <button
                           onClick={handleCrawl}
                           disabled={!settings.documentationUrl.trim() || isCrawling}
                           className="px-4 py-2 text-sm text-white bg-terminal-green hover:bg-green-600 dark:hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                         >
                           {isCrawling ? 'Crawling...' : 'Crawl'}
                         </button>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-500 mt-1">
                  Enter a documentation website URL or GitHub repository for the AI to reference
                </p>
              </div>
            </div>
          </div>

          {/* Model Provider Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <h3 className="text-lg font-semibold text-terminal-text">AI Model Provider</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Current Model Provider
                </label>
                {isLoadingProvider ? (
                  <div className="text-sm text-gray-600 dark:text-gray-400">Loading...</div>
                ) : modelProvider ? (
                  <div className="bg-gray-100 dark:bg-gray-800/50 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-terminal-text">
                          {modelProvider.model_type}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          Model: {modelProvider.model_name}
                          {modelProvider.base_url && ` • ${modelProvider.base_url}`}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-600 dark:text-gray-400">No provider information available</div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Switch Model Provider
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setProvider('lm_studio')}
                    disabled={isSwitchingProvider || modelProvider?.provider === 'lm_studio'}
                    className={`flex-1 px-4 py-2 text-sm rounded-lg ${
                      modelProvider?.provider === 'lm_studio'
                        ? 'bg-terminal-green text-white'
                        : 'bg-gray-600 text-white hover:bg-gray-500 dark:hover:bg-gray-500'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {isSwitchingProvider && modelProvider?.provider !== 'lm_studio' ? 'Switching...' : 'LM Studio (Local)'}
                  </button>
                  <button
                    onClick={() => setProvider('gemini')}
                    disabled={isSwitchingProvider || modelProvider?.provider === 'gemini'}
                    className={`flex-1 px-4 py-2 text-sm rounded-lg ${
                      modelProvider?.provider === 'gemini'
                        ? 'bg-terminal-green text-white'
                        : 'bg-gray-600 text-white hover:bg-gray-500 dark:hover:bg-gray-500'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {isSwitchingProvider && modelProvider?.provider !== 'gemini' ? 'Switching...' : 'Gemini API'}
                  </button>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-500 mt-1">
                  Choose between local LM Studio model or Google Gemini API. Make sure LM Studio is running for local models, or set GEMINI_API_KEY for Gemini.
                </p>
              </div>
            </div>
          </div>

          {/* Source Selection Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <h3 className="text-lg font-semibold text-terminal-text">Documentation Sources</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Active Documentation Source
                </label>
                <div className="flex gap-2">
                  <select
                    value={settings.activeSourceId}
                    onChange={(e) => setActiveSource(e.target.value)}
                    className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-terminal-text focus:border-terminal-green focus:outline-none"
                    disabled={isLoadingSources}
                  >
                    <option value="">
                      {isLoadingSources ? 'Loading sources...' : 'Select a documentation source'}
                    </option>
                    {sources.map((source) => (
                      <option key={source.source_id} value={source.source_id}>
                        {source.source_id.replace('source_', '').replace(/_/g, '.')} ({source.document_count} docs)
                      </option>
                    ))}
                  </select>
                         <button
                           onClick={loadSources}
                           disabled={isLoadingSources}
                           className="px-3 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 dark:hover:bg-blue-500 disabled:opacity-50"
                         >
                           {isLoadingSources ? 'Loading...' : 'Refresh'}
                         </button>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-500 mt-1">
                  Select which documentation source to use for AI responses. Each source is isolated and won't mix results.
                </p>
              </div>

              {sources.length > 0 && (
                <div className="bg-gray-100 dark:bg-gray-800/50 p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Available Sources:</h4>
                  <div className="space-y-2">
                    {sources.map((source) => (
                      <div
                        key={source.source_id}
                        className={`flex items-center justify-between p-3 border ${
                          settings.activeSourceId === source.source_id
                            ? 'border-terminal-green bg-green-100 dark:bg-green-900/20'
                            : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700/50'
                        }`}
                      >
                        <div>
                          <div className="text-sm font-medium text-terminal-text">
                            {source.source_id.replace('source_', '').replace(/_/g, '.')}
                          </div>
                          <div className="text-xs text-gray-600 dark:text-gray-400">
                            {source.document_count} documents • Created {new Date(source.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setActiveSource(source.source_id)}
                            className={`px-3 py-1 text-xs ${
                              settings.activeSourceId === source.source_id
                                ? 'bg-terminal-green text-white'
                                : 'bg-gray-600 text-white hover:bg-gray-500 dark:hover:bg-gray-500'
                            }`}
                          >
                            {settings.activeSourceId === source.source_id ? 'Active' : 'Select'}
                          </button>
                          <button
                            onClick={() => handleDeleteSource(source.source_id)}
                            disabled={deletingSourceId === source.source_id}
                            className="px-3 py-1 text-xs bg-red-600 text-white hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {deletingSourceId === source.source_id ? 'Deleting...' : 'Delete'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-terminal-border">
                 <button
                   onClick={handleReset}
                   className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-terminal-text dark:hover:text-white border border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                 >
                   Reset to Defaults
                 </button>
                 
                 <div className="flex items-center gap-3">
                   <button
                     onClick={onClose}
                     className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-terminal-text dark:hover:text-white border border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                   >
                     Cancel
                   </button>
                   <button
                     onClick={handleSave}
                     className="px-4 py-2 text-sm text-white bg-terminal-green hover:bg-green-600 dark:hover:bg-green-500"
                   >
                     Save Settings
                   </button>
                 </div>
        </div>
      </div>
    </div>
  )
}
