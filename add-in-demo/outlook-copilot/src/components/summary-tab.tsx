import { useEffect, useState } from "react";
import {
  summarizeEmail,
  summarizeMeeting,
  formatMeetingTime,
  type SummaryResult,
  type MeetingBrief,
} from "../api/claude-client";
import { useEmail, type MeetingData } from "../office-context";
import ErrorAlert from "./ui/error-alert";
import SectionHeading from "./ui/section-heading";
import BulletList from "./ui/bullet-list";

const TONE_STYLE: Record<NonNullable<SummaryResult["tone"]>, string> = {
  urgent:   "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  formal:   "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
  friendly: "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300",
  neutral:  "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300",
};
const TONE_LABEL: Record<NonNullable<SummaryResult["tone"]>, string> = {
  urgent: "Urgent", formal: "Formal", friendly: "Friendly", neutral: "Neutral",
};

function ToneBadge({ tone }: { tone?: SummaryResult["tone"] }) {
  if (!tone || !TONE_STYLE[tone]) return null;
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${TONE_STYLE[tone]}`}>
      {TONE_LABEL[tone]}
    </span>
  );
}

function SkeletonLines({ widths }: { widths: string[] }) {
  return (
    <div className="space-y-2">
      {widths.map((w, i) => (
        <div
          key={i}
          className="h-3.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
          style={{ width: w }}
        />
      ))}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="p-4 space-y-5">
      <div className="space-y-3">
        <div className="h-3 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <SkeletonLines widths={["100%", "85%", "72%"]} />
      </div>
      <div className="space-y-3">
        <div className="h-3 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <SkeletonLines widths={["92%", "68%"]} />
      </div>
    </div>
  );
}

function MeetingInfoCard({ meeting }: { meeting: MeetingData }) {
  const timeStr = `${formatMeetingTime(new Date(meeting.start))} – ${formatMeetingTime(new Date(meeting.end))}`;
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-3.5 space-y-2.5">
      <h2 className="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
        Meeting Details
      </h2>
      <div className="space-y-2">
        {meeting.organizer && (
          <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
            <svg className="w-4 h-4 shrink-0 text-gray-400 dark:text-gray-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span>{meeting.organizer}</span>
          </div>
        )}
        <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
          <svg className="w-4 h-4 shrink-0 text-gray-400 dark:text-gray-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>{timeStr}</span>
        </div>
        {meeting.location && (
          <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
            <svg className="w-4 h-4 shrink-0 text-gray-400 dark:text-gray-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>{meeting.location}</span>
          </div>
        )}
        {meeting.attendees.length > 0 && (
          <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
            <svg className="w-4 h-4 shrink-0 text-gray-400 dark:text-gray-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="leading-snug">{meeting.attendees.join(", ")}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function MeetingBriefView({ brief }: { brief: MeetingBrief }) {
  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-3.5">
        <div className="mb-3">
          <SectionHeading icon={
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z" />
            </svg>
          }>Key Points</SectionHeading>
        </div>
        <BulletList items={brief.bullets} />
      </div>

      {brief.prepItems.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-3.5">
          <div className="mb-3">
            <SectionHeading icon={
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            }>Preparation</SectionHeading>
          </div>
          <BulletList items={brief.prepItems} icon="check" />
        </div>
      )}
    </>
  );
}

export default function SummaryTab() {
  const { itemType, email, meeting } = useEmail();
  const [emailResult, setEmailResult] = useState<SummaryResult | null>(null);
  const [meetingResult, setMeetingResult] = useState<MeetingBrief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (itemType === "appointment" && meeting) {
      setLoading(true);
      setError(null);
      summarizeMeeting(
        meeting.subject,
        meeting.organizer,
        meeting.start,
        meeting.end,
        meeting.location,
        meeting.attendees,
        meeting.body,
      )
        .then(setMeetingResult)
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Summarization failed");
        })
        .finally(() => setLoading(false));
    } else if (email) {
      setLoading(true);
      setError(null);
      summarizeEmail(email.subject, email.body)
        .then(setEmailResult)
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Summarization failed");
        })
        .finally(() => setLoading(false));
    }
  }, [itemType, email, meeting]);

  if (loading) return <LoadingSkeleton />;

  if (error) {
    return (
      <div className="p-4">
        <ErrorAlert message={error} />
      </div>
    );
  }

  if (itemType === "appointment" && meeting) {
    return (
      <div className="p-3 space-y-3">
        <MeetingInfoCard meeting={meeting} />
        {meetingResult && <MeetingBriefView brief={meetingResult} />}
      </div>
    );
  }

  if (!emailResult) return null;

  return (
    <div className="p-3 space-y-3">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-3.5">
        <div className="flex items-center justify-between mb-3">
          <SectionHeading icon={
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z" />
            </svg>
          }>Key Points</SectionHeading>
          <ToneBadge tone={emailResult.tone} />
        </div>
        <BulletList items={emailResult.bullets} />
      </div>

      {emailResult.actionItems.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-3.5">
          <div className="mb-3">
            <SectionHeading icon={
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            }>Action Items</SectionHeading>
          </div>
          <BulletList items={emailResult.actionItems} icon="check" />
        </div>
      )}
    </div>
  );
}
