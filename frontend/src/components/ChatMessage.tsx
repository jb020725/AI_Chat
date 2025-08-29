import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp?: Date;
}

export const ChatMessage = ({ message, isUser, timestamp }: ChatMessageProps) => {
  return (
    <div className={cn(
      "flex w-full mb-4 animate-in fade-in-0 slide-in-from-bottom-2 duration-300",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[90%] sm:max-w-[80%] lg:max-w-[70%]",
        isUser ? "text-right" : "text-left"
      )}>
        <div className={cn(
          "rounded-2xl px-4 py-3 shadow-sm transition-all duration-200",
          isUser 
            ? "bg-blue-600 text-white ml-auto rounded-br-md" 
            : "bg-gray-50 text-gray-900 rounded-bl-md border border-gray-100"
        )}>
          <p className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap break-words">
            {message}
          </p>
        </div>
      </div>
    </div>
  );
};