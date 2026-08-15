
"use client";

import { useState, useEffect } from "react";

export const useFirstVisit = (key: string): [boolean, () => void] => {
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const visited = localStorage.getItem(key);
      if (!visited) {
        setIsFirstVisit(true);
      }
    }
  }, [key]);

  const setVisited = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem(key, "true");
      setIsFirstVisit(false);
    }
  };

  return [isFirstVisit, setVisited];
};
