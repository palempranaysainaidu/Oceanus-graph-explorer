
"use client";

import { Button } from "@/components/ui/button";
import { OceanusIcon } from "@/components/icons";
import { Globe, MessageCircle, BarChart3, Waves } from "lucide-react";
import Image from "next/image";
import { placeholderImages } from "@/lib/placeholder-images";
import Link from 'next/link';
import { ThemeToggle } from "./theme-toggle";
import { OceanCurrentsCanvas } from "./ocean-currents-canvas";

interface LandingPageProps {
  onStart: () => void;
}

export function LandingPage({ onStart }: LandingPageProps) {
  const mapVisualizationImage = placeholderImages.find(p => p.id === "map-visualization");
  const chatbotImage = placeholderImages.find(p => p.id === "chatbot-view");
  const floatDashboardImage = placeholderImages.find(p => p.id === "float-dashboard");

  return (
    <div className="flex h-full w-full flex-col bg-background text-foreground">
      <header className="sticky top-0 z-20 w-full border-b bg-background/95 backdrop-blur-sm">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-2">
            <OceanusIcon className="h-8 w-8 text-primary" />
            <h1 className="text-xl font-bold tracking-tight">
              Oceanus Insights
            </h1>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
             <Link href="#about-argo" className="text-muted-foreground transition-colors hover:text-foreground">
              What is Argo?
            </Link>
            <Link href="#features" className="text-muted-foreground transition-colors hover:text-foreground">
              Features
            </Link>
            <Link href="#gallery" className="text-muted-foreground transition-colors hover:text-foreground">
              Gallery
            </Link>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button onClick={onStart}>
              Start Your Journey
            </Button>
          </div>
        </div>
      </header>
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative flex h-screen w-full items-center justify-center text-center">
            <OceanCurrentsCanvas className="absolute inset-0 z-0"/>
            <div className="relative z-10 container flex flex-col items-center justify-center px-4 md:px-6">
                <div className="space-y-4">
                    <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl/none font-headline">
                    Unlock the Depths of Ocean Data
                    </h1>
                    <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
                    Explore the Indian Ocean with real-time Argo float data
                    visualizations and an intelligent chatbot assistant.
                    </p>
                </div>
                <div className="mt-8">
                    <Button size="lg" onClick={onStart}>
                    Explore the Map
                    </Button>
                </div>
            </div>
        </section>

        {/* About Argo Section */}
        <section id="about-argo" className="w-full py-12 md:py-24 lg:py-32">
          <div className="container mx-auto px-4 md:px-6">
            <div className="mx-auto grid max-w-5xl items-center gap-8 lg:grid-cols-2 lg:gap-12">
               <div className="flex flex-col justify-center space-y-4">
                 <div className="space-y-2">
                  <div className="inline-block rounded-lg bg-muted px-3 py-1 text-sm">About the Data</div>
                  <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">What is Argo?</h2>
                </div>
                <p className="max-w-[600px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  The Argo program is a global array of nearly 4,000 free-drifting profiling floats that measure the temperature and salinity of the upper 2000 meters of the ocean. 
                </p>
                <p className="max-w-[600px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  This allows for continuous monitoring of the state of the upper ocean, with all data being made publicly available within hours of collection. Our platform provides an intuitive interface to explore this rich dataset.
                </p>
               </div>
                <div className="flex items-center justify-center">
                    <Waves className="h-48 w-48 text-muted" />
                </div>
            </div>
          </div>
        </section>


        {/* Features Section */}
        <section id="features" className="w-full py-12 md:py-24 lg:py-32 bg-muted">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <div className="inline-block rounded-lg bg-background px-3 py-1 text-sm">Key Features</div>
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">Your Oceanographic Command Center</h2>
                <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Oceanus Insights combines powerful visualization tools with cutting-edge AI to give you unparalleled access to oceanographic data.
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl items-center gap-6 py-12 lg:grid-cols-3 lg:gap-12">
              <div className="flex flex-col justify-center space-y-4 text-center items-center">
                 <div className="rounded-full bg-secondary p-4">
                    <Globe className="h-8 w-8 text-secondary-foreground" />
                 </div>
                <h3 className="text-xl font-bold">Interactive Map</h3>
                <p className="text-muted-foreground">Visualize real-time Argo float locations across the Indian Ocean. Click to explore detailed sensor data.</p>
              </div>
              <div className="flex flex-col justify-center space-y-4 text-center items-center">
                <div className="rounded-full bg-secondary p-4">
                    <MessageCircle className="h-8 w-8 text-secondary-foreground" />
                </div>
                <h3 className="text-xl font-bold">AI Chatbot Assistant</h3>
                <p className="text-muted-foreground">Ask questions in plain English. Get educational summaries, expert analysis, or compare data between two floats.</p>
              </div>
              <div className="flex flex-col justify-center space-y-4 text-center items-center">
                <div className="rounded-full bg-secondary p-4">
                    <BarChart3 className="h-8 w-8 text-secondary-foreground" />
                </div>
                <h3 className="text-xl font-bold">Data Dashboards</h3>
                <p className="text-muted-foreground">Dive deep into historical data for temperature, salinity, and pressure with interactive charts and AI-generated insights.</p>
              </div>
            </div>
          </div>
        </section>

         {/* Gallery Section */}
        <section id="gallery" className="w-full py-12 md:py-24 lg:py-32">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                 <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">See It in Action</h2>
                <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  A glimpse into the powerful tools at your disposal.
                </p>
              </div>
            </div>
            <div className="mx-auto grid gap-8 py-12 sm:grid-cols-1 md:grid-cols-3">
              {mapVisualizationImage && <div className="relative overflow-hidden rounded-xl shadow-lg">
                <Image
                  src={mapVisualizationImage.imageUrl}
                  alt="Map Visualization Screenshot"
                  width={600}
                  height={400}
                  className="aspect-video w-full object-cover"
                  data-ai-hint={mapVisualizationImage.imageHint}
                />
                <div className="absolute bottom-0 w-full bg-gradient-to-t from-black/80 to-transparent p-4 text-white">
                  <h3 className="font-bold">Live Map View</h3>
                </div>
              </div>}
              {chatbotImage && <div className="relative overflow-hidden rounded-xl shadow-lg">
                <Image
                  src={chatbotImage.imageUrl}
                  alt="Chatbot Screenshot"
                  width={600}
                  height={400}
                  className="aspect-video w-full object-cover"
                  data-ai-hint={chatbotImage.imageHint}
                />
                 <div className="absolute bottom-0 w-full bg-gradient-to-t from-black/80 to-transparent p-4 text-white">
                  <h3 className="font-bold">AI-Powered Chatbot</h3>
                </div>
              </div>}
              {floatDashboardImage && <div className="relative overflow-hidden rounded-xl shadow-lg">
                <Image
                  src={floatDashboardImage.imageUrl}
                  alt="Dashboard Screenshot"
                  width={600}
                  height={400}
                  className="aspect-video w-full object-cover"
                  data-ai-hint={floatDashboardImage.imageHint}
                />
                 <div className="absolute bottom-0 w-full bg-gradient-to-t from-black/80 to-transparent p-4 text-white">
                  <h3 className="font-bold">Float Data Dashboard</h3>
                </div>
              </div>}
            </div>
          </div>
        </section>
        
        {/* CTA Section */}
        <section id="cta" className="w-full py-12 md:py-24 lg:py-32 bg-muted">
          <div className="container mx-auto flex flex-col items-center justify-center gap-4 px-4 text-center md:px-6">
            <div className="space-y-3">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">Ready to Dive In?</h2>
              <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl/relaxed">
                Your journey into the depths of ocean data starts now. Click the button to launch the interactive map and begin your exploration.
              </p>
            </div>
            <Button size="lg" onClick={onStart}>
              Unlock Your Knowledge
            </Button>
          </div>
        </section>
      </main>

      <footer className="w-full border-t py-6 text-center text-sm text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} Oceanus Insights. All rights reserved.</p>
      </footer>
    </div>
  );
}
