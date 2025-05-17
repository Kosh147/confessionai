import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Problem Solver',
  description: 'A web app to help solve your problems',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
} 