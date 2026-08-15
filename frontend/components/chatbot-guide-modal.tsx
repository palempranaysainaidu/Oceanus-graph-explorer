
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
import { GraduationCap, FlaskConical } from "lucide-react";

interface ChatbotGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatbotGuideModal({ isOpen, onClose }: ChatbotGuideModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Welcome to the Argo Chatbot</DialogTitle>
          <DialogDescription>
            Your AI assistant for exploring ocean data. It has two modes.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <GraduationCap className="h-6 w-6 text-secondary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold">Education Mode</h3>
              <p className="text-sm text-muted-foreground">
                Get simple, easy-to-understand answers. Perfect for learning!
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <FlaskConical className="h-6 w-6 text-secondary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold">Scientist Mode</h3>
              <p className="text-sm text-muted-foreground">
                Access technical, data-rich responses for expert analysis.
              </p>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={onClose}>Start Chatting</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
