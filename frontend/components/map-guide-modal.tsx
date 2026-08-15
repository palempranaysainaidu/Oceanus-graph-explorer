
"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Mouse, ZoomIn, Hand } from "lucide-react";

interface MapGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MapGuideModal({ isOpen, onClose }: MapGuideModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Welcome to the Map Explorer</DialogTitle>
          <DialogDescription>
            Here's a quick guide on how to navigate the ocean data.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <ZoomIn className="h-6 w-6 text-secondary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold">Zoom In and Out</h3>
              <p className="text-sm text-muted-foreground">
                Use your mouse wheel or the +/- controls to zoom.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <Hand className="h-6 w-6 text-secondary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold">Pan the Map</h3>
              <p className="text-sm text-muted-foreground">
                Click and drag to move around the map.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <Mouse className="h-6 w-6 text-secondary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold">Inspect a Float</h3>
              <p className="text-sm text-muted-foreground">
                Click on any pulsating dot to see its details.
              </p>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={onClose}>Got it!</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
