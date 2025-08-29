import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  isProcessing?: boolean;
}

export const ChatInput = ({ 
  onSendMessage, 
  disabled = false, 
  placeholder = "Type your message...",
  isProcessing = false
}: ChatInputProps) => {
  const [message, setMessage] = useState("");

  const handleSubmit = () => {
    if (message.trim() && !disabled && !isProcessing) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex items-end gap-3 p-4 bg-white border-t border-gray-100">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || isProcessing}
        className={cn(
          "min-h-[44px] max-h-32 resize-none border-gray-200 rounded-xl",
          "focus:border-blue-500 focus:ring-1 focus:ring-blue-500",
          "text-sm transition-all duration-200",
          (disabled || isProcessing) && "opacity-60 cursor-not-allowed"
        )}
      />
      <Button
        onClick={handleSubmit}
        disabled={disabled || isProcessing || !message.trim()}
        size="icon"
        className={cn(
          "h-11 w-11 shrink-0 rounded-xl transition-all duration-200",
          (disabled || isProcessing || !message.trim())
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
  );
};