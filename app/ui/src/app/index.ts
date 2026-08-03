/**
 * Protected workflow pages barrel (FEAT-API-12, Section 4.12).
 *
 * Access gate (`AuthenticationPage` at `/login`), protected layout, and
 * workflow page composing the single-page widget workspace from the public
 * clients, context, and components built in Sections 4.9–4.11.
 */

export { AuthenticationPage } from "./authentication-page";
export type { AuthenticationPageProps } from "./authentication-page";

export { ProtectedLayout } from "./protected-layout";
export type { ProtectedLayoutProps } from "./protected-layout";

export { WorkflowPage } from "./workflow-page";
export type { WorkflowPageProps } from "./workflow-page";
