import { useState } from "react";
import {
  getProvider, setProvider,
  setApiKey, clearApiKey, hasKey,
  type Provider,
} from "../api/key-store";

const PROVIDERS: { id: Provider; label: string; description: string; placeholder: string; docsUrl: string }[] = [
  {
    id: "anthropic",
    label: "Anthropic",
    description: "Claude models",
    placeholder: "sk-ant-api03-…",
    docsUrl: "console.anthropic.com",
  },
  {
    id: "deepseek",
    label: "DeepSeek",
    description: "DeepSeek Chat",
    placeholder: "sk-…",
    docsUrl: "platform.deepseek.com",
  },
];

function ProviderLogo({ id }: { id: Provider }) {
  if (id === "anthropic") {
    return (
      <div className="w-7 h-7 bg-[#d4a574] rounded-md flex items-center justify-center text-white font-bold text-sm shrink-0">
        A
      </div>
    );
  }
  return (
    <div className="w-7 h-7 bg-[#4355f5] rounded-md flex items-center justify-center text-white font-bold text-sm shrink-0">
      D
    </div>
  );
}

function KeySection({ provider }: { provider: Provider }) {
  const [input, setInput] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(hasKey(provider));
  const meta = PROVIDERS.find((p) => p.id === provider)!;

  function handleSave() {
    const trimmed = input.trim();
    if (!trimmed) return;
    setApiKey(trimmed, provider);
    setInput("");
    setSaved(true);
  }

  function handleClear() {
    clearApiKey(provider);
    setInput("");
    setSaved(false);
  }

  return (
    <div className="space-y-2.5">
      <h3 className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        API Key
      </h3>

      {saved ? (
        <div className="flex items-center gap-2 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
          <svg className="w-4 h-4 text-emerald-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm text-emerald-700 dark:text-emerald-300 flex-1">Key configured</span>
          <button
            onClick={handleClear}
            className="text-xs font-medium text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors"
          >
            Remove
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="relative">
            <input
              type={showKey ? "text" : "password"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              placeholder={meta.placeholder}
              className="w-full text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2.5 pr-14 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:border-[#0078d4] dark:focus:border-[#4da6e8] transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowKey((v) => !v)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
            >
              {showKey ? "Hide" : "Show"}
            </button>
          </div>
          <button
            onClick={handleSave}
            disabled={!input.trim()}
            className="w-full py-2.5 text-sm font-medium bg-[#0078d4] hover:bg-[#106ebe] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            Save Key
          </button>
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Get your key at{" "}
            <span className="font-mono text-gray-500 dark:text-gray-400">{meta.docsUrl}</span>
          </p>
        </div>
      )}
    </div>
  );
}

export default function SettingsTab() {
  const [activeProvider, setActiveProvider] = useState<Provider>(getProvider());

  function handleProviderChange(p: Provider) {
    setActiveProvider(p);
    setProvider(p);
  }

  return (
    <div className="p-4 space-y-5">
      <div className="space-y-2.5">
        <h2 className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          AI Provider
        </h2>
        <div className="space-y-2">
          {PROVIDERS.map((p) => {
            const isActive = activeProvider === p.id;
            return (
              <button
                key={p.id}
                onClick={() => handleProviderChange(p.id)}
                className={[
                  "w-full flex items-center gap-3 p-3 rounded-lg border text-left transition-all",
                  isActive
                    ? "border-[#0078d4] dark:border-[#4da6e8] bg-[#0078d4]/5 dark:bg-[#0078d4]/15"
                    : "border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-500",
                ].join(" ")}
              >
                <ProviderLogo id={p.id} />
                <div className="flex-1 min-w-0">
                  <p className={[
                    "text-sm font-medium",
                    isActive ? "text-[#0078d4] dark:text-[#4da6e8]" : "text-gray-800 dark:text-gray-200",
                  ].join(" ")}>
                    {p.label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{p.description}</p>
                </div>
                <div className={[
                  "w-4 h-4 rounded-full border-2 shrink-0 flex items-center justify-center transition-colors",
                  isActive
                    ? "border-[#0078d4] dark:border-[#4da6e8]"
                    : "border-gray-300 dark:border-gray-600",
                ].join(" ")}>
                  {isActive && (
                    <div className="w-2 h-2 bg-[#0078d4] dark:bg-[#4da6e8] rounded-full" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <KeySection key={activeProvider} provider={activeProvider} />

      <div className="pt-1 space-y-2 border-t border-gray-100 dark:border-gray-700">
        <p className="text-xs text-gray-400 dark:text-gray-500">
          Keys stored in localStorage — never sent anywhere except the selected provider.
        </p>
        {activeProvider === "deepseek" && (
          <div className="flex gap-2 p-2.5 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <svg className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd" />
            </svg>
            <p className="text-xs text-amber-700 dark:text-amber-400">
              DeepSeek may block browser-direct calls due to CORS. Test before relying on it.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
