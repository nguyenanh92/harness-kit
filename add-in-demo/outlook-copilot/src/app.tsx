import { useState } from "react";
import TabBar, { type Tab } from "./components/tab-bar";
import SummaryTab from "./components/summary-tab";
import ReplyTab from "./components/reply-tab";
import SettingsTab from "./components/settings-tab";
import TranslateTab from "./components/translate-tab";
import { useEmail } from "./office-context";
import { getApiKey, getProvider } from "./api/key-store";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>(getApiKey() ? "summary" : "settings");
  const { loading, error, email, meeting, itemType } = useEmail();
  const provider = getProvider();

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      <header className="shrink-0 bg-gradient-to-r from-[#0078d4] to-[#005fa3] dark:from-[#005a9e] dark:to-[#004987] px-4 py-2.5 flex items-center gap-2">
        <svg className="w-3.5 h-3.5 text-white/60 shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
        <p className="flex-1 text-xs text-white/85 truncate min-w-0">
          {loading ? "" : (email?.subject ?? meeting?.subject ?? "No item selected")}
        </p>
        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-md bg-white/20 text-white/90 shrink-0">
          {provider === "anthropic" ? "Claude" : "DeepSeek"}
        </span>
      </header>

      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <div className="w-5 h-5 border-2 border-[#0078d4] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-gray-400 dark:text-gray-500">Reading email…</p>
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center px-5">
          <div className="text-center space-y-3">
            <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M12 3a9 9 0 100 18A9 9 0 0012 3z" />
              </svg>
            </div>
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        </div>
      ) : (
        <>
          <TabBar active={activeTab} onChange={setActiveTab} itemType={itemType} />
          <main className="flex-1 overflow-y-auto">
            {activeTab === "summary" && <SummaryTab />}
            {activeTab === "reply" && <ReplyTab />}
            {activeTab === "translate" && <TranslateTab />}
            {activeTab === "settings" && <SettingsTab />}
          </main>
        </>
      )}
    </div>
  );
}
