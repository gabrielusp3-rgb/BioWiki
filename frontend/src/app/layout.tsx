import type { Metadata, Viewport } from "next";
import { cookies } from "next/headers";
import { Inter, Space_Grotesk } from "next/font/google";
import { BackgroundDNAMount } from "@/components/BackgroundDNAMount";
import { SplashScreen } from "@/components/SplashScreen";
import { LocaleProvider } from "@/lib/i18n/LocaleProvider";
import { LOCALE_COOKIE, directionOf, parseLocale } from "@/lib/i18n/locales";
import { siteUrl } from "@/lib/site";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-inter",
  display: "swap",
});

const SITE_URL = siteUrl();
const SITE_DESCRIPTION =
  "Explore the biological diversity of life through real molecular sequences from internationally recognised public databases.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "BIOWIKI — Universal Biological Sequence Database",
    template: "%s · BIOWIKI",
  },
  description: SITE_DESCRIPTION,
  applicationName: "BIOWIKI",
  category: "science",
  keywords: [
    "bioinformatics",
    "genomics",
    "DNA",
    "RNA",
    "protein",
    "CRISPR",
    "genome",
    "virus",
    "sequence database",
    "NCBI",
    "UniProt",
    "Ensembl",
  ],
  authors: [{ name: "BIOWIKI" }],
  creator: "BIOWIKI",
  publisher: "BIOWIKI",
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    siteName: "BIOWIKI",
    title: "BIOWIKI — Universal Biological Sequence Database",
    description: SITE_DESCRIPTION,
    url: SITE_URL,
    locale: "en_US",
    images: [{ url: "/brand-logo.png", width: 412, height: 405, alt: "BioWiki" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "BIOWIKI — Universal Biological Sequence Database",
    description: SITE_DESCRIPTION,
  },
  other: {
    "darkreader-lock": "true",
  },
};

const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      name: "BIOWIKI",
      url: SITE_URL,
      description: SITE_DESCRIPTION,
    },
    {
      "@type": "WebSite",
      name: "BIOWIKI",
      url: SITE_URL,
      description: SITE_DESCRIPTION,
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: `${SITE_URL}/search?q={query}`,
        },
        "query-input": "required name=query",
      },
    },
  ],
};

export const viewport: Viewport = {
  themeColor: "#050505",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const jar = await cookies();
  const locale = parseLocale(jar.get(LOCALE_COOKIE)?.value);
  return (
    <html
      lang={locale}
      dir={directionOf(locale)}
      className={`${spaceGrotesk.variable} ${inter.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-dvh bg-bg-primary font-body antialiased" suppressHydrationWarning>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
        <LocaleProvider initialLocale={locale}>
          <BackgroundDNAMount />
          {children}
          <SplashScreen />
        </LocaleProvider>
      </body>
    </html>
  );
}
