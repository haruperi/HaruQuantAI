/**
 * Strategy import route (cross-domain coverage for the Research workbench).
 *
 * V1 placed SQX Import under Edge Lab. In V2 external import belongs to Data
 * and Strategy, so this route drives Data's own registered import boundary and
 * reports the dialects Data actually supports — including when SQX is not one
 * of them — rather than presenting an importer the backend does not have.
 */

"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import { ApiClientError, apiClients } from "@/clients";

export default function Page(): ReactNode {
  const [dialects, setDialects] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const response = await apiClients.data.importDialects();
        if (cancelled) return;
        if (response.status === "error") setError(response.error.message);
        else setDialects(response.data);
      } catch (cause) {
        if (!cancelled) {
          setError(
            cause instanceof ApiClientError ? cause.message : "unavailable"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const names = dialects ? Object.keys(dialects) : [];
  const supportsSqx = names.some((name) => name.toLowerCase().includes("sqx"));

  return (
    <ProtectedLayout>
      <main className="research-root">
        <header className="research-page__head">
          <p className="research-eyebrow">Strategy / Data import</p>
          <h1>Strategy import</h1>
          <p>
            External import is owned by Data and Strategy. The dialect list
            below is Data&apos;s own, so this page can never offer a format the
            backend does not support.
          </p>
          <div className="research-links">
            <Link className="research-button" href="/workstation/research">
              Back to Research
            </Link>
          </div>
        </header>

        <section className="research-section">
          <header className="research-section__head">
            <div>
              <h3>Supported import dialects</h3>
              <p>Read from Data, not from a copy held here.</p>
            </div>
          </header>
          {loading ? (
            <p className="research-note">Loading owner dialect list…</p>
          ) : error ? (
            <p className="research-error" role="alert">
              {error}
            </p>
          ) : (
            <>
              <div className="research-chips">
                {names.length === 0 ? (
                  <span className="research-note">
                    Data reported no import dialects.
                  </span>
                ) : (
                  names.map((name) => (
                    <span
                      key={name}
                      className="research-badge research-badge--neutral"
                    >
                      {name}
                    </span>
                  ))
                )}
              </div>
              {supportsSqx ? null : (
                <p className="research-note">
                  Data does not currently register an SQX dialect. Until it
                  does, an SQX file cannot be imported here, and no other
                  surface in V2 imports one either.
                </p>
              )}
            </>
          )}
        </section>
      </main>
    </ProtectedLayout>
  );
}
