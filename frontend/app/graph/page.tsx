"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Loader2, AlertCircle, RefreshCcw } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_MAPS_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// Dynamically load Leaflet map component without SSR
const Map = dynamic(() => import("@/components/Map").then((mod) => mod.Map), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-100 animate-pulse rounded-md flex items-center justify-center">
      <Loader2 className="animate-spin text-slate-400 w-8 h-8" />
    </div>
  ),
});

interface FloatItem {
  float_id: string;
}

interface Stats {
  min_temp: number;
  max_temp: number;
  avg_temp: number;
  min_psal: number;
  max_psal: number;
  avg_psal: number;
}

interface HistoryItem {
  cycle_number: string;
  time: string;
  latitude: number;
  longitude: number;
  temperature: number;
  salinity: number;
  pressure: number;
}

export default function GraphExplorerPage() {
  const [floats, setFloats] = useState<FloatItem[]>([]);
  const [loadingFloats, setLoadingFloats] = useState(true);
  const [floatsError, setFloatsError] = useState("");

  const [selectedFloat, setSelectedFloat] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  const safeErrorMessage = (err: unknown): string => {
    if (err instanceof Error) return err.message;
    if (typeof err === "string") return err;
    if (err && typeof (err as { message?: string }).message === "string")
      return (err as { message: string }).message;
    try {
      return JSON.stringify(err);
    } catch {
      return "Unknown error";
    }
  };

  const fetchFloats = async () => {
    setLoadingFloats(true);
    setFloatsError("");
    try {
      const res = await fetch(`${API_URL}/api/graph/floats`);
      if (!res.ok) throw new Error(`Failed to fetch floats (${res.status})`);
      const data = await res.json();
      setFloats(data);
    } catch (err) {
      setFloatsError(safeErrorMessage(err) || "Unable to reach backend");
    } finally {
      setLoadingFloats(false);
    }
  };

  useEffect(() => {
    fetchFloats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectFloat = async (id: string) => {
    setSelectedFloat(id);
    setLoadingDetails(true);
    setDetailsError("");
    setHistory([]);
    setStats(null);
    try {
      const [histRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/api/graph/floats/${id}/history`),
        fetch(`${API_URL}/api/graph/floats/${id}/stats`),
      ]);
      if (!histRes.ok || !statsRes.ok)
        throw new Error("Failed to fetch float details");
      const histData = await histRes.json();
      const statsData = await statsRes.json();
      setHistory(histData);
      setStats(statsData);
    } catch (err) {
      setDetailsError(
        safeErrorMessage(err) || "Failed to load float details"
      );
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-slate-50 overflow-hidden text-slate-900">
      {/* Sidebar */}
      <div className="w-72 bg-white border-r flex flex-col shadow-sm z-10">
        <div className="p-4 border-b bg-slate-50 flex items-center justify-between">
          <h2 className="font-semibold text-lg">Argo Floats</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={fetchFloats}
            disabled={loadingFloats}
          >
            <RefreshCcw
              className={`w-4 h-4 ${loadingFloats ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
        <ScrollArea className="flex-1">
          {loadingFloats ? (
            <div className="p-8 flex justify-center text-slate-400">
              <Loader2 className="animate-spin w-6 h-6" />
            </div>
          ) : floatsError ? (
            <div className="p-4 text-center">
              <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
              <p className="text-sm text-red-600 mb-4">{floatsError}</p>
              <Button size="sm" variant="outline" onClick={fetchFloats}>
                Retry
              </Button>
            </div>
          ) : floats.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">
              No floats found.
            </div>
          ) : (
            <ul className="p-2 space-y-1">
              {floats.map((f) => (
                <li key={f.float_id}>
                  <button
                    onClick={() => selectFloat(f.float_id)}
                    className={`w-full text-left px-4 py-3 rounded-md text-sm transition-colors ${
                      selectedFloat === f.float_id
                        ? "bg-blue-100 text-blue-900 font-medium"
                        : "hover:bg-slate-100 text-slate-700"
                    }`}
                  >
                    Float #{f.float_id}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </ScrollArea>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col">
        {!selectedFloat ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <span className="text-3xl">🌊</span>
            </div>
            <h3 className="text-xl font-medium text-slate-600">
              Select a Float
            </h3>
            <p className="text-sm mt-2">
              Choose a float from the sidebar to view its journey map and
              measurement statistics.
            </p>
          </div>
        ) : loadingDetails ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        ) : detailsError ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-lg text-slate-800 mb-4">{detailsError}</p>
            <Button onClick={() => selectFloat(selectedFloat!)}>
              Try Again
            </Button>
          </div>
        ) : (
          <div className="flex-1 flex flex-col p-6 gap-6 overflow-y-auto">
            {/* Header / Stats */}
            <div>
              <h1 className="text-2xl font-bold mb-4">
                Float Journey: {selectedFloat}
              </h1>
              {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardHeader className="pb-2 pt-4 px-4">
                      <CardTitle className="text-xs text-slate-500 uppercase tracking-wider">
                        Avg Temp
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4">
                      <div className="text-2xl font-semibold text-orange-500">
                        {stats.avg_temp.toFixed(2)}°C
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2 pt-4 px-4">
                      <CardTitle className="text-xs text-slate-500 uppercase tracking-wider">
                        Temp Range
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4">
                      <div className="text-lg font-semibold text-orange-400">
                        {stats.min_temp?.toFixed(1) ?? "–"}° – {stats.max_temp?.toFixed(1) ?? "–"}°C
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2 pt-4 px-4">
                      <CardTitle className="text-xs text-slate-500 uppercase tracking-wider">
                        Avg Salinity
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4">
                      <div className="text-2xl font-semibold text-blue-500">
                        {stats.avg_psal.toFixed(2)} PSU
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2 pt-4 px-4">
                      <CardTitle className="text-xs text-slate-500 uppercase tracking-wider">
                        Salinity Range
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4">
                      <div className="text-lg font-semibold text-blue-400">
                        {stats.min_psal?.toFixed(1) ?? "–"} – {stats.max_psal?.toFixed(1) ?? "–"} PSU
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>

            {/* Map and Table */}
            <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-[400px]">
              {/* Map */}
              <div className="flex-1 rounded-xl overflow-hidden border shadow-sm min-h-[300px]">
                <Map
                  points={history.map((h) => ({
                    lat: h.latitude,
                    lng: h.longitude,
                    popup: `Cycle ${h.cycle_number}<br/>Date: ${h.time.substring(0, 10)}`,
                  }))}
                  type="polyline"
                />
              </div>

              {/* History Table */}
              <div className="w-full lg:w-96 flex flex-col rounded-xl overflow-hidden border shadow-sm bg-white">
                <div className="p-3 bg-slate-100 border-b font-semibold text-sm text-slate-700">
                  Chronological Readings ({history.length})
                </div>
                <ScrollArea className="flex-1 p-0">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-500 sticky top-0 border-b shadow-sm">
                      <tr>
                        <th className="px-3 py-2 font-medium">Cycle</th>
                        <th className="px-3 py-2 font-medium">Date</th>
                        <th className="px-3 py-2 font-medium">Temp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {history.map((h) => (
                        <tr
                          key={h.cycle_number}
                          className="hover:bg-slate-50"
                        >
                          <td className="px-3 py-2">{h.cycle_number}</td>
                          <td className="px-3 py-2 text-slate-600">
                            {h.time.substring(0, 10)}
                          </td>
                          <td className="px-3 py-2 font-medium text-slate-800">
                            {h.temperature.toFixed(2)}°
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </ScrollArea>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
