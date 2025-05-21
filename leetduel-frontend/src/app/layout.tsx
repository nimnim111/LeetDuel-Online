import type { Metadata } from "next";
import "./globals.css";
import { GameProvider } from "../context/GameContext";
import { Inter } from "next/font/google";
import { config } from "@fortawesome/fontawesome-svg-core";
import "@fortawesome/fontawesome-svg-core/styles.css";
config.autoAddCss = false;

export const metadata: Metadata = {
  title: "LeetDuel Online",
  description: "LeetDuel Online: Code duel against your friends!",
  icons: { icon: "/favicon.ico" },
};

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={inter.className} style={{ fontWeight: 300 }}>
        <GameProvider>{children}</GameProvider>
      </body>
    </html>
  );
}
