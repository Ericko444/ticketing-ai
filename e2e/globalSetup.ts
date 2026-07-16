import { execSync } from "child_process";
import * as path from "path";

const DB_PATH = path.resolve(__dirname, "../backend/ticketing.db");

export default async function globalSetup() {
  try {
    execSync(`sqlite3 "${DB_PATH}" "DELETE FROM tickets; DELETE FROM duplicate_email_log;"`);
    console.log("[e2e] DB cleared before suite");
  } catch {
    console.warn("[e2e] Could not clear DB — ensure sqlite3 is in PATH");
  }
}
