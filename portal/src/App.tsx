import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  Acquisition,
  Briefing,
  CapabilitySnapshot,
  Decision,
  HealthSnapshot,
  Lead,
  LaunchDeck,
  LeadPipeline,
  SovereignStatus,
  Task,
  UncertaintyReview,
  api,
  clearToken,
  getToken,
} from "./api";
import Login from "./Login";

type Tab = "launch" | "uncertainty" | "overview" | "empire" | "tasks" | "decisions" | "voice" | "activity";

function StatCard({ label, value, accent }: { label: string; value: number; accent?: string }) {
  return (
    <div className="stat-card">
      <span className="stat-value" style={{ color: accent }}>{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function Dashboard() {
  const [tab, setTab] = useState<Tab>("launch");
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [voiceSessions, setVoiceSessions] = useState<VoiceSession[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [capability, setCapability] = useState<CapabilitySnapshot | null>(null);
  const [acquisitions, setAcquisitions] = useState<Acquisition[]>([]);
  const [categories, setCategories] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [addName, setAddName] = useState("");
  const [addCategory, setAddCategory] = useState("network");
  const [addCost, setAddCost] = useState("");
  const [addPriority, setAddPriority] = useState("7");
  const [addStatus, setAddStatus] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadPipeline, setLeadPipeline] = useState<LeadPipeline | null>(null);
  const [launchDeck, setLaunchDeck] = useState<LaunchDeck | null>(null);
  const [ecoJobs, setEcoJobs] = useState<Array<Record<string, unknown>>>([]);
  const [ecoEconomics, setEcoEconomics] = useState<Record<string, unknown> | null>(null);
  const [sovereign, setSovereign] = useState<SovereignStatus | null>(null);
  const [health, setHealth] = useState<HealthSnapshot | null>(null);
  const [launchBusy, setLaunchBusy] = useState(false);
  const [leadName, setLeadName] = useState("");
  const [leadPhone, setLeadPhone] = useState("");
  const [leadCity, setLeadCity] = useState("Kansas City");
  const [leadEmail, setLeadEmail] = useState("");
  const [launchStatus, setLaunchStatus] = useState<string | null>(null);
  const [chatMessage, setChatMessage] = useState("");
  const [chatFile, setChatFile] = useState<File | null>(null);
  const [presaleHost, setPresaleHost] = useState("");
  const [presaleAddress, setPresaleAddress] = useState("");
  const [presaleCity, setPresaleCity] = useState("Kansas City");
  const [presaleWorker, setPresaleWorker] = useState("rah:closer");
  const [presaleProof, setPresaleProof] = useState("");
  const [presaleDrill, setPresaleDrill] = useState(false);
  const [uncertaintyReviews, setUncertaintyReviews] = useState<UncertaintyReview[]>([]);
  const [hunterSheet, setHunterSheet] = useState<Record<string, unknown> | null>(null);
  const [resolveIntent, setResolveIntent] = useState<Record<number, string>>({});

  const refresh = useCallback(async () => {
    try {
      const [b, t, d, v, a, cap, acq, cats, ld, sov, h, deck, pipe, eco, ej, unc, sheet] = await Promise.all([
        api.briefing(),
        api.tasks(),
        api.decisions(),
        api.voiceSessions(),
        api.activity(),
        api.capability().catch(() => null),
        api.acquisitions().catch(() => []),
        api.acquisitionCategories().catch(() => ({ categories: {} })),
        api.leads().catch(() => []),
        api.sovereignStatus().catch(() => null),
        api.health().catch(() => null),
        api.launchStatus().catch(() => null),
        api.leadPipeline().catch(() => null),
        api.ecoStatus().catch(() => null),
        api.ecoJobs().catch(() => []),
        api.uncertaintyReviews().catch(() => []),
        api.ecoHunterSheet().catch(() => null),
      ]);
      setBriefing(b);
      setTasks(t);
      setDecisions(d);
      setVoiceSessions(v);
      setActivity(a);
      setCapability(cap);
      setAcquisitions(acq);
      setLeads(ld);
      setSovereign(sov);
      setHealth(h);
      setLaunchDeck(deck);
      setLeadPipeline(pipe);
      setEcoEconomics((eco as { economics?: Record<string, unknown> })?.economics ?? null);
      setEcoJobs(ej);
      setUncertaintyReviews(unc);
      setHunterSheet(sheet);
      const categoryMap: Record<string, string> = cats.categories ?? {};
      setCategories(categoryMap);
      if (Object.keys(categoryMap).length && !categoryMap[addCategory]) {
        setAddCategory(Object.keys(categoryMap)[0]);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const stats = briefing?.stats;

  async function handleAddAcquisition(e: React.FormEvent) {
    e.preventDefault();
    setAddStatus(null);
    try {
      await api.addAcquisition({
        category: addCategory,
        name: addName,
        target_cost_cents: addCost ? Math.round(parseFloat(addCost) * 100) : 0,
        priority: parseInt(addPriority, 10) || 7,
      });
      setAddName("");
      setAddCost("");
      setAddStatus("Added to sovereign manifest.");
      await refresh();
    } catch (err) {
      setAddStatus(err instanceof Error ? err.message : "Failed to add");
    }
  }

  async function handleHuntLeads() {
    setLaunchBusy(true);
    setLaunchStatus(null);
    try {
      const result = await api.huntLeads(leadCity || "Kansas City", 25);
      const hunted = (result.hunted as number) ?? 0;
      const phones = (result.with_phone as number) ?? 0;
      setLaunchStatus(`Hunted ${hunted} leads (${phones} with phone). Pipeline filling.`);
      await refresh();
    } catch (err) {
      setLaunchStatus(err instanceof Error ? err.message : "Hunt failed");
    } finally {
      setLaunchBusy(false);
    }
  }

  async function handleEcoStrike() {
    setLaunchBusy(true);
    setLaunchStatus(null);
    try {
      const result = await api.ecoStrikeList();
      const count = (result.strike_list as unknown[])?.length ?? 0;
      setLaunchStatus(`Strike list: ${count} KCMO doors queued for hunters.`);
      await refresh();
    } catch (err) {
      setLaunchStatus(err instanceof Error ? err.message : "Strike list failed");
    } finally {
      setLaunchBusy(false);
    }
  }

  async function handleKillShot(drill = false) {
    setLaunchBusy(true);
    setLaunchStatus(null);
    try {
      const result = await api.killShot("Kansas City", drill);
      const hunted = (result.hunt as { strike_list?: unknown[] } | null)?.strike_list?.length ?? 0;
      setLaunchStatus(
        drill
          ? `Eco-Express drill. ${hunted} doors on strike list.`
          : `ECO-EXPRESS LIVE. ${hunted} doors targeted. Hunters deploy tomorrow.`,
      );
      await refresh();
    } catch (err) {
      setLaunchStatus(err instanceof Error ? err.message : "Launch failed");
    } finally {
      setLaunchBusy(false);
    }
  }

  async function handleAddLead(e: React.FormEvent) {
    e.preventDefault();
    setLaunchStatus(null);
    try {
      await api.addLead({
        name: leadName,
        phone: leadPhone,
        city: leadCity,
        email: leadEmail || undefined,
      });
      setLeadName("");
      setLeadPhone("");
      setLeadEmail("");
      setLaunchStatus("Lead fed to pipeline.");
      await refresh();
    } catch (err) {
      setLaunchStatus(err instanceof Error ? err.message : "Lead failed");
    }
  }

  async function handleChatSend(e: React.FormEvent) {
    e.preventDefault();
    setLaunchStatus(null);
    try {
      if (chatFile) {
        await api.readyRoomUpload(chatFile, chatMessage);
        setChatFile(null);
      } else if (chatMessage.trim()) {
        await api.readyRoomChat(chatMessage);
      }
      setChatMessage("");
      setLaunchStatus("Command sent.");
      await refresh();
    } catch (err) {
      setLaunchStatus(err instanceof Error ? err.message : "Chat failed");
    }
  }

  async function handlePresale(e: React.FormEvent) {
    e.preventDefault();
    setLaunchStatus(null);
    try {
      const result = await api.presale({
        host_name: presaleHost,
        property_address: presaleAddress,
        city_grid: presaleCity,
        worker_ref: presaleWorker,
        proof_notes: presaleProof,
        dry_run_closer: presaleDrill,
      });
      setLaunchStatus(`Presale recorded: ${JSON.stringify(result).slice(0, 120)}…`);
      await refresh();
    } catch (err) {
      setLaunchStatus(err instanceof Error ? err.message : "Presale failed");
    }
  }

  async function handleDrill() {
    setLaunchStatus(null);
    try {
      const result = await api.sovereignSimulate();
      setLaunchStatus(`Drill complete: ${JSON.stringify(result).slice(0, 120)}…`);
      await refresh();
    } catch (err) {
      setLaunchStatus(err instanceof Error ? err.message : "Drill failed");
    }
  }

  return (
    <div className="dashboard">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">◆</span>
          <div>
            <h1>Command Center</h1>
            <p className="mono status-live">● LIVE</p>
          </div>
        </div>
        <div className="topbar-actions">
          <button className="btn-ghost" onClick={refresh}>Refresh</button>
          <button className="btn-ghost" onClick={() => { clearToken(); window.location.reload(); }}>
            Logout
          </button>
        </div>
      </header>

      {briefing && (
        <section className="briefing-banner">
          <h2>{briefing.greeting}</h2>
          <p>Voice OS is standing by. Call your Vapi number anytime to command your empire.</p>
        </section>
      )}

      {stats && (
        <section className="stats-row">
          <StatCard label="Pending Tasks" value={stats.tasks_pending} accent="var(--warning)" />
          <StatCard label="In Progress" value={stats.tasks_in_progress} accent="var(--accent)" />
          <StatCard label="Completed" value={stats.tasks_completed} accent="var(--success)" />
          <StatCard label="Decisions Waiting" value={stats.decisions_pending} accent="var(--danger)" />
          <StatCard label="Uncertainty" value={stats.uncertainty_pending ?? 0} accent="var(--warning)" />
          <StatCard label="Voice Calls Today" value={stats.voice_sessions_today} accent="var(--voice)" />
        </section>
      )}

      <nav className="tabs">
        {(["launch", "uncertainty", "overview", "empire", "tasks", "decisions", "voice", "activity"] as Tab[]).map((t) => (
          <button
            key={t}
            className={tab === t ? "tab active" : "tab"}
            onClick={() => setTab(t)}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </nav>

      <main className="content">
        {loading && !briefing ? (
          <p className="loading">Loading command deck...</p>
        ) : tab === "launch" ? (
          <div className="grid-2">
            <Panel title="Eco-Express — D2C thermostat flips" wide>
              <div className="launch-hero">
                <p className="launch-phrase">
                  <strong>No hosts.</strong> Hunters close $149 at the door. RAH installs in 15 min.
                  {ecoEconomics && (
                    <> Net <strong>${String(ecoEconomics.net_profit_usd)}</strong>/door.</>
                  )}
                </p>
                <div className="launch-badges">
                  <span className={`badge ${launchDeck?.sara_wired ? "badge-completed" : "badge-pending"}`}>
                    SARA {launchDeck?.sara_wired ? "wired" : "run Wire SARA"}
                  </span>
                  <span className="badge badge-completed">
                    {ecoJobs.length} doors in pipeline
                  </span>
                  <span className="badge badge-completed">KCMO · Evergy rebate stack</span>
                </div>
              </div>
              <div className="launch-actions">
                <button
                  type="button"
                  className="btn-killshot"
                  disabled={launchBusy}
                  onClick={() => handleKillShot(false)}
                >
                  {launchBusy ? "Launching…" : "LAUNCH ECO-EXPRESS LIVE"}
                </button>
                <button
                  type="button"
                  className="btn-hunt"
                  disabled={launchBusy}
                  onClick={handleEcoStrike}
                >
                  {launchBusy ? "Building…" : "BUILD STRIKE LIST (Loop A)"}
                </button>
                <button
                  type="button"
                  className="btn-ghost launch-drill-inline"
                  disabled={launchBusy}
                  onClick={() => handleKillShot(true)}
                >
                  Sights on (drill)
                </button>
              </div>
              <p className="launch-hint">
                $149 homeowner − ~$50 hardware (rebate) − $40 installer = <strong>$59 net</strong>.
                Goal 4/day. Cash vault → your own properties later. Manual: vault/commander/eco-express-play.md
              </p>
            </Panel>
            <Panel title="Strike list — homeowner doors">
              {ecoJobs.length === 0 ? (
                <EmptyState text="No doors yet — tap BUILD STRIKE LIST or LAUNCH LIVE." />
              ) : (
                ecoJobs.slice(0, 20).map((j) => (
                  <div key={String(j.id)} className="row-item compact">
                    <div className="row-main">
                      <strong>{String(j.homeowner_name)}</strong>
                      <p>{String(j.address)} · {String(j.phone)}</p>
                    </div>
                    <span className="badge">{String(j.status)}</span>
                  </div>
                ))
              )}
            </Panel>
            <Panel title="Closer sheet — send hunter to door" wide>
              {hunterSheet ? (
                <>
                  <p className="launch-hint">
                    <strong>{String(hunterSheet.city)}</strong> — {String(hunterSheet.why_this_city)}
                    {" "}{String(hunterSheet.count)} doors ready · collect ${String(hunterSheet.collect_usd)} before work.
                  </p>
                  <pre className="pitch-block">{String(hunterSheet.pitch)}</pre>
                  {(hunterSheet.doors as Array<Record<string, unknown>>)?.slice(0, 15).map((d) => (
                    <div key={String(d.id)} className="row-item compact">
                      <div className="row-main">
                        <strong>#{String(d.id)} {String(d.homeowner_name)}</strong>
                        <p>{String(d.phone)} · {String(d.address)}</p>
                      </div>
                      <span className="badge">{String(d.status)}</span>
                    </div>
                  ))}
                </>
              ) : (
                <EmptyState text="Build strike list first — closer sheet fills automatically." />
              )}
            </Panel>
            <Panel title="Loop B — homeowner paid $149">
              <form className="add-form" onSubmit={async (e) => {
                e.preventDefault();
                setLaunchStatus(null);
                try {
                  const jobId = parseInt(presaleHost, 10);
                  await api.ecoPaymentConfirmed(jobId, presaleProof, presaleCity || "ASAP");
                  setLaunchStatus("Payment confirmed — Lowe's barcode + installer dispatched.");
                  await refresh();
                } catch (err) {
                  setLaunchStatus(err instanceof Error ? err.message : "Payment flow failed");
                }
              }}>
                <label>Job ID<input value={presaleHost} onChange={(e) => setPresaleHost(e.target.value)} required placeholder="from strike list" /></label>
                <label>Payment proof<input value={presaleProof} onChange={(e) => setPresaleProof(e.target.value)} required placeholder="Stripe / Cash App ref" /></label>
                <label>Install slot<input value={presaleCity} onChange={(e) => setPresaleCity(e.target.value)} placeholder="ASAP or 4:00 PM" /></label>
                <button type="submit" className="btn-primary">Confirm payment → dispatch install</button>
              </form>
            </Panel>
            <Panel title="Voice / chat (optional)">
              <form className="add-form chat-form" onSubmit={handleChatSend}>
                <label>
                  Command
                  <input
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    placeholder="launch eco express live"
                  />
                </label>
                <button type="submit" className="btn-primary">Send</button>
              </form>
            </Panel>
            {launchStatus && <p className="form-status launch-status wide">{launchStatus}</p>}
          </div>
        ) : tab === "uncertainty" ? (
          <div className="grid-2">
            <Panel title="Uncertainty queue — sensation held" wide>
              <p className="launch-hint">
                Low-confidence vision/OCR (&lt;85%) stops auto-execute. Approve, correct intent, or reject.
              </p>
              {uncertaintyReviews.length === 0 ? (
                <EmptyState text="No pending uncertainty reviews. System is clear." />
              ) : (
                uncertaintyReviews.map((r) => {
                  let payload: Record<string, unknown> = {};
                  try {
                    payload = JSON.parse(r.payload_json);
                  } catch {
                    payload = {};
                  }
                  return (
                    <div key={r.id} className="row-item">
                      <div className="row-main">
                        <strong>{r.source_node}</strong>
                        <p>Confidence {(r.confidence_score * 100).toFixed(0)}% — {r.reason || "review needed"}</p>
                        <p className="mono">{String(payload.suggested_intent || payload.intent || "")}</p>
                      </div>
                      <form
                        className="add-form compact"
                        onSubmit={async (e) => {
                          e.preventDefault();
                          setLaunchStatus(null);
                          try {
                            await api.uncertaintyResolve(r.id, {
                              action: "override",
                              corrected_intent: resolveIntent[r.id] || String(payload.suggested_intent || ""),
                              mode: "live",
                            });
                            await api.readyRoomScan();
                            setLaunchStatus(`Review ${r.id} approved — scan fired.`);
                            await refresh();
                          } catch (err) {
                            setLaunchStatus(err instanceof Error ? err.message : "Resolve failed");
                          }
                        }}
                      >
                        <input
                          value={resolveIntent[r.id] ?? String(payload.suggested_intent || "")}
                          onChange={(e) => setResolveIntent({ ...resolveIntent, [r.id]: e.target.value })}
                          placeholder="Corrected intent"
                        />
                        <button type="submit" className="btn-primary">Approve & execute</button>
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={async () => {
                            await api.uncertaintyResolve(r.id, { action: "reject" });
                            await refresh();
                          }}
                        >
                          Reject
                        </button>
                      </form>
                    </div>
                  );
                })
              )}
            </Panel>
            {launchStatus && <p className="form-status launch-status wide">{launchStatus}</p>}
          </div>
        ) : tab === "overview" ? (
          <div className="grid-2">
            <Panel title="Active Tasks">
              {(briefing?.pending_tasks ?? []).length === 0 ? (
                <EmptyState text="No active tasks. Call your voice agent to create one." />
              ) : (
                briefing!.pending_tasks.map((t) => <TaskRow key={t.id} task={t} />)
              )}
            </Panel>
            <Panel title="Decisions Needed">
              {(briefing?.pending_decisions ?? []).length === 0 ? (
                <EmptyState text="No pending decisions." />
              ) : (
                briefing!.pending_decisions.map((d) => <DecisionRow key={d.id} decision={d} />)
              )}
            </Panel>
            {capability && (
              <Panel title="Empire Capability (snapshot)" wide>
                <div className="empire-snapshot">
                  <p className="empire-summary">{capability.voice_summary}</p>
                  <div className="empire-stats">
                    <span>Tier {capability.empire.tier} — {capability.empire.label}</span>
                    <span>Ammo ${capability.liquidity.ammo_usd.toFixed(2)}</span>
                    <span>Float ${capability.liquidity.float_hold_usd.toFixed(2)}</span>
                    <span>Deployable ${capability.liquidity.total_deployable_usd.toFixed(2)}</span>
                  </div>
                  <ul className="empire-actions">
                    {capability.recommended_actions.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </div>
              </Panel>
            )}
            <Panel title="Recent Activity" wide>
              {(briefing?.recent_activity ?? []).map((a) => (
                <ActivityRow key={a.id} activity={a} />
              ))}
            </Panel>
          </div>
        ) : tab === "empire" ? (
          <div className="grid-2">
            <Panel title="What You Can Afford Now" wide>
              {!capability ? (
                <EmptyState text="Loading capability snapshot..." />
              ) : (
                <div className="empire-snapshot">
                  <p className="empire-summary">{capability.voice_summary}</p>
                  <div className="empire-stats">
                    <span>Tier {capability.empire.tier} — {capability.empire.label}</span>
                    <span>{capability.effective_rates.ammo_percent}% → ammo</span>
                    <span>{capability.effective_rates.hold_hours}h float</span>
                  </div>
                  {capability.ready_to_order.length > 0 && (
                    <>
                      <h4 className="section-label">Ready to order</h4>
                      {capability.ready_to_order.map((item) => (
                        <div key={item.id} className="row-item compact">
                          <div className="row-main">
                            <strong>{item.name}</strong>
                            <p>{item.capability}</p>
                          </div>
                          <span className="badge badge-completed">funded</span>
                        </div>
                      ))}
                    </>
                  )}
                  {capability.affordable_now.length > 0 && (
                    <>
                      <h4 className="section-label">Affordable now</h4>
                      {capability.affordable_now.map((item) => (
                        <div key={item.id} className="row-item compact">
                          <div className="row-main">
                            <strong>{item.name}</strong>
                            <p>{item.reason}</p>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                  {capability.next_unlocks.length > 0 && (
                    <>
                      <h4 className="section-label">Closest unlocks</h4>
                      {capability.next_unlocks.slice(0, 5).map((item) => (
                        <div key={item.id} className="row-item compact">
                          <div className="row-main">
                            <strong>{item.name}</strong>
                            <p>{item.funded_percent}% funded · ${item.remaining_usd.toFixed(2)} to go</p>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </Panel>
            <Panel title="Add to Manifest">
              <form className="add-form" onSubmit={handleAddAcquisition}>
                <label>
                  Name
                  <input value={addName} onChange={(e) => setAddName(e.target.value)} required placeholder="e.g. Starlink Mini" />
                </label>
                <label>
                  Category
                  <select value={addCategory} onChange={(e) => setAddCategory(e.target.value)}>
                    {Object.keys(categories).map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Target cost (USD)
                  <input value={addCost} onChange={(e) => setAddCost(e.target.value)} placeholder="2500" />
                </label>
                <label>
                  Priority (1-10)
                  <input value={addPriority} onChange={(e) => setAddPriority(e.target.value)} />
                </label>
                <button type="submit" className="btn-primary">Add target</button>
                {addStatus && <p className="form-status">{addStatus}</p>}
              </form>
            </Panel>
            <Panel title="Acquisition Queue" wide>
              {acquisitions.length === 0 ? (
                <EmptyState text="No targets yet." />
              ) : (
                acquisitions.map((a) => (
                  <div key={a.id} className="row-item">
                    <div className="row-main">
                      <strong>{a.name}</strong>
                      <p>{a.description || a.equipment_spec || a.category}</p>
                    </div>
                    <div className="row-meta">
                      <span className="badge">{a.status}</span>
                      <span className="mono">
                        ${(a.funded_cents / 100).toFixed(0)} / ${(a.target_cost_cents / 100).toFixed(0)}
                      </span>
                      <span className="mono">P{a.priority} · T{a.empire_tier}</span>
                    </div>
                  </div>
                ))
              )}
            </Panel>
          </div>
        ) : tab === "tasks" ? (
          <Panel title="All Tasks">
            {tasks.length === 0 ? (
              <EmptyState text="No tasks yet." />
            ) : (
              tasks.map((t) => <TaskRow key={t.id} task={t} />)
            )}
          </Panel>
        ) : tab === "decisions" ? (
          <Panel title="Decision Queue">
            {decisions.length === 0 ? (
              <EmptyState text="No decisions queued." />
            ) : (
              decisions.map((d) => <DecisionRow key={d.id} decision={d} />)
            )}
          </Panel>
        ) : tab === "voice" ? (
          <Panel title="Voice Sessions">
            {voiceSessions.length === 0 ? (
              <EmptyState text="No voice calls logged yet. Your first call will appear here." />
            ) : (
              voiceSessions.map((v) => <VoiceRow key={v.id} session={v} />)
            )}
          </Panel>
        ) : (
          <Panel title="Activity Log">
            {activity.map((a) => (
              <ActivityRow key={a.id} activity={a} />
            ))}
          </Panel>
        )}
      </main>

      <style>{dashboardStyles}</style>
    </div>
  );
}

function Panel({ title, children, wide }: { title: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <div className={`panel ${wide ? "wide" : ""}`}>
      <h3>{title}</h3>
      <div className="panel-body">{children}</div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="empty">{text}</p>;
}

function TaskRow({ task }: { task: Task }) {
  return (
    <div className="row-item">
      <div className="row-main">
        <strong>{task.title}</strong>
        {task.description && <p>{task.description}</p>}
      </div>
      <div className="row-meta">
        <span className={`badge badge-${task.status}`}>{task.status.replace("_", " ")}</span>
        <span className={`badge badge-priority-${task.priority}`}>{task.priority}</span>
        <span className="mono time">{timeAgo(task.created_at)}</span>
      </div>
    </div>
  );
}

function DecisionRow({ decision }: { decision: Decision }) {
  return (
    <div className="row-item">
      <div className="row-main">
        <strong>{decision.title}</strong>
        <p>{decision.context}</p>
        {decision.recommendation && (
          <p className="recommendation">Recommended: {decision.recommendation}</p>
        )}
      </div>
      <div className="row-meta">
        <span className={`badge badge-${decision.status}`}>{decision.status}</span>
        <span className="mono time">{timeAgo(decision.created_at)}</span>
      </div>
    </div>
  );
}

function VoiceRow({ session }: { session: VoiceSession }) {
  return (
    <div className="row-item">
      <div className="row-main">
        <strong>Voice Call #{session.id}</strong>
        <p>{session.summary || "No summary available."}</p>
      </div>
      <div className="row-meta">
        {session.duration_seconds != null && (
          <span className="mono">{Math.round(session.duration_seconds / 60)}m</span>
        )}
        <span className="mono time">{timeAgo(session.started_at)}</span>
      </div>
    </div>
  );
}

function ActivityRow({ activity }: { activity: Activity }) {
  return (
    <div className="row-item compact">
      <div className="row-main">
        <span className="mono event-type">{activity.event_type}</span>
        <p>{activity.message}</p>
      </div>
      <span className="mono time">{timeAgo(activity.created_at)}</span>
    </div>
  );
}

const dashboardStyles = `
  .dashboard { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
  .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
  .brand { display: flex; align-items: center; gap: 0.75rem; }
  .brand-icon { font-size: 1.5rem; color: var(--accent); }
  .brand h1 { font-size: 1.25rem; font-weight: 600; }
  .status-live { font-size: 0.7rem; color: var(--success); margin-top: 0.15rem; }
  .topbar-actions { display: flex; gap: 0.5rem; }
  .btn-ghost { background: transparent; border: 1px solid var(--border); color: var(--text-muted); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.875rem; }
  .btn-ghost:hover { border-color: var(--accent); color: var(--text); }
  .briefing-banner { background: linear-gradient(135deg, var(--bg-card), var(--bg-panel)); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
  .briefing-banner h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .briefing-banner p { color: var(--text-muted); }
  .stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
  .stat-card { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; text-align: center; }
  .stat-value { display: block; font-size: 2rem; font-weight: 700; }
  .stat-label { font-size: 0.8rem; color: var(--text-muted); }
  .tabs { display: flex; gap: 0.25rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0; }
  .tab { background: none; border: none; color: var(--text-muted); padding: 0.75rem 1.25rem; font-size: 0.9rem; border-bottom: 2px solid transparent; margin-bottom: -1px; }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
  .tab:hover { color: var(--text); }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }
  .panel { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .panel.wide { grid-column: 1 / -1; }
  .panel h3 { padding: 1rem 1.25rem; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); border-bottom: 1px solid var(--border); }
  .panel-body { padding: 0.5rem 0; max-height: 400px; overflow-y: auto; }
  .row-item { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; padding: 0.875rem 1.25rem; border-bottom: 1px solid var(--border); }
  .row-item:last-child { border-bottom: none; }
  .row-item.compact { align-items: center; }
  .row-main strong { display: block; margin-bottom: 0.15rem; }
  .row-main p { font-size: 0.875rem; color: var(--text-muted); }
  .recommendation { color: var(--accent) !important; font-style: italic; margin-top: 0.25rem; }
  .row-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 0.35rem; flex-shrink: 0; }
  .badge { font-size: 0.7rem; padding: 0.2rem 0.5rem; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.03em; background: var(--bg-card); }
  .badge-pending { color: var(--warning); }
  .badge-in_progress { color: var(--accent); }
  .badge-completed { color: var(--success); }
  .badge-priority-urgent { color: var(--danger); }
  .badge-persistence { color: var(--text-muted); font-size: 0.75rem; }
  .time { color: var(--text-muted); font-size: 0.75rem; }
  .event-type { font-size: 0.7rem; color: var(--voice); }
  .empty, .loading { padding: 2rem; text-align: center; color: var(--text-muted); }
  .empire-snapshot { padding: 0.5rem 1.25rem 1rem; }
  .empire-summary { color: var(--text); margin-bottom: 0.75rem; line-height: 1.5; }
  .empire-stats { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; font-size: 0.8rem; color: var(--accent); }
  .empire-actions { margin: 0; padding-left: 1.25rem; color: var(--text-muted); font-size: 0.875rem; }
  .empire-actions li { margin-bottom: 0.35rem; }
  .section-label { padding: 0.5rem 1.25rem 0; font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); }
  .add-form { padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 0.75rem; }
  .add-form label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--text-muted); }
  .add-form input, .add-form select { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem; color: var(--text); }
  .btn-primary { background: var(--accent); color: #000; border: none; border-radius: 8px; padding: 0.6rem 1rem; font-weight: 600; cursor: pointer; }
  .form-status { font-size: 0.8rem; color: var(--success); margin: 0; }
  .launch-hero { padding: 1rem 1.25rem 0.5rem; }
  .launch-phone { font-size: 1.25rem; font-weight: 600; }
  .launch-phone a { color: var(--voice); text-decoration: none; }
  .launch-phrase { color: var(--text-muted); font-size: 0.9rem; margin: 0.5rem 0; }
  .launch-badges { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
  .chat-form { border-top: 1px solid var(--border); }
  .launch-drill { margin: 0 1.25rem 1rem; }
  .launch-actions { padding: 0 1.25rem 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
  .btn-killshot {
    width: 100%; padding: 1rem; font-size: 1rem; font-weight: 700;
    background: #e53935; color: #fff; border: none; border-radius: 10px; cursor: pointer;
  }
  .btn-killshot:disabled { opacity: 0.6; }
  .btn-hunt {
    width: 100%; padding: 0.875rem; font-size: 0.95rem; font-weight: 600;
    background: var(--accent); color: #000; border: none; border-radius: 10px; cursor: pointer;
  }
  .btn-hunt:disabled { opacity: 0.6; }
  .launch-drill-inline { width: 100%; text-align: center; }
  .launch-hint { padding: 0 1.25rem 1rem; font-size: 0.8rem; color: var(--text-muted); margin: 0; }
  .pitch-block { white-space: pre-wrap; font-size: 0.75rem; background: var(--bg-elevated); padding: 0.75rem; border-radius: 6px; margin: 0 1.25rem 1rem; max-height: 200px; overflow: auto; }
  .pipeline-stats { padding: 0.75rem 1.25rem 0; font-size: 0.8rem; color: var(--accent); margin: 0; }
  .webhook-hint { padding: 0 1.25rem 1rem; font-size: 0.75rem; color: var(--text-muted); }
  .launch-status.wide { grid-column: 1 / -1; padding: 0 1.25rem 1rem; }
  .checkbox-row { flex-direction: row !important; align-items: center; gap: 0.5rem !important; }
`;

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());

  if (!authed) {
    return <Login onSuccess={() => setAuthed(true)} />;
  }

  return <Dashboard />;
}
