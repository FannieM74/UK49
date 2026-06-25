import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "UK49 Lotto Predictor",
  description: "AI-powered UK49 lottery analysis and predictions",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="text-xs sm:text-sm text-gray-400 hover:text-yellow-400 transition-colors duration-200 font-medium"
    >
      {children}
    </Link>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full bg-gray-950 text-gray-100">
        <nav className="sticky top-0 z-50 border-b border-gray-800/60 bg-gray-950/80 backdrop-blur-lg">
          <div className="max-w-6xl mx-auto flex items-center gap-5 sm:gap-8 px-4 py-3 sm:px-6 sm:py-3.5">
            <Link href="/" className="text-lg sm:text-xl font-bold gradient-text tracking-tight">UK49</Link>
            <div className="flex items-center gap-4 sm:gap-6">
              <NavLink href="/">Dashboard</NavLink>
              <NavLink href="/predictions">Predictions</NavLink>
              <NavLink href="/analysis">Analysis</NavLink>
              <NavLink href="/success">Success</NavLink>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
