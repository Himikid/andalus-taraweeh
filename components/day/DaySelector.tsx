type DaySelectorProps = {
  days: number[];
  selectedDay: number;
  onDayChange: (day: number) => void;
};

export default function DaySelector({ days, selectedDay, onDayChange }: DaySelectorProps) {
  const safeDays = days ?? [];

  if (!safeDays.length) {
    return <p className="text-sm text-muted">No published Ramadan days yet.</p>;
  }

  return (
    <section className="w-full max-w-xl">
      <p className="label-caps">Published Days</p>
      <label htmlFor="day-selector" className="mt-3 block text-sm text-muted">
        Select a day
      </label>

      <select
        id="day-selector"
        value={selectedDay}
        onChange={(event) => onDayChange(Number(event.target.value))}
        className="mt-3 w-full rounded-xl border border-line bg-charcoalLift px-4 py-3 text-sm text-ivory outline-none focus:border-sand"
      >
        {safeDays.map((day) => (
          <option key={day} value={day}>
            Ramadan Day {day}
          </option>
        ))}
      </select>
    </section>
  );
}
