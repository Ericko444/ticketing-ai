"use client";

import { useState } from "react";

const TEAMS = ["IT", "Support", "Helpdesk", "HR"] as const;

const TEAM_SELECTED: Record<string, string> = {
  IT: "border-blue-400 bg-blue-50 text-blue-800",
  Support: "border-emerald-400 bg-emerald-50 text-emerald-800",
  Helpdesk: "border-amber-400 bg-amber-50 text-amber-800",
  HR: "border-violet-400 bg-violet-50 text-violet-800",
};

interface SupervisorModalProps {
  onConfirm: (team: string) => void;
  onCancel: () => void;
}

export default function SupervisorModal({ onConfirm, onCancel }: SupervisorModalProps) {
  const [selectedTeam, setSelectedTeam] = useState<string>(TEAMS[0]);

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 pt-6 pb-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">Override Team Assignment</h2>
          <p className="text-xs text-slate-500 mt-0.5">Select the correct team for this ticket</p>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 gap-2">
            {TEAMS.map((t) => (
              <button
                key={t}
                onClick={() => setSelectedTeam(t)}
                className={`p-3 rounded-lg border-2 text-sm font-medium text-left transition-all ${
                  selectedTeam === t
                    ? TEAM_SELECTED[t]
                    : "border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="px-6 pb-6 flex gap-2 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(selectedTeam)}
            className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 font-medium transition-colors"
          >
            Confirm override
          </button>
        </div>
      </div>
    </div>
  );
}
