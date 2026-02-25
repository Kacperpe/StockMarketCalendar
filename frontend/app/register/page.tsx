export default function RegisterPage() {
  return (
    <main>
      <h1 className="pageTitle">Rejestracja</h1>
      <p className="subtitle">MVP: formularz pod `POST /api/auth/register`.</p>
      <div className="grid" style={{ maxWidth: 420 }}>
        <input className="field" type="email" placeholder="email@example.com" />
        <input className="field" type="password" placeholder="Hasło (min. 8 znaków)" />
        <button className="button primary">Załóż konto</button>
      </div>
    </main>
  );
}

