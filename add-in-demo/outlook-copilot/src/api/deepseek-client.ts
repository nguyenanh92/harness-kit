import { getApiKey } from "./key-store";
import type { SummaryResult, ReplyDraft, MeetingBrief, RsvpDraft } from "./claude-client";
import { formatMeetingTime } from "./claude-client";

const BASE_URL = "https://api.deepseek.com/chat/completions";
const MODEL = "deepseek-chat";

async function chat(prompt: string, maxTokens: number): Promise<string> {
  const key = getApiKey("deepseek");
  if (!key) throw new Error("No DeepSeek API key. Open Settings tab.");

  const res = await fetch(BASE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: "user", content: prompt }],
      max_tokens: maxTokens,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { error?: { message?: string } };
    throw new Error(`DeepSeek ${res.status}: ${body.error?.message ?? res.statusText}`);
  }

  const data = await res.json() as { choices: { message: { content: string } }[] };
  return data.choices[0].message.content;
}

export async function deepseekSummarize(subject: string, body: string): Promise<SummaryResult> {
  const text = await chat(
    `Summarize this email concisely.

Subject: ${subject}
Body:
${body}

Respond in JSON only (no markdown):
{
  "bullets": ["key point 1", "key point 2", "key point 3"],
  "actionItems": ["action 1", "action 2"],
  "tone": "urgent | formal | friendly | neutral"
}
Keep bullets <=15 words each. actionItems may be empty array if none.
tone MUST be exactly one of: urgent, formal, friendly, neutral.`,
    512,
  );
  return JSON.parse(text) as SummaryResult;
}

export async function deepseekReplies(
  subject: string,
  body: string,
  context?: string,
): Promise<ReplyDraft[]> {
  const contextLine = context?.trim() ? `\nAdditional user instruction: ${context.trim()}` : "";

  const text = await chat(
    `Generate 3 reply drafts for this email.

Subject: ${subject}
Body:
${body}

Respond in JSON only (no markdown):
[
  { "tone": "professional", "text": "..." },
  { "tone": "friendly", "text": "..." },
  { "tone": "brief", "text": "..." }
]
Each reply should be 1-3 sentences. Do not include a subject line.${contextLine}`,
    768,
  );
  return JSON.parse(text) as ReplyDraft[];
}

export async function deepseekTranslate(body: string, targetLanguage: string): Promise<string> {
  const text = await chat(
    `Translate the following email body to ${targetLanguage}. Return only the translated text, no explanation, no extra formatting.\n\n${body}`,
    1024,
  );
  return text.trim();
}

export async function deepseekSummarizeMeeting(
  subject: string,
  organizer: string,
  start: Date,
  end: Date,
  location: string,
  attendees: string[],
  description: string,
): Promise<MeetingBrief> {
  const attendeeList = attendees.length > 0 ? attendees.join(", ") : "Not specified";

  const text = await chat(
    `Analyze this meeting invitation and provide a structured briefing.

Meeting: ${subject}
Organizer: ${organizer}
Time: ${formatMeetingTime(start)} – ${formatMeetingTime(end)}
Location: ${location || "Not specified"}
Attendees: ${attendeeList}
Description:
${description}

Respond in JSON only (no markdown):
{
  "bullets": ["key point about purpose/agenda 1", "key point 2", "key point 3"],
  "prepItems": ["preparation item 1", "preparation item 2"]
}
bullets: meeting purpose, agenda, key context. <=15 words each. Max 4.
prepItems: what to prepare, review, or bring. May be empty array if none.`,
    512,
  );
  return JSON.parse(text) as MeetingBrief;
}

export async function deepseekRsvp(
  subject: string,
  organizer: string,
  start: Date,
  description: string,
): Promise<RsvpDraft[]> {
  const text = await chat(
    `Draft 3 short RSVP responses for this meeting invitation.

Meeting: ${subject}
Organizer: ${organizer}
Time: ${formatMeetingTime(start)}
Description: ${description.slice(0, 500)}

Respond in JSON only (no markdown):
[
  { "type": "accept", "text": "..." },
  { "type": "decline", "text": "..." },
  { "type": "tentative", "text": "..." }
]
Each response: 1-2 sentences, professional tone, no subject line.`,
    512,
  );
  return JSON.parse(text) as RsvpDraft[];
}
