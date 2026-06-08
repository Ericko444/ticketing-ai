CLASSIFY_PROMPT = """\
You are a support ticket router. Given the email below, decide which team should handle it.

Teams:
- IT: Hardware issues, software installation, network/VPN, device problems, system access
- Support: Product questions, billing, account issues, general customer complaints
- Helpdesk: Password resets, login problems, internal tool access, employee onboarding
- HR: Leave requests, payroll questions, benefits, workplace conduct, hiring

Respond with ONLY valid JSON in this exact format:
{{"team": "<team>", "confidence": <0.0-1.0>}}

The confidence value must reflect how certain you are. Use a value below 0.8 if the email could belong to more than one team.

Email subject: {subject}
Email body:
{body}
"""

EVALUATE_PROMPT = """\
You are a quality checker for a support ticket routing system.

A ticket was routed to the "{assigned_team}" team. Review the decision and determine if it is correct.

Teams:
- IT: Hardware issues, software installation, network/VPN, device problems, system access
- Support: Product questions, billing, account issues, general customer complaints
- Helpdesk: Password resets, login problems, internal tool access, employee onboarding
- HR: Leave requests, payroll questions, benefits, workplace conduct, hiring

Respond with ONLY valid JSON in this exact format:
{{"verdict": "<verdict>"}}

Where verdict is one of:
- "correct": The assigned team is clearly the right choice
- "uncertain": The routing is plausible but another team could also be appropriate
- "incorrect": The ticket clearly belongs to a different team

Email subject: {subject}
Email body:
{body}
Assigned team: {assigned_team}
"""
