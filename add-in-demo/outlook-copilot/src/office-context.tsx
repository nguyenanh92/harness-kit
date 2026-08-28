import { createContext, useContext, useEffect, useState } from "react";

export type ItemType = "message" | "appointment";

export interface EmailData {
  subject: string;
  sender: string;
  body: string;
}

export interface MeetingData {
  subject: string;
  organizer: string;
  start: Date;
  end: Date;
  location: string;
  body: string;        // meeting description
  attendees: string[]; // display names only, max 10
}

interface OfficeContextValue {
  itemType: ItemType | null;
  email: EmailData | null;
  meeting: MeetingData | null;
  loading: boolean;
  error: string | null;
}

const OfficeCtx = createContext<OfficeContextValue>({
  itemType: null,
  email: null,
  meeting: null,
  loading: true,
  error: null,
});

export function useEmail() {
  return useContext(OfficeCtx);
}

function readCurrentItem(): Promise<{ itemType: ItemType; email?: EmailData; meeting?: MeetingData }> {
  return new Promise((resolve, reject) => {
    const item = Office.context?.mailbox?.item;

    if (!item) {
      // Dev mode fallback — mock email
      resolve({
        itemType: "message",
        email: {
          subject: "[Dev mode] Sample email subject",
          sender: "sender@example.com",
          body: "This is a sample email body for local development. It contains multiple sentences to test the summarizer. The meeting is scheduled for next Monday at 10am. Please confirm your attendance by Friday.",
        },
      });
      return;
    }

    const isAppt = item.itemType === Office.MailboxEnums.ItemType.Appointment;

    item.body.getAsync("text", {}, (result) => {
      if (result.status === Office.AsyncResultStatus.Failed) {
        reject(new Error(result.error.message));
        return;
      }

      if (isAppt) {
        const appt = item as Office.AppointmentRead;
        const allAttendees: string[] = [];
        ([...(appt.requiredAttendees ?? []), ...(appt.optionalAttendees ?? [])])
          .slice(0, 10)
          .forEach((a) => {
            const name = (a as any).displayName || (a as any).emailAddress || "";
            if (name) allAttendees.push(name);
          });

        resolve({
          itemType: "appointment",
          meeting: {
            subject: typeof appt.subject === "string" ? appt.subject : "",
            organizer: (appt as any).organizer?.displayName ?? (appt as any).organizer?.emailAddress ?? "",
            start: (appt as any).start ?? new Date(),
            end: (appt as any).end ?? new Date(),
            location: (appt as any).location ?? "",
            body: result.value,
            attendees: allAttendees,
          },
        });
      } else {
        resolve({
          itemType: "message",
          email: {
            subject: item.subject ?? "",
            sender: (item as any).from?.emailAddress ?? "",
            body: result.value,
          },
        });
      }
    });
  });
}

export function OfficeProvider({ children }: { children: React.ReactNode }) {
  const [itemType, setItemType] = useState<ItemType | null>(null);
  const [email, setEmail] = useState<EmailData | null>(null);
  const [meeting, setMeeting] = useState<MeetingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    readCurrentItem()
      .then((data) => {
        setItemType(data.itemType);
        if (data.email) setEmail(data.email);
        if (data.meeting) setMeeting(data.meeting);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to read item");
        setLoading(false);
      });
  }, []);

  return (
    <OfficeCtx.Provider value={{ itemType, email, meeting, loading, error }}>
      {children}
    </OfficeCtx.Provider>
  );
}
