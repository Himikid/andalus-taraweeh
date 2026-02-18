import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Taraweeh Live – Andalus Centre Glasgow",
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
      <body>{children}</body>
    </html>
  );
}
