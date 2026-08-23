"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

/**
 * Seeds a search-style query state from a URL parameter (`?q=` by default) so
 * links from the global search bar deep-link straight into a pre-filled
 * explorer. Re-syncs whenever the surrounding navigation changes the params.
 * Must be called from a component rendered under a `<Suspense>` boundary, per
 * Next.js App Router requirements for `useSearchParams`.
 */
export function useQueryParamSync(setQuery: (value: string) => void, param = "q") {
  const searchParams = useSearchParams();

  useEffect(() => {
    const value = searchParams.get(param);
    if (value) setQuery(value);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, param]);
}
