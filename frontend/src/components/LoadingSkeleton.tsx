export default function LoadingSkeleton({ className = 'h-32' }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-white/5 ${className}`} />;
}