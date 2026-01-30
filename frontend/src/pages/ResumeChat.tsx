import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useResumeWebSocket } from '../hooks/useResumeWebSocket';
import CareerTimeline from '../components/Resume/CareerTimeline';

// Timeline data - work experience and education
const timelineItems = [
  {
    company: 'SA Water',
    title: 'Data + Performance Analyst',
    start_date: '2023-11',
    end_date: 'Present',
    type: 'work' as const,
    highlight: 'Automated regulatory reporting from 2-3 weeks to hours',
  },
  {
    company: 'Dept. of Energy, Environment & Climate Action',
    title: 'Data Analyst',
    start_date: '2019-04',
    end_date: '2023-11',
    type: 'work' as const,
    highlight: 'Built dashboards in Tableau & Power BI for stakeholders',
  },
  {
    company: 'Dept. of Premier and Cabinet (NSW)',
    title: 'Graduate Analyst',
    start_date: '2018-02',
    end_date: '2019-04',
    type: 'work' as const,
    highlight: 'Automated data collection with Python',
  },
  {
    company: 'James Cook University',
    title: 'Master of Data Science',
    start_date: '2018-01',
    end_date: '2020-12',
    type: 'education' as const,
    highlight: '',
  },
];

const ResumeChat: React.FC = () => {
  const [input, setInput] = useState('');
  const [showTimeline, setShowTimeline] = useState(true);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { messages, isConnected, isThinking, thinkingStep, sendMessage } = useResumeWebSocket();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Handle mobile keyboard visibility using visualViewport API
  useEffect(() => {
    const viewport = window.visualViewport;
    if (!viewport) return;

    const handleResize = () => {
      // Calculate keyboard height as difference between window and viewport
      const keyboardH = window.innerHeight - viewport.height;
      setKeyboardHeight(keyboardH > 50 ? keyboardH : 0); // Only set if significant (keyboard)
    };

    viewport.addEventListener('resize', handleResize);
    viewport.addEventListener('scroll', handleResize);

    return () => {
      viewport.removeEventListener('resize', handleResize);
      viewport.removeEventListener('scroll', handleResize);
    };
  }, []);

  // Scroll to bottom when keyboard appears or messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking, keyboardHeight]);

  // Also scroll on focus as backup
  const handleInputFocus = () => {
    setTimeout(() => scrollToBottom(), 300);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;
    sendMessage(input.trim());
    setInput('');
  };

  const suggestedQuestions = [
    "What did you do at SA Water?",
    "What are your Data Science skills?",
    "What's a highlight of your career?",
    "Tell me about your AI projects",
  ];

  return (
    <div
      ref={containerRef}
      className="min-h-screen bg-gray-50"
      style={{ paddingBottom: keyboardHeight > 0 ? `${keyboardHeight}px` : undefined }}
    >
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-gray-900">
                Chat with my Resume
              </h1>
              <p className="text-xs sm:text-sm text-gray-600 mt-0.5 sm:mt-1">
                Ask about my experience, skills, and background
              </p>
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <button
                onClick={() => setShowTimeline(!showTimeline)}
                className="text-xs sm:text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="hidden xs:inline">{showTimeline ? 'Hide' : 'Show'}</span> Timeline
              </button>
              <Link
                to="/"
                className="text-xs sm:text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span className="hidden xs:inline">Back to</span> Home
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
        {/* Career Timeline - Full Width */}
        {showTimeline && (
          <div className="mb-4 sm:mb-8">
            <CareerTimeline items={timelineItems} />
          </div>
        )}

        {/* Chat Panel - Full Width */}
        <div className="flex flex-col h-[calc(100vh-14rem)] sm:h-[calc(100vh-20rem)] bg-white rounded-lg shadow-md border border-gray-200">
          {/* Connection Status */}
          <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-4 sm:mt-8 px-2">
                <h2 className="text-base sm:text-xl font-semibold mb-1 sm:mb-2">Hi, I'm Kyll's AI Resume Assistant</h2>
                <p className="text-xs sm:text-sm mb-3 sm:mb-4">Ask me anything about his experience, skills, or projects.</p>
                <div className="flex flex-col sm:flex-row sm:flex-wrap justify-center gap-2">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => sendMessage(question)}
                      disabled={!isConnected || isThinking}
                      className="text-xs sm:text-sm px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-left sm:text-center"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-3xl rounded-lg px-3 py-2 sm:px-4 sm:py-3 ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm sm:text-base">{message.text}</div>
                </div>
              </div>
            ))}

            {/* Thinking Indicator */}
            {isThinking && (
              <div className="flex justify-start">
                <div className="max-w-[85%] sm:max-w-3xl rounded-lg px-3 py-2 sm:px-4 sm:py-3 bg-gray-100 text-gray-900">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-xs sm:text-sm">{thinkingStep}</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Disclaimer */}
          <div className="px-3 py-1.5 text-center">
            <p className="text-xs text-gray-400">
              AI-generated responses may be inaccurate. For demonstration only.
            </p>
          </div>

          {/* Input Area */}
          <form onSubmit={handleSubmit} className="border-t border-gray-200 p-3 sm:p-4">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onFocus={handleInputFocus}
                placeholder="Ask about experience, skills..."
                disabled={!isConnected || isThinking}
                className="flex-1 px-3 py-2 sm:px-4 text-sm sm:text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={!isConnected || isThinking || !input.trim()}
                className="px-4 py-2 sm:px-6 text-sm sm:text-base bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
              >
                {isThinking ? '...' : 'Send'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};

export default ResumeChat;
