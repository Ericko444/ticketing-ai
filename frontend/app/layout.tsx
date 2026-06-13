import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TicketAI",
  description: "AI-powered email ticketing dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur-sm">
          <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md bg-indigo-600 flex items-center justify-center text-white text-xs font-bold select-none">
                T
              </div>
              <span className="font-semibold text-slate-900 tracking-tight">TicketAI</span>
            </div>
            <nav className="flex items-center gap-6 text-sm">
              <Link
                href="/"
                className="text-slate-500 hover:text-slate-900 font-medium transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/supervisor"
                className="text-slate-500 hover:text-slate-900 font-medium transition-colors"
              >
                Supervisor Queue
              </Link>
            </nav>
          </div>
        </header>
        <div className="flex-1">{children}</div>
      </body>
    </html>
  );
}
