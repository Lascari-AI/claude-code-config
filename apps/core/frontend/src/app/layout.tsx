import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LAI Session Manager",
  description:
    "Manage projects and session workflows for AI-assisted development",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background`}
      >
        {/* Navigation Header */}
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center">
            <Link href="/projects" className="flex items-center space-x-2">
              <span className="font-bold text-xl">LAI</span>
              <span className="text-muted-foreground hidden sm:inline-block">
                Session Manager
              </span>
            </Link>
            <nav className="ml-auto flex items-center space-x-4">
              <Link
                href="/projects"
                className="text-sm font-medium transition-colors hover:text-primary"
              >
                Projects
              </Link>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
