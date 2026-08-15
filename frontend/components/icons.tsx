
import type { SVGProps } from "react";

export function OceanusIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
      <path d="M7 10.5A2.5 2.5 0 019.5 8" />
      <path d="M14.5 16a2.5 2.5 0 01-2.5-2.5" />
      <path d="M17 13.5a2.5 2.5 0 01-2.5-2.5" />
    </svg>
  );
}
