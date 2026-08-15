"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ReTooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  ReferenceLine,
  Legend,
} from "recharts";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Points, PointMaterial, Text } from "@react-three/drei";
import * as THREE from "three";

export type AdvancedVizSpec = {
  type: "line" | "scatter" | "area" | "bar" | "composed" | "map_points" | "heatmap" | "scatter3d" | "surface3d" | "volume3d";
  title?: string;
  subtitle?: string;
  data: { fields: string[]; rows: any[] };
  encodings: Record<string, string>;
  options?: {
    tooltip?: boolean;
    connectNulls?: boolean;
    animation?: boolean;
    gradient?: boolean;
    theme?: "light" | "dark";
    colors?: string[];
    showLegend?: boolean;
    showGrid?: boolean;
    showAxes?: boolean;
    interactive?: boolean;
  };
  styling?: {
    width?: number;
    height?: number;
    margin?: { top: number; right: number; bottom: number; left: number };
  };
};

export function AdvancedVisualizationRenderer({ spec }: { spec: AdvancedVizSpec }) {
  const [isLoaded, setIsLoaded] = useState(false);
  
  useEffect(() => {
    setIsLoaded(true);
  }, []);

  if (!isLoaded) {
    return <div className="w-full h-64 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-lg" />;
  }

  switch (spec.type) {
    case "line": return <AdvancedLineViz spec={spec} />;
    case "scatter": return <AdvancedScatterViz spec={spec} />;
    case "area": return <AdvancedAreaViz spec={spec} />;
    case "bar": return <AdvancedBarViz spec={spec} />;
    case "composed": return <AdvancedComposedViz spec={spec} />;
    case "map_points": return <AdvancedMapPointsViz spec={spec} />;
    case "heatmap": return <AdvancedHeatmapViz spec={spec} />;
    case "scatter3d": return <AdvancedScatter3DViz spec={spec} />;
    case "surface3d": return <AdvancedSurface3DViz spec={spec} />;
    case "volume3d": return <AdvancedVolume3DViz spec={spec} />;
    default: return null;
  }
}

function AdvancedLineViz({ spec }: { spec: AdvancedVizSpec }) {
  const { x, y } = spec.encodings as { x: string; y: string };
  const data = useMemo(() =>
    spec.data.rows.map((r) => ({ 
      ...r, 
      [x]: r[x], 
      [y]: Number(r[y]),
      formattedX: new Date(r[x]).toLocaleDateString?.() || r[x],
      formattedY: Number(r[y])?.toFixed(3) || r[y]
    })).filter((r) => r[y] != null),
  [spec, x, y]);

  const colors = spec.options?.colors || ["#8884d8", "#82ca9d", "#ffc658", "#ff7300"];
  const height = spec.styling?.height || 400;

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart 
            data={data} 
            margin={spec.styling?.margin || { top: 20, right: 30, left: 20, bottom: 20 }}
          >
            {spec.options?.showGrid !== false && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {spec.options?.showAxes !== false && (
              <>
                <XAxis 
                  dataKey={x} 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
              </>
            )}
            <ReTooltip 
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px",
                color: "#f9fafb"
              }}
              formatter={(value, name) => [typeof value === "number" ? value.toFixed(3) : value, name]}
              labelFormatter={(label) => `Time: ${label}`}
            />
            {spec.options?.showLegend !== false && <Legend />}
            <Line 
              type="monotone" 
              connectNulls={!!spec.options?.connectNulls} 
              dataKey={y} 
              stroke={colors[0]} 
              strokeWidth={3}
              dot={{ fill: colors[0], strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: colors[0], strokeWidth: 2 }}
              animationDuration={spec.options?.animation !== false ? 1000 : 0}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AdvancedScatterViz({ spec }: { spec: AdvancedVizSpec }) {
  const { x, y } = spec.encodings as { x: string; y: string };
  const data = useMemo(() => 
    spec.data.rows.map((r) => ({ 
      x: Number(r[x]), 
      y: Number(r[y]),
      originalData: r
    })).filter((r) => isFinite(r.x) && isFinite(r.y)),
  [spec, x, y]);

  const colors = spec.options?.colors || ["#82ca9d"];
  const height = spec.styling?.height || 400;

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={spec.styling?.margin || { top: 20, right: 30, left: 20, bottom: 20 }}>
            {spec.options?.showGrid !== false && <CartesianGrid stroke="#e5e7eb" />}
            {spec.options?.showAxes !== false && (
              <>
                <XAxis 
                  dataKey="x" 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                  type="number"
                />
                <YAxis 
                  dataKey="y" 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                  type="number"
                />
              </>
            )}
            <ReTooltip 
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px",
                color: "#f9fafb"
              }}
              formatter={(value, name) => [typeof value === "number" ? value.toFixed(3) : value, name]}
            />
            <Scatter 
              data={data} 
              fill={colors[0]}
              stroke={colors[0]}
              strokeWidth={1}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AdvancedAreaViz({ spec }: { spec: AdvancedVizSpec }) {
  const { x, y } = spec.encodings as { x: string; y: string };
  const data = useMemo(() =>
    spec.data.rows.map((r) => ({ 
      ...r, 
      [x]: r[x], 
      [y]: Number(r[y])
    })).filter((r) => r[y] != null),
  [spec, x, y]);

  const colors = spec.options?.colors || ["#8884d8"];
  const height = spec.styling?.height || 400;

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart 
            data={data} 
            margin={spec.styling?.margin || { top: 20, right: 30, left: 20, bottom: 20 }}
          >
            {spec.options?.showGrid !== false && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {spec.options?.showAxes !== false && (
              <>
                <XAxis 
                  dataKey={x} 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
              </>
            )}
            <ReTooltip 
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px",
                color: "#f9fafb"
              }}
              formatter={(value, name) => [typeof value === "number" ? value.toFixed(3) : value, name]}
            />
            <Area 
              type="monotone" 
              dataKey={y} 
              stroke={colors[0]} 
              fill={colors[0]}
              fillOpacity={0.6}
              strokeWidth={2}
              animationDuration={spec.options?.animation !== false ? 1000 : 0}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AdvancedBarViz({ spec }: { spec: AdvancedVizSpec }) {
  const { x, y } = spec.encodings as { x: string; y: string };
  const data = useMemo(() =>
    spec.data.rows.map((r) => ({ 
      ...r, 
      [x]: r[x], 
      [y]: Number(r[y])
    })).filter((r) => r[y] != null),
  [spec, x, y]);

  const colors = spec.options?.colors || ["#8884d8"];
  const height = spec.styling?.height || 400;

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart 
            data={data} 
            margin={spec.styling?.margin || { top: 20, right: 30, left: 20, bottom: 20 }}
          >
            {spec.options?.showGrid !== false && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {spec.options?.showAxes !== false && (
              <>
                <XAxis 
                  dataKey={x} 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
              </>
            )}
            <ReTooltip 
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px",
                color: "#f9fafb"
              }}
              formatter={(value, name) => [typeof value === "number" ? value.toFixed(3) : value, name]}
            />
            <Bar 
              dataKey={y} 
              fill={colors[0]}
              stroke={colors[0]}
              strokeWidth={1}
              animationDuration={spec.options?.animation !== false ? 1000 : 0}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AdvancedComposedViz({ spec }: { spec: AdvancedVizSpec }) {
  const { x, y1, y2 } = spec.encodings as { x: string; y1: string; y2: string };
  const data = useMemo(() =>
    spec.data.rows.map((r) => ({ 
      ...r, 
      [x]: r[x], 
      [y1]: Number(r[y1]),
      [y2]: Number(r[y2])
    })).filter((r) => r[y1] != null && r[y2] != null),
  [spec, x, y1, y2]);

  const colors = spec.options?.colors || ["#8884d8", "#82ca9d"];
  const height = spec.styling?.height || 400;

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart 
            data={data} 
            margin={spec.styling?.margin || { top: 20, right: 30, left: 20, bottom: 20 }}
          >
            {spec.options?.showGrid !== false && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {spec.options?.showAxes !== false && (
              <>
                <XAxis 
                  dataKey={x} 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  axisLine={{ stroke: "#d1d5db" }}
                  tickLine={{ stroke: "#d1d5db" }}
                />
              </>
            )}
            <ReTooltip 
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px",
                color: "#f9fafb"
              }}
              formatter={(value, name) => [typeof value === "number" ? value.toFixed(3) : value, name]}
            />
            <Legend />
            <Bar dataKey={y1} fill={colors[0]} />
            <Line type="monotone" dataKey={y2} stroke={colors[1]} strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AdvancedMapPointsViz({ spec }: { spec: AdvancedVizSpec }) {
  const ref = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !ref.current) return;
    
    // Lazy-load Leaflet
    Promise.all([
      import("leaflet"),
      import("leaflet.heat").catch(() => null)
    ]).then(([L]) => {
      const container = ref.current!;
      container.innerHTML = "";
      
      const map = L.map(container, { 
        center: [0, 0], 
        zoom: 2, 
        worldCopyJump: true,
        zoomControl: true,
        attributionControl: true
      });
      
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { 
        attribution: "© OpenStreetMap contributors",
        maxZoom: 18
      }).addTo(map);
      
      const latKey = spec.encodings.lat;
      const lonKey = spec.encodings.lon;
      const points: [number, number][] = [];
      
      spec.data.rows.forEach((r) => {
        const lat = Number(r[latKey]);
        const lon = Number(r[lonKey]);
        if (isFinite(lat) && isFinite(lon)) {
          points.push([lat, lon]);
          const marker = L.circleMarker([lat, lon], { 
            radius: 4, 
            color: "#0ea5e9",
            fillColor: "#0ea5e9",
            fillOpacity: 0.7,
            weight: 2
          });
          
          if (spec.options?.tooltip) {
            marker.bindTooltip(`${lat.toFixed(3)}, ${lon.toFixed(3)}`, {
              direction: "top",
              offset: [0, -10]
            });
          }
          marker.addTo(map);
        }
      });
      
      if (points.length) {
        map.fitBounds(L.latLngBounds(points as any), { padding: [20, 20] });
      }
      
      setIsLoaded(true);
      
      return () => map.remove();
    });
  }, [spec]);

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="relative">
        <div ref={ref} className="h-96 w-full rounded-md overflow-hidden border border-gray-200 dark:border-gray-700" />
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>
    </div>
  );
}

function AdvancedHeatmapViz({ spec }: { spec: AdvancedVizSpec }) {
  const ref = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !ref.current) return;
    
    Promise.all([
      import("leaflet"),
      import("leaflet.heat").catch(() => null)
    ]).then(([L]) => {
      const container = ref.current!;
      container.innerHTML = "";
      
      const map = L.map(container, { 
        center: [0, 0], 
        zoom: 2, 
        worldCopyJump: true,
        zoomControl: true
      });
      
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { 
        attribution: "© OpenStreetMap contributors"
      }).addTo(map);
      
      const latKey = spec.encodings.lat;
      const lonKey = spec.encodings.lon;
      const valKey = spec.encodings.value;
      const heatData: [number, number, number][] = [];
      
      spec.data.rows.forEach((r) => {
        const lat = Number(r[latKey]);
        const lon = Number(r[lonKey]);
        const val = Number(r[valKey]);
        if (isFinite(lat) && isFinite(lon) && isFinite(val)) {
          heatData.push([lat, lon, val]);
        }
      });
      
      if (heatData.length > 0) {
        map.whenReady(() => {
          try {
            // @ts-ignore - heat plugin augments Leaflet namespace
            L.heatLayer(heatData, { 
              radius: 20, 
              blur: 15, 
              maxZoom: 8,
              gradient: {
                0.4: 'blue',
                0.6: 'cyan',
                0.7: 'lime',
                0.8: 'yellow',
                1.0: 'red'
              }
            }).addTo(map);
            map.fitBounds(L.latLngBounds(heatData.map(([a, b]) => [a, b]) as any), { padding: [20, 20] });
          } catch (error) {
            console.warn("Failed to add heat layer:", error);
          }
        });
      }
      
      setIsLoaded(true);
      
      return () => map.remove();
    });
  }, [spec]);

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="relative">
        <div ref={ref} className="h-96 w-full rounded-md overflow-hidden border border-gray-200 dark:border-gray-700" />
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>
    </div>
  );
}

function AdvancedScatter3DViz({ spec }: { spec: AdvancedVizSpec }) {
  const points = useMemo(() => {
    const { x, y, z } = spec.encodings as { x: string; y: string; z: string };
    return spec.data.rows.slice(0, 5000).map((r) => ({
      x: Number(r[x]),
      y: Number(r[y]),
      z: Number(r[z]),
      originalData: r
    })).filter((p) => isFinite(p.x) && isFinite(p.y) && isFinite(p.z));
  }, [spec]);

  const positions = useMemo(() => {
    const pos = new Float32Array(points.length * 3);
    for (let i = 0; i < points.length; i++) {
      pos[i * 3 + 0] = points[i].x;
      pos[i * 3 + 1] = points[i].y;
      pos[i * 3 + 2] = -points[i].z; // Invert Z for depth
    }
    return pos;
  }, [points]);

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="h-96 w-full rounded-md overflow-hidden border border-gray-200 dark:border-gray-700">
        <Canvas camera={{ position: [0, 0, 200], fov: 45 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <Points positions={positions}>
            <PointMaterial
              transparent
              color="#4f46e5"
              size={2}
              sizeAttenuation={true}
              depthWrite={false}
            />
          </Points>
          <OrbitControls enableDamping dampingFactor={0.05} />
        </Canvas>
      </div>
    </div>
  );
}

function AdvancedSurface3DViz({ spec }: { spec: AdvancedVizSpec }) {
  // Placeholder for surface visualization
  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="h-96 w-full rounded-md overflow-hidden border border-gray-200 dark:border-gray-700 flex items-center justify-center">
        <p className="text-gray-500">3D Surface visualization coming soon...</p>
      </div>
    </div>
  );
}

function AdvancedVolume3DViz({ spec }: { spec: AdvancedVizSpec }) {
  // Placeholder for volume visualization
  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
      {spec.title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{spec.title}</h3>
          {spec.subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{spec.subtitle}</p>}
        </div>
      )}
      <div className="h-96 w-full rounded-md overflow-hidden border border-gray-200 dark:border-gray-700 flex items-center justify-center">
        <p className="text-gray-500">3D Volume visualization coming soon...</p>
      </div>
    </div>
  );
}
