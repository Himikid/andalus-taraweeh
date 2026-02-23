type RecitersInfoProps = {
  compact?: boolean;
};

export default function RecitersInfo({ compact = false }: RecitersInfoProps) {
  return (
    <section className="w-full">
      <p className="label-caps">Reciters</p>
      <p className="mt-2 text-sm leading-6 text-muted">
        Experienced reciters with different riwayat and transmission styles. Each night is unique.
      </p>

      <div className={`mt-5 flex flex-col gap-7 ${compact ? "" : "sm:flex-row sm:items-start sm:gap-12"}`}>
        <article>
          <p className="text-lg font-medium text-ivory sm:text-xl">Sheikh Samir</p>
          <p className="mt-1 text-sm text-muted">Alexandria, Egypt</p>
          <p className="mt-2 text-xs leading-5 text-muted">
            <span className="block">Day 1: Al-Susi 'an Abi 'Amr.</span>
            <span className="block">Day 2: Al-Susi 'an Abi 'Amr.</span>
            <span className="block">Day 3: Ruways 'an Ya'qub.</span>
            <span className="block">Day 4: Ibn Dhakwan 'an Ibn 'Amir.</span>
            <span className="block">Day 5: Hafs 'an 'Asim.</span>
          </p>
        </article>

        <article>
          <p className="text-lg font-medium text-ivory sm:text-xl">Sheikh Hasan</p>
          <p className="mt-1 text-sm text-muted">Libya</p>
          <p className="mt-2 text-xs leading-5 text-muted">
            Recites in Qalun and Warsh.
          </p>
        </article>
      </div>
    </section>
  );
}
