"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useRef, useState, useMemo } from "react";
import { getFloatLocations, getFloatDetails, ArgoFloat, MeasurementPoint, FloatLocation } from '../lib/argo-data';
import { mockFloatLocations } from '../lib/mock-data';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Line, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from "recharts";
import { ChartConfig, ChartContainer, ChartTooltip } from "@/components/ui/chart";
import { generateFloatInsights } from "@/ai/flows/float-insights";
import { Skeleton } from "./ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs";
import { Button } from "./ui/button";
import { Label } from "@/components/ui/label";

// Fix for Leaflet default markers in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// --- Icon Definitions ---
const defaultIcon = L.divIcon({
  className: "pulsating-dot-container",
  html: '<div class="pulsating-dot"></div>',
  iconSize: [12, 12],
  iconAnchor: [6, 6]
});

const highlightedIcon = L.divIcon({
  className: "pulsating-dot-container",
  html: '<div class="pulsating-dot" style="background-color: hsl(var(--chart-2));"></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const primaryCompareIcon = L.divIcon({
  className: "pulsating-dot-container",
  html: '<div class="pulsating-dot" style="background-color: hsl(var(--chart-1));"></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const compareIcon = L.divIcon({
  className: "pulsating-dot-container",
  html: '<div class="pulsating-dot" style="background-color: hsl(var(--chart-5));"></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

// --- Chart Configuration ---
const chartConfig = {
  temperature: { label: "Temp (°C)", color: "hsl(var(--chart-1))" },
  salinity: { label: "Salinity (PSS)", color: "hsl(var(--chart-2))" },
  pressure: { label: "Pressure (dbar)", color: "hsl(var(--chart-3))" },
} satisfies ChartConfig;

type ChartVariable = keyof typeof chartConfig;
type ChartXAxis = "time" | "latitude" | "longitude";

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
    return (
      <div className="p-2 text-sm bg-background/90 border rounded-lg shadow-lg">
        <p className="text-muted-foreground">{new Date(dataPoint.date).toLocaleString()}</p>
        <p className="text-muted-foreground">Lat: {dataPoint.latitude?.toFixed(4)}°</p>
        <p className="text-muted-foreground mb-2">Lon: {dataPoint.longitude?.toFixed(4)}°</p>
        {payload.map((lineData: any) => (
          lineData.value != null &&
          <p key={lineData.dataKey} className="font-medium" style={{ color: lineData.color }}>
            {lineData.name}: {lineData.value?.toFixed(2)}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// --- Main Component ---
export function MapVisualization() {
  const [popupData, setPopupData] = useState<Map<string, ArgoFloat>>(new Map());
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());
  const [isMapInitialized, setIsMapInitialized] = useState(false);

  const [argoFloatLocations, setArgoFloatLocations] = useState<FloatLocation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedFloat, setSelectedFloat] = useState<ArgoFloat | null>(null);
  const [selectedFloatB, setSelectedFloatB] = useState<ArgoFloat | null>(null);
  const [isCompareMode, setIsCompareMode] = useState(false);
  const [isLoadingDetailsB, setIsLoadingDetailsB] = useState(false);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);

  const [insights, setInsights] = useState<string | null>(null);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);

  const [activeVariable, setActiveVariable] = useState<ChartVariable>("temperature");
  const [activeXAxis, setActiveXAxis] = useState<ChartXAxis>("time");

  // --- Data Fetching ---
  useEffect(() => {
    console.log('🌊 Starting to fetch float locations...');
    getFloatLocations()
      .then(data => {
        console.log('🌊 Received float data:', data);
        if (data && data.length > 0) {
          console.log('✅ Successfully loaded', data.length, 'float locations');
          setArgoFloatLocations(data);
        } else {
          console.log('❌ No float locations received');
          setError("No float locations received from API.");
        }
      })
      .catch(e => {
        console.error('❌ Error fetching float locations:', e);
        setError(`Failed to load float locations: ${e.message}`);
      })
      .finally(() => {
        console.log('🏁 Float locations fetch completed');
        setIsLoading(false);
      });
  }, []);


  useEffect(() => {
    console.log('🚀 Map initialization starting...');

    const initMap = () => {
      if (!mapRef.current) {
        console.log('❌ mapRef not available yet');
        return false;
      }

      if (mapInstance.current) {
        console.log('✅ Map already initialized');
        return true;
      }

      console.log('📐 Container dimensions:', {
        width: mapRef.current.offsetWidth,
        height: mapRef.current.offsetHeight
      });

      // If container has no size, return false to retry
      if (mapRef.current.offsetWidth === 0 || mapRef.current.offsetHeight === 0) {
        console.log('📦 Container has zero dimensions');
        return false;
      }

      try {
        console.log('🗺️ Creating Leaflet map...');

        const map = L.map(mapRef.current, {
          center: [5, 78],
          zoom: 4,
          zoomControl: true
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
          subdomains: 'abcd',
          maxZoom: 20
        }).addTo(map);

        mapInstance.current = map;
        setIsMapInitialized(true);

        console.log('✅ Map initialized successfully!');

        // Force resize after a short delay
        setTimeout(() => {
          map.invalidateSize();
          console.log('📏 Map size invalidated');
        }, 100);

        return true;
      } catch (error) {
        console.error('❌ Error initializing map:', error);
        return false;
      }
    };

    // Try to initialize immediately
    if (!initMap()) {
      console.log('⏳ Initialization failed, setting up retry...');

      // Retry every 200ms until successful or max retries reached
      const retryInterval = setInterval(() => {
        console.log('🔄 Retrying map initialization...');
        if (initMap()) {
          clearInterval(retryInterval);
          console.log('🎯 Retry successful!');
        }
      }, 200);

      // Stop retrying after 5 seconds
      setTimeout(() => {
        clearInterval(retryInterval);
        console.log('⏰ Retry timeout reached');
      }, 5000);

      return () => {
        clearInterval(retryInterval);
      };
    }

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
        setIsMapInitialized(false);
      }
    };
  }, []);

  // --- Add this temporary debug effect ---
  useEffect(() => {
    console.log('🔍 COMPONENT MOUNT STATUS:', {
      hasMapRef: !!mapRef.current,
      mapRefCurrent: mapRef.current,
      isMapInitialized,
      mapInstance: !!mapInstance.current
    });

    // Check dimensions multiple times to see progression
    const checkDims = () => {
      if (mapRef.current) {
        console.log('📏 CURRENT DIMENSIONS:', {
          offsetWidth: mapRef.current.offsetWidth,
          offsetHeight: mapRef.current.offsetHeight,
          clientWidth: mapRef.current.clientWidth,
          clientHeight: mapRef.current.clientHeight,
          scrollWidth: mapRef.current.scrollWidth,
          scrollHeight: mapRef.current.scrollHeight,
          // Check CSS styles
          display: window.getComputedStyle(mapRef.current).display,
          position: window.getComputedStyle(mapRef.current).position,
          visibility: window.getComputedStyle(mapRef.current).visibility
        });
      }
    };

    checkDims();
    const timer1 = setTimeout(checkDims, 100);
    const timer2 = setTimeout(checkDims, 500);
    const timer3 = setTimeout(checkDims, 1000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  // --- Debug useEffect (REPLACE your current one) ---
  useEffect(() => {
    console.log('🔍 Map debug status:', {
      hasMapRef: !!mapRef.current,
      isMapInitialized,
      mapInstance: !!mapInstance.current,
      containerSize: mapRef.current ? {
        offsetWidth: mapRef.current.offsetWidth,
        offsetHeight: mapRef.current.offsetHeight,
        clientWidth: mapRef.current.clientWidth,
        clientHeight: mapRef.current.clientHeight
      } : 'no ref'
    });
  }, [isMapInitialized, mapRef.current]); // Added mapRef.current to dependencies

  // --- Update Markers ---
  // --- Update Markers ---
  // --- Update Markers ---
useEffect(() => {
    if (!mapInstance.current || !isMapInitialized || argoFloatLocations.length === 0) {
        return;
    }

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current.clear();

    const isAlreadySelectedForCompare = (floatId: string) => {
        return (selectedFloat?.id === floatId) || (selectedFloatB?.id === floatId);
    };

    // Add new markers with proper click handling and dynamic popups
    argoFloatLocations.forEach(float => {
        // Use createPopupContent with undefined to get the initial "Loading" state
        const popupContent = createPopupContent(float, undefined);
        
        const marker = L.marker([float.latitude, float.longitude], { icon: defaultIcon })
            .addTo(mapInstance.current!)
            .bindPopup(popupContent);

        marker.on('click', (e) => {
            e.originalEvent?.stopPropagation();
            
            // Scenario 1: We are in Compare Mode
            if (isCompareMode) {
                // If the clicked float is ALREADY part of the comparison, update the popup and stop.
                if (isAlreadySelectedForCompare(float.id)) {
                    const floatDetails = (selectedFloat?.id === float.id) ? selectedFloat : selectedFloatB;
                    if (floatDetails && marker) {
                        marker.setPopupContent(createPopupContent(float, floatDetails));
                        marker.openPopup();
                    }
                    return; // Stop here. No reload needed.
                }
                // If it's a new, unselected float, select it as the second float.
                handleSelectFloatB(float.id);
            }
            // Scenario 2: We are NOT in Compare Mode
            else {
                handleSelectFloat(float.id);
            }
        });

        markersRef.current.set(float.id, marker);
    });

    // Update highlights
    if (selectedFloat) {
        const marker = markersRef.current.get(selectedFloat.id);
        if (marker) {
            marker.setIcon(isCompareMode ? primaryCompareIcon : highlightedIcon);
            // Also update the popup content to show the active dashboard details
            marker.setPopupContent(createPopupContent(selectedFloat, selectedFloat));
        }
    }

    if (isCompareMode && selectedFloatB) {
        const marker = markersRef.current.get(selectedFloatB.id);
        if (marker) {
            marker.setIcon(compareIcon);
            // Also update the popup content for the second float
            marker.setPopupContent(createPopupContent(selectedFloatB, selectedFloatB));
        }
    }
}, [argoFloatLocations, selectedFloat, selectedFloatB, isCompareMode, isMapInitialized]);

  // Add this debug effect
  useEffect(() => {
    console.log('Current state:', {
      selectedFloat: selectedFloat?.id,
      isLoadingDetails,
      isLoadingInsights,
      markersCount: markersRef.current.size
    });
  }, [selectedFloat, isLoadingDetails, isLoadingInsights]);

  const createPopupContent = (float: FloatLocation, details?: ArgoFloat) => {
    const getLatestValue = (points: MeasurementPoint[] = []) => {
        if (!details || points.length === 0) return "N/A";
        const latest = points[points.length - 1];
        return latest.value ? latest.value.toFixed(2) : "N/A";
    };

    const dashboardStatus = details ?
        `<p class="text-xs text-green-600 font-medium mt-2">✓ Dashboard active</p>` :
        `<p class="text-sm text-blue-600 mt-2">Loading dashboard...</p>`;

    return `
        <div class="space-y-2 min-w-[220px] p-3">
            <h3 class="font-bold text-lg border-b pb-2">Float ${float.id}</h3>
            <p><strong>Position:</strong> ${float.latitude.toFixed(4)}°N, ${float.longitude.toFixed(4)}°E</p>
            <p><strong>Last Reported:</strong> ${new Date(float.lastReported).toLocaleDateString()}</p>
            <p><strong>Temp:</strong> ${getLatestValue(details?.temperature)}°C</p>
            <p><strong>Salinity:</strong> ${getLatestValue(details?.salinity)} PSS</p>
            <p><strong>Pressure:</strong> ${getLatestValue(details?.pressure)} dbar</p>
            ${dashboardStatus}
        </div>
    `;
};
  // Helper function to get latest measurement value
  const getLatestValue = (points: MeasurementPoint[]) => {
    if (!points || points.length === 0) return "N/A";
    const latest = points[points.length - 1];
    return latest.value ? latest.value.toFixed(2) : "N/A";
  };

  // --- Data Processing for Charts ---
  const chartData = useMemo(() => {
    if (!selectedFloat) return [];

    const downsample = (data: MeasurementPoint[]) => {
      const MAX_POINTS = 400;
      if (data.length <= MAX_POINTS) return data;
      const interval = Math.floor(data.length / MAX_POINTS);
      return data.filter((_, i) => i % interval === 0);
    };

    const dataA = selectedFloat[activeVariable] || [];
    if (!isCompareMode || !selectedFloatB) {
      return downsample(dataA).map(p => ({ ...p, valueA: p.value }));
    }

    const dataB = selectedFloatB[activeVariable] || [];
    const sampledA = downsample(dataA);
    const sampledB = downsample(dataB);
    const xAxisKey = activeXAxis === 'time' ? 'date' : activeXAxis;
    const dataMap = new Map();

    sampledA.forEach(p => dataMap.set(p[xAxisKey as keyof MeasurementPoint], { ...p, valueA: p.value }));
    sampledB.forEach(p => {
      const key = p[xAxisKey as keyof MeasurementPoint];
      const existing = dataMap.get(key) || { date: p.date, latitude: p.latitude, longitude: p.longitude, [xAxisKey]: key };
      dataMap.set(key, { ...existing, valueB: p.value });
    });

    const combined = Array.from(dataMap.values());
    if (xAxisKey === 'date') {
      return combined.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }
    return combined.sort((a, b) => (a[xAxisKey] ?? 0) - (b[xAxisKey] ?? 0));
  }, [selectedFloat, selectedFloatB, isCompareMode, activeVariable, activeXAxis]);

  const yAxisDomain = useMemo(() => {
    const allValues = chartData.flatMap(p => [p.valueA, p.valueB]).filter(v => v != null) as number[];
    if (allValues.length === 0) return [0, 10];

    const minVal = Math.min(...allValues);
    const maxVal = Math.max(...allValues);

    if (maxVal - minVal < 1) {
      if (minVal < 5) return [0, 10];
      const padding = minVal * 0.1;
      return [Math.floor(minVal - padding), Math.ceil(maxVal + padding)];
    }

    const padding = (maxVal - minVal) * 0.1;
    return [Math.floor(minVal - padding), Math.ceil(maxVal + padding)];
  }, [chartData]);

  // --- Handler Functions ---
  const handleSelectFloat = async (floatId: string) => {
    // 1. Check if the float is already selected and we are NOT in compare mode.
    // This check must happen before any state is cleared.
    if (selectedFloat?.id === floatId && !isCompareMode) {
      // The data is already loaded and displayed.
      // We can immediately update the popup to show "Dashboard active" without re-loading.
      const marker = markersRef.current.get(floatId);
      if (marker) {
        const floatLocation = argoFloatLocations.find(f => f.id === floatId);
        if (floatLocation) {
          const updatedPopupContent = `
                    <div class="space-y-2 min-w-[220px] p-3">
                      <h3 class="font-bold text-lg border-b pb-2">Float ${floatLocation.id}</h3>
                      <p><strong>Position:</strong> ${floatLocation.latitude.toFixed(4)}°N, ${floatLocation.longitude.toFixed(4)}°E</p>
                      <p><strong>Last Reported:</strong> ${new Date(floatLocation.lastReported).toLocaleDateString()}</p>
                      <p class="text-xs text-green-600 font-medium mt-2">✓ Dashboard active</p>
                    </div>
                `;
          marker.setPopupContent(updatedPopupContent);
        }
      }
      return; // Exit the function immediately.
    }

    // 2. If it's a new selection, proceed with the loading sequence.
    // setIsCompareMode(false);
    setSelectedFloatB(null);
    setIsLoadingDetails(true);
    setInsights(null);
    setSelectedFloat(null);

    try {
      const newFloatDetails = await getFloatDetails(floatId);
      setSelectedFloat(newFloatDetails);
      setIsLoadingDetails(false);

      if (newFloatDetails && mapInstance.current) {
        mapInstance.current.setView([newFloatDetails.latitude, newFloatDetails.longitude], 6);

        setIsLoadingInsights(true);
        const insightInput = {
          id: newFloatDetails.id,
          lastReported: newFloatDetails.lastReported,
          latitude: newFloatDetails.latitude,
          longitude: newFloatDetails.longitude,
          temperature: newFloatDetails.temperature.at(-1)?.value ?? 0,
          salinity: newFloatDetails.salinity.at(-1)?.value ?? 0,
          pressure: newFloatDetails.pressure.at(-1)?.value ?? 0
        };
        generateFloatInsights({ floatData: insightInput })
          .then(result => {
            setInsights(result.insights);
          })
          .catch(error => {
            console.error("Error fetching insights:", error);
            setInsights("Analysis unavailable");
          })
          .finally(() => {
            setIsLoadingInsights(false);
          });
      }
    } catch (error) {
      console.error("Error loading float details:", error);
      setError("Failed to load float details.");
      setInsights("Failed to load data");
      setIsLoadingDetails(false);
      setIsLoadingInsights(false);
    }
  };

  const handleSelectFloatB = async (floatId: string) => {
    if (selectedFloatB?.id === floatId) return;

    // Set loading state to true
    setIsLoadingDetailsB(true);

    try {
      const newFloatBDetails = await getFloatDetails(floatId);
      setSelectedFloatB(newFloatBDetails);

      if (selectedFloat && newFloatBDetails && mapInstance.current) {
        const markerA = markersRef.current.get(selectedFloat.id);
        const markerB = markersRef.current.get(newFloatBDetails.id);

        if (markerA && markerB) {
          const group = L.featureGroup([markerA, markerB]);
          mapInstance.current.fitBounds(group.getBounds(), { padding: [50, 50] });
        }
      }
    } catch (error) {
      console.error("Error loading float B details:", error);
    } finally {
      // Set loading state to false, regardless of success or failure
      setIsLoadingDetailsB(false);
    }
  };

  // --- Chart Rendering Function ---
  const renderTrajectoryChart = () => (
    <ChartContainer config={chartConfig} className="h-60 w-full">
      <LineChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey={activeXAxis === 'time' ? 'date' : activeXAxis}
          type={activeXAxis === 'time' ? 'category' : 'number'}
          allowDuplicatedCategory={false}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          tickFormatter={(v) => activeXAxis === 'time' ? new Date(v).toLocaleDateString([], { month: 'short', day: 'numeric' }) : `${Number(v).toFixed(1)}°`}
        />
        <YAxis
          domain={yAxisDomain}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          width={40}
        />
        <Tooltip content={<CustomTooltip />} />
        {isCompareMode && <Legend />}
        <Line
          dataKey="valueA"
          name={`A: ${selectedFloat?.id ?? ''}`}
          type="monotone"
          stroke={chartConfig[activeVariable].color}
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        {isCompareMode && selectedFloatB && (
          <Line
            dataKey="valueB"
            name={`B: ${selectedFloatB.id ?? ''}`}
            type="monotone"
            stroke="hsl(var(--chart-5))"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        )}
      </LineChart>
    </ChartContainer>
  );

  // --- Render ---
  if (isLoading) {
    return <div className="flex items-center justify-center h-screen w-full">Loading map...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-screen w-full text-red-500">{error}</div>;
  }

  return (
    <div className="flex h-screen w-full flex-col md:flex-row min-h-0"> {/* Added min-h-0 */}
      <aside className="w-full max-w-sm flex-shrink-0 border-r bg-card text-card-foreground">
        {/* CHANGE 1: Make the Card a vertical flex container */}
        <Card className="flex h-full flex-col rounded-none border-none shadow-none">
          <CardHeader>
            <CardTitle>Float Dashboard</CardTitle>
            <CardDescription>Select a float to view its data.</CardDescription>
          </CardHeader>

          {/* CHANGE 2: Make the CardContent scrollable */}
          <CardContent className="flex-1 space-y-4 overflow-y-auto p-4">
            <Select onValueChange={handleSelectFloat} value={selectedFloat?.id ?? ""}>
              <SelectTrigger>
                <SelectValue placeholder="Select an Argo Float" />
              </SelectTrigger>
              <SelectContent>
                {argoFloatLocations.map(f => (
                  <SelectItem key={f.id} value={f.id}>{f.id}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {isCompareMode && selectedFloat && (
              <div className="p-3 border bg-muted rounded-lg space-y-3">
                <div className="flex justify-between items-center">
                  <p className="text-sm font-medium">Comparing: {selectedFloat?.id}</p>
                  <Button variant="ghost" size="sm" onClick={() => { setIsCompareMode(false); setSelectedFloatB(null); }}>
                    Exit
                  </Button>
                </div>
                <Select onValueChange={handleSelectFloatB} value={selectedFloatB?.id ?? ""}>
                  <SelectTrigger className="bg-background">
                    <SelectValue placeholder="Select Float B" />
                  </SelectTrigger>
                  <SelectContent>
                    {argoFloatLocations.filter(f => f.id !== selectedFloat?.id).map(f => (
                      <SelectItem key={f.id} value={f.id}>{f.id}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* The main conditional rendering logic starts here */}
            {isLoadingDetails || (isCompareMode && isLoadingDetailsB) ? (
              <div className="space-y-4 pt-4">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  <span className="text-sm text-gray-600">Loading float data...</span>
                </div>
                <Skeleton className="h-48 w-full" />
              </div>
            ) : selectedFloat ? (
              <div className="space-y-6 pt-4">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-lg">Trajectory Charts</h3>
                    {!isCompareMode && (
                      <Button variant="outline" size="sm" onClick={() => setIsCompareMode(true)}>
                        Compare
                      </Button>
                    )}
                  </div>
                  <>
                    <div className="space-y-1.5">
                      <Label>Variable</Label>
                      <Tabs value={activeVariable} onValueChange={(v) => setActiveVariable(v as ChartVariable)}>
                        <TabsList className="grid w-full grid-cols-3">
                          <TabsTrigger value="temperature">Temp</TabsTrigger>
                          <TabsTrigger value="salinity">Salinity</TabsTrigger>
                          <TabsTrigger value="pressure">Pressure</TabsTrigger>
                        </TabsList>
                      </Tabs>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Plot Against</Label>
                      <div className="flex items-center justify-between gap-2">
                        {(['time', 'latitude', 'longitude'] as ChartXAxis[]).map(axis => (
                          <Button key={axis} variant={activeXAxis === axis ? "secondary" : "ghost"} size="sm" className="flex-1 capitalize" onClick={() => setActiveXAxis(axis)}>
                            {axis}
                          </Button>
                        ))}
                      </div>
                    </div>
                    <div className="pt-2">
                      {renderTrajectoryChart()}
                    </div>
                  </>
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">AI Insights</h3>
                  {isLoadingInsights ? (
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500"></div>
                        <span className="text-sm text-gray-600">Analyzing data...</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">{insights}</p>
                  )}
                </div>
              </div>
            ) : (
              !isLoading && (
                <div className="text-center text-muted-foreground pt-10">
                  Select a float to view its detailed data.
                </div>
              )
            )}
          </CardContent>
        </Card>
      </aside>

      <div className="relative flex-1">
        <div ref={mapRef} className="h-full w-full" />
        {!isMapInitialized && (
          <div className="absolute inset-0 flex items-center justify-center bg-muted">
            <p className="text-muted-foreground">Loading map...</p>
          </div>
        )}
      </div>
    </div>
  );
}