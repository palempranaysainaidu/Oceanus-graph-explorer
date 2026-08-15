"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Loader2, AlertCircle, Search } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const Map = dynamic(() => import("@/components/Map").then((mod) => mod.Map), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-100 animate-pulse flex items-center justify-center">
      <Loader2 className="animate-spin text-slate-400 w-8 h-8" />
    </div>
  ),
});

interface SearchResult {
  float_id: string;
  cycle_number: string;
  time: string;
  latitude: number;
  longitude: number;
  temperature: number;
}

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SearchCyclesPage() {
  const [minTemp, setMinTemp] = useState("10");
  const [maxTemp, setMaxTemp] = useState("15");
  const [results, setResults] = useState<SearchResult[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const runSearch = async () => {
    if (!minTemp || !maxTemp) return;

    setLoading(true);
    setError("");
    setHasSearched(true);

    try {
      const res = await fetch(
        `${API_URL}/api/graph/search/cycles?min_temp=${minTemp}&max_temp=${maxTemp}`
      );
      if (!res.ok) throw new Error(`Search failed (${res.status})`);
      const data = await res.json();
      setResults(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to execute search. Check if backend is running.";
      setError(msg);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    runSearch();
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-50 overflow-hidden text-slate-900">
      {/* Control Bar */}
      <div className="bg-white border-b shadow-sm z-10 px-6 py-4">
        <form onSubmit={handleSearch} className="flex items-end gap-4 max-w-4xl mx-auto">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">Min Temperature (°C)</label>
            <Input 
              type="number" 
              step="0.1" 
              value={minTemp} 
              onChange={(e) => setMinTemp(e.target.value)} 
              placeholder="e.g. 10" 
              required 
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">Max Temperature (°C)</label>
            <Input 
              type="number" 
              step="0.1" 
              value={maxTemp} 
              onChange={(e) => setMaxTemp(e.target.value)} 
              placeholder="e.g. 15" 
              required 
            />
          </div>
          <Button type="submit" disabled={loading} className="px-8">
            {loading ? <Loader2 className="animate-spin w-4 h-4 mr-2" /> : <Search className="w-4 h-4 mr-2" />}
            Search Graph
          </Button>
        </form>
      </div>

      {/* Results Area */}
      <div className="flex-1 flex overflow-hidden">
        {!hasSearched && !loading ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8">
            <Search className="w-16 h-16 text-slate-300 mb-4" />
            <h3 className="text-xl font-medium text-slate-600">Search Argo Graph</h3>
            <p className="text-sm mt-2 max-w-md text-center">
              Enter a temperature range above to find all matching measurement cycles across every float in the CognoDB database.
            </p>
          </div>
        ) : loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
              <p className="text-slate-600 font-medium">Querying graph...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-lg text-slate-800 mb-4">{error}</p>
            <Button onClick={runSearch}>Try Again</Button>
          </div>
        ) : results.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4 text-2xl">🧊</div>
            <h3 className="text-xl font-medium text-slate-600">No Cycles Found</h3>
            <p className="text-sm mt-2">There are no measurements in the range {minTemp}°C to {maxTemp}°C.</p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col lg:flex-row w-full h-full">
            {/* Map Area */}
            <div className="flex-1 h-full relative z-0">
              <Map
                type="markers"
                points={results.map((r) => ({
                  lat: r.latitude,
                  lng: r.longitude,
                  popup: `Float: ${r.float_id} <br/> Temp: ${r.temperature.toFixed(2)}°C`,
                }))}
              />
              <div className="absolute top-4 left-4 z-[400] bg-white/90 backdrop-blur px-4 py-2 rounded shadow text-sm font-medium text-slate-700">
                Found {results.length} matching cycles
              </div>
            </div>

            {/* List Area */}
            <div className="w-full lg:w-[450px] border-l bg-white flex flex-col h-full shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] z-10">
              <div className="p-4 border-b bg-slate-50 font-semibold text-slate-700">
                Matching Cycles
              </div>
              <ScrollArea className="flex-1 p-0">
                <table className="w-full text-sm text-left">
                  <thead className="bg-white text-slate-500 sticky top-0 border-b z-20">
                    <tr>
                      <th className="px-4 py-3 font-medium">Float</th>
                      <th className="px-4 py-3 font-medium">Date</th>
                      <th className="px-4 py-3 font-medium">Temp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {results.map((r, i) => (
                      <tr key={`${r.float_id}-${r.cycle_number}-${i}`} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-blue-600">#{r.float_id}</td>
                        <td className="px-4 py-3 text-slate-600">{r.time.substring(0, 10)}</td>
                        <td className="px-4 py-3 font-medium text-slate-800">{r.temperature.toFixed(2)}°</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
