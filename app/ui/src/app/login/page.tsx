/**
 * Login/register route segment (`/login`).
 *
 * Framework entry point for the access gate. Delegates only to
 * `AuthenticationPage`. Next.js App Router default export.
 */

"use client";

import type { ReactNode } from "react";

import { AuthenticationPage } from "../authentication-page";

export default function LoginPage(): ReactNode {
  return <AuthenticationPage />;
}
