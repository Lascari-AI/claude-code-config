"use client";

/**
 * Breadcrumbs Component
 *
 * Navigation breadcrumbs for deep page hierarchies.
 */

import Link from "next/link";
import { cn } from "@/lib/utils";

export interface BreadcrumbItem {
  /** Display label */
  label: string;
  /** Link href (optional - last item typically has no href) */
  href?: string;
}

interface BreadcrumbsProps {
  /** Array of breadcrumb items */
  items: BreadcrumbItem[];
  /** Separator element */
  separator?: React.ReactNode;
  /** Additional class names */
  className?: string;
}

/**
 * Breadcrumb navigation component.
 *
 * @example
 * <Breadcrumbs
 *   items={[
 *     { label: "Projects", href: "/projects" },
 *     { label: "My Project", href: "/projects/my-project" },
 *     { label: "Session 1" },
 *   ]}
 * />
 */
export function Breadcrumbs({
  items,
  separator = <ChevronRight className="w-4 h-4 text-muted-foreground" />,
  className,
}: BreadcrumbsProps) {
  if (items.length === 0) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn("flex items-center gap-1 text-sm", className)}
    >
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <div key={index} className="flex items-center gap-1">
            {index > 0 && <span className="mx-1">{separator}</span>}
            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span
                className={cn(
                  isLast ? "text-foreground font-medium" : "text-muted-foreground"
                )}
              >
                {item.label}
              </span>
            )}
          </div>
        );
      })}
    </nav>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  );
}
