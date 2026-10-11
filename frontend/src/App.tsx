import { useEffect, useState, type ChangeEvent } from "react";
import { ecoLoopApi, getSessionId } from "./api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Bot,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Coins,
  Droplets,
  FileImage,
  Leaf,
  MessageCircle,
  Recycle,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Sprout,
  Upload,
  Wallet,
  Zap,
} from "lucide-react";
import "./App.css";

type Page =
  | "Dashboard"
  | "Scan Waste"
  | "AI Assistant"
  | "Recycling Finder"
  | "My Impact";

const navigation: { label: Page; icon: typeof Leaf }[] = [
  { label: "Dashboard", icon: BarChart3 },
  { label: "Scan Waste", icon: FileImage },
  { label: "AI Assistant", icon: MessageCircle },
  { label: "Recycling Finder", icon: Recycle },
  { label: "My Impact", icon: Activity },
];

const activities = [
  {
    icon: Recycle,
    color: "mint",
    title: "Plastic bottle",
    detail: "Recycling Â· Completed",
    amount: "0.05 kg",
    time: "Today",
  },
  {
    icon: Sprout,
    color: "yellow",
    title: "Organic kitchen waste",
    detail: "Composting Â· Completed",
    amount: "1.20 kg",
    time: "Yesterday",
  },
  {
    icon: Zap,
    color: "purple",
    title: "Old electronics",
    detail: "E-waste Â· Collection pending",
    amount: "0.80 kg",
    time: "2 days ago",
  },
];

function Dashboard({
  navigate,
}: {
  navigate: (page: Page) => void;
}) {
  return (
    <>
      <section className="welcome-row">
        <div>
          <div className="eyebrow">
            <Sparkles size={14} /> YOUR CIRCULAR JOURNEY
          </div>
          <h1>Make waste matter.</h1>
          <p className="welcome-description">
            Every item has another possibility. Discover yours.
          </p>
        </div>

        <button className="primary-button" onClick={() => navigate("Scan Waste")}>
          <Upload size={17} /> Scan your waste
        </button>
      </section>

      <section className="hero-card">
        <div className="hero-content">
          <span className="hero-pill">
            <Leaf size={14} /> SMALL ACTIONS. REAL CHANGE.
          </span>
          <h2>What if waste was<br />just a new beginning?</h2>
          <p>
            Scan an item, discover its next life, and find a better
            way to reduce what goes to waste.
          </p>
          <button
            className="hero-button"
            onClick={() => navigate("Scan Waste")}
          >
            Discover an item's value <ArrowRight size={16} />
          </button>
        </div>

        <div className="hero-art" aria-hidden="true">
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="art-glow" />
          <div className="art-bottle">
            <div className="bottle-cap" />
            <div className="bottle-neck" />
            <div className="bottle-body">
              <Leaf size={49} strokeWidth={1.5} />
            </div>
          </div>
          <div className="floating-badge badge-leaf">
            <Sprout size={21} />
          </div>
          <div className="floating-badge badge-recycle">
            <Recycle size={23} />
          </div>
        </div>
      </section>

      <div className="section-heading">
        <div>
          <h2>Your impact overview</h2>
          <p>Track your progress toward a less wasteful future.</p>
        </div>
        <button className="text-button" onClick={() => navigate("My Impact")}>
          View details <ChevronRight size={16} />
        </button>
      </div>

      <section className="stats-grid">
        <StatCard
          icon={Recycle}
          color="mint"
          label="Waste recovered"
          value="2.05 kg"
          change="Illustrative demo data"
        />
        <StatCard
          icon={Coins}
          color="yellow"
          label="Potential earnings"
          value="â‚¹ 24"
          change="Example estimate only"
        />
        <StatCard
          icon={Sprout}
          color="purple"
          label="Actions completed"
          value="12"
          change="Illustrative demo data"
        />
        <StatCard
          icon={Droplets}
          color="blue"
          label="Resources saved"
          value="â€”"
          change="Not yet measured"
        />
      </section>

      <div className="content-grid">
        <section className="panel activity-panel">
          <div className="panel-heading">
            <div>
              <h3>Recent activity</h3>
              <p>Example records to preview the experience</p>
            </div>
            <button
              className="icon-button"
              aria-label="View impact"
              onClick={() => navigate("My Impact")}
            >
              <ArrowUpRight size={19} />
            </button>
          </div>

          <div className="activity-list">
            {activities.map((item) => {
              const Icon = item.icon;

              return (
                <div className="activity-item" key={item.title}>
                  <div className={`activity-icon ${item.color}`}>
                    <Icon size={20} />
                  </div>
                  <div className="activity-copy">
                    <strong>{item.title}</strong>
                    <span>{item.detail}</span>
                  </div>
                  <div className="activity-amount">
                    <strong>{item.amount}</strong>
                    <span>{item.time}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="demo-note">
            <CircleHelp size={15} />
            These records are sample data, not verified real-world impact.
          </div>
        </section>

        <section className="panel action-panel">
          <div className="panel-heading">
            <div>
              <h3>Explore possibilities</h3>
              <p>Choose a better next step.</p>
            </div>
            <Sparkles size={20} className="green-icon" />
          </div>

          <ActionCard
            icon={Bot}
            title="Ask EcoLoop AI"
            description="Find practical ways to reuse an item."
            color="mint"
            onClick={() => navigate("AI Assistant")}
          />
          <ActionCard
            icon={Recycle}
            title="Find recycling options"
            description="Explore responsible disposal routes."
            color="blue"
            onClick={() => navigate("Recycling Finder")}
          />
          <ActionCard
            icon={Wallet}
            title="Discover earning options"
            description="Learn about potential scrap value."
            color="yellow"
            onClick={() => navigate("Recycling Finder")}
          />
        </section>
      </div>

      <section className="bottom-banner">
        <div className="banner-icon"><Zap size={22} /></div>
        <div>
          <strong>Waste can power new possibilities.</strong>
          <p>Explore reuse, recycling, and responsible waste-to-energy pathways.</p>
        </div>
        <button onClick={() => navigate("AI Assistant")}>
          Explore <ArrowRight size={15} />
        </button>
      </section>
    </>
  );
}

function StatCard({
  icon: Icon,
  color,
  label,
  value,
  change,
}: {
  icon: typeof Leaf;
  color: string;
  label: string;
  value: string;
  change: string;
}) {
  return (
    <article className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <div className={`stat-icon ${color}`}><Icon size={19} /></div>
      </div>
      <strong className="stat-value">{value}</strong>
      <span className="stat-caption">{change}</span>
    </article>
  );
}

function ActionCard({
  icon: Icon,
  title,
  description,
  color,
  onClick,
}: {
  icon: typeof Leaf;
  title: string;
  description: string;
  color: string;
  onClick: () => void;
}) {
  return (
    <button className="action-card" onClick={onClick}>
      <span className={`action-icon ${color}`}><Icon size={20} /></span>
      <span className="action-copy">
        <strong>{title}</strong>
        <span>{description}</span>
      </span>
      <ChevronRight size={17} className="action-chevron" />
    </button>
  );
}

function ScanWaste() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [item, setItem] = useState("");
  const [material, setMaterial] = useState("plastic");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];

    if (!selected) return;

    if (!selected.type.startsWith("image/")) {
      setMessage("Please select an image file.");
      return;
    }

    if (selected.size > 5 * 1024 * 1024) {
      setMessage("Choose an image smaller than 5 MB.");
      return;
    }

    if (preview) URL.revokeObjectURL(preview);

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setMessage("");
    setResult(null);
  }

  async function analyzeItem() {
    if (!file && !item.trim()) {
      setMessage("Upload a waste photo or describe the item before analyzing.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResult(null);

    try {
      let response: Record<string, unknown>;

      if (file) {
        // Read the selected image and convert it to a Base64 data string.
        const imageData = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();

          reader.onload = () => {
            if (typeof reader.result !== "string") {
              reject(new Error("Unable to read the selected image."));
              return;
            }

            const commaIndex = reader.result.indexOf(",");

            if (commaIndex === -1) {
              reject(new Error("The selected image has an invalid format."));
              return;
            }

            resolve(reader.result.slice(commaIndex + 1));
          };

          reader.onerror = () => {
            reject(new Error("Unable to read the selected image."));
          };

          reader.readAsDataURL(file);
        });

        response = await ecoLoopApi.analyzeImage(
          imageData,
          file.type,
          item.trim(),
        );
      } else {
        response = await ecoLoopApi.analyze(
          item.trim(),
          material as
            | "plastic"
            | "paper"
            | "glass"
            | "metal"
            | "organic"
            | "electronic"
            | "textile"
            | "unknown",
        );
      }

      setResult(response);
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Unable to analyze this item. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="feature-page">
      <div className="eyebrow">
        <Sparkles size={14} /> WASTE INTELLIGENCE
      </div>

      <h1>Give your waste a second chance.</h1>

      <p className="page-description">
        Upload a waste photo for AI-powered visual recognition, or describe
        the item to receive personalized reuse, recycling, and safety guidance.
      </p>

      <div className="panel upload-panel">
        <label className="upload-zone">
          {preview ? (
            <img
              className="image-preview"
              src={preview}
              alt="Selected waste item"
            />
          ) : (
            <>
              <div className="upload-icon">
                <Upload size={27} />
              </div>
              <strong>Choose an image (optional)</strong>
              <span>PNG, JPG or WEBP · Maximum 5 MB</span>
            </>
          )}

          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handleFile}
          />
        </label>

        {file && <p className="selected-file">{file.name}</p>}

        <label htmlFor="waste-description">
          <strong>Describe your waste item</strong>
        </label>

        <input
          id="waste-description"
          className="waste-description-input"
          value={item}
          onChange={(event) => setItem(event.target.value)}
          placeholder="Example: empty plastic water bottle"
          maxLength={200}
        />

        <label htmlFor="waste-material">
          <strong>Material category</strong>
        </label>

        <select
          id="waste-material"
          className="waste-description-input"
          value={material}
          onChange={(event) => setMaterial(event.target.value)}
        >
          <option value="plastic">Plastic</option>
          <option value="paper">Paper and cardboard</option>
          <option value="glass">Glass</option>
          <option value="metal">Metal</option>
          <option value="organic">Organic waste</option>
          <option value="electronic">Electronic waste</option>
          <option value="textile">Textiles and clothing</option>
          <option value="unknown">Unknown material</option>
        </select>

        {message && (
          <div className="inline-message" role="alert">
            {message}
          </div>
        )}

        <button
          className="primary-button full-button"
          disabled={loading || (!item.trim() && !file)}
          onClick={() => void analyzeItem()}
        >
          <Sparkles size={17} />
            {loading
              ? "Analyzing waste with AI..."
              : file
                ? "Identify waste from photo"
                : "Analyze waste item"}
        </button>
      </div>

      {result && (
        <section className="panel info-card" aria-live="polite">
          <CheckCircle2 size={24} className="green-icon" />
          <h2>Recommendations</h2>

          <p>
            <strong>Identified material: </strong>
            {String(
              result.identified_material ??
              result.material ??
              material,
            )}
          </p>

          <pre className="analysis-result">
            {JSON.stringify(result, null, 2)}
          </pre>

          <p>
            AI-generated recommendations are estimates. Verify material
            identification and local recycling rules before disposal.
          </p>
        </section>
      )}

      <div className="info-grid">
        <InfoCard
          icon={Sprout}
          title="Reuse first"
          text="Discover practical ways to extend an item's useful life."
        />
        <InfoCard
          icon={Recycle}
          title="Recycle responsibly"
          text="Check appropriate recycling options for each material."
        />
        <InfoCard
          icon={ShieldCheck}
          title="Safety matters"
          text="Follow material-specific handling and disposal guidance."
        />
      </div>
    </section>
  );
}

function InfoCard({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof Leaf;
  title: string;
  text: string;
}) {
  return (
    <article className="panel info-card">
      <Icon size={22} className="green-icon" />
      <strong>{title}</strong>
      <p>{text}</p>
    </article>
  );
}

function AIAssistant() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; text: string }[]
  >([
    {
      role: "assistant",
      text: "Vanakkam! 🌱 What kind of waste are you dealing with? Ask me about reuse, recycling, composting, or responsible disposal.",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(message?: string) {
    const text = (message ?? input).trim();

    if (!text || loading) return;

    setMessages((current) => [
      ...current,
      { role: "user", text },

      
    ]);

    setInput("");
    setError("");
    setLoading(true);

    try {
      const result = await ecoLoopApi.chat(text);

      const answer =
        typeof result.answer === "string"
          ? result.answer
          : typeof result.message === "string"
            ? result.message
            : "The backend responded, but no answer was provided.";

      setMessages((current) => [
        ...current,
        { role: "assistant", text: answer },
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to contact the EcoLoop AI backend.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="feature-page">
      <div className="eyebrow">
        <Sparkles size={14} /> ECOLOOP ASSISTANT
      </div>

      <h1>Let's rethink waste.</h1>

      <p className="page-description">
        Explore ideas for reuse, recycling, creative projects and
        responsible waste management.
      </p>

      <div className="panel chat-panel">
        <div className="chat-heading">
          <div className="assistant-avatar">
            <Bot size={24} />
          </div>

          <div>
            <strong>EcoLoop AI</strong>
            <span>Waste and circular-economy assistant</span>
          </div>

          <span className="demo-status">
            {loading ? "Thinking..." : "Connected interface"}
          </span>
        </div>

        <div className="chat-messages" aria-live="polite">
          {messages.map((message, index) => (
            <div
              className={`chat-bubble ${
                message.role === "user"
                  ? "user-bubble"
                  : "assistant-bubble"
              }`}
              key={`${message.role}-${index}`}
            >
              {message.role === "assistant" ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.text.replace(/\\([*_`])/g, "$1")}
                </ReactMarkdown>
              ) : (
                message.text
              )}
            </div>
          ))}

          {loading && (
            <div className="chat-bubble assistant-bubble">
              <span className="typing-indicator" role="status">
                EcoLoop AI is thinking...
              </span>
            </div>
          )}
        </div>

        {error && (
          <div className="inline-message" role="alert">
            {error}
          </div>
        )}

        <div className="suggestion-list">
          {[
            "What can I create from plastic bottles?",
            "How do I recycle old electronics?",
            "How can kitchen waste become useful?",
          ].map((suggestion) => (
            <button
              key={suggestion}
              disabled={loading}
              onClick={() => void sendMessage(suggestion)}
            >
              {suggestion}
              <ArrowUpRight size={14} />
            </button>
          ))}
        </div>

        <form
          className="chat-input-row"
          onSubmit={(event) => {
            event.preventDefault();
            void sendMessage();
          }}
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about any waste item..."
            aria-label="Your question"
            disabled={loading}
          />

          <button
            className="primary-button send-button"
            type="submit"
            aria-label="Send message"
            disabled={loading || !input.trim()}
          >
            <Send size={17} />
          </button>
        </form>

        <p className="chat-disclaimer">
          Guidance is generated by the connected backend. Verify local
          recycling rules before disposing of materials.
        </p>
      </div>
    </section>
  );
}
function RecyclingFinder() {
  type RecyclingCategory = {
    id: string;
    name: string;
    reuse: string[];
    recycle: string[];
    upcycle: string[];
    safety: string[];
  };

  const [categories, setCategories] = useState<RecyclingCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadCategories() {
      setLoading(true);
      setError("");

      try {
        const result = await ecoLoopApi.recycling();

        const data = result.categories;

        if (!Array.isArray(data)) {
          throw new Error("The recycling API returned an unexpected response.");
        }

        if (!cancelled) {
          setCategories(data as RecyclingCategory[]);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load recycling guidance.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadCategories();

    return () => {
      cancelled = true;
    };
  }, []);

  const icons = [Recycle, FileImage, ShieldCheck, Sprout, Zap, Leaf, Droplets];
  const colors = ["mint", "yellow", "purple", "blue"];

  return (
    <section className="feature-page">
      <div className="eyebrow">
        <Recycle size={14} /> CIRCULAR ECONOMY
      </div>

      <h1>Give materials another life.</h1>

      <p className="page-description">
        Explore reuse, recycling, upcycling and safety guidance
        provided by the EcoLoop AI backend.
      </p>

      {loading && (
        <div className="panel info-card" role="status">
          Loading recycling guidance...
        </div>
      )}

      {error && (
        <div className="panel info-card" role="alert">
          <strong>Unable to load recycling guidance</strong>
          <p>{error}</p>
          <button
            className="primary-button"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && categories.length === 0 && (
        <div className="panel info-card">
          No recycling categories are available yet.
        </div>
      )}

      {!loading && !error && categories.length > 0 && (
        <div className="finder-grid">
          {categories.map((item, index) => {
            const Icon = icons[index % icons.length];

            return (
              <article className="panel material-card" key={item.id}>
                <div
                  className={`material-icon ${colors[index % colors.length]}`}
                >
                  <Icon size={25} />
                </div>

                <span className="material-type">
                  {item.id.toUpperCase()}
                </span>

                <h3>{item.name}</h3>

                <p>
                  <strong>Reuse</strong>
                  <br />
                  {item.reuse?.[0] ?? "Check suitable reuse options."}
                </p>

                <p>
                  <strong>Recycling</strong>
                  <br />
                  {item.recycle?.[0] ?? "Check local recycling guidance."}
                </p>

                {item.upcycle?.length > 0 && (
                  <p>
                    <strong>Upcycling</strong>
                    <br />
                    {item.upcycle[0]}
                  </p>
                )}

                {item.safety?.length > 0 && (
                  <p>
                    <strong>Safety</strong>
                    <br />
                    {item.safety[0]}
                  </p>
                )}

                <span className="listing-note">
                  General guidance · Verify local rules
                </span>
              </article>
            );
          })}
        </div>
      )}

      <div className="panel notice-panel">
        <ShieldCheck size={21} />
        <div>
          <strong>Dispose of waste responsibly</strong>
          <p>
            This information provides general guidance. Collection
            availability, accepted materials and disposal rules vary
            by location. Live recycler listings have not yet been connected.
          </p>
        </div>
      </div>
    </section>
  );
}

function MyImpact() {
  const [impact, setImpact] = useState<Record<string, unknown> | null>(null);
  const [actions, setActions] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadImpact() {
    setLoading(true);
    setError("");

    try {
      const sessionId = getSessionId();

      const [impactResponse, actionsResponse] = await Promise.all([
        ecoLoopApi.getImpact(sessionId),
        ecoLoopApi.getActions(sessionId),
      ]);

      const actionData =
        actionsResponse.actions ??
        actionsResponse.items ??
        [];

      setImpact(impactResponse);
      setActions(Array.isArray(actionData) ? actionData : []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your impact records.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadImpact();
  }, []);

  const totalActions = Number(
    impact?.totalRecordedActions ?? actions.length,
  );

  const totalItems = Number(
    impact?.totalReportedItems ?? 0,
  );

  const carbonSavings = impact?.carbonSavingsKg;

  return (
    <section className="feature-page">
      <div className="eyebrow">
        <Activity size={14} /> YOUR IMPACT
      </div>

      <h1>Every action counts.</h1>

      <p className="page-description">
        Track the waste-reduction actions you report to EcoLoop AI.
      </p>

      <div className="panel ledger-panel">
        <div className="panel-heading">
          <div>
            <h3>Recovery ledger</h3>
            <p>Your session's recorded actions</p>
          </div>

          <ShieldCheck size={22} className="green-icon" />
        </div>

        {loading && (
          <div className="inline-message" role="status">
            Loading your impact records...
          </div>
        )}

        {error && (
          <div className="inline-message" role="alert">
            <p>{error}</p>

            <button
              className="primary-button"
              onClick={() => void loadImpact()}
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="ledger-summary">
              <div>
                <span>Reported items</span>
                <strong>{totalItems}</strong>
              </div>

              <div>
                <span>Recorded actions</span>
                <strong>{totalActions}</strong>
              </div>

              <div>
                <span>Carbon savings</span>
                <strong>
                  {typeof carbonSavings === "number"
                    ? `${carbonSavings} kg`
                    : "Not measured"}
                </strong>
              </div>
            </div>

            <div className="ledger-note">
              <CheckCircle2 size={18} />

              <span>
                Records are self-reported unless independently verified.
                Carbon savings are not calculated unless the backend
                provides a measured value.
              </span>
            </div>

            <div className="panel-heading">
              <div>
                <h3>Recent actions</h3>
                <p>Actions associated with this browser session</p>
              </div>

              <button
                className="icon-button"
                onClick={() => void loadImpact()}
                aria-label="Refresh impact records"
              >
                <Activity size={18} />
              </button>
            </div>

            {actions.length === 0 ? (
              <p className="page-description">
                No actions recorded yet. Once action recording is connected,
                your reported activities will appear here.
              </p>
            ) : (
              <div className="activity-list">
                {actions.map((action, index) => (
                  <div
                    className="activity-item"
                    key={String(action.actionId ?? index)}
                  >
                    <div className="activity-icon mint">
                      <Recycle size={20} />
                    </div>

                    <div className="activity-copy">
                      <strong>
                        {String(action.item ?? "Waste item")}
                      </strong>

                      <span>
                        {String(action.actionType ?? "Action")} ·{" "}
                        {String(action.material ?? "Unknown material")}
                      </span>
                    </div>

                    <div className="activity-amount">
                      <strong>
                        {String(action.quantity ?? 1)}
                      </strong>

                      <span>
                        {typeof action.createdAt === "string"
                          ? new Date(action.createdAt).toLocaleDateString()
                          : "Recorded"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <p className="page-description">
        Impact data is scoped to the session identifier stored in this
        browser. It is not an authenticated user account.
      </p>
    </section>
  );
}

function App() {
  const [page, setPage] = useState<Page>("Dashboard");
  const [search, setSearch] = useState("");

  const activeNav = navigation.find((item) => item.label === page);
  const ActiveIcon = activeNav?.icon ?? Leaf;

  function navigate(next: Page) {
    setPage(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => navigate("Dashboard")}>
          <span className="brand-mark"><Recycle size={25} /></span>
          <span>
            <strong>ecoloop<span>ai</span></strong>
            <small>WASTE LESS. LIVE MORE.</small>
          </span>
        </button>

        <div className="nav-label">WORKSPACE</div>
        <nav className="main-navigation">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              onClick={() => navigate(label)}
              className={`nav-item ${page === label ? "active" : ""}`}
            >
              <Icon size={19} />
              <span>{label}</span>
              {label === "AI Assistant" && <span className="new-badge">AI</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="eco-tip">
            <div className="tip-icon"><Sprout size={19} /></div>
            <strong>A little greener, every day.</strong>
            <p>Choose reuse before disposal whenever it's safe and practical.</p>
          </div>

          <div className="sidebar-footer">
            <span className="footer-dot" />
            <span>Hackathon build Â· Preview</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>EcoLoop AI</span><ChevronRight size={14} />
            <strong><ActiveIcon size={15} /> {page}</strong>
          </div>

          <div className="topbar-right">
            <label className="search-box">
              <Search size={17} />
              <input
                placeholder="Search ideas..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                aria-label="Search ideas"
              />
              {search && (
                <button onClick={() => setSearch("")} aria-label="Clear search">Ã—</button>
              )}
            </label>
            <div className="avatar">E</div>
          </div>
        </header>

        <div className="page-content">
          {page === "Dashboard" && <Dashboard navigate={navigate} />}
          {page === "Scan Waste" && <ScanWaste />}
          {page === "AI Assistant" && <AIAssistant />}
          {page === "Recycling Finder" && <RecyclingFinder />}
          {page === "My Impact" && <MyImpact />}

          <footer className="page-footer">
            <span>© 2026 EcoLoop AI</span>
            <span>Designed for a more circular future <Leaf size={13} /></span>
          </footer>
        </div>
      </main>
    </div>
  );
}

export default App;