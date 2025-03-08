import type { Metadata } from "next";
import "./globals.css";
import { GameProvider } from "../context/GameContext";

import { Roboto } from "next/font/google";

const roboto = Roboto({
  weight: "300",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "LeetDuel",
  description: "Code duel against your friends!",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={roboto.className}>
        <GameProvider>{children}</GameProvider>
      </body>
    </html>
  );
}
