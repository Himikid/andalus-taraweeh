export default function Header() {
  return (
    <header className="mx-auto flex w-full max-w-3xl flex-col items-center gap-6 text-center">
      <p className="label-caps">Andalus Centre Glasgow</p>

      <p className="arabic-basmala text-[2.2rem] leading-relaxed text-sand sm:text-[2.9rem]">
        بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ
      </p>

      <h1 className="font-[var(--font-heading)] text-[2.5rem] leading-[1.02] text-ivory sm:text-[3.25rem] lg:text-[4rem]">
        Andalus Taraweeh
      </h1>

      <p className="max-w-2xl pt-2 text-sm leading-8 text-muted sm:text-base">
        Join Taraweeh live each night and revisit past recitations whenever you wish.
      </p>
    </header>
  );
}
