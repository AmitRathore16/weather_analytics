import React, { useState, useEffect, useRef } from "react";

// Simple custom component to render basic markdown elements (bold, tables, lists)
const MarkdownRenderer = ({ text }) => {
  if (!text) return null;

  // Split content by code blocks if any
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="markdown-content">
      {parts.map((part, idx) => {
        if (part.startsWith("```")) {
          const code = part.replace(/^```[a-zA-Z]*\n?/, "").replace(/```$/, "");
          return (
            <pre key={idx} className="code-block-embed">
              <code>{code}</code>
            </pre>
          );
        }

        const lines = part.split("\n");
        let inList = false;
        let listItems = [];
        let inTable = false;
        let tableRows = [];
        const renderedElements = [];

        const flushList = (key) => {
          if (listItems.length > 0) {
            renderedElements.push(
              <ul key={`list-${key}`} style={{ margin: "8px 0 8px 20px" }}>
                {listItems.map((li, lIdx) => (
                  <li key={lIdx} style={{ marginBottom: "4px" }}>{li}</li>
                ))}
              </ul>
            );
            listItems = [];
            inList = false;
          }
        };

        const flushTable = (key) => {
          if (tableRows.length > 0) {
            const headerRow = tableRows[0];
            const dataRows = tableRows.slice(1);
            renderedElements.push(
              <table key={`table-${key}`} className="markdown-table">
                <thead>
                  <tr>
                    {headerRow.map((cell, cIdx) => (
                      <th key={cIdx}>{cell}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataRows.map((row, rIdx) => (
                    <tr key={rIdx}>
                      {row.map((cell, cIdx) => (
                        <td key={cIdx}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            );
            tableRows = [];
            inTable = false;
          }
        };

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];

          // Check for table row
          if (line.trim().startsWith("|")) {
            flushList(i);
            inTable = true;
            const cells = line
              .split("|")
              .map((c) => c.trim())
              .filter((c, cIdx, arr) => cIdx > 0 && cIdx < arr.length - 1);
            if (cells.length > 0 && !cells.every((c) => c.match(/^-+$/))) {
              tableRows.push(cells);
            }
            continue;
          } else {
            flushTable(i);
          }

          // Check for list
          if (line.trim().startsWith("* ") || line.trim().startsWith("- ")) {
            inList = true;
            listItems.push(renderInlineFormatting(line.trim().substring(2)));
            continue;
          } else {
            flushList(i);
          }

          if (line.trim() !== "") {
            renderedElements.push(
              <p key={i} style={{ marginBottom: "8px" }}>
                {renderInlineFormatting(line)}
              </p>
            );
          }
        }

        flushList(lines.length);
        flushTable(lines.length);

        return <React.Fragment key={idx}>{renderedElements}</React.Fragment>;
      })}
    </div>
  );
};

function renderInlineFormatting(text) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: "assistant",
      text: "Hello! Ask me any questions about the weather database.",
      sqlQuery: null,
    },
  ]);
  const [inputVal, setInputVal] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showSqlIndex, setShowSqlIndex] = useState({});

  const [showDbModal, setShowDbModal] = useState(false);
  const [updatingDb, setUpdatingDb] = useState(false);
  const [dbUpdateResult, setDbUpdateResult] = useState(null);

  const chatEndRef = useRef(null);

  useEffect(() => {
    if (chatOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isSending, chatOpen]);

  const handleNewChat = () => {
    setMessages([
      {
        sender: "assistant",
        text: "Hello! Ask me any questions about the weather database.",
        sqlQuery: null,
      },
    ]);
    setShowSqlIndex({});
    setInputVal("");
  };

  const toggleSql = (index) => {
    setShowSqlIndex((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const handleSend = async (textToSend) => {
    const text = textToSend || inputVal;
    if (!text.trim()) return;

    setMessages((prev) => [...prev, { sender: "user", text, sqlQuery: null }]);
    if (!textToSend) setInputVal("");
    setIsSending(true);

    const history = messages.slice(1).map((m) => ({ sender: m.sender, text: m.text }));

    try {
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: data.response,
            sqlQuery: data.sqlQuery,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: "Sorry, I encountered an error. Please try again.",
            sqlQuery: null,
          },
        ]);
      }
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: "Could not connect to the backend server. Make sure the Node server is running on http://localhost:5001.",
          sqlQuery: null,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const triggerRefreshDatabase = async () => {
    setShowDbModal(true);
    setUpdatingDb(true);
    setDbUpdateResult(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/refresh-database`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setDbUpdateResult({
          success: true,
          message:
            "Database updated successfully. Refresh your dashboard in Power BI to view the latest analytics.",
        });
      } else {
        setDbUpdateResult({
          success: false,
          message: data.error || "Database update failed. Please check the backend.",
        });
      }
    } catch (err) {
      console.error("Refresh Database Error:", err);
      setDbUpdateResult({
        success: false,
        message: "Could not reach the backend server.",
      });
    } finally {
      setUpdatingDb(false);
    }
  };

  const suggestionChips = [
    "What is the average temp in ajmer?",
    "Compare Chennai vs Delhi air quality today.",
    "Which city has the highest UV index?",
    "Analyse chances of rain for this week.",
  ];

  return (
    <div className="app-container">
      <header className="app-navbar">
        <div className="navbar-logo">
          <h2>Weather Dashboard Project</h2>
        </div>

        <nav className="navbar-links">
          <button
            className={`nav-btn ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            Dashboard
          </button>

        </nav>

        <div className="navbar-actions">
          <button className="btn-refresh-db" onClick={triggerRefreshDatabase}>
            Refresh Database
          </button>
        </div>
      </header>

      <main className="main-content">
        {activeTab === "dashboard" ? (
          <div className={`dashboard-layout ${chatOpen ? "chat-open" : ""}`}>
            <section className="dashboard-pane">
              <iframe
                title="dashboard"
                src="https://app.powerbi.com/reportEmbed?reportId=398f5f4a-9175-4cb1-abe6-2cdb9b153b99&autoAuth=true&ctid=945ef104-7619-4ac0-aebb-ed348ffd933d"
                allowFullScreen={true}
              ></iframe>
            </section>

            <section className={`chatbot-pane ${chatOpen ? "open" : ""}`}>
              <div className="chat-header">
                <h3>Chat Assistant</h3>
                <div className="chat-header-actions">
                  <button className="btn-new-chat" onClick={handleNewChat}>
                    New Chat
                  </button>
                  <button
                    className="btn-close-chat"
                    onClick={() => setChatOpen(false)}
                    aria-label="Close chat"
                  >
                    ×
                  </button>
                </div>
              </div>

              <div className="chat-messages">
                {messages.map((msg, index) => (
                  <div key={index} className={`message-container ${msg.sender}`}>
                    <div className={`message-bubble ${msg.sender}`}>
                      <MarkdownRenderer text={msg.text} />

                      {msg.sqlQuery && (
                        <div className="sql-preview-section">
                          <button className="sql-toggle-btn" onClick={() => toggleSql(index)}>
                            {showSqlIndex[index] ? "Hide Executed SQL" : "View Executed SQL"}
                          </button>
                          {showSqlIndex[index] && (
                            <pre className="sql-query-block">
                              <code>{msg.sqlQuery}</code>
                            </pre>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isSending && (
                  <div className="chat-loading">
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="suggestion-chips">
                {suggestionChips.map((chip, idx) => (
                  <button
                    key={idx}
                    className="suggestion-chip"
                    onClick={() => handleSend(chip)}
                    disabled={isSending}
                  >
                    {chip}
                  </button>
                ))}
              </div>

              <form
                className="chat-input-bar"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
              >
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask about weather, AQI, trends..."
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  disabled={isSending}
                />
                <button className="btn-send" type="submit" disabled={isSending || !inputVal.trim()}>
                  Send
                </button>
              </form>
            </section>

            {!chatOpen && (
              <button
                className="chat-fab"
                onClick={() => setChatOpen(true)}
                aria-label="Open chat assistant"
              >
                Chat
              </button>
            )}
          </div>
        ) : null}
      </main>

      {showDbModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            {updatingDb ? (
              <div className="refresh-loading">
                <div className="spinner"></div>
                <p>Fetching weather for 14 cities, updating SQL, and removing duplicates. This usually takes 1–2 minutes.</p>
              </div>
            ) : (
              <div className="refresh-done">
                <p className={dbUpdateResult?.success ? "success-text" : "error-text"}>
                  {dbUpdateResult?.message}
                </p>
                <button className="modal-close-btn" onClick={() => setShowDbModal(false)}>
                  OK
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
