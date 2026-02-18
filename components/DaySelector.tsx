type DaySelectorProps = {
  selectedDay: number;
  onDayChange: (day: number) => void;
};

export default function DaySelector({ selectedDay, onDayChange }: DaySelectorProps) {
  return (
    <div className="w-full rounded-lg border border-white/10 bg-panel/70 p-4">
      <label htmlFor="day-selector" className="mb-2 block text-sm text-emerald-100/90">
        Select Taraweeh Day
      </label>
      <select
        id="day-selector"
        value={selectedDay}
        onChange={(event) => onDayChange(Number(event.target.value))}
        className="w-full rounded-md border border-white/15 bg-charcoal px-3 py-2 text-sm text-white outline-none ring-0 focus:border-accentSoft"
      >
        {Array.from({ length: 30 }, (_, index) => {
          const day = index + 1;
          return (
            <option key={day} value={day}>
              Day {day}
            </option>
          );
        })}
      </select>
    </div>
  );
}
