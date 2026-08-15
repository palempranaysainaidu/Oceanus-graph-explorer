"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix standard Leaflet icon paths in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

export type MapPoint = {
  lat: number;
  lng: number;
  popup?: string;
};

interface MapProps {
  points: MapPoint[];
  type?: "polyline" | "markers";
}

export function Map({ points, type = "polyline" }: MapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletInstance = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    // Initialize map only once
    if (!leafletInstance.current) {
      leafletInstance.current = L.map(mapRef.current).setView([0, 0], 2);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(leafletInstance.current);
    }

    const map = leafletInstance.current;
    
    // Clear existing layers (excluding the base tile layer)
    map.eachLayer((layer) => {
      if (!(layer instanceof L.TileLayer)) {
        map.removeLayer(layer);
      }
    });

    if (points.length === 0) return;

    const latLngs = points.map((p) => [p.lat, p.lng] as [number, number]);

    if (type === "polyline") {
      const polyline = L.polyline(latLngs, { color: "blue", weight: 3 }).addTo(map);
      
      // Add start and end markers
      if (points.length > 0) {
        L.circleMarker(latLngs[0], { radius: 5, color: "green", fillOpacity: 0.8 }).addTo(map).bindPopup("Start");
        L.circleMarker(latLngs[latLngs.length - 1], { radius: 5, color: "red", fillOpacity: 0.8 }).addTo(map).bindPopup("End");
      }
      map.fitBounds(polyline.getBounds(), { padding: [20, 20] });
    } else {
      const group = L.featureGroup();
      points.forEach((p) => {
        const marker = L.circleMarker([p.lat, p.lng], {
          radius: 6,
          color: "blue",
          fillOpacity: 0.7,
        });
        if (p.popup) {
          marker.bindPopup(p.popup);
        }
        marker.addTo(group);
      });
      group.addTo(map);
      map.fitBounds(group.getBounds(), { padding: [20, 20] });
    }

    return () => {
      // Clean up map instance on component unmount
      if (leafletInstance.current) {
        leafletInstance.current.remove();
        leafletInstance.current = null;
      }
    };
  }, [points, type]);

  return <div ref={mapRef} className="w-full h-full rounded-md z-0" />;
}
