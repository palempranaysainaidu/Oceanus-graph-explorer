// Simple test script to check API connectivity
async function testAPI() {
    try {
        console.log('Testing API connection...');
        
        // Test the floats endpoint
        const response = await fetch('http://127.0.0.1:8000/api/floats');
        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API Response:', data);
        console.log('Number of floats:', data.length);
        
        if (data.length > 0) {
            console.log('Sample float:', data[0]);
        }
        
    } catch (error) {
        console.error('API Test Error:', error);
    }
}

testAPI();