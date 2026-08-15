"use client";

import React, { useEffect, useMemo, useRef } from "react";
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
} from "recharts";
// Do not import Leaflet on the server. We'll require it inside effects on the client.

export type VizSpec = {
  type: "line" | "scatter" | "map_points" | "heatmap" | "scatter3d";
  title?: string;
  data: { fields: string[]; rows: any[] };
  encodings: Record<string, string>;
  options?: { tooltip?: boolean; connectNulls?: boolean };
};

export function VisualizationRenderer({ spec }: { spec: VizSpec }) {
  if (spec.type === "line") return <LineViz spec={spec} />;
  if (spec.type === "scatter") return <ScatterViz spec={spec} />;
  if (spec.type === "map_points") return <MapPointsViz spec={spec} />;
  if (spec.type === "heatmap") return <HeatmapViz spec={spec} />;
  if (spec.type === "scatter3d") return <Scatter3DViz spec={spec} />;
  return null;
}

function LineViz({ spec }: { spec: VizSpec }) {
  const { x, y } = spec.encodings as { x: string; y: string };
  const data = useMemo(() =>
    spec.data.rows.map((r) => ({ ...r, [x]: r[x], [y]: Number(r[y]) })).filter((r) => r[y] != null),
  [spec, x, y]);
  return (
    <div className="w-full h-64">
      {spec.title && <h4 className="mb-2 text-sm font-semibold">{spec.title}</h4>}
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={x} tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <ReTooltip formatter={(v) => (typeof v === "number" ? v.toFixed(3) : v)} />
          <Line type="monotone" connectNulls={!!spec.options?.connectNulls} dataKey={y} stroke="#8884d8" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function ScatterViz({ spec }: { spec: VizSpec }) {
  const { x, y } = spec.encodings as { x: string; y: string };
  const data = useMemo(() => spec.data.rows.map((r) => ({ x: Number(r[x]), y: Number(r[y]) })), [spec, x, y]);
  return (
    <div className="w-full h-64">
      {spec.title && <h4 className="mb-2 text-sm font-semibold">{spec.title}</h4>}
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
          <CartesianGrid />
          <XAxis dataKey="x" tick={{ fontSize: 10 }} type="number" />
          <YAxis dataKey="y" tick={{ fontSize: 10 }} type="number" />
          <ReTooltip formatter={(v) => (typeof v === "number" ? v.toFixed(3) : v)} />
          <Scatter data={data} fill="#82ca9d" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

function MapPointsViz({ spec }: { spec: VizSpec }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (typeof window === "undefined" || !ref.current) return;
    // Lazy-load Leaflet only on the client to avoid SSR window reference
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const L = require("leaflet");
    try { require("leaflet.heat"); } catch {}
    const container = ref.current;
    container.innerHTML = "";
    const map = L.map(container, { center: [0, 0], zoom: 2, worldCopyJump: true });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap" }).addTo(map);
    const latKey = spec.encodings.lat;
    const lonKey = spec.encodings.lon;
    const points: [number, number][] = [];
    spec.data.rows.forEach((r) => {
      const lat = Number(r[latKey]);
      const lon = Number(r[lonKey]);
      if (isFinite(lat) && isFinite(lon)) {
        points.push([lat, lon]);
        const marker = L.circleMarker([lat, lon], { radius: 3, color: "#0ea5e9" });
        if (spec.options?.tooltip) marker.bindTooltip(`${lat.toFixed(3)}, ${lon.toFixed(3)}`);
        marker.addTo(map);
      }
    });
    if (points.length) map.fitBounds(L.latLngBounds(points as any), { padding: [20, 20] });
    return () => map.remove();
  }, [spec]);
  return (
    <div className="w-full">
      {spec.title && <h4 className="mb-2 text-sm font-semibold">{spec.title}</h4>}
      <div ref={ref} className="h-64 w-full rounded-md overflow-hidden" />
    </div>
  );
}

function HeatmapViz({ spec }: { spec: VizSpec }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (typeof window === "undefined" || !ref.current) return;
    // Lazy-load Leaflet and heat plugin on the client
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const L = require("leaflet");
    try { require("leaflet.heat"); } catch {}
    const container = ref.current;
    container.innerHTML = "";
    const map = L.map(container, { center: [0, 0], zoom: 2, worldCopyJump: true });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap" }).addTo(map);
    const latKey = spec.encodings.lat;
    const lonKey = spec.encodings.lon;
    const valKey = spec.encodings.value;
    const heatData: [number, number, number][] = [];
    spec.data.rows.forEach((r) => {
      const lat = Number(r[latKey]);
      const lon = Number(r[lonKey]);
      const val = Number(r[valKey]);
      if (isFinite(lat) && isFinite(lon) && isFinite(val)) heatData.push([lat, lon, val]);
    });
    // Only add heat layer if we have data and the map container has dimensions
    if (heatData.length > 0) {
      // Wait for map to be ready before adding heat layer
      map.whenReady(() => {
        try {
          // @ts-ignore - heat plugin augments Leaflet namespace
          L.heatLayer(heatData, { radius: 15, blur: 12, maxZoom: 6 }).addTo(map);
          map.fitBounds(L.latLngBounds(heatData.map(([a, b]) => [a, b]) as any), { padding: [20, 20] });
        } catch (error) {
          console.warn("Failed to add heat layer:", error);
        }
      });
    }
    return () => map.remove();
  }, [spec]);
  return (
    <div className="w-full">
      {spec.title && <h4 className="mb-2 text-sm font-semibold">{spec.title}</h4>}
      <div ref={ref} className="h-64 w-full rounded-md overflow-hidden" />
    </div>
  );
}

function Scatter3DViz({ spec }: { spec: VizSpec }) {
  // Minimal placeholder: instruct user to install three for richer 3D; otherwise show map points as fallback.
  // For now, render as 2D scatter if three is not available to avoid runtime errors.
  try {
    // Lazy require to avoid SSR import issues
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const THREE = require("three");
    return <ThreeScatter spec={spec} THREE={THREE} />;
  } catch {
    // Fallback to 2D scatter
    const fallback: VizSpec = {
      ...spec,
      type: "scatter",
      title: spec.title ? `${spec.title} (2D fallback)` : "3D scatter (2D fallback)",
      encodings: { x: spec.encodings.x || spec.encodings.lon, y: spec.encodings.y || spec.encodings.lat },
    } as any;
    return <ScatterViz spec={fallback} />;
  }
}

function ThreeScatter({ spec, THREE }: { spec: VizSpec; THREE: any }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const width = canvas.clientWidth;
    const height = 256;
    canvas.width = width;
    canvas.height = height;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000);
    camera.position.set(0, 0, 200);
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(width, height);

    const points = spec.data.rows.slice(0, 5000).map((r) => ({
      x: Number(r[spec.encodings.x || "longitude"]),
      y: Number(r[spec.encodings.y || "latitude"]),
      z: Number(r[spec.encodings.z || "pres_adjusted"]),
    }));
    const geom = new THREE.BufferGeometry();
    const positions = new Float32Array(points.length * 3);
    for (let i = 0; i < points.length; i++) {
      positions[i * 3 + 0] = points[i].x;
      positions[i * 3 + 1] = points[i].y;
      positions[i * 3 + 2] = -points[i].z; // depth inverted
    }
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({ size: 2, color: 0x4f46e5 });
    const cloud = new THREE.Points(geom, mat);
    scene.add(cloud);

    const controls = new (require("three/examples/jsm/controls/OrbitControls").OrbitControls)(camera, renderer.domElement);
    controls.enableDamping = true;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    function onMove(e: MouseEvent) {
      const rect = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObject(cloud);
      if (intersects.length && tooltipRef.current) {
        const idx = intersects[0].index ?? 0;
        const p = points[idx];
        tooltipRef.current.style.opacity = "1";
        tooltipRef.current.style.left = e.clientX + 8 + "px";
        tooltipRef.current.style.top = e.clientY + 8 + "px";
        tooltipRef.current.innerText = `${p.x.toFixed(3)}, ${p.y.toFixed(3)}, ${p.z.toFixed(2)}`;
      } else if (tooltipRef.current) {
        tooltipRef.current.style.opacity = "0";
      }
    }
    canvas.addEventListener("mousemove", onMove);

    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    function onResize() {
      const w = canvas.clientWidth;
      const h = 256;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      canvas.removeEventListener("mousemove", onMove);
      renderer.dispose();
    };
  }, [spec, THREE]);

  return (
    <div className="w-full">
      {spec.title && <h4 className="mb-2 text-sm font-semibold">{spec.title}</h4>}
      <div className="relative w-full">
        <canvas ref={canvasRef} className="w-full h-64" />
        <div ref={tooltipRef} className="pointer-events-none absolute left-0 top-0 rounded bg-black/70 px-2 py-1 text-xs text-white opacity-0" />
      </div>
    </div>
  );
}


