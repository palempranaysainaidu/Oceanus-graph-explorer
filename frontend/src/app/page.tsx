"use client";

import { useState, Suspense } from "react";
import { LandingPage } from "@/components/landing-page";
import { MainApp } from "@/components/main-app";
import { Toaster } from "@/components/ui/toaster";

export default function Home() {
  const [journeyStarted, setJourneyStarted] = useState(false);

  const handleStart = () => setJourneyStarted(true);
  const handleReset = () => setJourneyStarted(false);

  return (
    <Suspense>
      {!journeyStarted ? (
        <LandingPage onStart={handleStart} />
      ) : (
        <MainApp onReset={handleReset} />
      )}
      <Toaster />
    </Suspense>
  );
}
