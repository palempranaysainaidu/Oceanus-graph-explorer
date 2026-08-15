
"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Globe, MessageCircle, Network } from "lucide-react";
import dynamic from "next/dynamic";
import { Suspense, useState, useEffect } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarTrigger,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarContent,
  SidebarInset,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { OceanusIcon } from "@/components/icons";
import { Chatbot } from "@/components/chatbot";
import { useFirstVisit } from "@/hooks/use-first-visit";
import { MapGuideModal } from "@/components/map-guide-modal";
import { Button } from "./ui/button";
import { GraphExplorer } from "@/components/graph-explorer";
import { ThemeToggle } from "./theme-toggle";

const MapVisualization = dynamic(
  () => import("@/components/map-visualization").then((mod) => mod.MapVisualization),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center bg-background">
        <Skeleton className="h-full w-full" />
      </div>
    ),
  }
);


interface MainAppProps {
  onReset: () => void;
}

function MapPageWrapper() {
  const [isFirstVisit, setVisited] = useFirstVisit("map-guide-visited");
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    setIsModalOpen(isFirstVisit);
  }, [isFirstVisit]);

  return (
    <>
      <MapGuideModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setVisited();
        }}
      />
      <MapVisualization />
    </>
  );
}

function MainContent() {
  const searchParams = useSearchParams();
  const view = searchParams.get("view") || "chatbot";

  return (
    <>
      {view === "map" && <MapPageWrapper />}
      {view === "chatbot" && <Chatbot />}
      {view === "graph" && <GraphExplorer />}
    </>
  );
}

export function MainApp({ onReset }: MainAppProps) {
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") || "chatbot";

  return (
    <SidebarProvider>
      <Sidebar collapsible="icon">
        <SidebarHeader>
          <div className="flex items-center justify-between">
             <Button variant="link" className="p-0 h-auto" onClick={onReset}>
              <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap text-foreground">
                <OceanusIcon className="size-7 shrink-0" />
                <span className="text-lg font-semibold group-data-[state=collapsed]:hidden">Oceanus Insights</span>
              </div>
            </Button>
            <SidebarTrigger />
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarMenu>
            <SidebarMenuItem>
              <Link href="?view=chatbot" className="w-full">
                <SidebarMenuButton
                  isActive={activeView === "chatbot"}
                  tooltip="Argo Chatbot"
                >
                  <MessageCircle />
                  <span>Argo Chatbot</span>
                </SidebarMenuButton>
              </Link>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <Link href="?view=map" className="w-full">
                <SidebarMenuButton
                  isActive={activeView === "map"}
                  tooltip="Map Visualization"
                >
                  <Globe />
                  <span>Map Visualization</span>
                </SidebarMenuButton>
              </Link>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <Link href="?view=graph" className="w-full">
                <SidebarMenuButton
                  isActive={activeView === "graph"}
                  tooltip="Knowledge Graph"
                >
                  <Network />
                  <span>Knowledge Graph</span>
                </SidebarMenuButton>
              </Link>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarContent>
        <SidebarFooter>
            <ThemeToggle />
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <div className="relative z-10 h-full w-full">
          <Suspense fallback={<Skeleton className="h-full w-full" />}>
            <MainContent />
          </Suspense>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
