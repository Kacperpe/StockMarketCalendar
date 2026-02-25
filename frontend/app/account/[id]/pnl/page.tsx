import WhitePnlCalendar from "../../../../components/WhitePnlCalendar";

export function generateStaticParams() {
  return [{ id: "1" }];
}

export default async function PnlPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <main>
      <h1 className="pageTitle">Daily PnL Calendar - account #{id}</h1>
      <p className="subtitle">
        White calendar view with weekly summaries and day details (ready for API integration).
      </p>
      <WhitePnlCalendar />
    </main>
  );
}

