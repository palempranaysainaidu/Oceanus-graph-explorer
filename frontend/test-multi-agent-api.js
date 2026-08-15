/**
 * Test script for the Multi-Agent RAG API connection
 */

const BACKEND_URL = 'http://localhost:8000';

async function testMultiAgentAPI() {
  console.log('🧪 Testing Multi-Agent RAG API Connection');
  console.log('=' .repeat(50));

  try {
    // Test 1: Health Check
    console.log('\n1. Testing health check...');
    const healthResponse = await fetch(`${BACKEND_URL}/health`);
    console.log(`   Status: ${healthResponse.status}`);
    
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log(`   Service: ${healthData.service}`);
      console.log(`   Status: ${healthData.status}`);
    }

    // Test 2: Detailed Health Check
    console.log('\n2. Testing detailed health check...');
    const detailedHealthResponse = await fetch(`${BACKEND_URL}/health/detailed`);
    console.log(`   Status: ${detailedHealthResponse.status}`);
    
    if (detailedHealthResponse.ok) {
      const detailedHealth = await detailedHealthResponse.json();
      console.log(`   Overall Status: ${detailedHealth.status}`);
      console.log(`   Agent System: ${detailedHealth.components?.agent_system?.status}`);
    }

    // Test 3: Create Session
    console.log('\n3. Testing session creation...');
    const sessionResponse = await fetch(`${BACKEND_URL}/api/v1/sessions/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_preferences: {
          detail_level: 'comprehensive',
          preferred_regions: ['Arabian Sea', 'Bay of Bengal']
        }
      }),
    });

    console.log(`   Status: ${sessionResponse.status}`);
    
    let sessionId = null;
    if (sessionResponse.ok) {
      const sessionData = await sessionResponse.json();
      sessionId = sessionData.session_id;
      console.log(`   Session ID: ${sessionId}`);
      console.log(`   Created: ${sessionData.created_at}`);
    }

    // Test 4: Send Chat Message
    if (sessionId) {
      console.log('\n4. Testing chat message...');
      const chatResponse = await fetch(`${BACKEND_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: 'Show me temperature data for float 7902073',
          session_id: sessionId,
          timeout: 60
        }),
      });

      console.log(`   Status: ${chatResponse.status}`);
      
      if (chatResponse.ok) {
        const chatData = await chatResponse.json();
        console.log(`   Response Length: ${chatData.response.length} characters`);
        console.log(`   Session ID: ${chatData.session_id}`);
        console.log(`   Response Time: ${chatData.metadata.response_time}s`);
        console.log(`   Has Context: ${chatData.metadata.has_context}`);
        console.log(`   Agent Type: ${chatData.metadata.agent_type}`);
        console.log(`   First 200 chars: ${chatData.response.substring(0, 200)}...`);
      } else {
        const errorData = await chatResponse.json().catch(() => null);
        console.log(`   Error: ${JSON.stringify(errorData, null, 2)}`);
      }

      // Test 5: Get Session History
      console.log('\n5. Testing session history...');
      const historyResponse = await fetch(`${BACKEND_URL}/api/v1/sessions/${sessionId}/history`);
      console.log(`   Status: ${historyResponse.status}`);
      
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        console.log(`   Total Messages: ${historyData.total_messages}`);
        console.log(`   Context: ${JSON.stringify(historyData.context, null, 2)}`);
      }
    }

    // Test 6: Get Examples
    console.log('\n6. Testing examples endpoint...');
    const examplesResponse = await fetch(`${BACKEND_URL}/api/v1/chat/examples`);
    console.log(`   Status: ${examplesResponse.status}`);
    
    if (examplesResponse.ok) {
      const examplesData = await examplesResponse.json();
      console.log(`   Example Categories: ${Object.keys(examplesData.examples || {}).join(', ')}`);
      console.log(`   Supported Regions: ${examplesData.supported_regions?.length || 0}`);
    }

    console.log('\n' + '='.repeat(50));
    console.log('✅ Multi-Agent RAG API testing completed!');
    console.log('🧠 The system is ready for frontend integration!');

  } catch (error) {
    console.error('\n❌ Error during testing:', error.message);
    console.log('\n💡 Make sure the API is running:');
    console.log('   cd backend-chatbot-test/api');
    console.log('   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000');
  }
}

// Run the test
testMultiAgentAPI();