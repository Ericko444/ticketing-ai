# Phase 7 Summary: Frontend

**Date:** 2026-06-10
**Commits:** c249758 (Task 16), 1879920 (Task 17), 2611095 (Task 18), 1cdc1fe (Task 19)
**Tests:** 14 new — all passing. Build clean. Lint clean.

## What Was Built

### Task 16 — Scaffold (`c249758`)
- Next.js 16.2.9 + React 19 + Tailwind v4 + TypeScript via `create-next-app`
- `lib/api.ts`: `Ticket` interface + typed `getTickets`, `getTicket`, `approveRouting`, `overrideRouting` fetch wrappers
- `lib/useTicketStream.ts`: `EventSource` hook; reconnects with exponential backoff (1 s → 30 s cap) on `onerror`
- `jest.config.ts` / `jest.setup.ts`: `next/jest` + `@testing-library/jest-dom`; explicit `moduleNameMapper` for `@/` alias (needed because `next/jest`'s auto-mapper didn't propagate to subdirectory test files)
- `.env.local.example` with `NEXT_PUBLIC_API_URL`

### Task 17 — Dashboard (`1879920`)
- `app/page.tsx`: loads initial tickets with `getTickets()`, merges SSE stream via `useMemo` (avoids `react-hooks/set-state-in-effect` lint rule)
- `components/TicketCard.tsx`: subject, sender, `TeamBadge`, ⚠ pending-review indicator, timestamp
- `components/TeamBadge.tsx`: IT=blue, Support=green, Helpdesk=yellow, HR=purple (Tailwind `bg-*/text-*` pairs)

### Task 18 — Ticket detail (`2611095`)
- `components/TicketDetail.tsx`: full detail view — subject, sender, body, team, confidence %, evaluator verdict, supervisor action, final team, status, received timestamp
- `app/tickets/[id]/page.tsx`: thin client wrapper; extracts `id` with React's `use()` on the async `params` promise (Next.js 15+ async params API), delegates rendering to `TicketDetail`
- Tests target `TicketDetail` directly to avoid `use(Promise.resolve())` jsdom incompatibility (React's `use()` suspends even on pre-resolved native promises; requires `Suspense` or a different testing strategy)

### Task 19 — Supervisor queue (`1cdc1fe`)
- `app/supervisor/page.tsx`: fetches all tickets, filters `status === "pending_supervisor"`, table with subject / proposed team / confidence / verdict / actions; optimistic removal on approve or override
- `components/SupervisorModal.tsx`: modal with `<select>` for IT/Support/Helpdesk/HR and Confirm/Cancel

## Files Created / Modified

| File | Change |
|---|---|
| `frontend/lib/api.ts` | New — Ticket type + fetch functions |
| `frontend/lib/useTicketStream.ts` | New — SSE hook with backoff reconnect |
| `frontend/.env.local.example` | New — env var docs |
| `frontend/jest.config.ts` | New — jest config |
| `frontend/jest.setup.ts` | New — jest-dom setup |
| `frontend/package.json` | Modified — added test/test:watch scripts |
| `frontend/app/layout.tsx` | Modified — updated metadata title |
| `frontend/app/page.tsx` | New — dashboard |
| `frontend/components/TicketCard.tsx` | New |
| `frontend/components/TeamBadge.tsx` | New |
| `frontend/__tests__/TicketCard.test.tsx` | New — 6 tests |
| `frontend/components/TicketDetail.tsx` | New — testable detail component |
| `frontend/app/tickets/[id]/page.tsx` | New — route wrapper |
| `frontend/__tests__/tickets/TicketDetailPage.test.tsx` | New — 3 tests |
| `frontend/app/supervisor/page.tsx` | New — supervisor queue |
| `frontend/components/SupervisorModal.tsx` | New — override modal |
| `frontend/__tests__/supervisor/SupervisorPage.test.tsx` | New — 5 tests |

## Decisions Made During Implementation

- **`use()` + jsdom**: React's `use(promise)` hook suspends even on `Promise.resolve()` in jsdom because native promises lack React's internal `_status` / `_result` properties. Fixed by extracting `TicketDetail` as a plain client component (accepts `id: string`) and keeping the page as a minimal wrapper. Tests target `TicketDetail` directly.
- **SSE merge via `useMemo`**: The Next.js eslint config includes `react-hooks/set-state-in-effect` which disallows calling `setState` inside an effect body. Changed the stream-ticket merge from a secondary `useEffect` to a `useMemo` that derives the combined list from both `initialTickets` and `streamTickets`.
- **`moduleNameMapper`**: Despite `next/jest` auto-handling tsconfig paths, `@/` alias resolution failed in tests located in subdirectories (`__tests__/tickets/`, `__tests__/supervisor/`). Added explicit `"^@/(.*)$": "<rootDir>/$1"` to `jest.config.ts` to fix it.
- **`ts-node`**: Required for jest to parse the `jest.config.ts` TypeScript file.
