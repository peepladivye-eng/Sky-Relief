export const en = {
  // Nav
  nProduct: "Product",
  nHow: "How it works",
  nEvidence: "Evidence",
  nLimits: "Limits",
  signIn: "Sign in",
  signOut: "Sign out",
  openCc: "Open command center",

  // Hero
  badge: "Built for flood response",
  h1: "Know who is cut off before the water recedes.",
  sub: "SkyRelief reads radar before and after a flood, checks it against ground reports and rainfall, and ranks the villages rescuers should reach first.",
  ctaPrimary: "Open the Assam 2022 event",
  srcRain: "Rainfall",
  srcReports: "Ground reports",

  // Hero cards
  illus: "Illustration",
  statArea: "flooded, 45.3% of the region",
  statEvent: "Assam floods, June 2022",
  signalLost: "Signal lost",
  flooded: "Flooded",
  statScore: "Priority score",

  // Evidence
  evidence: "Every sentence in the brief points to a source. Sentences without one are removed.",
  chRadar: "Radar mask",
  chRoad: "Road map",
  chTower: "Tower map",

  // Features
  featTitle: "What rescuers get",
  featLead: "A ranked list, a map and a message they can send.",
  f1h: "Silent-flooded villages",
  f1p: "Flooded on radar and no reports received. Marked Signal lost and ranked high.",
  f2h: "Roads, bridges and towers",
  f2p: "Likely impassable and likely offline, inferred from flood extent. Not a structural inspection.",
  f3h: "Brief in English and Hindi",
  f3p: "Short enough for WhatsApp. Copy it and send it.",

  // How it works
  howTitle: "How it works",
  s1h: "Compare radar",
  s1p: "Sentinel-1 images from before and after the flood.",
  s2h: "Build the flood mask",
  s2p: "Water that was not there before is marked as flooded.",
  s3h: "Check the evidence",
  s3p: "Ground reports and rainfall confirm or contradict the radar.",
  s4h: "Rank and write",
  s4p: "Villages are scored and the brief is written with sources.",

  // Preview
  pvTitle: "The screen rescuers use",

  // Honest
  honTitle: "Honest by design",
  honLead: "A rescue tool that overstates is worse than none.",
  h1h: "Skipped steps show as skipped",
  h1p: "If a check did not run, you see it in amber with the reason.",
  h2h: "Not measured stays not measured",
  h2p: "No accuracy figure appears unless it was computed.",
  h3h: "Likely, not destroyed",
  h3p: "Flood extent shows where roads and towers are probably affected. It does not prove damage.",

  // CTA
  ctaTitle: "See who to reach first",
  ctaLead: "Open a real flood event and run the analysis.",
  readLimits: "Read the limits",

  // Footer
  foot: "Built for the Multimodal AI Hackathon 2026, Track B",

  // Login
  loginTitle: "Sign in to SkyRelief",
  loginSub: "Open the flood response workspace.",
  roleLabel: "I am a",
  rResp: "Responder",
  rAna: "Analyst",
  rObs: "Observer",
  email: "Email",
  password: "Password",
  showPw: "Show",
  hidePw: "Hide",
  showPwLabel: "Show password",
  hidePwLabel: "Hide password",
  remember: "Remember this device",
  forgot: "Forgot password?",
  forgotHelp: "Ask the team admin to reset it.",
  loginBtn: "Sign in",
  loginLoading: "Signing in\u2026",
  loginSuccess: "Signed in. Opening your event\u2026",
  loginError: "Email or password is not right. Check them and try again.",
  loginRateLimit: "Too many tries. Wait a minute and try again.",
  or: "or",
  guest: "Continue as guest (Observer)",
  loginNote: "Sign-in only controls who can open the workspace. It does not change any data or score.",

  // Events
  eventsTitle: "Choose a flood event",
  eventsEmpty: "No events found. Check that the data folder has at least one event.",
  eventsLoading: "Loading events\u2026",

  // Command center
  runAnalysis: "Run analysis",
  analysing: "Analysing\u2026",
  limitsNav: "Limits and evaluation",
  sampleChip: "Sample data",

  // Limits
  limitsTitle: "Limits and evaluation",
  backToMap: "Back to map",

  // 404
  notFoundTitle: "Page not found",
  notFoundSub: "The page you are looking for does not exist.",
  notFoundHome: "Go home",
} as const

export const hi: { [K in keyof typeof en]: string } = {
  nProduct: "उत्पाद",
  nHow: "कैसे काम करता है",
  nEvidence: "प्रमाण",
  nLimits: "सीमाएँ",
  signIn: "साइन इन",
  signOut: "साइन आउट",
  openCc: "कमांड सेंटर खोलें",

  badge: "बाढ़ राहत के लिए बना",
  h1: "पानी उतरने से पहले जानें कि कौन कट गया है।",
  sub: "SkyRelief बाढ़ से पहले और बाद के रडार चित्र पढ़ता है, ज़मीनी रिपोर्ट और वर्षा से मिलाता है, और बताता है कि बचावकर्मी सबसे पहले किन गाँवों तक पहुँचें।",
  ctaPrimary: "असम 2022 घटना खोलें",
  srcRain: "वर्षा",
  srcReports: "ज़मीनी रिपोर्ट",

  illus: "चित्रण",
  statArea: "बाढ़ग्रस्त, क्षेत्र का 45.3%",
  statEvent: "असम बाढ़, जून 2022",
  signalLost: "संपर्क टूटा",
  flooded: "बाढ़ग्रस्त",
  statScore: "प्राथमिकता अंक",

  evidence: "संक्षेप का हर वाक्य एक स्रोत से जुड़ा है। बिना स्रोत वाले वाक्य हटा दिए जाते हैं।",
  chRadar: "रडार मास्क",
  chRoad: "सड़क मानचित्र",
  chTower: "टावर मानचित्र",

  featTitle: "बचावकर्मियों को क्या मिलता है",
  featLead: "एक क्रमबद्ध सूची, एक नक्शा और भेजने लायक संदेश।",
  f1h: "चुपचाप डूबे गाँव",
  f1p: "रडार पर बाढ़ और कोई रिपोर्ट नहीं। इन्हें संपर्क टूटा चिह्नित कर ऊपर रखा जाता है।",
  f2h: "सड़कें, पुल और टावर",
  f2p: "बाढ़ के दायरे से अनुमानित: संभवतः अवरुद्ध और बंद। संरचनात्मक जाँच नहीं।",
  f3h: "अंग्रेज़ी और हिन्दी में संक्षेप",
  f3p: "व्हाट्सऐप के लिए छोटा। कॉपी करें और भेजें।",

  howTitle: "कैसे काम करता है",
  s1h: "रडार की तुलना",
  s1p: "बाढ़ से पहले और बाद की Sentinel-1 छवियाँ।",
  s2h: "बाढ़ मास्क बनाना",
  s2p: "जो पानी पहले नहीं था, उसे बाढ़ चिह्नित किया जाता है।",
  s3h: "प्रमाण जाँचना",
  s3p: "ज़मीनी रिपोर्ट और वर्षा रडार की पुष्टि या खंडन करती हैं।",
  s4h: "क्रम और लेखन",
  s4p: "बस्तियों को अंक मिलते हैं और संक्षेप स्रोतों सहित लिखा जाता है।",

  pvTitle: "बचावकर्मियों की स्क्रीन",

  honTitle: "ईमानदारी से बना",
  honLead: "बढ़ा-चढ़ाकर बताने वाला राहत उपकरण न होने से बुरा है।",
  h1h: "छोड़े गए चरण छोड़े हुए दिखते हैं",
  h1p: "अगर कोई जाँच नहीं चली, तो वह कारण सहित पीले रंग में दिखती है।",
  h2h: "मापा नहीं गया तो मापा नहीं गया",
  h2p: "जो गणना नहीं हुई, उसका कोई सटीकता आँकड़ा नहीं दिखता।",
  h3h: "संभावित, नष्ट नहीं",
  h3p: "बाढ़ का दायरा बताता है कि सड़कें और टावर शायद प्रभावित हैं। यह क्षति का प्रमाण नहीं।",

  ctaTitle: "देखें सबसे पहले कहाँ पहुँचना है",
  ctaLead: "एक असली बाढ़ घटना खोलें और विश्लेषण चलाएँ।",
  readLimits: "सीमाएँ पढ़ें",

  foot: "मल्टीमॉडल AI हैकाथॉन 2026, ट्रैक B के लिए बनाया गया",

  loginTitle: "SkyRelief में साइन इन करें",
  loginSub: "बाढ़ राहत कार्यक्षेत्र खोलें।",
  roleLabel: "मैं हूँ",
  rResp: "रिस्पॉन्डर",
  rAna: "विश्लेषक",
  rObs: "पर्यवेक्षक",
  email: "ईमेल",
  password: "पासवर्ड",
  showPw: "दिखाएँ",
  hidePw: "छिपाएँ",
  showPwLabel: "पासवर्ड दिखाएँ",
  hidePwLabel: "पासवर्ड छिपाएँ",
  remember: "इस डिवाइस को याद रखें",
  forgot: "पासवर्ड भूल गए?",
  forgotHelp: "टीम एडमिन से रीसेट करने को कहें।",
  loginBtn: "साइन इन",
  loginLoading: "साइन इन हो रहा है…",
  loginSuccess: "साइन इन हो गया। आपकी घटना खुल रही है…",
  loginError: "ईमेल या पासवर्ड सही नहीं है। जाँचकर फिर कोशिश करें।",
  loginRateLimit: "बहुत अधिक प्रयास। एक मिनट बाद फिर कोशिश करें।",
  or: "या",
  guest: "अतिथि के रूप में जारी रखें (पर्यवेक्षक)",
  loginNote: "साइन-इन केवल यह तय करता है कि कार्यक्षेत्र कौन खोल सकता है। यह किसी डेटा या अंक को नहीं बदलता।",

  eventsTitle: "बाढ़ घटना चुनें",
  eventsEmpty: "कोई घटना नहीं मिली। जाँचें कि डेटा फ़ोल्डर में कम से कम एक घटना है।",
  eventsLoading: "घटनाएँ लोड हो रही हैं…",

  runAnalysis: "विश्लेषण चलाएँ",
  analysing: "विश्लेषण हो रहा है…",
  limitsNav: "सीमाएँ और मूल्यांकन",
  sampleChip: "नमूना डेटा",

  limitsTitle: "सीमाएँ और मूल्यांकन",
  backToMap: "मानचित्र पर वापस",

  notFoundTitle: "पृष्ठ नहीं मिला",
  notFoundSub: "आप जिस पृष्ठ को खोज रहे हैं वह मौजूद नहीं है।",
  notFoundHome: "मुखपृष्ठ पर जाएँ",
}

export type Strings = { [K in keyof typeof en]: string }
export type Lang = "en" | "hi"

export function t(lang: Lang): Strings {
  return lang === "hi" ? hi : en
}
