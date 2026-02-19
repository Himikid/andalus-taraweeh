import DayPageClient from "@/components/day/DayPageClient";
import { availableTaraweehDays } from "@/data/taraweehVideos";

type DayPageProps = {
  params: {
    day: string;
  };
};

export function generateStaticParams() {
  return availableTaraweehDays.map((day) => ({ day: String(day) }));
}

export default function DayPage({ params }: DayPageProps) {
  const parsedDay = Number(params.day);
  return <DayPageClient initialDay={Number.isNaN(parsedDay) ? 1 : parsedDay} />;
}
