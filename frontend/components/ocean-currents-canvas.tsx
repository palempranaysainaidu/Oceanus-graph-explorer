"use client";

import { useRef, useEffect, HTMLAttributes } from 'react';
import { createNoise2D } from 'simplex-noise';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';

interface OceanCurrentsCanvasProps extends HTMLAttributes<HTMLCanvasElement> {}

export function OceanCurrentsCanvas({ className, ...props }: OceanCurrentsCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { resolvedTheme } = useTheme();
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    const noise2D = createNoise2D();

    let width = canvas.offsetWidth;
    let height = canvas.offsetHeight;
    canvas.width = width;
    canvas.height = height;

    const particleCount = 5000;
    const particles: Particle[] = [];
    const particleSize = 2;
    const speed = 0.5;
    const noiseScale = 0.005;

    class Particle {
      x: number;
      y: number;
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
      }

      update() {
        const angle = noise2D(this.x * noiseScale, this.y * noiseScale) * Math.PI * 2;
        this.x += Math.cos(angle) * speed;
        this.y += Math.sin(angle) * speed;

        if (this.x > width) this.x = 0;
        if (this.x < 0) this.x = width;
        if (this.y > height) this.y = 0;
        if (this.y < 0) this.y = height;
      }

      draw(context: CanvasRenderingContext2D) {
        context.beginPath();
        context.arc(this.x, this.y, particleSize, 0, Math.PI * 2);
        context.fill();
      }
    }

    const init = () => {
      particles.length = 0;
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    };
    
    const animate = () => {
        const isDark = resolvedTheme === 'dark';
        ctx.fillStyle = isDark ? 'rgba(30, 41, 59, 0.05)' : 'rgba(241, 245, 249, 0.05)'; // slate-800, slate-100
        ctx.fillRect(0, 0, width, height);

        ctx.fillStyle = isDark ? 'rgba(100, 116, 139, 0.5)' : 'rgba(100, 116, 139, 0.5)'; // slate-500
        particles.forEach(p => {
            p.update();
            p.draw(ctx);
        });

        animationFrameId = window.requestAnimationFrame(animate);
    };

    const handleResize = () => {
      width = canvas.offsetWidth;
      height = canvas.offsetHeight;
      canvas.width = width;
      canvas.height = height;
      init();
    };

    window.addEventListener('resize', handleResize);
    
    init();
    animate();

    return () => {
      window.cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };

  }, [resolvedTheme]);

  return <canvas ref={canvasRef} className={cn("h-full w-full", className)} {...props} />;
}
