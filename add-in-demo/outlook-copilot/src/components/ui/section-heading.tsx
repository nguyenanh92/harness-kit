import type { ReactNode } from "react";

interface SectionHeadingProps {
  icon: ReactNode;
  children: ReactNode;
}

export default function SectionHeading({ icon, children }: SectionHeadingProps) {
  return (
    <h2 className="flex items-center gap-1.5 text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
      {icon}
      {children}
    </h2>
  );
}
