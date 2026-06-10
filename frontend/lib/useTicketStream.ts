"use client";

import { useEffect, useState } from "react";
import type { Ticket } from "./api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useTicketStream(): Ticket[] {
  const [events, setEvents] = useState<Ticket[]>([]);

  useEffect(() => {
    let es: EventSource;
    let retryDelay = 1000;
    let retryTimer: ReturnType<typeof setTimeout>;

    function connect() {
      es = new EventSource(`${API_URL}/stream`);

      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "ticket_routed" && data.ticket) {
            setEvents((prev) => [data.ticket as Ticket, ...prev]);
            retryDelay = 1000;
          }
        } catch {
          // ignore malformed SSE payloads
        }
      };

      es.onerror = () => {
        es.close();
        retryTimer = setTimeout(() => {
          retryDelay = Math.min(retryDelay * 2, 30000);
          connect();
        }, retryDelay);
      };
    }

    connect();

    return () => {
      clearTimeout(retryTimer);
      es?.close();
    };
  }, []);

  return events;
}
