/** Universal resource envelopes. Domain document meaning belongs to its producer. */
export interface ResourceRef {
  readonly id: string;
  readonly revision: number;
  readonly schema_id: string;
  readonly schema_version: string;
  readonly digest: string;
  readonly media_type: string;
  readonly producer_id: string;
  readonly producer_version: string;
}
export interface ResourceBytes {
  readonly content_base64: string;
  readonly schema: string;
}
