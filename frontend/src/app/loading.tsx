import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Skeleton } from "@/components/ui";

export default function Loading() {
  return (
    <>
      <SiteHeader />
      <main aria-hidden id="main" className="pt-16">
        <Container width="wide" className="flex flex-col gap-8 py-16">
          <Skeleton width={180} height={12} />
          <Skeleton width={420} height={36} />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} height={180} />
            ))}
          </div>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
