"use client";

import { useState } from "react";

const TEAMS = ["IT", "Support", "Helpdesk", "HR"] as const;

interface SupervisorModalProps {
  onConfirm: (team: string) => void;
  onCancel: () => void;
}

export default function SupervisorModal({
  onConfirm,
  onCancel,
}: SupervisorModalProps) {
  const [selectedTeam, setSelectedTeam] = useState<string>(TEAMS[0]);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-80">
        <h2 className="text-lg font-semibold mb-4">Override Team Assignment</h2>
        <label className="block text-sm text-gray-600 mb-1">Select team</label>
        <select
          value={selectedTeam}
          onChange={(e) => setSelectedTeam(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm mb-4"
        >
          {TEAMS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <div className="flex gap-2 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded border hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(selectedTeam)}
            className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
