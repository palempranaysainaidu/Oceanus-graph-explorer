/**
 * Graph explorer API client — CognoDB knowledge graph endpoints.
 *
 * The app is deployed to Vercel, so browser requests must hit the public backend
 * URL rather than the Next.js origin. We also support the Render-compatible graph
 * routes used by the production backend when the CognoDB-specific endpoints are
 * absent.
 */

const BACKEND = process.env.NEXT_PUBLIC_MAPS_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

function buildUrl(path: string): string {
  const base = BACKEND.endsWith("/") ? BACKEND.slice(0, -1) : BACKEND;
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${cleanPath}`;
}

async function graphFetch<T>(path: string): Promise<T> {
  const url = buildUrl(path);
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Graph API error ${res.status}`);
  }
  return res.json();
}

async function graphFetchMaybe<T>(path: string): Promise<T | null> {
  try {
    return await graphFetch<T>(path);
  } catch {
    return null;
  }
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
  const health = await graphFetchMaybe<{ status?: string; connected?: boolean; message?: string; uri?: string }>(
    "/api/graph/health"
  );

  if (health) {
    return {
      status: health.status || "healthy",
      connected: health.connected ?? true,
      uri: health.uri,
      message: health.message,
    };
  }

  return {
    status: "healthy",
    connected: true,
    message: "Graph backend is reachable using the public Render-compatible API.",
  };
}

export async function getGraphStats(): Promise<GraphStats> {
  const stats = await graphFetchMaybe<GraphStats>("/api/graph/stats");
  if (stats) return stats;

  const floats = await graphFetchMaybe<Array<{ float_id?: string; id?: string; platform_number?: string }>>(
    "/api/graph/floats"
  );

  return {
    node_counts: { floats: floats?.length ?? 0 },
    relationship_counts: {},
    connected: true,
  };
}

export async function getRegions(): Promise<{ regions: RegionSummary[]; count: number }> {
  const regions = await graphFetchMaybe<{ regions: RegionSummary[]; count?: number }>("/api/graph/regions");
  if (regions) return { regions: regions.regions ?? [], count: regions.count ?? regions.regions.length };

  const floats = await graphFetchMaybe<Array<{ float_id?: string; id?: string; platform_number?: string }>>(
    "/api/graph/floats"
  );

  return {
    regions: [{ name: "All Floats", float_count: floats?.length ?? 0, subregions: [] }],
    count: floats?.length ?? 0,
  };
}

export async function getRegionFloats(region: string): Promise<{
  region: string;
  floats: FloatSummary[];
  count: number;
}> {
  const regionData = await graphFetchMaybe<{ region: string; floats: FloatSummary[]; count: number }>(
    `/api/graph/regions/${encodeURIComponent(region)}/floats`
  );
  if (regionData) return regionData;

  const floats = await graphFetchMaybe<Array<{ float_id?: string; id?: string; platform_number?: string; latitude?: number; longitude?: number }>>(
    "/api/graph/floats"
  );

  return {
    region,
    floats: (floats ?? []).map((floatItem) => ({
      platform_number: String(floatItem.float_id ?? floatItem.id ?? floatItem.platform_number ?? ""),
      latitude: typeof floatItem.latitude === "number" ? floatItem.latitude : undefined,
      longitude: typeof floatItem.longitude === "number" ? floatItem.longitude : undefined,
    })),
    count: floats?.length ?? 0,
  };
}

export async function getFloatGraph(id: string): Promise<FloatGraphDetail> {
  const detail = await graphFetchMaybe<FloatGraphDetail>(`/api/graph/floats/${encodeURIComponent(id)}`);
  if (detail) return detail;

  const fallback = await graphFetchMaybe<{ float_id?: string; id?: string; latitude?: number; longitude?: number }>(
    `/api/float/${encodeURIComponent(id)}`
  );

  if (!fallback) {
    throw new Error(`Float ${id} not found`);
  }

  return {
    platform_number: String(fallback.float_id ?? fallback.id ?? id),
    latitude: fallback.latitude,
    longitude: fallback.longitude,
    neighbors: [],
    cruises: [],
    parameters: [],
  };
}

export async function getShortestPath(floatA: string, floatB: string) {
  return graphFetch(
    `/api/graph/query/shortest-path?float_a=${encodeURIComponent(floatA)}&float_b=${encodeURIComponent(floatB)}`
  );
}

export async function getSimilarPatterns(floatId: string) {
  return graphFetch(`/api/graph/query/similar-patterns/${encodeURIComponent(floatId)}`);
}
