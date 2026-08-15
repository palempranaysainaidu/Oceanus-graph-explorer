/**
 * Graph explorer API client — CognoDB knowledge graph endpoints.
 */

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function graphFetch<T>(path: string): Promise<T> {
  const url = typeof window !== "undefined" ? path : `${BACKEND}${path}`;
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Graph API error ${res.status}`);
  }
  return res.json();
}

export interface GraphHealth {
  status: string;
  connected: boolean;
  uri?: string;
  message?: string;
}

export interface RegionSummary {
  name: string;
  float_count: number;
  subregions: string[];
}

export interface FloatSummary {
  platform_number: string;
  latitude?: number;
  longitude?: number;
}

export interface FloatGraphDetail {
  platform_number: string;
  latitude?: number;
  longitude?: number;
  region?: string;
  neighbors: string[];
  cruises: Array<{ cruise_id: string; cycle_number: number; time: string }>;
  parameters: Array<{ parameter: string; measurement_count: number }>;
}

export interface GraphStats {
  node_counts: Record<string, number>;
  relationship_counts: Record<string, number>;
  connected: boolean;
}

export async function getGraphHealth(): Promise<GraphHealth> {
  return graphFetch<GraphHealth>("/api/graph/health");
}

export async function getGraphStats(): Promise<GraphStats> {
  return graphFetch<GraphStats>("/api/graph/stats");
}

export async function getRegions(): Promise<{ regions: RegionSummary[]; count: number }> {
  return graphFetch("/api/graph/regions");
}

export async function getRegionFloats(region: string): Promise<{
  region: string;
  floats: FloatSummary[];
  count: number;
}> {
  return graphFetch(`/api/graph/regions/${encodeURIComponent(region)}/floats`);
}

export async function getFloatGraph(id: string): Promise<FloatGraphDetail> {
  return graphFetch(`/api/graph/floats/${encodeURIComponent(id)}`);
}

export async function getShortestPath(floatA: string, floatB: string) {
  return graphFetch(
    `/api/graph/query/shortest-path?float_a=${encodeURIComponent(floatA)}&float_b=${encodeURIComponent(floatB)}`
  );
}

export async function getSimilarPatterns(floatId: string) {
  return graphFetch(`/api/graph/query/similar-patterns/${encodeURIComponent(floatId)}`);
}
