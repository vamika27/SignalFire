"use client";

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  BookOpenText,
  Code2,
  ClipboardList,
  Database,
  ExternalLink,
  FileText,
  Flame,
  Layers3,
  Search,
  ShieldCheck,
  Sparkles,
  TableProperties
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

type ExecutiveSummary = {
  generatedAt: string;
  lastPipelineRun: string;
  scope: string;
  dataSource: string;
  kpis: {
    companiesAnalyzed: number;
    secDocumentsProcessed: number;
    topEmergingTheme: string;
    highestConsultingOpportunityScore: number;
    themeScoresGenerated: number;
    lastPipelineRun: string;
  };
  brief: {
    situation: string;
    signal: string;
    implication: string;
    recommendedNextRead: string;
  };
  opportunityLeader: {
    company: string;
    industry: string;
    theme: string;
    consultingOpportunityScore: number;
    signalFireScore: number;
    strategicRiskScore: number;
  };
  coverage: Array<{
    ticker: string;
    company: string;
    documents: number;
    minDate: string;
    maxDate: string;
  }>;
};

type CompanyProfile = {
  company: string;
  industry: string;
  dominantTheme: string;
  themeMomentum: number;
  consultingOpportunityScore: number;
  strategicRiskScore: number;
  emergingTheme: string;
  emergingThemeGrowthRate: number;
  ticker: string;
  signalFireScore: number;
  readinessScore: number;
  topKeywords: string[];
  themeEvolution: Array<{ year: number; theme: string; theme_intensity: number }>;
};

type RadarRow = {
  rank: number;
  ticker: string;
  company: string;
  industry: string;
  theme: string;
  dominantTheme: string;
  consulting_opportunity_score: number;
  signal_fire_score: number;
  strategic_risk_score: number;
  strategic_momentum_score: number;
  transformation_readiness_score: number;
  priority_growth_rate: number;
  explanation: string;
};

type ThemeTrend = {
  theme: string;
  score: number;
  topCompany: string;
  topCompanyScore: number;
  averageOpportunity: number;
  signal: string;
  trend: Array<{ year: number; themeIntensity: number }>;
};

type ThemeTrendsPayload = {
  themes: ThemeTrend[];
  companyThemeScores: Array<{
    ticker: string;
    company: string;
    industry: string;
    year: number;
    theme: string;
    theme_intensity: number;
  }>;
};

type IndustryPayload = {
  rows: Array<{
    industry: string;
    year: number;
    theme: string;
    theme_intensity: number;
    company_count: number;
  }>;
  fastestIndustries: Array<{ industry: string; avgIntensity: number; companyCount: number }>;
};

type KeywordsPayload = {
  byCompany: Record<string, Array<{ term: string; rank: number; tfidf_weight: number }>>;
  globalTerms: Array<{ term: string; weight: number; companies: number }>;
};

type MethodologyPayload = {
  flow: Array<{ step: number; title: string; description: string }>;
  formulas: Array<{ name: string; formula: string }>;
  limitations: string[];
};

type AppData = {
  executive: ExecutiveSummary;
  companies: CompanyProfile[];
  radar: RadarRow[];
  themeTrends: ThemeTrendsPayload;
  industry: IndustryPayload;
  keywords: KeywordsPayload;
  methodology: MethodologyPayload;
};

const navItems = [
  ["brief", "Brief"],
  ["radar", "Radar"],
  ["themes", "Themes"],
  ["companies", "Companies"],
  ["industries", "Industries"],
  ["methodology", "Methodology"]
] as const;

const chartColors = ["#5F6F52", "#9CAF88", "#B48A5A", "#7B8267", "#C7A77A", "#8DA978"];

function formatNumber(value: number, digits = 0) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(value);
}

function formatDate(value: string) {
  if (!value) return "Unavailable";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(value));
}

async function loadJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Unable to load ${path}`);
  }
  return response.json() as Promise<T>;
}

function useDashboardData() {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    Promise.all([
      loadJson<ExecutiveSummary>("/data/executive_summary.json"),
      loadJson<CompanyProfile[]>("/data/company_profiles.json"),
      loadJson<RadarRow[]>("/data/opportunity_radar.json"),
      loadJson<ThemeTrendsPayload>("/data/theme_trends.json"),
      loadJson<IndustryPayload>("/data/industry_trends.json"),
      loadJson<KeywordsPayload>("/data/keywords.json"),
      loadJson<MethodologyPayload>("/data/methodology.json")
    ])
      .then(([executive, companies, radar, themeTrends, industry, keywords, methodology]) => {
        if (mounted) setData({ executive, companies, radar, themeTrends, industry, keywords, methodology });
      })
      .catch((caught: Error) => {
        if (mounted) setError(caught.message);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return { data, error };
}

function AnimatedCounter({ value, suffix = "", decimals = 0 }: { value: number; suffix?: string; decimals?: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 900;
    const startedAt = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(value * eased);
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return (
    <span>
      {formatNumber(display, decimals)}
      {suffix}
    </span>
  );
}

function Section({
  id,
  eyebrow,
  title,
  children,
  className = ""
}: {
  id: string;
  eyebrow?: string;
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.section
      id={id}
      className={`scroll-mt-28 py-16 ${className}`}
      initial={{ opacity: 0, y: 36 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-90px" }}
      transition={{ duration: 0.7, ease: "easeOut" }}
    >
      <div className="mb-8">
        {eyebrow ? <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--deep-sage)]">{eyebrow}</p> : null}
        <h2 className="font-heading text-4xl font-semibold leading-tight text-[var(--ink)] md:text-6xl">{title}</h2>
      </div>
      {children}
    </motion.section>
  );
}

function LoadingState() {
  return (
    <main className="min-h-screen px-6 py-10">
      <div className="mx-auto max-w-7xl">
        <div className="paper-card rounded-[2rem] p-8">
          <div className="flex items-center gap-3 text-[var(--deep-sage)]">
            <Sparkles className="h-5 w-5 animate-pulse" />
            <span className="font-mono text-sm uppercase tracking-[0.24em]">Loading SignalFire brief</span>
          </div>
          <div className="mt-8 grid gap-5 md:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div key={item} className="h-40 animate-pulse rounded-3xl bg-[rgba(221,210,191,0.45)]" />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

function TopNav() {
  return (
    <nav className="sticky top-0 z-50 border-b border-[rgba(221,210,191,0.75)] bg-[rgba(251,248,241,0.86)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <a href="#top" className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-2xl bg-[var(--deep-sage)] text-[var(--paper)] shadow-card">
            <Flame className="h-5 w-5" />
          </span>
          <span>
            <span className="block font-heading text-2xl font-semibold leading-none">SignalFire</span>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">Strategic intelligence</span>
          </span>
        </a>
        <div className="hidden items-center gap-1 rounded-full border border-[var(--line)] bg-[rgba(255,253,247,0.72)] p-1 lg:flex">
          {navItems.map(([id, label]) => (
            <a
              key={id}
              href={`#${id}`}
              className="rounded-full px-4 py-2 text-sm text-[var(--muted)] transition hover:bg-[var(--light-sage)] hover:text-[var(--ink)]"
            >
              {label}
            </a>
          ))}
        </div>
        <a
          href="https://github.com/vamika27/SignalFire"
          className="hidden items-center gap-2 rounded-full bg-[var(--ink)] px-4 py-2 text-sm text-[var(--paper)] transition hover:-translate-y-0.5 hover:bg-[var(--deep-sage)] md:flex"
        >
          Source <Code2 className="h-4 w-4" />
        </a>
      </div>
    </nav>
  );
}

function Hero({ executive }: { executive: ExecutiveSummary }) {
  return (
    <section id="top" className="grain-mask px-5 pb-12 pt-12 md:pt-18">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <motion.div
          initial={{ opacity: 0, y: 36 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-[rgba(255,253,247,0.78)] px-4 py-2 font-mono text-xs uppercase tracking-[0.22em] text-[var(--deep-sage)] shadow-card">
            <ShieldCheck className="h-4 w-4" />
            Smoke-test validated with real SEC data
          </div>
          <h1 className="font-heading text-6xl font-semibold leading-[0.92] text-[var(--ink)] md:text-8xl">
            SignalFire
          </h1>
          <p className="mt-4 font-mono text-sm uppercase tracking-[0.28em] text-[var(--deep-sage)]">
            Strategic Priority Intelligence Platform
          </p>
          <p className="mt-6 max-w-2xl text-xl leading-8 text-[var(--muted)]">
            Detecting emerging corporate priorities from SEC disclosures before they become obvious to investors,
            competitors, or consulting firms.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            {["Real SEC Data", "NLP Pipeline", "Strategic Scoring", "Smoke-Test Validated"].map((pill) => (
              <span
                key={pill}
                className="rounded-full border border-[rgba(95,111,82,0.22)] bg-[rgba(221,232,210,0.64)] px-4 py-2 text-sm text-[var(--deep-sage)]"
              >
                {pill}
              </span>
            ))}
          </div>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <a
              href="#brief"
              className="group inline-flex items-center justify-center gap-2 rounded-full bg-[var(--deep-sage)] px-6 py-3 text-[var(--paper)] shadow-card transition hover:-translate-y-1 hover:bg-[var(--ink)]"
            >
              View Intelligence Brief
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
            </a>
            <a
              href="#methodology"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-[var(--line)] bg-[rgba(255,253,247,0.78)] px-6 py-3 text-[var(--ink)] transition hover:-translate-y-1 hover:border-[var(--sage)]"
            >
              Methodology
              <BookOpenText className="h-4 w-4" />
            </a>
            <a
              href="https://github.com/vamika27/SignalFire"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-[var(--line)] px-6 py-3 text-[var(--muted)] transition hover:-translate-y-1 hover:bg-[var(--paper)] hover:text-[var(--ink)]"
            >
              Source Code
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </motion.div>

        <motion.div
          className="clipboard paper-card rounded-[2.25rem] p-6 pt-12 md:p-8 md:pt-14"
          initial={{ opacity: 0, rotate: 1.6, y: 40 }}
          animate={{ opacity: 1, rotate: 0, y: 0 }}
          transition={{ delay: 0.15, duration: 0.8, ease: "easeOut" }}
        >
          <div className="flex items-start justify-between gap-4 border-b border-[var(--line)] pb-5">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Executive docket</p>
              <h2 className="font-heading text-4xl font-semibold">SEC Signal Snapshot</h2>
            </div>
            <span className="rounded-full bg-[var(--beige)] px-3 py-1 font-mono text-xs text-[var(--deep-sage)]">
              {executive.scope}
            </span>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <KpiCard label="Companies analyzed" value={executive.kpis.companiesAnalyzed} icon={<Database />} />
            <KpiCard label="SEC documents" value={executive.kpis.secDocumentsProcessed} icon={<FileText />} />
            <KpiCard label="Theme scores" value={executive.kpis.themeScoresGenerated} icon={<Layers3 />} />
            <KpiCard
              label="Highest opportunity"
              value={executive.kpis.highestConsultingOpportunityScore}
              decimals={1}
              icon={<BarChart3 />}
            />
          </div>
          <div className="mt-5 rounded-3xl border border-[var(--line)] bg-[rgba(245,235,221,0.42)] p-5">
            <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Top emerging theme</p>
            <p className="mt-2 font-heading text-3xl font-semibold text-[var(--deep-sage)]">
              {executive.kpis.topEmergingTheme}
            </p>
            <p className="mt-3 text-sm text-[var(--muted)]">Last pipeline run: {formatDate(executive.kpis.lastPipelineRun)}</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function KpiCard({
  label,
  value,
  decimals = 0,
  icon
}: {
  label: string;
  value: number;
  decimals?: number;
  icon: React.ReactNode;
}) {
  return (
    <motion.div
      className="rounded-3xl border border-[var(--line)] bg-[rgba(255,253,247,0.78)] p-5 transition hover:-translate-y-1 hover:shadow-card"
      whileHover={{ y: -4 }}
    >
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--light-sage)] text-[var(--deep-sage)]">
        {icon}
      </div>
      <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-[var(--muted)]">{label}</p>
      <p className="mt-2 font-heading text-4xl font-semibold">
        <AnimatedCounter value={value} decimals={decimals} />
      </p>
    </motion.div>
  );
}

function ExecutiveBrief({ executive }: { executive: ExecutiveSummary }) {
  const entries = [
    ["Situation", executive.brief.situation],
    ["Signal", executive.brief.signal],
    ["Implication", executive.brief.implication],
    ["Recommended next read", executive.brief.recommendedNextRead]
  ];

  return (
    <Section id="brief" eyebrow="Executive intelligence brief" title="A consultant-style readout, not a generic dashboard.">
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="paper-card rounded-[2rem] p-7 md:p-10">
          <div className="mb-6 flex items-center justify-between gap-4">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Briefing memo</p>
              <h3 className="font-heading text-4xl font-semibold">Current SEC smoke-test read</h3>
            </div>
            <ClipboardList className="h-10 w-10 text-[var(--accent)]" />
          </div>
          <div className="space-y-6">
            {entries.map(([label, text], index) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, x: -18 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                className="grid gap-3 border-t border-[var(--line)] pt-5 md:grid-cols-[180px_1fr]"
              >
                <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--deep-sage)]">{label}</p>
                <p className="text-lg leading-8 text-[var(--muted)]">{text}</p>
              </motion.div>
            ))}
          </div>
        </div>
        <div className="rounded-[2rem] border border-[var(--line)] bg-[rgba(221,232,210,0.55)] p-7 shadow-card">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--deep-sage)]">Opportunity leader</p>
          <h3 className="mt-3 font-heading text-5xl font-semibold">{executive.opportunityLeader.company}</h3>
          <p className="mt-2 text-[var(--muted)]">{executive.opportunityLeader.industry}</p>
          <div className="memo-rule my-6" />
          <dl className="space-y-5">
            <MetricLine label="Theme" value={executive.opportunityLeader.theme} />
            <MetricLine label="Opportunity" value={formatNumber(executive.opportunityLeader.consultingOpportunityScore, 1)} />
            <MetricLine label="SignalFire" value={formatNumber(executive.opportunityLeader.signalFireScore, 1)} />
            <MetricLine label="Risk" value={formatNumber(executive.opportunityLeader.strategicRiskScore, 1)} />
          </dl>
        </div>
      </div>
    </Section>
  );
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">{label}</dt>
      <dd className="font-heading text-2xl font-semibold text-[var(--ink)]">{value}</dd>
    </div>
  );
}

function ScaleGuide({
  title,
  unit,
  min,
  max,
  lowLabel,
  midLabel,
  highLabel
}: {
  title: string;
  unit: string;
  min: string;
  max: string;
  lowLabel: string;
  midLabel: string;
  highLabel: string;
}) {
  return (
    <div className="rounded-[1.5rem] border border-[var(--line)] bg-[rgba(255,253,247,0.74)] p-4 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--deep-sage)]">{title}</p>
          <p className="mt-1 text-sm leading-5 text-[var(--muted)]">{unit}</p>
        </div>
        <span className="rounded-full bg-[var(--beige)] px-3 py-1 font-mono text-[11px] text-[var(--deep-sage)]">
          {min} → {max}
        </span>
      </div>
      <div className="mt-4 h-2 rounded-full bg-gradient-to-r from-[rgba(221,232,210,0.75)] via-[var(--sage)] to-[var(--deep-sage)]" />
      <div className="mt-3 grid grid-cols-3 gap-2 text-[11px] leading-4 text-[var(--muted)]">
        <span>{lowLabel}</span>
        <span className="text-center">{midLabel}</span>
        <span className="text-right">{highLabel}</span>
      </div>
    </div>
  );
}

function OpportunityRadar({ rows }: { rows: RadarRow[] }) {
  const [theme, setTheme] = useState("All themes");
  const [company, setCompany] = useState("");
  const [sortKey, setSortKey] = useState<"consulting_opportunity_score" | "signal_fire_score" | "strategic_risk_score">(
    "consulting_opportunity_score"
  );
  const [hoveredRank, setHoveredRank] = useState<number | null>(null);
  const themes = useMemo(() => ["All themes", ...Array.from(new Set(rows.map((row) => row.theme))).sort()], [rows]);
  const scoreRange = useMemo(() => {
    const scores = rows.map((row) => row.consulting_opportunity_score);
    return { min: Math.min(...scores), max: Math.max(...scores) };
  }, [rows]);

  const filtered = useMemo(() => {
    return rows
      .filter((row) => theme === "All themes" || row.theme === theme)
      .filter((row) => row.company.toLowerCase().includes(company.toLowerCase()))
      .sort((a, b) => b[sortKey] - a[sortKey])
      .slice(0, 16)
      .map((row, index) => ({ ...row, visibleRank: index + 1 }));
  }, [rows, theme, company, sortKey]);
  const activeRow = filtered.find((row) => row.visibleRank === hoveredRank) ?? filtered[0];

  return (
    <Section id="radar" eyebrow="Opportunity radar" title="Ranked company signals for consulting opportunity.">
      <div className="paper-card overflow-hidden rounded-[2rem]">
        <div className="grid gap-4 border-b border-[var(--line)] bg-[rgba(245,235,221,0.48)] p-5 lg:grid-cols-[1fr_1fr_1fr]">
          <label className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Theme filter</span>
            <select
              value={theme}
              onChange={(event) => setTheme(event.target.value)}
              className="w-full rounded-2xl border border-[var(--line)] bg-[var(--paper)] px-4 py-3 text-sm outline-none transition focus:border-[var(--sage)]"
            >
              {themes.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Company filter</span>
            <div className="flex items-center gap-2 rounded-2xl border border-[var(--line)] bg-[var(--paper)] px-4 py-3">
              <Search className="h-4 w-4 text-[var(--muted)]" />
              <input
                value={company}
                onChange={(event) => setCompany(event.target.value)}
                placeholder="Search company"
                className="w-full bg-transparent text-sm outline-none"
              />
            </div>
          </label>
          <label className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Sort by</span>
            <select
              value={sortKey}
              onChange={(event) => setSortKey(event.target.value as typeof sortKey)}
              className="w-full rounded-2xl border border-[var(--line)] bg-[var(--paper)] px-4 py-3 text-sm outline-none transition focus:border-[var(--sage)]"
            >
              <option value="consulting_opportunity_score">Consulting Opportunity Score</option>
              <option value="signal_fire_score">SignalFire Score</option>
              <option value="strategic_risk_score">Strategic Risk Score</option>
            </select>
          </label>
        </div>
        <div className="grid gap-4 border-b border-[var(--line)] bg-[rgba(255,253,247,0.56)] p-5 lg:grid-cols-[1fr_340px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeRow ? `${activeRow.ticker}-${activeRow.theme}` : "empty"}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
              className="rounded-[1.5rem] border border-[var(--line)] bg-[var(--paper)] p-4"
            >
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--deep-sage)]">
                Hover insight
              </p>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                {activeRow?.explanation ?? "Hover a ranked company row to inspect why it appears in the radar."}
              </p>
            </motion.div>
          </AnimatePresence>
          <ScaleGuide
            title="Opportunity score scale"
            unit="Index points from 0 to 100; higher means stronger consulting opportunity in this smoke test."
            min={formatNumber(scoreRange.min, 1)}
            max={formatNumber(scoreRange.max, 1)}
            lowLabel="Lower priority"
            midLabel="Watchlist"
            highLabel="Highest signal"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-[var(--line)] bg-[rgba(255,253,247,0.7)] font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                <th className="px-5 py-4">Rank</th>
                <th className="px-5 py-4">Company</th>
                <th className="px-5 py-4">Industry</th>
                <th className="px-5 py-4">Dominant Theme</th>
                <th className="px-5 py-4">Opportunity</th>
                <th className="px-5 py-4">SignalFire</th>
                <th className="px-5 py-4">Risk</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr
                  key={`${row.ticker}-${row.theme}`}
                  onMouseEnter={() => setHoveredRank(row.visibleRank)}
                  onMouseLeave={() => setHoveredRank(null)}
                  className="group border-b border-[rgba(221,210,191,0.7)] align-top transition-colors duration-300 hover:bg-[rgba(221,232,210,0.38)]"
                >
                  <td className="px-5 py-4 font-mono text-sm text-[var(--deep-sage)]">#{row.visibleRank}</td>
                  <td className="px-5 py-4">
                    <p className="font-semibold">{row.company}</p>
                    <p className="font-mono text-xs text-[var(--muted)]">{row.ticker}</p>
                  </td>
                  <td className="px-5 py-4 text-sm text-[var(--muted)]">{row.industry}</td>
                  <td className="px-5 py-4">
                    <span className="rounded-full bg-[var(--light-sage)] px-3 py-1 text-xs text-[var(--deep-sage)]">
                      {row.dominantTheme}
                    </span>
                  </td>
                  <td className="px-5 py-4 font-mono font-semibold">{formatNumber(row.consulting_opportunity_score, 1)}</td>
                  <td className="px-5 py-4 font-mono">{formatNumber(row.signal_fire_score, 1)}</td>
                  <td className="px-5 py-4 font-mono">{formatNumber(row.strategic_risk_score, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Section>
  );
}

function ThemeMomentumBoard({ themes }: { themes: ThemeTrend[] }) {
  const scoreRange = useMemo(() => {
    const scores = themes.map((theme) => theme.score);
    return { min: Math.min(...scores), max: Math.max(...scores) };
  }, [themes]);

  return (
    <Section id="themes" eyebrow="Theme momentum board" title="Strategic priorities by momentum signal.">
      <div className="mb-6 grid gap-4 lg:grid-cols-[1fr_360px]">
        <p className="max-w-3xl text-lg leading-8 text-[var(--muted)]">
          Theme cards use a 0-100 strategic momentum index. The mini-lines show directional theme intensity across
          available SEC filing years in the smoke-test output.
        </p>
        <ScaleGuide
          title="Theme momentum scale"
          unit="Index points from 0 to 100; higher means the theme is accelerating more strongly."
          min={formatNumber(scoreRange.min, 1)}
          max={formatNumber(scoreRange.max, 1)}
          lowLabel="Lower momentum"
          midLabel="Developing"
          highLabel="Accelerating"
        />
      </div>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {themes.map((theme, index) => (
          <motion.article
            key={theme.theme}
            className="paper-card rounded-[2rem] p-6 transition hover:-translate-y-1 hover:shadow-paper"
            whileHover={{ y: -6 }}
            initial={{ opacity: 0, y: 28 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.04 }}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Theme</p>
                <h3 className="mt-2 font-heading text-3xl font-semibold">{theme.theme}</h3>
              </div>
              <span className="rounded-2xl bg-[var(--beige)] px-3 py-2 font-mono text-sm text-[var(--deep-sage)]">
                {formatNumber(theme.score, 1)}
              </span>
            </div>
            <div className="mt-5 h-2 overflow-hidden rounded-full bg-[rgba(221,210,191,0.55)]">
              <motion.div
                className="h-full rounded-full bg-[var(--deep-sage)]"
                initial={{ width: 0 }}
                whileInView={{ width: `${Math.min(theme.score, 100)}%` }}
                viewport={{ once: true }}
                transition={{ duration: 0.8 }}
              />
            </div>
            <p className="mt-5 text-sm leading-6 text-[var(--muted)]">{theme.signal}</p>
            <div className="mt-5 h-24">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={theme.trend}>
                  <Tooltip
                    formatter={(value) => [formatNumber(Number(value), 4), "Intensity"]}
                    labelFormatter={(label) => `Year ${label}`}
                    contentStyle={{ background: "#FFFDF7", border: "1px solid #DDD2BF", borderRadius: 16 }}
                  />
                  <Line type="monotone" dataKey="themeIntensity" stroke="#5F6F52" strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex items-center justify-between border-t border-[var(--line)] pt-4 text-sm">
              <span className="text-[var(--muted)]">Top company</span>
              <span className="font-semibold text-[var(--deep-sage)]">{theme.topCompany}</span>
            </div>
          </motion.article>
        ))}
      </div>
    </Section>
  );
}

function CompanyProfileSheet({ companies, keywords }: { companies: CompanyProfile[]; keywords: KeywordsPayload }) {
  const [selected, setSelected] = useState(companies[0]?.company ?? "");
  const company = companies.find((item) => item.company === selected) ?? companies[0];

  const chartData = useMemo(() => {
    if (!company) return [];
    const totals = company.themeEvolution.reduce<Record<string, number>>((acc, row) => {
      acc[row.theme] = (acc[row.theme] ?? 0) + row.theme_intensity;
      return acc;
    }, {});
    const topThemes = Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([theme]) => theme);
    const byYear = new Map<number, Record<string, number>>();
    company.themeEvolution.forEach((row) => {
      if (!topThemes.includes(row.theme)) return;
      const yearRow = byYear.get(row.year) ?? { year: row.year };
      yearRow[row.theme] = row.theme_intensity;
      byYear.set(row.year, yearRow);
    });
    return Array.from(byYear.values()).sort((a, b) => Number(a.year) - Number(b.year));
  }, [company]);

  if (!company) return null;

  return (
    <Section id="companies" eyebrow="Company intelligence profile" title="A briefing sheet for each company.">
      <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <div className="paper-card rounded-[2rem] p-6">
          <label className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Select company</span>
            <select
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
              className="w-full rounded-2xl border border-[var(--line)] bg-[var(--paper)] px-4 py-3 outline-none focus:border-[var(--sage)]"
            >
              {companies.map((item) => (
                <option key={item.company}>{item.company}</option>
              ))}
            </select>
          </label>
          <div className="mt-8 rounded-[1.75rem] bg-[var(--beige)] p-6">
            <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">{company.ticker}</p>
            <h3 className="mt-2 font-heading text-5xl font-semibold">{company.company}</h3>
            <p className="mt-2 text-[var(--muted)]">{company.industry}</p>
            <div className="memo-rule my-6" />
            <div className="space-y-4">
              <MetricLine label="Dominant" value={company.dominantTheme} />
              <MetricLine label="Emerging" value={company.emergingTheme} />
              <MetricLine label="Opportunity" value={formatNumber(company.consultingOpportunityScore, 1)} />
              <MetricLine label="Readiness" value={formatNumber(company.readinessScore, 1)} />
              <MetricLine label="Risk" value={formatNumber(company.strategicRiskScore, 1)} />
            </div>
          </div>
          <div className="mt-5">
            <ScaleGuide
              title="Profile score scale"
              unit="Opportunity, readiness, risk, and SignalFire values use 0-100 index points."
              min="0"
              max="100"
              lowLabel="Lower"
              midLabel="Moderate"
              highLabel="Higher"
            />
          </div>
        </div>
        <div className="clipboard paper-card rounded-[2.25rem] p-6 pt-12 md:p-8 md:pt-14">
          <div className="grid gap-6 xl:grid-cols-[1fr_0.8fr]">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--deep-sage)]">Theme evolution</p>
              <div className="mt-4 h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid stroke="#DDD2BF" strokeDasharray="4 4" vertical={false} />
                    <XAxis dataKey="year" tick={{ fill: "#777568", fontSize: 12 }} />
                    <YAxis tick={{ fill: "#777568", fontSize: 12 }} width={42} />
                    <Tooltip contentStyle={{ background: "#FFFDF7", border: "1px solid #DDD2BF", borderRadius: 16 }} />
                    {Object.keys(chartData[0] ?? {})
                      .filter((key) => key !== "year")
                      .map((key, index) => (
                        <Line
                          key={key}
                          type="monotone"
                          dataKey={key}
                          stroke={chartColors[index % chartColors.length]}
                          strokeWidth={2.5}
                          dot={{ r: 3 }}
                        />
                      ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--deep-sage)]">Top keywords</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {(keywords.byCompany[company.company] ?? company.topKeywords.map((term) => ({ term }))).slice(0, 14).map((item) => (
                  <span
                    key={item.term}
                    className="rounded-full border border-[var(--line)] bg-[rgba(255,253,247,0.8)] px-3 py-2 text-sm text-[var(--muted)]"
                  >
                    {item.term}
                  </span>
                ))}
              </div>
              <div className="mt-8 rounded-3xl border border-[var(--line)] bg-[rgba(221,232,210,0.42)] p-5">
                <p className="font-mono text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Briefing note</p>
                <p className="mt-3 leading-7 text-[var(--muted)]">
                  This profile summarizes the SEC smoke-test outputs for {company.company}. Treat scores as derived
                  analytical constructs for product validation, not company-reported metrics.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}

function IndustryIntelligence({ industry }: { industry: IndustryPayload }) {
  const themes = useMemo(() => Array.from(new Set(industry.rows.map((row) => row.theme))).slice(0, 10), [industry]);
  const industries = useMemo(() => Array.from(new Set(industry.rows.map((row) => row.industry))).slice(0, 8), [industry]);
  const intensityRange = useMemo(() => {
    const values = industry.rows.map((row) => row.theme_intensity);
    return { min: Math.min(...values), max: Math.max(...values) };
  }, [industry.rows]);
  const maxIntensity = Math.max(intensityRange.max, 0.001);

  const lookup = useMemo(() => {
    const map = new Map<string, number>();
    industry.rows.forEach((row) => {
      const key = `${row.industry}-${row.theme}`;
      map.set(key, Math.max(map.get(key) ?? 0, row.theme_intensity));
    });
    return map;
  }, [industry]);

  return (
    <Section id="industries" eyebrow="Industry intelligence" title="Theme penetration across sectors.">
      <div className="grid gap-6">
        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="paper-card rounded-[2rem] p-6">
            <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Fastest-moving industries</p>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              Bars show average strategic theme intensity by industry across the processed SEC smoke-test filings.
            </p>
            <div className="mt-4 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={industry.fastestIndustries.slice(0, 8)} layout="vertical" margin={{ left: 22, right: 22 }}>
                  <CartesianGrid stroke="#DDD2BF" strokeDasharray="4 4" horizontal={false} />
                  <XAxis type="number" hide />
                  <YAxis dataKey="industry" type="category" width={170} tick={{ fill: "#777568", fontSize: 12 }} />
                  <Tooltip
                    formatter={(value) => [formatNumber(Number(value), 4), "Average intensity"]}
                    contentStyle={{ background: "#FFFDF7", border: "1px solid #DDD2BF", borderRadius: 16 }}
                  />
                  <Bar dataKey="avgIntensity" radius={[0, 10, 10, 0]}>
                    {industry.fastestIndustries.slice(0, 8).map((_, index) => (
                      <Cell key={index} fill={chartColors[index % chartColors.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <ScaleGuide
            title="Theme intensity unit"
            unit="TF-IDF/cosine similarity intensity. Higher values mean the theme appears more strongly in disclosure language."
            min={formatNumber(intensityRange.min, 4)}
            max={formatNumber(intensityRange.max, 4)}
            lowLabel="Faint signal"
            midLabel="Visible signal"
            highLabel="Strongest signal"
          />
        </div>
        <div className="paper-card rounded-[2rem] p-6">
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <TableProperties className="h-5 w-5 text-[var(--accent)]" />
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Intensity heatmap</p>
            </div>
            <p className="text-sm text-[var(--muted)]">Darker cells indicate stronger theme intensity.</p>
          </div>
          <div className="overflow-x-auto pb-2">
            <div className="min-w-[1340px]">
              <div className="grid grid-cols-[190px_repeat(10,minmax(108px,1fr))] gap-1.5">
                <div className="rounded-xl bg-[rgba(245,235,221,0.55)] px-3 py-3 font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">
                  Industry
                </div>
                {themes.map((theme) => (
                  <div
                    key={theme}
                    className="flex min-h-14 items-center justify-center rounded-xl bg-[var(--beige)] px-2 py-2 text-center text-[11px] leading-4 text-[var(--muted)]"
                  >
                    {theme}
                  </div>
                ))}
                {industries.map((industryName) => (
                  <div key={industryName} className="contents">
                    <div className="flex min-h-14 items-center rounded-xl bg-[rgba(255,253,247,0.78)] px-3 py-3 text-sm font-semibold leading-5">
                      {industryName}
                    </div>
                    {themes.map((theme) => {
                      const value = lookup.get(`${industryName}-${theme}`) ?? 0;
                      const opacity = 0.16 + (value / maxIntensity) * 0.78;
                      return (
                        <div
                          key={`${industryName}-${theme}`}
                          title={`${industryName} / ${theme}: ${formatNumber(value, 4)}`}
                          className="flex min-h-14 items-center justify-center rounded-xl border border-[rgba(221,210,191,0.55)] px-2 py-3 text-center font-mono text-[11px] text-[var(--ink)]"
                          style={{ backgroundColor: `rgba(156, 175, 136, ${opacity})` }}
                        >
                          {formatNumber(value, 3)}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}

function MethodologyFlow({ methodology }: { methodology: MethodologyPayload }) {
  return (
    <Section id="methodology" eyebrow="Methodology flow" title="From SEC filing to opportunity radar.">
      <div className="grid gap-8 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="relative space-y-4">
          <div className="absolute left-6 top-8 h-[calc(100%-4rem)] w-px bg-[var(--line)]" />
          {methodology.flow.map((step, index) => (
            <motion.div
              key={step.step}
              className="paper-card relative rounded-3xl p-5 pl-20"
              initial={{ opacity: 0, x: -24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.06 }}
            >
              <span className="absolute left-4 top-5 grid h-10 w-10 place-items-center rounded-full bg-[var(--deep-sage)] font-mono text-sm text-[var(--paper)]">
                {step.step}
              </span>
              <h3 className="font-heading text-2xl font-semibold">{step.title}</h3>
              <p className="mt-2 leading-6 text-[var(--muted)]">{step.description}</p>
            </motion.div>
          ))}
        </div>
        <div className="space-y-5">
          {methodology.formulas.map((formula) => (
            <motion.div key={formula.name} className="paper-card rounded-[2rem] p-6" whileHover={{ y: -4 }}>
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--deep-sage)]">{formula.name}</p>
              <p className="mt-3 text-lg leading-8 text-[var(--muted)]">{formula.formula}</p>
            </motion.div>
          ))}
          <div className="rounded-[2rem] border border-[var(--line)] bg-[rgba(95,111,82,0.08)] p-6">
            <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--deep-sage)]">Data source & limitations</p>
            <ul className="mt-4 space-y-3 text-[var(--muted)]">
              {methodology.limitations.map((item) => (
                <li key={item} className="flex gap-3">
                  <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-[var(--accent)]" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Section>
  );
}

function SourceCodeCta() {
  return (
    <section className="py-12">
      <motion.div
        className="paper-card mx-auto max-w-7xl rounded-[2.4rem] p-8 md:p-10"
        initial={{ opacity: 0, scale: 0.98 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
      >
        <div className="grid gap-6 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--deep-sage)]">Source-code dossier</p>
            <h2 className="mt-2 font-heading text-4xl font-semibold">Built as a reproducible analytics product.</h2>
            <p className="mt-3 max-w-3xl text-[var(--muted)]">
              Python exports real processed SEC outputs to static JSON, and the Vercel-ready frontend presents the
              smoke-test validation as an executive strategy brief.
            </p>
          </div>
          <a
            href="https://github.com/vamika27/SignalFire"
            className="inline-flex items-center justify-center gap-3 rounded-full bg-[var(--ink)] px-6 py-4 text-[var(--paper)] transition hover:-translate-y-1 hover:bg-[var(--deep-sage)]"
          >
            View GitHub Repository
            <Code2 className="h-5 w-5" />
          </a>
        </div>
      </motion.div>
    </section>
  );
}

export default function Home() {
  const { data, error } = useDashboardData();

  if (error) {
    return (
      <main className="min-h-screen px-5 py-12">
        <div className="paper-card mx-auto max-w-3xl rounded-[2rem] p-8">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--deep-sage)]">Data loading error</p>
          <h1 className="mt-3 font-heading text-5xl font-semibold">Static SignalFire data was not found.</h1>
          <p className="mt-4 text-[var(--muted)]">{error}</p>
          <code className="mt-6 block rounded-2xl bg-[var(--beige)] p-4 font-mono text-sm">
            python3 -m signalfire.src.export_frontend_data
          </code>
        </div>
      </main>
    );
  }

  if (!data) return <LoadingState />;

  return (
    <>
      <TopNav />
      <main>
        <Hero executive={data.executive} />
        <div className="mx-auto max-w-7xl px-5">
          <ExecutiveBrief executive={data.executive} />
          <OpportunityRadar rows={data.radar} />
          <ThemeMomentumBoard themes={data.themeTrends.themes} />
          <CompanyProfileSheet companies={data.companies} keywords={data.keywords} />
          <IndustryIntelligence industry={data.industry} />
          <MethodologyFlow methodology={data.methodology} />
          <SourceCodeCta />
        </div>
      </main>
      <footer className="border-t border-[var(--line)] bg-[rgba(251,248,241,0.78)] px-5 py-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 text-sm text-[var(--muted)] md:flex-row md:items-center md:justify-between">
          <p>
            Built by <span className="font-semibold text-[var(--ink)]">Vamika Negi</span> · Python, DuckDB, NLP, Next.js
          </p>
          <p>Data: SEC EDGAR · Current view: 2-filing smoke-test validation</p>
        </div>
      </footer>
    </>
  );
}
