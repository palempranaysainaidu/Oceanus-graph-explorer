

// NEW: A simple type for the initial list of floats returned by /api/floats
export interface FloatLocation {
  id: string;
  latitude: number;
  longitude: number;
  lastReported: string;
}

// This is the full data type for a single float's details from /api/float/{id}
export interface MeasurementPoint {
  date: string;
  value: number | null;
  latitude: number;
  longitude: number;
}
export interface ArgoFloat {
  id: string;
  lastReported: string;
  latitude: number;
  longitude: number;
  temperature: MeasurementPoint[];
  salinity: MeasurementPoint[];
  pressure: MeasurementPoint[];
}

const MAPS_BACKEND_URL = process.env.NEXT_PUBLIC_MAPS_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// Function #1: Fetches the lightweight list of all float locations
export async function getFloatLocations(): Promise<FloatLocation[]> {
  try {
    const url = typeof window !== 'undefined' ? '/api/floats' : `${MAPS_BACKEND_URL}/api/floats`;
    console.log('🔗 Attempting to fetch floats from:', url);
    const response = await fetch(url);
    console.log('📡 Response received:', response.status, response.statusText);
    
    if (!response.ok) {
      throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('📊 Data parsed successfully:', data.length, 'floats');
    return data;
  } catch (error) {
    console.error("❌ There was a problem fetching the Argo float locations:", error);
    // Secondary fallback to direct backend URL if proxy failed
    try {
      const fallbackRes = await fetch(`${MAPS_BACKEND_URL}/api/floats`);
      if (fallbackRes.ok) return await fallbackRes.json();
    } catch (e) {
      console.error("❌ Fallback fetch also failed:", e);
    }
    return []; 
  }
}

// Function #2: Fetches the detailed time-series data for ONE float
export async function getFloatDetails(floatId: string): Promise<ArgoFloat | null> {
  try {
    const url = typeof window !== 'undefined' ? `/api/float/${floatId}` : `${MAPS_BACKEND_URL}/api/float/${floatId}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Network response was not ok: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`There was a problem fetching details for float ${floatId}:`, error);
    try {
      const fallbackRes = await fetch(`${MAPS_BACKEND_URL}/api/float/${floatId}`);
      if (fallbackRes.ok) return await fallbackRes.json();
    } catch (e) {
      // ignore fallback error
    }
    return null;
  }
}