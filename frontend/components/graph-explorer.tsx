"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Database,
  GitBranch,
  Loader2,
  MapPin,
  Network,
  RefreshCw,
  Ship,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  getFloatGraph,
  getGraphHealth,
  getGraphStats,
  getRegionFloats,
  getRegions,
  getShortestPath,
  getSimilarPatterns,
  type FloatGraphDetail,
  type GraphHealth,
  type RegionSummary,
} from "@/lib/graph-api";

type LoadState = "loading" | "ready" | "error" | "empty";

export function GraphExplorer() {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [health, setHealth] = useState<GraphHealth | null>(null);
  const [regions, setRegions] = useState<RegionSummary[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [regionFloats, setRegionFloats] = useState<string[]>([]);
  const [selectedFloat, setSelectedFloat] = useState<string | null>(null);
  const [floatDetail, setFloatDetail] = useState<FloatGraphDetail | null>(null);
  const [pathResult, setPathResult] = useState<Record<string, unknown> | null>(null);
  const [similarResult, setSimilarResult] = useState<Record<string, unknown> | null>(null);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [detailLoading, setDetailLoading] = useState(false);

  const loadOverview = useCallback(async () => {
    setLoadState("loading");
    setErrorMessage("");
    try {
      const h = await getGraphHealth();
      setHealth(h);
      if (!h.connected) {
        setLoadState("error");
        setErrorMessage(
          h.message || "CognoDB is not connected. Add credentials to backend .env and run the seed script."
        );
        return;
      }
      const [regionData, statsData] = await Promise.all([getRegions(), getGraphStats()]);
      setRegions(regionData.regions || []);
      setStats(statsData.node_counts || {});
      if (!regionData.regions?.length) {
        setLoadState("empty");
        setErrorMessage("Graph is connected but empty. Run: python Data_populating/seed_cognodb.py");
        return;
      }
      setLoadState("ready");
    } catch (e) {
      setLoadState("error");
      setErrorMessage(e instanceof Error ? e.message : "Failed to load graph data");
    }
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  const selectRegion = async (name: string) => {
    setSelectedRegion(name);
    setSelectedFloat(null);
    setFloatDetail(null);
    setPathResult(null);
    setSimilarResult(null);
    try {
      const data = await getRegionFloats(name);
      setRegionFloats(
        (data.floats || []).map((f) => f.platform_number).filter(Boolean)
      );
    } catch {
      setRegionFloats([]);
    }
  };

  const selectFloat = async (id: string) => {
    setSelectedFloat(id);
    setDetailLoading(true);
    setPathResult(null);
    setSimilarResult(null);
    try {
      const detail = await getFloatGraph(id);
      setFloatDetail(detail);
    } catch {
      setFloatDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const runPathQuery = async () => {
    if (!selectedFloat || regionFloats.length < 2) return;
    const other = regionFloats.find((f) => f !== selectedFloat);
    if (!other) return;
    try {
      const result = await getShortestPath(selectedFloat, other);
      setPathResult(result);
    } catch (e) {
      setPathResult({ error: e instanceof Error ? e.message : "Path query failed" });
    }
  };

  const runSimilarQuery = async () => {
    if (!selectedFloat) return;
    try {
      const result = await getSimilarPatterns(selectedFloat);
      setSimilarResult(result);
    } catch (e) {
      setSimilarResult({ error: e instanceof Error ? e.message : "Similarity query failed" });
    }
  };

  if (loadState === "loading") {
    return (
      <div className="flex h-full flex-col gap-4 p-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (loadState === "error") {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-lg">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Graph database unavailable</AlertTitle>
          <AlertDescription className="mt-2 space-y-2">
            <p>{errorMessage}</p>
            <Button variant="outline" size="sm" onClick={loadOverview}>
              <RefreshCw className="mr-2 h-4 w-4" /> Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loadState === "empty") {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Alert className="max-w-lg">
          <Database className="h-4 w-4" />
          <AlertTitle>Empty knowledge graph</AlertTitle>
          <AlertDescription className="mt-2 space-y-2">
            <p>{errorMessage}</p>
            <Button variant="outline" size="sm" onClick={loadOverview}>
              <RefreshCw className="mr-2 h-4 w-4" /> Refresh
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden p-4 md:p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Knowledge Graph Explorer</h1>
          <p className="text-sm text-muted-foreground">
            Explore Argo floats, regions, and relationships in CognoDB
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={health?.connected ? "default" : "destructive"}>
            {health?.connected ? "CognoDB connected" : "Disconnected"}
          </Badge>
          <Button variant="ghost" size="icon" onClick={loadOverview}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(stats).slice(0, 4).map(([label, count]) => (
          <Card key={label}>
            <CardHeader className="pb-2">
              <CardDescription>{label} nodes</CardDescription>
              <CardTitle className="text-2xl">{count}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-3">
        {/* Regions */}
        <Card className="lg:col-span-1 flex flex-col min-h-0">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <MapPin className="h-4 w-4" /> Regions
            </CardTitle>
            <CardDescription>Click a region to see floats</CardDescription>
          </CardHeader>
          <CardContent className="min-h-0 flex-1">
            <ScrollArea className="h-[280px] pr-2">
              <div className="space-y-1">
                {regions.map((r) => (
                  <Button
                    key={r.name}
                    variant={selectedRegion === r.name ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => selectRegion(r.name)}
                  >
                    <span className="truncate">{r.name}</span>
                    <Badge variant="outline" className="ml-auto">{r.float_count}</Badge>
                  </Button>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Floats in region */}
        <Card className="lg:col-span-1 flex flex-col min-h-0">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Ship className="h-4 w-4" /> Floats
            </CardTitle>
            <CardDescription>
              {selectedRegion ? `In ${selectedRegion}` : "Select a region"}
            </CardDescription>
          </CardHeader>
          <CardContent className="min-h-0 flex-1">
            {!selectedRegion ? (
              <p className="text-sm text-muted-foreground">Choose a region to list floats.</p>
            ) : regionFloats.length === 0 ? (
              <p className="text-sm text-muted-foreground">No floats in this region.</p>
            ) : (
              <ScrollArea className="h-[280px] pr-2">
                <div className="space-y-1">
                  {regionFloats.map((id) => (
                    <Button
                      key={id}
                      variant={selectedFloat === id ? "secondary" : "ghost"}
                      className="w-full justify-start font-mono text-sm"
                      onClick={() => selectFloat(id)}
                    >
                      {id}
                    </Button>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Float detail + graph queries */}
        <Card className="lg:col-span-1 flex flex-col min-h-0">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Network className="h-4 w-4" /> Relationships
            </CardTitle>
            <CardDescription>
              {selectedFloat ? `Float ${selectedFloat}` : "Select a float"}
            </CardDescription>
          </CardHeader>
          <CardContent className="min-h-0 flex-1">
            {detailLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading graph...
              </div>
            ) : !floatDetail ? (
              <p className="text-sm text-muted-foreground">
                Select a float to view cruises, parameters, and run graph queries.
              </p>
            ) : (
              <ScrollArea className="h-[280px] pr-2">
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Region: </span>
                    {floatDetail.region}
                  </div>
                  <div>
                    <span className="text-muted-foreground">NEAR_FLOAT neighbors: </span>
                    {floatDetail.neighbors?.length
                      ? floatDetail.neighbors.join(", ")
                      : "None within 120 km"}
                  </div>
                  <Separator />
                  <div>
                    <span className="font-medium">Cruises ({floatDetail.cruises?.length || 0})</span>
                    <ul className="mt-1 list-inside list-disc text-muted-foreground">
                      {(floatDetail.cruises || []).slice(0, 5).map((c) => (
                        <li key={c.cruise_id}>{c.cruise_id}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-2">
                    <Button size="sm" variant="outline" onClick={runPathQuery}>
                      <GitBranch className="mr-1 h-3 w-3" /> Shortest path
                    </Button>
                    <Button size="sm" variant="outline" onClick={runSimilarQuery}>
                      Similar patterns
                    </Button>
                  </div>
                  {pathResult && (
                    <Alert>
                      <AlertTitle>Shortest path (NEAR_FLOAT)</AlertTitle>
                      <AlertDescription className="font-mono text-xs">
                        {JSON.stringify(pathResult, null, 2)}
                      </AlertDescription>
                    </Alert>
                  )}
                  {similarResult && (
                    <Alert>
                      <AlertTitle>Overlapping patterns</AlertTitle>
                      <AlertDescription className="font-mono text-xs max-h-32 overflow-auto">
                        {JSON.stringify(similarResult, null, 2)}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
