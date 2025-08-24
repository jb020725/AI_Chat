// src/components/ChatBox.tsx
import { useState, useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Bot, User, Sparkles } from "lucide-react";
import { cn } from "../lib/utils";
import { sendMessage } from "@/lib/api";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export const ChatBox = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Add welcome message on component mount
  useEffect(() => {
    const welcomeMessage: Message = {
      id: "welcome",
      text: "Hello! I'm your professional student visa consultant. I can help you with visa applications for USA, UK, South Korea, and Australia. What country are you interested in studying in?",
      isUser: false,
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector(
        '[data-radix-scroll-area-viewport]'
      ) as HTMLElement | null;
      if (viewport) viewport.scrollTop = viewport.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsTyping(true);

    try {
      const data = await sendMessage(userMessage.text);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data?.response || "I'm sorry, I couldn't process your request.",
        isUser: false,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        text: "I'm sorry, I'm having trouble connecting right now. Please try again.",
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
      // Restore focus to the textarea after sending message
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="flex-none bg-white/80 backdrop-blur-sm border-b border-slate-200 px-6 py-4">
        <div className="flex items-center justify-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-semibold text-slate-800">Student Visa AI</h1>
        </div>
        <p className="text-center text-sm text-slate-600 mt-1">
          Powered by AI • USA • Canada • UK • South Korea • Australia
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea ref={scrollAreaRef} className="h-full">
          <div className="px-6 py-4 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex w-full animate-in fade-in-0 slide-in-from-bottom-2 duration-300",
                  message.isUser ? "justify-end" : "justify-start"
                )}
              >
                <div className="flex items-start space-x-3 max-w-[80%]">
                  {!message.isUser && (
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div
                    className={cn(
                      "rounded-2xl px-4 py-3 shadow-sm",
                      message.isUser
                        ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-br-md"
                        : "bg-white text-slate-800 rounded-bl-md border border-slate-200"
                    )}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
                    <p
                      className={cn(
                        "text-xs mt-2 opacity-70",
                        message.isUser ? "text-blue-100" : "text-slate-500"
                      )}
                    >
                      {message.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>

                  {message.isUser && (
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 border border-slate-200">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Input */}
      <div className="flex-none bg-white/80 backdrop-blur-sm border-t border-slate-200 px-6 py-4">
        <div className="flex items-end space-x-3">
          <Textarea
            ref={textareaRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about student visas, requirements, or application processes..."
            disabled={isTyping}
            className="min-h-[44px] max-h-32 resize-none border-slate-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm"
          />
          <Button
            onClick={handleSendMessage}
            disabled={isTyping || !inputMessage.trim()}
            size="icon"
            className="h-11 w-11 shrink-0 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

