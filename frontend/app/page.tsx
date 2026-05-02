export default function HomePage() {
  return (
    <section>
      <h1>Люстерко</h1>
      <p>
        MVP — система моніторингу психологічного стану за запрошенням.
      </p>
      <p style={{ marginTop: 16 }}>
        <a href="/login" className="btn">
          Увійти
        </a>
      </p>
      <p style={{ fontSize: "0.875rem", marginTop: 24, color: "#666" }}>
        Новий користувач? Перейдіть за посиланням з інвайт-листа,
        отриманого від адміністратора.
      </p>
    </section>
  );
}
