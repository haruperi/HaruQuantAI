export interface Alarm { id: string; rootId: string; message: string; priority: number; state: "active" | "acknowledged" | "resolved"; }
