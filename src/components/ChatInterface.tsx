import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, HelpCircle, CheckCircle, BookOpen, Sparkles, Bot, Upload, Paperclip } from 'lucide-react';
// import { useToast } from '@/hooks/use-toast';
import brainIllustration from '@/assets/brain-illustration.jpg';
import studyDesk from '@/assets/study-desk.jpg';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (content: string, type: 'user' | 'ai') => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

<<<<<<< HEAD
  const callBackendHint = async (mode: 'hint' | 'check') => {
    try {
      const response = await fetch('http://localhost:8000/give-hint', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
=======
  const callBackendHint = async (mode: 'hint' | 'check', learned: string = '') => {
    try {
      const response = await fetch('http://localhost:8000/give-hint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learned: learned || inputValue || 'Current work context',
          question: learned || inputValue || ''
        })
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
<<<<<<< HEAD
      const data = await response.json();
      return data.hint || 'No response from server';
    } catch (error) {
      console.error('Error calling backend:', error);
      return mode === 'hint' 
        ? 'Unable to get hint at the moment. Please try again.'
        : 'Unable to check work at the moment. Please try again.';
=======
      // The endpoint returns JSON with hint field
      const result = await response.json();
      return result.hint || 'No response from server';
    } catch (error) {
      console.error('Error calling backend:', error);
      return mode === 'hint' 
        ? '💡 **Hint:** Unable to get hint at the moment. Please try again.'
        : '🔍 **Check:** Unable to check work at the moment. Please try again.';
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
    }
  };

  const simulateAIResponse = async (userInput: string, mode: 'hint' | 'check' | 'general') => {
    setIsLoading(true);
    
    let response = '';
    
    if (mode === 'hint' || mode === 'check') {
<<<<<<< HEAD
      response = await callBackendHint(mode);
=======
      response = await callBackendHint(mode, userInput);
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
    } else {
      // Simulate API delay for general responses
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
      response = `Regarding "${userInput}": I understand you're asking about this topic. Let me provide some guidance and insights that might help you.`;
    }
    
    addMessage(response, 'ai');
    setIsLoading(false);
  };

  const handleSubmit = async (mode: 'hint' | 'check' | 'general' = 'general') => {
    if (!inputValue.trim()) {
      console.log("Empty message - please enter a question or request.");
      return;
    }

    const userMessage = inputValue.trim();
    addMessage(userMessage, 'user');
    setInputValue('');
    
    await simulateAIResponse(userMessage, mode);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setUploadedFiles(prev => [...prev, ...files]);
    
    files.forEach(file => {
      console.log(`File uploaded: ${file.name} has been attached to your message.`);
    });
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="h-screen w-full flex flex-col relative overflow-hidden">
      
      {/* Content Layer */}
      <div className="relative z-10 flex flex-col h-full">
        {/* Elegant Header with Background Image */}
        <div 
          className="flex-shrink-0 p-6 border-b border-purple-200/50 shadow-sm relative bg-cover bg-center"
          style={{ backgroundImage: `url('https://images.unsplash.com/photo-1481627834876-b7833e8f5570?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2000&q=80')` }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-purple-900/80 via-indigo-900/70 to-violet-900/80 backdrop-blur-sm"></div>
          <div className="relative z-10 flex items-center justify-between px-8">
            {/* Left side decorative image */}
            <div className="flex items-center">
              <img 
                src="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80" 
                alt="" 
                className="w-8 h-8 rounded-full object-cover opacity-60 shadow-sm"
              />
            </div>
            
            {/* Center content */}
            <div className="flex items-center gap-4">
              <Bot className="w-6 h-6 text-purple-200" />
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-100 to-indigo-100 bg-clip-text text-transparent">
                Step by Step
              </h1>
              <div className="p-2 rounded-full bg-gradient-to-r from-indigo-400 to-violet-400 shadow-lg">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
            </div>
            
            {/* Right side decorative image */}
            <div className="flex items-center">
              <img 
                src="https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80" 
                alt="" 
                className="w-8 h-8 rounded-full object-cover opacity-60 shadow-sm"
              />
            </div>
          </div>
        </div>

        {/* Messages Area - Takes remaining space */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-muted-foreground mb-6">
                <div className="relative w-32 h-32 mx-auto mb-6">
                  <img 
                    src={brainIllustration} 
                    alt="AI Brain" 
                    className="w-full h-full object-cover rounded-2xl shadow-lg"
                  />
                  <div className="absolute inset-0 bg-primary/10 rounded-2xl" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <BookOpen className="w-12 h-12 text-primary" />
                  </div>
                </div>
                <h3 className="text-lg font-medium mb-2">Ready to Learn?</h3>
                <p>Start by asking a question, requesting a hint, or sharing your work for review.</p>
                
                {/* Study Tips */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 max-w-2xl mx-auto">
                  <div className="bg-primary-light rounded-xl p-4 text-left">
                    <div className="flex items-center gap-3 mb-2">
                      <img src={studyDesk} alt="Study tips" className="w-8 h-8 rounded-lg object-cover" />
                      <span className="font-medium text-primary">Study Tips</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Ask specific questions for better answers</p>
                  </div>
                  <div className="bg-accent rounded-xl p-4 text-left">
                    <div className="flex items-center gap-3 mb-2">
                      <HelpCircle className="w-8 h-8 text-primary" />
                      <span className="font-medium text-primary">Get Hints</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Use hints when you're stuck on problems</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto p-10 space-y-8 relative">
              {/* Left side decorative images */}
              <div className="fixed left-4 top-[20%] transform -translate-y-1/2 opacity-20 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/3145/3145765.png" 
                  alt="" 
                  className="w-16 h-16 object-contain"
                />
              </div>
              <div className="fixed left-4 top-[35%] transform -translate-y-1/2 opacity-15 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/2232/2232688.png" 
                  alt="" 
                  className="w-12 h-12 object-contain"
                />
              </div>
              <div className="fixed left-4 top-[50%] transform -translate-y-1/2 opacity-20 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/3534/3534033.png" 
                  alt="" 
                  className="w-14 h-14 object-contain"
                />
              </div>
              <div className="fixed left-4 top-[65%] transform -translate-y-1/2 opacity-10 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/2232/2232688.png" 
                  alt="" 
                  className="w-10 h-10 object-contain"
                />
              </div>
              <div className="fixed left-4 top-[80%] transform -translate-y-1/2 opacity-15 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/3145/3145765.png" 
                  alt="" 
                  className="w-12 h-12 object-contain"
                />
              </div>
              
              {/* Right side decorative images */}
              <div className="fixed right-4 top-[20%] transform -translate-y-1/2 opacity-20 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/2436/2436874.png" 
                  alt="" 
                  className="w-16 h-16 object-contain"
                />
              </div>
              <div className="fixed right-4 top-[35%] transform -translate-y-1/2 opacity-15 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/3534/3534015.png" 
                  alt="" 
                  className="w-12 h-12 object-contain"
                />
              </div>
              <div className="fixed right-4 top-[50%] transform -translate-y-1/2 opacity-20 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/2436/2436729.png" 
                  alt="" 
                  className="w-14 h-14 object-contain"
                />
              </div>
              <div className="fixed right-4 top-[65%] transform -translate-y-1/2 opacity-10 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/3145/3145765.png" 
                  alt="" 
                  className="w-10 h-10 object-contain"
                />
              </div>
              <div className="fixed right-4 top-[80%] transform -translate-y-1/2 opacity-15 z-0">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/2436/2436874.png" 
                  alt="" 
                  className="w-12 h-12 object-contain"
                />
              </div>
              
              {messages.map((message) => (
                <div key={message.id} className="space-y-3 relative z-10">
                  {message.type === 'user' ? (
                    <div className="font-bold text-gray-900 text-xl leading-relaxed tracking-wide">
                      {message.content}
                    </div>
                  ) : (
                    <div className="text-gray-700 text-lg leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="space-y-2">
                  <div className="text-gray-700 text-lg leading-relaxed flex items-center space-x-3">
                    <div className="text-muted-foreground italic">Thinking...</div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

        {/* Elegant Input Area at Bottom */}
        <div className="flex-shrink-0 border-t border-purple-200/50 bg-white/85 backdrop-blur-md p-6 shadow-lg">
          <div className="max-w-4xl mx-auto flex flex-col space-y-5">
            {/* Study Action Buttons */}
            <div className="flex flex-wrap gap-4 justify-center">
              <Button 
                variant="outline" 
                onClick={() => {
                  addMessage('Give hint', 'user');
                  simulateAIResponse('Give hint', 'hint');
                }}
                disabled={isLoading}
                className="flex items-center gap-2 px-6 py-2 border-purple-200 hover:bg-purple-50 hover:border-purple-300 transition-all duration-200 shadow-sm"
              >
                <HelpCircle className="w-4 h-4 text-purple-600" />
                <span className="font-medium text-lg">Give Hint</span>
              </Button>
              <Button 
                variant="outline" 
                onClick={() => {
                  addMessage('Check work', 'user');
                  simulateAIResponse('Check work', 'check');
                }}
                disabled={isLoading}
                className="flex items-center gap-2 px-6 py-2 border-indigo-200 hover:bg-indigo-50 hover:border-indigo-300 transition-all duration-200 shadow-sm"
              >
                <CheckCircle className="w-4 h-4 text-indigo-600" />
                <span className="font-medium text-lg">Check Work</span>
              </Button>
            </div>
            
            {/* File Upload Area */}
            {uploadedFiles.length > 0 && (
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-200">
                <div className="flex items-center gap-2 mb-3">
                  <Paperclip className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-purple-700">Attached Files:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center gap-2 bg-white rounded-lg px-3 py-2 border border-purple-200">
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <button 
                        onClick={() => removeFile(index)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Enhanced Input Field */}
            <div className="flex gap-4 items-center">
              <Button
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                className="h-14 px-4 border-purple-200 hover:bg-purple-50 hover:border-purple-300 transition-all duration-200"
              >
                <Upload className="w-5 h-5 text-purple-600" />
              </Button>
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question"
                disabled={isLoading}
                className="flex-1 h-14 text-lg px-6 border-purple-200 focus:border-purple-400 focus:ring-purple-200 rounded-xl shadow-sm bg-white/80 backdrop-blur-sm"
              />
              <Button 
                onClick={() => handleSubmit()}
                disabled={!inputValue.trim() || isLoading}
                className="h-14 px-6 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl shadow-lg transition-all duration-200 transform hover:scale-105"
              >
                <Send className="w-5 h-5" />
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;