import { useEffect, useState } from "react";
import { generateReplies, generateRsvp, type ReplyDraft, type RsvpDraft } from "../api/claude-client";
import { useEmail } from "../office-context";
import CopyButton from "./copy-button";

const SESSION_KEY = "hk_reply_instructions";
const MAX_CONTEXT = 200;

const TONE_CONFIG: Record<ReplyDraft["tone"], { label: string; borderClass: string; badgeClass: string }> = {
  professional: {
    label: "Professional",
    borderClass: "border-l-[#0078d4]",
    badgeClass: "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
  },
  friendly: {
    label: "Friendly",
    borderClass: "border-l-emerald-500",
    badgeClass: "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300",
  },
  brief: {
    label: "Brief",
    borderClass: "border-l-purple-500",
    badgeClass: "bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300",
  },
};

const RSVP_CONFIG: Record<RsvpDraft["type"], { label: string; borderClass: string; badgeClass: string }> = {
  accept: {
    label: "Accept",
    borderClass: "border-l-emerald-500",
    badgeClass: "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300",
  },
  decline: {
    label: "Decline",
    borderClass: "border-l-red-500",
    badgeClass: "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  },
  tentative: {
    label: "Tentative",
    borderClass: "border-l-amber-500",
    badgeClass: "bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
  },
};

function insertIntoCompose(text: string) {
  const item = (typeof Office !== "undefined" && Office.context?.mailbox?.item) || null;
  if (!item || typeof item.body?.setAsync !== "function") return;
  item.body.setAsync(text, { coercionType: "text" }, () => {});
}

function ReplyCard({ draft }: { draft: ReplyDraft }) {
  const config = TONE_CONFIG[draft.tone];
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 border-l-4 ${config.borderClass} p-3 space-y-2.5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-150`}>
      <div className="flex items-center justify-between">
        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${config.badgeClass}`}>
          {config.label}
        </span>
        <div className="flex items-center gap-1.5">
          <CopyButton text={draft.text} />
          <button
            onClick={() => insertIntoCompose(draft.text)}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded border border-[#0078d4]/40 text-[#0078d4] dark:text-[#4da6e8] hover:bg-[#0078d4]/5 dark:hover:bg-[#0078d4]/20 transition-colors"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            Insert
          </button>
        </div>
      </div>
      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{draft.text}</p>
    </div>
  );
}

function RsvpCard({ draft }: { draft: RsvpDraft }) {
  const config = RSVP_CONFIG[draft.type];
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 border-l-4 ${config.borderClass} p-3 space-y-2.5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-150`}>
      <div className="flex items-center justify-between">
        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${config.badgeClass}`}>
          {config.label}
        </span>
        <CopyButton text={draft.text} />
      </div>
      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{draft.text}</p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 border-l-4 border-l-gray-200 dark:border-l-gray-600 p-3 space-y-2.5 animate-pulse"
        >
          <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded-full" />
          <div className="space-y-1.5">
            <div className="h-3.5 bg-gray-200 dark:bg-gray-700 rounded w-full" />
            <div className="h-3.5 bg-gray-200 dark:bg-gray-700 rounded w-5/6" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ReplyTab() {
  const { email, meeting, itemType } = useEmail();
  const isAppointment = itemType === "appointment";

  const [drafts, setDrafts] = useState<ReplyDraft[]>([]);
  const [rsvpDrafts, setRsvpDrafts] = useState<RsvpDraft[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [instructions, setInstructions] = useState(
    () => sessionStorage.getItem(SESSION_KEY) ?? "",
  );
  const [showInstructions, setShowInstructions] = useState(false);

  function handleInstructionsChange(val: string) {
    const trimmed = val.slice(0, MAX_CONTEXT);
    setInstructions(trimmed);
    sessionStorage.setItem(SESSION_KEY, trimmed);
  }

  async function runGenerate(context?: string) {
    if (isAppointment && meeting) {
      setLoading(true);
      setError(null);
      try {
        const result = await generateRsvp(meeting.subject, meeting.organizer, meeting.start, meeting.body);
        setRsvpDrafts(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "RSVP generation failed");
      } finally {
        setLoading(false);
      }
    } else if (email) {
      setLoading(true);
      setError(null);
      try {
        const result = await generateReplies(email.subject, email.body, context);
        setDrafts(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Reply generation failed");
      } finally {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    runGenerate();
    // runGenerate is intentionally omitted — auto-generate on mount uses no context
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [email, meeting, itemType]);

  return (
    <div className="p-4 space-y-3">
      {loading && <LoadingSkeleton />}

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {!loading && isAppointment && rsvpDrafts.map((draft) => (
        <RsvpCard key={draft.type} draft={draft} />
      ))}

      {!loading && !isAppointment && drafts.map((draft) => (
        <ReplyCard key={draft.tone} draft={draft} />
      ))}

      {/* Customize reply panel — email only */}
      {!loading && !isAppointment && (
        <div className="border-t border-gray-100 dark:border-gray-700 pt-2.5">
          <button
            onClick={() => setShowInstructions((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg
              className={`w-3 h-3 transition-transform ${showInstructions ? "rotate-90" : ""}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {showInstructions ? "Hide instructions" : "Customize reply"}
          </button>

          {showInstructions && (
            <div className="mt-2.5 space-y-2">
              <div className="relative">
                <textarea
                  value={instructions}
                  onChange={(e) => handleInstructionsChange(e.target.value)}
                  placeholder='e.g. "decline politely" or "ask for more time"'
                  rows={3}
                  className="w-full text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 resize-none text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:border-[#0078d4] dark:focus:border-[#4da6e8] transition-colors"
                />
                <span className="absolute bottom-2 right-2.5 text-[10px] text-gray-400 dark:text-gray-500 select-none">
                  {instructions.length}/{MAX_CONTEXT}
                </span>
              </div>
              <button
                onClick={() => runGenerate(instructions.trim() || undefined)}
                disabled={loading}
                className="w-full py-2 text-sm font-medium bg-[#0078d4] hover:bg-[#106ebe] disabled:opacity-40 text-white rounded-lg transition-colors"
              >
                Regenerate
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
