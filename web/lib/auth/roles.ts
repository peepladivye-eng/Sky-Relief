import type { Role } from "./session"

export interface RoleConfig {
  label: string
  labelHi: string
  description: string
  descriptionHi: string
  defaultTab: "reports" | "brief" | "limits"
  expandTrace: boolean
}

export const ROLE_CONFIG: Record<Role, RoleConfig> = {
  responder: {
    label: "Responder",
    labelHi: "रिस्पॉन्डर",
    description: "Starts with the priority list and ground reports.",
    descriptionHi: "प्राथमिकता सूची और ज़मीनी रिपोर्ट से शुरू होता है।",
    defaultTab: "reports",
    expandTrace: false,
  },
  analyst: {
    label: "Analyst",
    labelHi: "विश्लेषक",
    description: "Starts with the agent run open, so you can see each step.",
    descriptionHi: "एजेंट रन खुला रहता है ताकि हर चरण दिखे।",
    defaultTab: "reports",
    expandTrace: true,
  },
  observer: {
    label: "Observer",
    labelHi: "पर्यवेक्षक",
    description: "Starts with the WhatsApp brief.",
    descriptionHi: "व्हाट्सऐप संक्षेप से शुरू होता है।",
    defaultTab: "brief",
    expandTrace: false,
  },
}
