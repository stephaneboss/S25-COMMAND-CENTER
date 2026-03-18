import type { ReactNode } from "react";

interface StatsCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: ReactNode;
  trend?: {
    direction: "up" | "down" | "neutral";
    label: string;
  };
  accentColor?: "emerald" | "blue" | "amber" | "red" | "purple";
}

const ACCENT_STYLES: Record<string, { icon: string; value: string; badge: string }> = {
  emerald: {
    icon: "bg-emerald-100 text-emerald-700",
    value: "text-gray-900",
    badge: "bg-emerald-50 text-emerald-700",
  },
  blue: {
    icon: "bg-blue-100 text-blue-700",
    value: "text-gray-900",
    badge: "bg-blue-50 text-blue-700",
  },
  amber: {
    icon: "bg-amber-100 text-amber-700",
    value: "text-gray-900",
    badge: "bg-amber-50 text-amber-700",
  },
  red: {
    icon: "bg-red-100 text-red-700",
    value: "text-gray-900",
    badge: "bg-red-50 text-red-700",
  },
  purple: {
    icon: "bg-purple-100 text-purple-700",
    value: "text-gray-900",
    badge: "bg-purple-50 text-purple-700",
  },
};

export function StatsCard({
  label,
  value,
  sub,
  icon,
  trend,
  accentColor = "emerald",
}: StatsCardProps) {
  const styles = ACCENT_STYLES[accentColor];

  return (
    <div className="rounded-xl bg-white border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-500 truncate">{label}</p>
          <p className={`mt-1.5 text-2xl font-bold ${styles.value} truncate`}>
            {value}
          </p>
          {sub && (
            <p className="mt-1 text-xs text-gray-400 truncate">{sub}</p>
          )}
          {trend && (
            <div className="mt-2 flex items-center gap-1">
              {trend.direction === "up" && (
                <svg className="h-3.5 w-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7H7" />
                </svg>
              )}
              {trend.direction === "down" && (
                <svg className="h-3.5 w-3.5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10h10" />
                </svg>
              )}
              <span
                className={`text-xs font-medium ${
                  trend.direction === "up"
                    ? "text-emerald-600"
                    : trend.direction === "down"
                    ? "text-red-600"
                    : "text-gray-500"
                }`}
              >
                {trend.label}
              </span>
            </div>
          )}
        </div>

        {icon && (
          <div className={`flex-shrink-0 rounded-lg p-2.5 ${styles.icon}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
