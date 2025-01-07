import React, { useState } from 'react'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'schedule' | 'analytics' | 'settings'>('dashboard')

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <div>Dashboard</div>
      case 'schedule':
        return <div>Schedule</div>
      case 'analytics':
        return <div>Analytics</div>
      case 'settings':
        return <div>Settings</div>
      default:
        return <div>Dashboard</div>
    }
  }

  return (
    <div className="min-h-screen bg-primary-50">
      <header className="bg-primary-600 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Spreadify AI</h1>
          <nav className="space-x-4">
            <button 
              className={`text-white hover:text-primary-200 ${currentView === 'dashboard' ? 'underline' : ''}`}
              onClick={() => setCurrentView('dashboard')}
            >
              Dashboard
            </button>
            <button 
              className={`text-white hover:text-primary-200 ${currentView === 'schedule' ? 'underline' : ''}`}
              onClick={() => setCurrentView('schedule')}
            >
              Schedule
            </button>
            <button 
              className={`text-white hover:text-primary-200 ${currentView === 'analytics' ? 'underline' : ''}`}
              onClick={() => setCurrentView('analytics')}
            >
              Analytics
            </button>
            <button 
              className={`text-white hover:text-primary-200 ${currentView === 'settings' ? 'underline' : ''}`}
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
