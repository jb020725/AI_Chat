export type LeadDraft = Partial<{
  name: string;
  email: string;
  phone: string;
  target_country: string;
  preferred_intake: string; // e.g., "Fall 2025", "January 2026"
  study_level: string; // bachelor, master, phd, diploma
  gpa_grades: string; // e.g., "3.5/4.0", "85%", "A-"
  study_field: string; // e.g., "Computer Science", "Business Administration"
}>;

const months = [
  "january","february","march","april","may","june",
  "july","august","september","october","november","december",
  "jan","feb","mar","apr","jun","jul","aug","sep","oct","nov","dec"
];

const supportedCountries = {
  "united states": "USA", "usa": "USA", "u.s.": "USA", "us": "USA", "america": "USA",
  "canada": "Canada", "canadian": "Canada",
  "uk": "UK", "united kingdom": "UK", "britain": "UK", "england": "UK",
  "australia": "Australia", "australian": "Australia",
  "south korea": "South Korea", "korea": "South Korea", "korean": "South Korea", "kores": "South Korea"
};

const studyLevels = {
  "bachelor": "Bachelor", "bachelors": "Bachelor", "undergraduate": "Bachelor", "ug": "Bachelor",
  "master": "Master", "masters": "Master", "graduate": "Master", "ms": "Master", "ma": "Master",
  "phd": "PhD", "doctorate": "PhD", "doctor": "PhD", "dphil": "PhD",
  "diploma": "Diploma", "certificate": "Diploma"
};

function titleCase(s: string) {
  return s
    .toLowerCase()
    .replace(/\b([a-z])/g, (m, c) => c.toUpperCase())
    .replace(/\s+/g, " ")
    .trim();
}

function normPhone(raw: string) {
  const cleaned = raw.trim().replace(/(?!^\+)[^\d]/g, "");
  return cleaned.startsWith("+") ? cleaned : cleaned.replace(/^\+?/, "+");
}

function guessNameFromEmail(email: string | undefined) {
  if (!email) return undefined;
  const local = email.split("@")[0];
  // janak.bhat_34 -> "Janak Bhat"
  const candidate = local.replace(/[._-]+/g, " ").replace(/\d+/g, " ").trim();
  if (candidate.length >= 2) return titleCase(candidate);
  return undefined;
}

function guessNameFromText(text: string) {
  // 1) Explicit patterns
  const lower = text.toLowerCase();
  let m =
    lower.match(/(?:my name is|name\s*:\s*|this is|i am|i'm)\s+([a-z][a-z\s.'-]{1,60})/) ||
    lower.match(/^\s*([a-z][a-z\s.'-]{1,60})\s*,/); // bare name at start before a comma
  if (m) return titleCase(m[1]);

  // 2) If the message looks like "Firstname Lastname, email, phone"
  const firstClause = text.split(",")[0]?.trim();
  if (firstClause && /^[A-Za-z][A-Za-z\s.'-]{1,60}$/.test(firstClause) && /\s/.test(firstClause)) {
    return titleCase(firstClause);
  }
  return undefined;
}

function extractStudyLevel(text: string): string | undefined {
  const lower = text.toLowerCase();
  for (const [key, value] of Object.entries(studyLevels)) {
    if (lower.includes(key)) return value;
  }
  return undefined;
}

function extractGPA(text: string): string | undefined {
  // Match various GPA formats
  const patterns = [
    /\b(\d+\.\d+)\s*\/\s*4\.0\b/i,  // 3.5/4.0
    /\b(\d+\.\d+)\s*gpa\b/i,         // 3.5 GPA
    /\b(\d+\.\d+)\b/,                // 3.5
    /\b(\d+)%\b/,                     // 85%
    /\b([A-Z][+-]?)\b/               // A, A-, B+
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return match[1];
  }
  return undefined;
}

function extractStudyField(text: string): string | undefined {
  // Common study fields
  const fields = [
    "computer science", "cs", "software engineering", "information technology",
    "business administration", "mba", "finance", "marketing", "economics",
    "engineering", "mechanical engineering", "electrical engineering", "civil engineering",
    "medicine", "nursing", "pharmacy", "biology", "chemistry", "physics",
    "mathematics", "statistics", "data science", "artificial intelligence",
    "psychology", "sociology", "political science", "international relations",
    "architecture", "design", "fashion", "media", "journalism", "law"
  ];
  
  const lower = text.toLowerCase();
  for (const field of fields) {
    if (lower.includes(field)) {
      return titleCase(field);
    }
  }
  return undefined;
}

export function extractLead(prev: LeadDraft, text: string) {
  const draft: LeadDraft = { ...prev };
  const lower = text.toLowerCase();

  // email
  if (!draft.email) {
    const m = text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i);
    if (m) draft.email = m[0];
  }

  // phone
  if (!draft.phone) {
    const m = text.match(/(\+?\d[\d\s().-]{6,}\d)/);
    if (m) draft.phone = normPhone(m[0]);
  }

  // name (multiple strategies)
  if (!draft.name) {
    draft.name = guessNameFromText(text) || guessNameFromEmail(draft.email);
  }

  // target country (only supported countries)
  if (!draft.target_country) {
    for (const [key, value] of Object.entries(supportedCountries)) {
      if (lower.includes(key)) { 
        draft.target_country = value; 
        break; 
      }
    }
  }

  // preferred intake: "<month> <year>" or just month
  if (!draft.preferred_intake) {
    const monthRe = new RegExp(`\\b(${months.join("|")})\\b\\s*(\\d{4})?`, "i");
    const m = text.match(monthRe);
    if (m) {
      const month = m[1];
      const year = m[2] || "";
      draft.preferred_intake = month[0].toUpperCase() + month.slice(1).toLowerCase() + (year ? ` ${year}` : "");
    }
  }

  // study level
  if (!draft.study_level) {
    draft.study_level = extractStudyLevel(text);
  }

  // GPA/grades
  if (!draft.gpa_grades) {
    draft.gpa_grades = extractGPA(text);
  }

  // study field
  if (!draft.study_field) {
    draft.study_field = extractStudyField(text);
  }

  const missing: (keyof Required<LeadDraft>)[] = [];
  if (!draft.name) missing.push("name");
  if (!draft.email) missing.push("email");
  if (!draft.phone) missing.push("phone");
  if (!draft.target_country) missing.push("target_country");
  if (!draft.preferred_intake) missing.push("preferred_intake");
  if (!draft.study_level) missing.push("study_level");
  if (!draft.gpa_grades) missing.push("gpa_grades");
  if (!draft.study_field) missing.push("study_field");

  return {
    draft,
    isComplete: !!(draft.name && draft.email && draft.phone && draft.target_country),
    missing,
    changed: JSON.stringify(draft) !== JSON.stringify(prev),
  };
}

export function wantsLead(text: string) {
  const s = text.toLowerCase();
  return ["apply","admission","consult","call me","contact me","book","enroll","enrol","appointment","help me","guide me","interested"]
    .some(k => s.includes(k));
}

export function isCountrySupported(country: string): boolean {
  return Object.values(supportedCountries).includes(country);
}

export function getSupportedCountries(): string[] {
  return Object.values(supportedCountries);
}
