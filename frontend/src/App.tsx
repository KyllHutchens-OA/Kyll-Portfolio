import ChatContainer from './components/Chat/ChatContainer'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            AFL Analytics Agent
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Ask questions about AFL statistics (1990-2025)
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ChatContainer />
      </main>
    </div>
  )
}

export default App
