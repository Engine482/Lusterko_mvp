import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";

import { AppShell } from "@/components/AppShell";

import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
  variable: "--font-inter",
  display: "swap",
});

const TITLE = "Люстерко — моніторинг стану особового складу";
const DESCRIPTION =
  "MVP системи короткого психофізіологічного самозвіту, baseline-оцінки та командирського огляду стану підрозділу.";

export const metadata: Metadata = {
  title: {
    default: TITLE,
    template: "%s · Люстерко",
  },
  description: DESCRIPTION,
  applicationName: "Люстерко",
  authors: [{ name: "Volodymyr Motornyi" }],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    locale: "uk_UA",
    type: "website",
    siteName: "Люстерко",
  },
  twitter: {
    card: "summary",
    title: TITLE,
    description: DESCRIPTION,
  },
  appleWebApp: {
    capable: true,
    title: "Люстерко",
    statusBarStyle: "black-translucent",
  },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#0b1120",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="uk" className={inter.variable}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
