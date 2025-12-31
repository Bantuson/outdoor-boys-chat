import { useState, useEffect, useRef, FormEvent } from 'react';
import { Send, Loader2, Mountain, Fish, Hammer, Snowflake, Utensils, Lightbulb, Smile, Wifi, WifiOff } from 'lucide-react';
import { rag } from '@/lib/rag-pipeline';
import type { ChatMessage, FactSource, ModelStatus } from '@/types/knowledge-base';

const EXAMPLE_QUESTIONS = [
  { icon: Snowflake, text: 'How do I build a snow shelter?' },
  { icon: Fish, text: 'What are the best ice fishing tips?' },
  { icon: Hammer, text: 'How do I start building a cabin?' },
  { icon: Utensils, text: 'What campfire recipes do you recommend?' },
  { icon: Smile, text: 'Tell me a dad joke!' },
];

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [modelStatus, setModelStatus] = useState<ModelStatus>('idle');
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadStatus, setLoadStatus] = useState('');
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Track online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize RAG on mount
  useEffect(() => {
    async function init() {
      setModelStatus('loading');
      try {
        await rag.initialize((progress, status) => {
          setLoadProgress(progress);
          setLoadStatus(status);
        });
        setModelStatus('ready');
        
        // Welcome message
        setMessages([{
          id: '0',
          role: 'assistant',
          content: '🏕️ Hey there, outdoor enthusiast! I\'m your Outdoor Boys knowledge assistant. Ask me about winter survival, cabin building, ice fishing, recipes, or if you just need a dad joke to brighten your day!',
          timestamp: new Date(),
        }]);
      } catch (error) {
        console.error('Failed to initialize:', error);
        setModelStatus('error');
      }
    }
    init();
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || modelStatus !== 'ready' || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const { response, sources } = await rag.query(userMessage.content);
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
        sources,
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Query failed:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I had trouble finding that information. Try rephrasing your question!',
        timestamp: new Date(),
      }]);
    }

    setIsLoading(false);
  }

  function handleExampleClick(question: string) {
    setInput(question);
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-green-50 to-white">
      {/* Header */}
      <header className="bg-green-800 text-white p-4 shadow-lg">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Mountain className="w-8 h-8" />
            <div>
              <h1 className="text-xl font-bold">Outdoor Boys Chat</h1>
              <p className="text-green-200 text-sm">Your offline-ready wilderness guide</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isOffline ? (
              <span className="flex items-center gap-1 text-yellow-300 text-sm">
                <WifiOff className="w-4 h-4" /> Offline
              </span>
            ) : (
              <span className="flex items-center gap-1 text-green-300 text-sm">
                <Wifi className="w-4 h-4" /> Online
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Loading Overlay */}
      {modelStatus === 'loading' && (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <Loader2 className="w-16 h-16 text-green-600 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Setting up your guide...</h2>
            <p className="text-gray-600 mb-4">{loadStatus}</p>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-green-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${loadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">{Math.round(loadProgress)}%</p>
            <p className="text-xs text-gray-400 mt-4">
              First load downloads the AI model (~2-4GB). <br />
              After that, works completely offline! 🏕️
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {modelStatus === 'error' && (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <p className="text-red-600 mb-4">Failed to load the AI model.</p>
            <p className="text-gray-600 mb-4">
              Make sure you're using a browser with WebGPU support (Chrome 113+).
            </p>
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Chat Area */}
      {modelStatus === 'ready' && (
        <>
          <main className="flex-1 overflow-y-auto p-4">
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] p-4 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-green-600 text-white rounded-br-md'
                        : 'bg-white shadow-md border border-gray-100 rounded-bl-md'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    
                    {/* Source references */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-500 mb-1">📺 From videos:</p>
                        <div className="flex flex-wrap gap-1">
                          {message.sources.map((source, i) => (
                            <a
                              key={i}
                              href={`https://youtube.com/watch?v=${source.videoId}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded hover:bg-green-100"
                            >
                              {source.videoTitle.slice(0, 30)}...
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white shadow-md border border-gray-100 p-4 rounded-2xl rounded-bl-md">
                    <div className="flex items-center gap-2 text-gray-500">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Searching the wilderness...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </main>

          {/* Example Questions */}
          {messages.length <= 1 && (
            <div className="px-4 pb-2">
              <div className="max-w-3xl mx-auto">
                <p className="text-sm text-gray-500 mb-2">Try asking:</p>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleExampleClick(q.text)}
                      className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:bg-green-50 hover:border-green-300 transition-colors"
                    >
                      <q.icon className="w-4 h-4 text-green-600" />
                      {q.text}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 bg-white border-t border-gray-200">
            <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about survival tips, fishing, recipes..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </>
      )}
    </div>
  );
}
