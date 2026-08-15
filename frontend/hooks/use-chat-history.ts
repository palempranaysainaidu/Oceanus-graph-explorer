"use client";

import { useState, useEffect } from "react";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  exampleQuestions?: string[];
};

const CHAT_HISTORY_KEY = "oceanus-chat-history";

export const useChatHistory = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load chat history from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const savedHistory = localStorage.getItem(CHAT_HISTORY_KEY);
        if (savedHistory) {
          const parsedHistory = JSON.parse(savedHistory);
          setMessages(parsedHistory);
        }
      } catch (error) {
        console.error("Failed to load chat history:", error);
      } finally {
        setIsLoaded(true);
      }
    }
  }, []);

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    if (isLoaded && typeof window !== "undefined") {
      try {
        localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages));
      } catch (error) {
        console.error("Failed to save chat history:", error);
      }
    }
  }, [messages, isLoaded]);

  const addMessage = (message: Message) => {
    setMessages(prev => [...prev, message]);
  };

  const clearHistory = () => {
    setMessages([]);
    if (typeof window !== "undefined") {
      localStorage.removeItem(CHAT_HISTORY_KEY);
    }
  };

  return {
    messages,
    addMessage,
    clearHistory,
    setMessages,
    isLoaded
  };
};