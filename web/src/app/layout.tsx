import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EcoEdith | AI learning studio",
  description: "Upload study materials and learn with an AI tutor.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
