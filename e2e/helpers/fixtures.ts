export interface EmailFixture {
  subject: string;
  body: string;
  sender: string;
  team: "IT" | "Support" | "Helpdesk" | "HR";
}

const IT: EmailFixture[] = [
  {
    subject: "VPN keeps disconnecting every 30 minutes",
    body: "My VPN drops connection repeatedly when working from home. Windows 11 laptop, Cisco AnyConnect v4.10. Tried reinstalling — no luck.",
    sender: "alice@acme.com",
    team: "IT",
  },
  {
    subject: "Cannot install software — missing admin rights",
    body: "I need to install Figma on my Mac but the OS says I don't have administrator privileges. Can you grant me rights or install it remotely?",
    sender: "carlos@acme.com",
    team: "IT",
  },
  {
    subject: "External monitor showing no signal",
    body: "The external monitor at my standing desk stopped working after I switched USB-C adapters. Laptop screen is fine. Dell U2722D monitor.",
    sender: "diana@acme.com",
    team: "IT",
  },
  {
    subject: "Laptop blue-screen after Windows update",
    body: "My work laptop BSODs on startup since the automatic Windows update last night. Error: DRIVER_IRQL_NOT_LESS_OR_EQUAL.",
    sender: "evan@acme.com",
    team: "IT",
  },
];

const SUPPORT: EmailFixture[] = [
  {
    subject: "Order #58291 still not received after 3 weeks",
    body: "I placed order #58291 on the 1st and it still hasn't arrived. Tracking shows 'In Transit' since day 2. Please investigate.",
    sender: "customer1@gmail.com",
    team: "Support",
  },
  {
    subject: "Wrong item delivered — need replacement",
    body: "I ordered a blue jacket size M but received a red jacket size L. Please arrange a return label and send the correct item.",
    sender: "customer2@yahoo.com",
    team: "Support",
  },
  {
    subject: "Subscription charged after cancellation",
    body: "I cancelled my subscription on the 15th but was still billed on the 30th. Please issue a full refund to my card ending in 4829.",
    sender: "customer3@outlook.com",
    team: "Support",
  },
  {
    subject: "Account locked — cannot log in",
    body: "My account has been locked after too many login attempts. I'm unable to access my purchase history or pending orders.",
    sender: "customer4@gmail.com",
    team: "Support",
  },
];

const HR: EmailFixture[] = [
  {
    subject: "Annual leave request — July 14–25",
    body: "I'd like to request annual leave from 14 July to 25 July inclusive. I have 12 days of remaining entitlement. Please confirm.",
    sender: "emily@acme.com",
    team: "HR",
  },
  {
    subject: "Maternity leave — starting paperwork",
    body: "I'm 28 weeks pregnant and need to begin the maternity leave process. What forms do I need to submit and by when?",
    sender: "fiona@acme.com",
    team: "HR",
  },
  {
    subject: "Employment verification letter for mortgage",
    body: "My bank is requesting an official employment verification letter for a mortgage application. Could HR provide this on company letterhead?",
    sender: "george@acme.com",
    team: "HR",
  },
];

const HELPDESK: EmailFixture[] = [
  {
    subject: "Password reset — locked out of company account",
    body: "I've been locked out of my company email after 5 failed login attempts. I'm on-site but can't work. Please reset my password urgently.",
    sender: "henry@acme.com",
    team: "Helpdesk",
  },
  {
    subject: "New employee — no system access on first week",
    body: "I started Monday and still have no access to Slack, Jira, Confluence, or the internal wiki. My manager is Sarah Johnson.",
    sender: "iris@acme.com",
    team: "Helpdesk",
  },
  {
    subject: "Two-factor authentication app not working",
    body: "My authenticator app was wiped when I got a new phone. I'm unable to log into any company systems. Need MFA reset.",
    sender: "james@acme.com",
    team: "Helpdesk",
  },
];

const AMBIGUOUS: EmailFixture[] = [
  {
    subject: "I need help",
    body: "Something is wrong and I'm not sure who to contact. Can someone please assist me as soon as possible?",
    sender: "confused@acme.com",
    team: "IT",
  },
  {
    subject: "Urgent — please help",
    body: "I have an urgent problem. I'm not sure which department handles this.",
    sender: "urgent@acme.com",
    team: "IT",
  },
  {
    subject: "Question about company policy",
    body: "Hi, I had a quick question but I'm not sure who to ask. Could someone direct me to the right team?",
    sender: "inquirer@acme.com",
    team: "IT",
  },
];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export const fixtures = {
  it: (): EmailFixture => pick(IT),
  support: (): EmailFixture => pick(SUPPORT),
  hr: (): EmailFixture => pick(HR),
  helpdesk: (): EmailFixture => pick(HELPDESK),
  ambiguous: (): EmailFixture => pick(AMBIGUOUS),
  /** Returns one random fixture from each team. */
  onePerTeam: (): EmailFixture[] => [pick(IT), pick(SUPPORT), pick(HR), pick(HELPDESK)],
};
