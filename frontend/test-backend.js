// Simple test script to check backend connection
const testBackend = async () => {
  const urls = [
    'http://localhost:8001/',
    'http://127.0.0.1:8001/',
    'http://0.0.0.0:8001/'
  ];
  
  for (const url of urls) {
    try {
      console.log(`Testing connection to: ${url}`);
      
      // Test health endpoint
      const healthResponse = await fetch(url);
      console.log('✅ Health check status:', healthResponse.status);
      const healthData = await healthResponse.json();
      console.log('✅ Health check response:', healthData);
      
      // Test chat endpoint
      const chatResponse = await fetch(`${url}api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            { role: 'user', content: 'Hello, how many floats are there?' }
          ]
        }),
      });
      
      console.log('✅ Chat response status:', chatResponse.status);
      const chatData = await chatResponse.json();
      console.log('✅ Chat response:', chatData);
      
      console.log(`✅ SUCCESS: Backend is accessible at ${url}`);
      break;
      
    } catch (error) {
      console.log(`❌ Failed to connect to ${url}:`, error.message);
    }
  }
};

testBackend();