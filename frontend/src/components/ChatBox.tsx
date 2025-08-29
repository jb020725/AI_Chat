// src/components/ChatBox.tsx
import { useState, useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Sparkles, Search, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { sendMessage } from "@/lib/api";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export const ChatBox = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
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

  // Auto-scroll to bottom with smooth animation
  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector(
        '[data-radix-scroll-area-viewport]'
      ) as HTMLElement | null;
      if (viewport) {
        viewport.scrollTo({
          top: viewport.scrollHeight,
          behavior: 'smooth'
        });
      }
    }
  }, [messages, isProcessing]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsProcessing(true);

    // Hide mobile keyboard by blurring textarea
    if (textareaRef.current) {
      textareaRef.current.blur();
    }

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
      setIsProcessing(false);
      // Restore focus after a delay for smooth UX
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 500);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header - Clean and minimal */}
      <div className="flex-none bg-white border-b border-gray-100 px-4 py-3 sm:px-6">
        <div className="flex items-center justify-center space-x-2">
          <div className="w-7 h-7 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <h1 className="text-lg font-semibold text-gray-900">Student Visa AI</h1>
        </div>
      </div>

      {/* Messages - Full width, mobile optimized */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea ref={scrollAreaRef} className="h-full">
          <div className="px-4 py-4 space-y-4 sm:px-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex w-full animate-in fade-in-0 slide-in-from-bottom-2 duration-500",
                  message.isUser ? "justify-end" : "justify-start"
                )}
              >
                <div className={cn(
                  "max-w-[90%] sm:max-w-[80%] lg:max-w-[70%]",
                  message.isUser ? "text-right" : "text-left"
                )}>
                  <div
                    className={cn(
                      "rounded-2xl px-4 py-3 shadow-sm transition-all duration-300 transform",
                      message.isUser
                        ? "bg-blue-600 text-white ml-auto rounded-br-md animate-in slide-in-from-right-2"
                        : "bg-gray-50 text-gray-900 rounded-bl-md border border-gray-100 animate-in slide-in-from-left-2"
                    )}
                  >
                    <p className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap break-words">
                      {message.text}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {/* Processing indicator - Animated search with movement */}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="max-w-[90%] sm:max-w-[80%] lg:max-w-[70%]">
                  <div className="bg-gray-50 rounded-2xl rounded-bl-md px-4 py-3 border border-gray-100 animate-in slide-in-from-left-2 duration-300">
                    <div className="flex items-center space-x-3 text-gray-600">
                      <div className="relative">
                        <Search className="w-4 h-4 animate-pulse text-blue-500" />
                        <div className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full animate-ping"></div>
                      </div>
                      <span className="text-sm font-medium">Searching for information...</span>
                      <div className="flex space-x-1">
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></div>
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce delay-100"></div>
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce delay-200"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Input - Mobile optimized, always enabled */}
      <div className="flex-none bg-white border-t border-gray-100 px-4 py-3 sm:px-6">
        <div className="flex items-end space-x-3">
          <Textarea
            ref={textareaRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about student visas, requirements, or application processes..."
            disabled={false} // Always enabled for smooth UX
            className="min-h-[44px] max-h-32 resize-none border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm rounded-xl transition-all duration-200 mobile-input"
          />
          <Button
            onClick={handleSendMessage}
            disabled={isProcessing || !inputMessage.trim()}
            size="icon"
            className={cn(
              "h-11 w-11 shrink-0 rounded-xl transition-all duration-200 touch-target",
              isProcessing || !inputMessage.trim()
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md"
            )}
          >
            {isProcessing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

