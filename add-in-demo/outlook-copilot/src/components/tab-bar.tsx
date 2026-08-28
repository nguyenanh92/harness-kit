export type Tab = "summary" | "reply" | "translate" | "settings";

interface TabBarProps {
  active: Tab;
  onChange: (tab: Tab) => void;
  itemType?: "message" | "appointment" | null;
}

function TabIcon({ id }: { id: Tab }) {
  if (id === "summary") {
    return (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
          d="M9 12h6m-6 4h6M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z" />
      </svg>
    );
  }
  if (id === "reply") {
    return (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
          d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
      </svg>
    );
  }
  if (id === "translate") {
    return (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
          d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
      </svg>
    );
  }
  return (
    <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

const TABS: { id: Tab; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "reply", label: "Reply" },
  { id: "translate", label: "Translate" },
  { id: "settings", label: "Settings" },
];

export default function TabBar({ active, onChange, itemType }: TabBarProps) {
  return (
    <div className="shrink-0 px-2 pt-2 pb-2 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700">
      <div className="flex bg-gray-100 dark:bg-gray-700 rounded-xl p-1 gap-0.5">
        {TABS.map((tab) => {
          const isActive = active === tab.id;
          const label = tab.id === "reply" && itemType === "appointment" ? "RSVP" : tab.label;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={[
                "flex-1 flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[10px] font-medium transition-all duration-150",
                isActive
                  ? "bg-white dark:bg-gray-600 text-[#0078d4] dark:text-[#4da6e8] shadow-sm"
                  : "text-gray-400 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-200",
              ].join(" ")}
            >
              <TabIcon id={tab.id} />
              <span>{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
