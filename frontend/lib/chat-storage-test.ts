// Simple utility to test chat history storage
export const testChatStorage = () => {
  if (typeof window === "undefined") return;
  
  const testMessages = [
    {
      id: "test-1",
      role: "user" as const,
      content: "Hello, this is a test message"
    },
    {
      id: "test-2", 
      role: "assistant" as const,
      content: "This is a test response"
    }
  ];
  
  // Save test data
  localStorage.setItem("oceanus-chat-history", JSON.stringify(testMessages));
  console.log("Test messages saved to localStorage");
  
  // Retrieve and verify
  const retrieved = localStorage.getItem("oceanus-chat-history");
  if (retrieved) {
    const parsed = JSON.parse(retrieved);
    console.log("Retrieved messages:", parsed);
    return parsed;
  }
  
  return null;
};