import Link from "next/link";

export default function NotFound() {
  return (
    <section className="not-found">
      <h1>Сторінку не знайдено</h1>
      <p>Такої сторінки немає або посилання застаріло.</p>
      <Link className="btn" href="/">
        Повернутися на головну
      </Link>
    </section>
  );
}
