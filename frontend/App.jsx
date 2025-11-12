import React, { useState } from "react";

function App() {
  const [pergunta, setPergunta] = useState("");
  const [resposta, setResposta] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    setLoading(true);
    setResposta("");
    const resp = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta }),
    });
    const data = await resp.json();
    setResposta(data.resposta);
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>Assistente Ezinho</h2>
      <textarea
        rows={3}
        style={{ width: "100%" }}
        value={pergunta}
        onChange={e => setPergunta(e.target.value)}
        placeholder="Digite sua pergunta..."
      />
      <button onClick={handleAsk} disabled={loading || !pergunta.trim()}>
        {loading ? "Consultando..." : "Perguntar"}
      </button>
      {resposta && (
        <div style={{ marginTop: 24, background: "#eaf4ff", padding: 16, borderRadius: 8 }}>
          <b>Resposta:</b>
          <div style={{ whiteSpace: "pre-wrap", color: "#0a2e6d" }}>{resposta}</div>
        </div>
      )}
    </div>
  );
}

export default App;
