import type { Metadata } from "next"
import "./globals.css"
import { Navbar } from "@/components/layout/navbar"

export const metadata: Metadata = {
  title: "Harness Engineering",
  description: "Skills and Agents marketplace with usage dashboard",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh" suppressHydrationWarning>
      <body className="font-sans">
        <div className="min-h-screen bg-background flex flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  )
}
