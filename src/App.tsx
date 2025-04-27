import React, { useState } from 'react'
import './App.css'
import Dashboard from './components/Dashboard'
import Schedule from './components/Schedule'
import Settings from './components/Settings'
import Analytics from './components/Analytics'

function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'schedule' | 'analytics' | 'settings'>('dashboard')

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />
      case 'schedule':
        return <Schedule />
      case 'analytics':
        return <Analytics />
      case 'settings':
        return <Settings />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-600 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">LightSMS</h1>
          <nav className="space-x-4">
            <button 
              className={`text-white hover:text-blue-200 ${currentView === 'dashboard' ? 'underline' : ''}`}
              onClick={() => setCurrentView('dashboard')}
            >
              Dashboard
            </button>
            <button 
              className={`text-white hover:text-blue-200 ${currentView === 'schedule' ? 'underline' : ''}`}
              onClick={() => setCurrentView('schedule')}
            >
              Schedule
            </button>
            <button 
              className={`text-white hover:text-blue-200 ${currentView === 'analytics' ? 'underline' : ''}`}
              onClick={() => setCurrentView('analytics')}
            >
              Analytics
            </button>
            <button 
              className={`text-white hover:text-blue-200 ${currentView === 'settings' ? 'underline' : ''}`}
              onClick={() => setCurrentView('settings')}
            >
              Settings
            </button>
          </nav>
        </div>
      </header>
      <main className="container mx-auto p-4">
        {renderView()}
      </main>
    </div>
  )
}

export default App
