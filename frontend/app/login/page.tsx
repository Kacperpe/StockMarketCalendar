export default function LoginPage() {
  return (
    <main>
      <h1 className="pageTitle">Logowanie</h1>
      <p className="subtitle">MVP: formularz pod `POST /api/auth/login`.</p>
      <div className="grid" style={{ maxWidth: 420 }}>
        <input className="field" type="email" placeholder="email@example.com" />
        <input className="field" type="password" placeholder="Hasło" />
        <button className="button primary">Zaloguj</button>
      </div>
    </main>
  );
}

