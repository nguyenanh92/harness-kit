import Anthropic from "@anthropic-ai/sdk";
import { getApiKey, getProvider } from "./key-store";
import { deepseekSummarize, deepseekReplies, deepseekTranslate, deepseekSummarizeMeeting, deepseekRsvp } from "./deepseek-client";

const ANTHROPIC_MODEL = "claude-haiku-4-5-20251001";

export interface SummaryResult {
  bullets: string[];
  actionItems: string[];
  tone?: "urgent" | "formal" | "friendly" | "neutral";
}

export type ReplyTone = "professional" | "friendly" | "brief";

export interface ReplyDraft {
  tone: ReplyTone;
  text: string;
}

export interface MeetingBrief {
  bullets: string[];
  prepItems: string[];
}

export type RsvpType = "accept" | "decline" | "tentative";

export interface RsvpDraft {
  type: RsvpType;
  text: string;
}

export function formatMeetingTime(dt: Date): string {
  return dt.toLocaleString("en-US", {
    weekday: "short", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function makeAnthropicClient(): Anthropic {
  const key = getApiKey("anthropic");
  if (!key) throw new Error("No Anthropic API key. Open Settings tab.");
  return new Anthropic({ apiKey: key, dangerouslyAllowBrowser: true });
}

export async function summarizeEmail(subject: string, body: string): Promise<SummaryResult> {
  if (getProvider() === "deepseek") return deepseekSummarize(subject, body);

  const message = await makeAnthropicClient().messages.create({
    model: ANTHROPIC_MODEL,
    max_tokens: 512,
    messages: [
      {
        role: "user",
        content: `Summarize this email concisely.

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
      },
    ],
  });

  const text = message.content[0].type === "text" ? message.content[0].text : "";
  return JSON.parse(text) as SummaryResult;
}

export async function generateReplies(
  subject: string,
  body: string,
  context?: string,
): Promise<ReplyDraft[]> {
  if (getProvider() === "deepseek") return deepseekReplies(subject, body, context);

  const contextLine = context?.trim() ? `\nAdditional user instruction: ${context.trim()}` : "";

  const message = await makeAnthropicClient().messages.create({
    model: ANTHROPIC_MODEL,
    max_tokens: 768,
    messages: [
      {
        role: "user",
        content: `Generate 3 reply drafts for this email.

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
      },
    ],
  });

  const text = message.content[0].type === "text" ? message.content[0].text : "[]";
  return JSON.parse(text) as ReplyDraft[];
}

export async function translateEmail(body: string, targetLanguage: string): Promise<string> {
  if (getProvider() === "deepseek") return deepseekTranslate(body, targetLanguage);

  const message = await makeAnthropicClient().messages.create({
    model: ANTHROPIC_MODEL,
    max_tokens: 1024,
    messages: [
      {
        role: "user",
        content: `Translate the following email body to ${targetLanguage}. Return only the translated text, no explanation, no extra formatting.\n\n${body}`,
      },
    ],
  });

  const text = message.content[0].type === "text" ? message.content[0].text : "";
  return text.trim();
}

export async function summarizeMeeting(
  subject: string,
  organizer: string,
  start: Date,
  end: Date,
  location: string,
  attendees: string[],
  description: string,
): Promise<MeetingBrief> {
  if (getProvider() === "deepseek") {
    return deepseekSummarizeMeeting(subject, organizer, start, end, location, attendees, description);
  }

  const attendeeList = attendees.length > 0 ? attendees.join(", ") : "Not specified";

  const message = await makeAnthropicClient().messages.create({
    model: ANTHROPIC_MODEL,
    max_tokens: 512,
    messages: [{
      role: "user",
      content: `Analyze this meeting invitation and provide a structured briefing.

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
    }],
  });

  const text = message.content[0].type === "text" ? message.content[0].text : "";
  return JSON.parse(text) as MeetingBrief;
}

export async function generateRsvp(
  subject: string,
  organizer: string,
  start: Date,
  description: string,
): Promise<RsvpDraft[]> {
  if (getProvider() === "deepseek") {
    return deepseekRsvp(subject, organizer, start, description);
  }

  const message = await makeAnthropicClient().messages.create({
    model: ANTHROPIC_MODEL,
    max_tokens: 512,
    messages: [{
      role: "user",
      content: `Draft 3 short RSVP responses for this meeting invitation.

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
    }],
  });

  const text = message.content[0].type === "text" ? message.content[0].text : "[]";
  return JSON.parse(text) as RsvpDraft[];
}
