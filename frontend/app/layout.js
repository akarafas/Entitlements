export const metadata = {
  title: 'Entitlements Support Console',
  description: 'Support UI for managing user entitlements',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'Arial, sans-serif', margin: 20 }}>{children}</body>
    </html>
  );
}
