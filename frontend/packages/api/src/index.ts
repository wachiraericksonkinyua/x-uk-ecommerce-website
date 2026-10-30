// Re-export the auto-generated schema types and our thin fetch client.
// NOTE: `schema.d.ts` contains only types, so this must be a type-only
// re-export — otherwise bundlers try to resolve a runtime module that
// does not exist.
export type * from "./schema";
export * from "./client";
