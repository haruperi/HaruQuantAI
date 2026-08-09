export interface QualificationView { status: "qualified" | "ineligible" | "expired" | "unknown"; curriculumVersion: string | null; remediation: readonly string[]; }
