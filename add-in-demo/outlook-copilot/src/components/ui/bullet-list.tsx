interface BulletListProps {
  items: string[];
  icon?: "dot" | "check";
}

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

function DotIcon() {
  return <span className="w-1.5 h-1.5 rounded-full bg-[#0078d4] dark:bg-[#4da6e8] shrink-0 mt-1.5" />;
}

export default function BulletList({ items, icon = "dot" }: BulletListProps) {
  return (
    <ul className="space-y-2.5">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2.5 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          {icon === "check" ? <CheckIcon /> : <DotIcon />}
          {item}
        </li>
      ))}
    </ul>
  );
}
