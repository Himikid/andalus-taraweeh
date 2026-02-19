const RAMADAN_START = new Date("2026-02-18T00:00:00");
const GLASGOW_TIMEZONE = "Europe/London";

function getLondonDate(date: Date) {
  return new Date(date.toLocaleString("en-US", { timeZone: GLASGOW_TIMEZONE }));
}

export function getDateForRamadanDay(day: number) {
  const date = new Date(RAMADAN_START);
  date.setDate(RAMADAN_START.getDate() + day - 1);

  return date.toLocaleDateString("en-GB", {
    month: "short",
    day: "numeric"
  });
}

export function getCurrentRamadanDay() {
  const londonNow = getLondonDate(new Date());
  const londonStart = getLondonDate(RAMADAN_START);

  const diffMs = londonNow.getTime() - londonStart.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1;

  if (diffDays < 1 || diffDays > 30) {
    return null;
  }

  return diffDays;
}
