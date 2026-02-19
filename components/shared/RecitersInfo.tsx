type RecitersInfoProps = {
  compact?: boolean;
};

export default function RecitersInfo({ compact = false }: RecitersInfoProps) {
  return (
    <section className="w-full">
      <p className="label-caps">Reciters</p>

      <div className={`mt-5 flex flex-col gap-7 ${compact ? "" : "sm:flex-row sm:items-start sm:gap-12"}`}>
        <article>
          <p className="text-lg font-medium text-ivory sm:text-xl">Shaikh Samier</p>
          <p className="mt-1 text-sm text-muted">Alexandria, Egypt</p>
        </article>

        <article>
          <p className="text-lg font-medium text-ivory sm:text-xl">Sheikh Hasan</p>
          <p className="mt-1 text-sm text-muted">Libya</p>
        </article>
      </div>
    </section>
  );
}
