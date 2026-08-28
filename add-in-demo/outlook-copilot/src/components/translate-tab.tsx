import { useState } from "react";
import { translateEmail } from "../api/claude-client";
import { useEmail } from "../office-context";
import CopyButton from "./copy-button";

interface Language {
  code: string;
  name: string;   // passed to API prompt
  label: string;  // displayed in UI
}

const LANGUAGES: Language[] = [
  { code: "vi", name: "Vietnamese",           label: "Tiếng Việt" },
  { code: "en", name: "English",              label: "English"    },
  { code: "zh", name: "Chinese (Simplified)", label: "中文"       },
  { code: "ja", name: "Japanese",             label: "日本語"      },
  { code: "ko", name: "Korean",               label: "한국어"      },
  { code: "fr", name: "French",               label: "Français"   },
  { code: "de", name: "German",               label: "Deutsch"    },
  { code: "es", name: "Spanish",              label: "Español"    },
];

function LoadingSkeleton() {
  return (
    <div className="space-y-2 pt-1">
      {[100, 88, 94, 72].map((w, i) => (
        <div
          key={i}
          className="h-3.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
          style={{ width: `${w}%` }}
        />
      ))}
    </div>
  );
}

export default function TranslateTab() {
  const { email, meeting } = useEmail();
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeLang, setActiveLang] = useState<Language | null>(null);

  async function handleTranslate(lang: Language) {
    const bodyText = email?.body ?? meeting?.body ?? "";
    if (!bodyText) return;
    setActiveLang(lang);
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const translated = await translateEmail(bodyText, lang.name);
      setResult(translated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Translation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="flex items-center gap-1.5 text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
        </svg>
        Translate to
      </h2>

      <div className="grid grid-cols-2 gap-1.5">
        {LANGUAGES.map((lang) => {
          const isActive = activeLang?.code === lang.code;
          return (
            <button
              key={lang.code}
              onClick={() => handleTranslate(lang)}
              disabled={loading}
              className={[
                "py-2 px-3 text-sm font-medium rounded-lg border transition-all duration-150 disabled:opacity-60 truncate",
                isActive
                  ? "bg-[#0078d4] border-[#0078d4] text-white"
                  : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-[#0078d4]/60 hover:text-[#0078d4] dark:hover:text-[#4da6e8]",
              ].join(" ")}
            >
              {lang.label}
            </button>
          );
        })}
      </div>

      {!loading && !result && !error && (
        <p className="text-xs text-gray-400 dark:text-gray-500 text-center pt-1">
          Select a language to translate
        </p>
      )}

      {loading && <LoadingSkeleton />}

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {result && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {activeLang?.label}
            </span>
            <CopyButton text={result} />
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
            {result}
          </p>
        </div>
      )}
    </div>
  );
}
