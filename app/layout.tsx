import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import { Noto_Naskh_Arabic } from "next/font/google";
import "./globals.css";

const arabicFont = Noto_Naskh_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic-web",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Andalus Taraweeh – Live",
  description:
    "Watch Taraweeh prayers live and access indexed Ramadan recitations from Andalus Centre Glasgow."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={arabicFont.variable}>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
