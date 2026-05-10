export default async function RegisterSentPage({
  searchParams,
}: {
  searchParams: Promise<{ email?: string }>;
}) {
  const { email = "" } = await searchParams;

  return (
    <section className="auth-card">
      <h1>Перевірте пошту</h1>
      <p>
        Якщо вказана адреса {email ? <strong>{email}</strong> : "ваша адреса"}{" "}
        ще не зареєстрована, ми надіслали на неї лист із посиланням для
        підтвердження. Перейдіть за ним, щоб задати пароль і завершити
        реєстрацію.
      </p>
      <p className="text-muted" style={{ fontSize: "0.875rem", marginTop: 16 }}>
        Лист не приходить? Перевірте папку «Спам». Посилання дійсне 24 години.
      </p>
      <p style={{ marginTop: 24 }}>
        <a href="/login" className="btn btn--ghost">
          Повернутися на сторінку входу
        </a>
      </p>
    </section>
  );
}
