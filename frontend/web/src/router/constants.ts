/**
 * Stable shell paths.
 *
 * `/dashboard/workplace` is the canonical post-login workspace. `/home` is
 * retained only as a compatibility entry for existing bookmarks and state.
 */
export const CANONICAL_HOME_PATH = "/dashboard/workplace" as const;
export const LEGACY_HOME_PATH = "/home" as const;
