import React, { useState } from 'react';
import {
  Zap,
  RefreshCw,
  Sliders,
  Eye,
  Activity,
  Check,
  Plus,
  Key,
  ShieldCheck,
  Globe,
  CreditCard,
  ArrowRight,
  Search,
  Copy,
  CheckCircle2,
  Layers,
  Cpu,
  Server,
  TrendingUp,
  Sparkles,
  Lock,
} from 'lucide-react';

interface Integration {
  id: string;
  provider: 'stripe' | 'chargebee' | 'recurly';
  status: 'live' | 'syncing' | 'error' | 'disconnected';
  last_synced_at?: string;
  plansCount: number;
}

interface PreviewState {
  planId: string;
  planName: string;
  baseAmount: number;
  baseCurrency: string;
  targetCurrency: string;
  targetCountry: string;
  translatedAmount: number;
  taxLabel: string;
  complianceNote: string;
  ruleVersion: string;
}

interface ActivityLog {
  id: string;
  timestamp: string;
  method: string;
  endpoint: string;
  region: string;
  status: number;
  latencyMs: number;
  summary: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'integrations' | 'rules' | 'preview' | 'activity'>('integrations');
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyLabel, setNewKeyLabel] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isDeploying, setIsDeploying] = useState(false);

  // 1. Integrations State
  const [integrations, setIntegrations] = useState<Integration[]>([
    { id: '1', provider: 'stripe', status: 'live', last_synced_at: 'Just now', plansCount: 12 },
    { id: '2', provider: 'chargebee', status: 'live', last_synced_at: '5 mins ago', plansCount: 6 },
    { id: '3', provider: 'recurly', status: 'disconnected', plansCount: 0 },
  ]);

  // 2. Rules Engine Config State
  const [selectedCurrencies, setSelectedCurrencies] = useState<string[]>(['EUR', 'GBP', 'JPY', 'AUD', 'BRL']);
  const [regulationProfile, setRegulationProfile] = useState<string>('EU_VAT_GDPR');
  const [taxMode, setTaxMode] = useState<'inclusive' | 'exclusive'>('exclusive');
  const [roundingStrategy, setRoundingStrategy] = useState<string>('nearest_99');
  const [psychologicalPricing, setPsychologicalPricing] = useState<boolean>(true);

  // 3. Live Preview Studio State
  const [preview, setPreview] = useState<PreviewState>({
    planId: 'plan_pro',
    planName: 'Pro Tier',
    baseAmount: 49.00,
    baseCurrency: 'USD',
    targetCurrency: 'EUR',
    targetCountry: 'DE',
    translatedAmount: 58.99,
    taxLabel: '+ 19% VAT (DE)',
    complianceNote: 'EU VAT + GDPR Compliant',
    ruleVersion: 'v2.4',
  });

  // 4. Activity Logs
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([
    { id: 'log_1', timestamp: '22:57:42', method: 'POST', endpoint: '/v1/translate', region: 'DE', status: 200, latencyMs: 38, summary: '49.00 USD -> 58.99 EUR' },
    { id: 'log_2', timestamp: '22:56:10', method: 'GET', endpoint: '/v1/prices/plan_pro', region: 'GB', status: 200, latencyMs: 42, summary: 'Pro Tier: 49.00 USD -> 44.99 GBP' },
    { id: 'log_3', timestamp: '22:54:15', method: 'POST', endpoint: '/v1/translate', region: 'JP', status: 200, latencyMs: 29, summary: '49.00 USD -> 7400 JPY' },
    { id: 'log_4', timestamp: '22:50:03', method: 'POST', endpoint: '/v1/translate', region: 'BR', status: 200, latencyMs: 48, summary: '49.00 USD -> 279.99 BRL' },
  ]);

  const currencyFlagMap: Record<string, string> = {
    EUR: '🇪🇺',
    GBP: '🇬🇧',
    JPY: '🇯🇵',
    AUD: '🇦🇺',
    CAD: '🇨🇦',
    BRL: '🇧🇷',
    INR: '🇮🇳',
    MXN: '🇲🇽',
    SGD: '🇸🇬',
  };

  // Actions
  const handleDeployRules = () => {
    setIsDeploying(true);
    setTimeout(() => {
      setIsDeploying(false);
      setToastMessage('Rules deployed to Velo Edge Network in 42ms');
      setTimeout(() => setToastMessage(null), 4000);
    }, 800);
  };

  const handleRefreshPreview = (curr?: string, plan?: string) => {
    const targetCurr = curr || preview.targetCurrency;
    const isEnt = (plan || preview.planId) === 'plan_ent';
    const baseAmt = isEnt ? 199.00 : 49.00;

    let fx = 0.92;
    let symbol = '€';
    let country = 'DE';
    let taxStr = '+ 19% VAT (DE)';

    if (targetCurr === 'GBP') { fx = 0.79; symbol = '£'; country = 'GB'; taxStr = '+ 20% VAT (UK)'; }
    if (targetCurr === 'JPY') { fx = 152.4; symbol = '¥'; country = 'JP'; taxStr = '+ 10% JCT (JP)'; }
    if (targetCurr === 'AUD') { fx = 1.51; symbol = 'A$'; country = 'AU'; taxStr = '+ 10% GST (AU)'; }
    if (targetCurr === 'BRL') { fx = 5.65; symbol = 'R$'; country = 'BR'; taxStr = '+ 17% ISS/ICMS (BR)'; }

    let gross = baseAmt * fx;
    if (taxMode === 'exclusive') {
      const taxRate = country === 'DE' ? 0.19 : country === 'GB' ? 0.20 : 0.10;
      gross *= (1 + taxRate);
    }

    let finalVal = Math.ceil(gross) - 0.01;
    if (targetCurr === 'JPY') finalVal = Math.round(gross);

    setPreview({
      planId: isEnt ? 'plan_ent' : 'plan_pro',
      planName: isEnt ? 'Enterprise Tier' : 'Pro Tier',
      baseAmount: baseAmt,
      baseCurrency: 'USD',
      targetCurrency: targetCurr,
      targetCountry: country,
      translatedAmount: Number(finalVal.toFixed(2)),
      taxLabel: taxMode === 'inclusive' ? `incl. ${taxStr.replace('+ ', '')}` : taxStr,
      complianceNote: `${regulationProfile.replace('_', ' ')} Compliant`,
      ruleVersion: 'v2.4',
    });
  };

  const handleGenerateKey = () => {
    if (!newKeyLabel) return;
    const key = `velo_live_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`;
    setGeneratedKey(key);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  return (
    <div className="app-container">
      {/* Glass Header */}
      <header className="app-header">
        <div className="logo-group">
          <div className="logo-icon">
            <Zap size={22} />
          </div>
          <span className="logo-title">Velo Engine</span>
          <div className="status-indicator">
            <div className="pulse-dot" />
            <span>Edge Node: Online</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button className="btn-glow" onClick={() => { setShowKeyModal(true); setGeneratedKey(null); setNewKeyLabel(''); }}>
            <Key size={16} /> New API Key
          </button>
        </div>
      </header>

      {/* Nav Tabs */}
      <nav className="nav-tabs-bar">
        <button
          className={`tab-btn ${activeTab === 'integrations' ? 'active' : ''}`}
          onClick={() => setActiveTab('integrations')}
        >
          <Layers className="tab-icon" size={18} /> Integrations
        </button>
        <button
          className={`tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          <Sliders className="tab-icon" size={18} /> Rules Engine
        </button>
        <button
          className={`tab-btn ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
        >
          <Eye className="tab-icon" size={18} /> Live Preview Studio
        </button>
        <button
          className={`tab-btn ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          <Activity className="tab-icon" size={18} /> Activity Monitor
        </button>
      </nav>

      {/* Main Content */}
      <main className="main-wrapper">
        {/* Top Hero Metrics Bar */}
        <div className="hero-stats-grid">
          <div className="stat-card">
            <div className="stat-icon-wrapper">
              <Globe size={22} />
            </div>
            <div>
              <div className="stat-val">{selectedCurrencies.length} Active</div>
              <div className="stat-lbl">Target Currencies</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10B981' }}>
              <TrendingUp size={22} />
            </div>
            <div>
              <div className="stat-val">&lt; 42ms</div>
              <div className="stat-lbl">Median API Latency</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3B82F6' }}>
              <Cpu size={22} />
            </div>
            <div>
              <div className="stat-val">18 Plans</div>
              <div className="stat-lbl">Synced Provider Plans</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B' }}>
              <ShieldCheck size={22} />
            </div>
            <div>
              <div className="stat-val">v2.4 Active</div>
              <div className="stat-lbl">Deployed Rule Version</div>
            </div>
          </div>
        </div>

        {/* Tab 1: Integrations */}
        {activeTab === 'integrations' && (
          <div className="glass-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Connected Billing Connectors</h2>
                <p className="panel-sub">Sync plans & prices automatically from Stripe, Chargebee, and Recurly.</p>
              </div>
            </div>

            <div className="integrations-grid">
              {integrations.map((item) => (
                <div key={item.id} className="integration-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div className={`provider-badge ${item.provider}-badge`}>
                        {item.provider === 'stripe' ? 'S' : item.provider === 'chargebee' ? 'C' : 'R'}
                      </div>
                      <div>
                        <h3 style={{ textTransform: 'capitalize', fontSize: '16px', fontWeight: 700 }}>{item.provider}</h3>
                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{item.plansCount} Plans Synced</span>
                      </div>
                    </div>

                    <span className={`status-pill status-${item.status}`}>
                      ● {item.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="breakdown-row">
                    <span style={{ color: 'var(--text-muted)' }}>Last Synced</span>
                    <span style={{ fontWeight: 600 }}>{item.last_synced_at || 'Never'}</span>
                  </div>

                  <button className="btn-glass" style={{ width: '100%', justifyContent: 'center' }}>
                    {item.status === 'disconnected' ? 'Connect Provider' : 'Re-sync Connector'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 2: Rules Engine */}
        {activeTab === 'rules' && (
          <div className="glass-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Rules Engine & Regulation Studio</h2>
                <p className="panel-sub">Configure currency groups, regional compliance, tax treatment, and charm rounding.</p>
              </div>

              <button className="btn-glow" onClick={handleDeployRules} disabled={isDeploying}>
                {isDeploying ? <RefreshCw className="spin" size={16} /> : <Sparkles size={16} />}
                {isDeploying ? 'Deploying Rules...' : 'Save & Deploy to Edge'}
              </button>
            </div>

            {/* Target Currency Groups */}
            <div style={{ marginBottom: '28px' }}>
              <label className="form-label">Target Currency Groups</label>
              <div className="currency-grid">
                {Object.keys(currencyFlagMap).map((c) => {
                  const isSelected = selectedCurrencies.includes(c);
                  return (
                    <div
                      key={c}
                      className={`curr-pill ${isSelected ? 'active' : ''}`}
                      onClick={() => {
                        if (isSelected) {
                          setSelectedCurrencies(selectedCurrencies.filter((item) => item !== c));
                        } else {
                          setSelectedCurrencies([...selectedCurrencies, c]);
                        }
                      }}
                    >
                      <span style={{ fontSize: '18px' }}>{currencyFlagMap[c]}</span>
                      <span>{c}</span>
                      {isSelected && <Check size={14} style={{ color: 'var(--accent-primary)', marginLeft: 'auto' }} />}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Regulation Profile */}
            <div style={{ marginBottom: '28px' }}>
              <label className="form-label">Regional Compliance & Regulation Profile</label>
              <select
                className="select-glass"
                value={regulationProfile}
                onChange={(e) => setRegulationProfile(e.target.value)}
              >
                <option value="EU_VAT_GDPR">🇪🇺 EU VAT + GDPR Article 13 Compliance</option>
                <option value="INDIA_GST">🇮🇳 India GST Act 2017 Compliance</option>
                <option value="BRAZIL_LGPD">🇧🇷 Brazil LGPD + ISS/ICMS Tax Integration</option>
              </select>
            </div>

            {/* Tax Mode & Rounding Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '28px' }}>
              <div>
                <label className="form-label">Tax Display Mode</label>
                <select
                  className="select-glass"
                  value={taxMode}
                  onChange={(e) => setTaxMode(e.target.value as any)}
                >
                  <option value="exclusive">Tax Exclusive (Base Price + Regional Tax)</option>
                  <option value="inclusive">Tax Inclusive (Gross Price with Tax Embedded)</option>
                </select>
              </div>

              <div>
                <label className="form-label">Charm Rounding Strategy</label>
                <select
                  className="select-glass"
                  value={roundingStrategy}
                  onChange={(e) => setRoundingStrategy(e.target.value)}
                >
                  <option value="nearest_99">Charm Pricing (.99 ending)</option>
                  <option value="whole">Nearest Whole Currency Unit (.00)</option>
                  <option value="nearest_00">Exact Decimal (.00)</option>
                </select>
              </div>
            </div>

            {/* Psychological Pricing Toggle */}
            <div
              className="curr-pill active"
              style={{ width: 'fit-content', padding: '14px 20px' }}
              onClick={() => setPsychologicalPricing(!psychologicalPricing)}
            >
              <input type="checkbox" checked={psychologicalPricing} readOnly />
              <span style={{ fontWeight: 600 }}>Enable Psychological Post-Processing (.99 Ceiling Rounding)</span>
            </div>
          </div>
        )}

        {/* Tab 3: Live Preview Studio */}
        {activeTab === 'preview' && (
          <div className="glass-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Live Pricing Translation Studio</h2>
                <p className="panel-sub">Inspect real-time price translation side-by-side with regional tax and rounding breakdown.</p>
              </div>

              <button className="btn-glass" onClick={() => handleRefreshPreview()}>
                <RefreshCw size={16} /> Recompute Translation
              </button>
            </div>

            {/* Selectors */}
            <div style={{ display: 'flex', gap: '20px', marginBottom: '28px' }}>
              <div style={{ flex: 1 }}>
                <label className="form-label">Select Synced Plan</label>
                <select
                  className="select-glass"
                  value={preview.planId}
                  onChange={(e) => handleRefreshPreview(preview.targetCurrency, e.target.value)}
                >
                  <option value="plan_pro">Pro Tier ($49.00 USD / mo)</option>
                  <option value="plan_ent">Enterprise Tier ($199.00 USD / mo)</option>
                </select>
              </div>

              <div style={{ width: '220px' }}>
                <label className="form-label">Target Currency</label>
                <select
                  className="select-glass"
                  value={preview.targetCurrency}
                  onChange={(e) => handleRefreshPreview(e.target.value)}
                >
                  <option value="EUR">🇪🇺 EUR (Germany)</option>
                  <option value="GBP">🇬🇧 GBP (United Kingdom)</option>
                  <option value="JPY">🇯🇵 JPY (Japan)</option>
                  <option value="AUD">🇦🇺 AUD (Australia)</option>
                  <option value="BRL">🇧🇷 BRL (Brazil)</option>
                </select>
              </div>
            </div>

            {/* Side-by-side Studio Cards */}
            <div className="preview-studio">
              {/* Original Base Card */}
              <div className="source-card">
                <span className="form-label" style={{ color: 'var(--text-muted)' }}>Original Source Price</span>
                <div className="giant-price">
                  ${preview.baseAmount.toFixed(2)}
                  <span style={{ fontSize: '18px', color: 'var(--text-muted)', marginLeft: '8px' }}>{preview.baseCurrency}</span>
                </div>

                <div className="breakdown-row">
                  <span>Source Plan</span>
                  <span style={{ fontWeight: 600 }}>{preview.planName}</span>
                </div>
                <div className="breakdown-row">
                  <span>Billing Interval</span>
                  <span style={{ fontWeight: 600 }}>Monthly</span>
                </div>
                <div className="breakdown-row" style={{ borderBottom: 'none' }}>
                  <span>Source Currency</span>
                  <span style={{ fontWeight: 600 }}>USD ($)</span>
                </div>
              </div>

              {/* Translated Local Card */}
              <div className="target-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="form-label" style={{ color: '#818CF8' }}>Translated Display Price</span>
                  <span className="status-pill status-live">
                    <Sparkles size={12} /> {preview.ruleVersion}
                  </span>
                </div>

                <div className="giant-price giant-price-translated">
                  {preview.targetCurrency === 'EUR' ? '€' : preview.targetCurrency === 'GBP' ? '£' : preview.targetCurrency === 'JPY' ? '¥' : '$'}
                  {preview.translatedAmount}
                  <span style={{ fontSize: '20px', color: 'var(--text-secondary)', marginLeft: '8px' }}>{preview.targetCurrency}</span>
                </div>

                <div className="breakdown-row">
                  <span>Tax Treatment</span>
                  <span style={{ fontWeight: 700, color: '#10B981' }}>{preview.taxLabel}</span>
                </div>
                <div className="breakdown-row">
                  <span>Regulation Protocol</span>
                  <span style={{ fontWeight: 600 }}>{preview.complianceNote}</span>
                </div>
                <div className="breakdown-row" style={{ borderBottom: 'none' }}>
                  <span>Rounding Strategy</span>
                  <span style={{ fontWeight: 600 }}>Charm (.99) Ceiling</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Activity Monitor */}
        {activeTab === 'activity' && (
          <div className="glass-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Real-Time Activity Monitor</h2>
                <p className="panel-sub">Live audit trail of `/v1/*` public translation API calls.</p>
              </div>
            </div>

            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Method</th>
                    <th>Endpoint</th>
                    <th>Region</th>
                    <th>Request Summary</th>
                    <th>Latency</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {activityLogs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ color: 'var(--text-muted)' }}>{log.timestamp}</td>
                      <td>
                        <span className="code-badge" style={{ color: log.method === 'POST' ? '#6366F1' : '#10B981' }}>
                          {log.method}
                        </span>
                      </td>
                      <td className="code-badge">{log.endpoint}</td>
                      <td style={{ fontWeight: 700 }}>{log.region}</td>
                      <td style={{ fontWeight: 600 }}>{log.summary}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{log.latencyMs} ms</td>
                      <td>
                        <span className="status-pill status-live">
                          ● {log.status} OK
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Deploy Toast */}
      {toastMessage && (
        <div className="toast-floating">
          <CheckCircle2 size={18} style={{ color: '#10B981' }} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* New API Key Modal */}
      {showKeyModal && (
        <div className="modal-overlay" onClick={() => setShowKeyModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="panel-title" style={{ marginBottom: '10px' }}>Issue New API Key</h3>

            {!generatedKey ? (
              <div>
                <p className="panel-sub" style={{ marginBottom: '20px' }}>
                  Provide a descriptive label for where this API key will be authorized.
                </p>

                <div style={{ marginBottom: '20px' }}>
                  <label className="form-label">API Key Label</label>
                  <input
                    className="input-glass"
                    placeholder="e.g. Pricing Page Production Node"
                    value={newKeyLabel}
                    onChange={(e) => setNewKeyLabel(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                  <button className="btn-glass" onClick={() => setShowKeyModal(false)}>Cancel</button>
                  <button className="btn-glow" onClick={handleGenerateKey}>Generate Key</button>
                </div>
              </div>
            ) : (
              <div>
                <p className="panel-sub" style={{ color: '#10B981', marginBottom: '16px' }}>
                  Key issued! Copy it immediately. For security reasons, it will never be displayed again.
                </p>

                <div style={{ display: 'flex', gap: '10px', marginBottom: '24px' }}>
                  <input
                    className="input-glass"
                    readOnly
                    value={generatedKey}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', background: '#030712' }}
                  />
                  <button className="btn-glass" onClick={() => copyToClipboard(generatedKey)}>
                    {copiedKey ? <Check size={16} style={{ color: '#10B981' }} /> : <Copy size={16} />}
                  </button>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="btn-glow" onClick={() => setShowKeyModal(false)}>Done</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
