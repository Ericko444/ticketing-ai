const TEAM_COLORS: Record<string, string> = {
  IT: "bg-blue-100 text-blue-800",
  Support: "bg-green-100 text-green-800",
  Helpdesk: "bg-yellow-100 text-yellow-800",
  HR: "bg-purple-100 text-purple-800",
};

export default function TeamBadge({ team }: { team: string }) {
  const color = TEAM_COLORS[team] ?? "bg-gray-100 text-gray-800";
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}
    >
      {team}
    </span>
  );
}
