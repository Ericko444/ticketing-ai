# Intent: Department Authentication

Confirmed via interview-me on 2026-07-16.

- **Outcome:** Email+password login gates the app. Team members only see/query their own team's tickets; the supervisor logs in through the same system but retains full visibility across all teams.
- **User:** IT/Support/Helpdesk/HR staff (team-scoped) and the single global supervisor (unscoped), both authenticated via a new `users` table (email, password hash, team/role) that replaces `config.yaml`'s member-list role.
- **Why now:** Dashboard is currently unauthenticated and shows every team's tickets to everyone — this is the top item on the roadmap and needs to land before other features assume access control exists.
- **Success:** Enforcement is server-side, not cosmetic — `GET /tickets`, `GET /tickets/{id}`, and supervisor endpoints all filter/reject by the logged-in user's team; a direct link to another team's ticket 403/404s. Session held via HTTP-only cookie so SSE (`/stream`) works without a workaround.
- **Constraint:** No admin UI. Accounts are provisioned once via a seed script that migrates the current `config.yaml` roster into `users` and sets initial passwords.
- **Out of scope:** Self-service registration, forgot-password/reset flow, per-team supervisors, and an admin UI for managing accounts — all deferred to later roadmap items.

## Key decisions from the interview

1. Auth is email+password, not magic link — a new `users` table owns credentials (not `config.yaml`).
2. `config.yaml` is trimmed to team metadata (names, supervisor email); team membership moves to the DB.
3. Supervisor authenticates through the same system as team members (role-based, not a separate gate).
4. Team scoping is enforced server-side on every relevant endpoint, not just hidden in the UI.
5. Session is an HTTP-only cookie, chosen specifically because `EventSource`/SSE can't send `Authorization` headers but does send cookies automatically — avoids a token-in-query-string workaround for `/stream`.
6. Accounts are provisioned via a one-time seed script, not open registration — avoids anyone self-claiming a team.
7. No password reset flow in v1 — recovery is an admin re-running the seed script / manual DB update.
