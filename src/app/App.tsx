import { useState } from "react";

type Status = "yes" | "no" | "partial";

interface Capability {
  category: string;
  feature: string;
  figmaMake: Status;
  claudeCode: Status;
  figmaMakeNote?: string;
  claudeCodeNote?: string;
}

interface RecommendationCard {
  tool: string;
  color: string;
  accent: string;
  tagline: string;
  personas: Persona[];
  integrationTips: string[];
  populationPercent: number;
  populationLabel: string;
  populationReasoning: string;
}

interface Persona {
  role: string;
  reason: string;
}

const capabilities: Capability[] = [
  // Design & Visual
  {
    category: "Design & Visual",
    feature: "Native Figma file integration",
    figmaMake: "yes",
    claudeCode: "no",
    figmaMakeNote: "Frame-to-code natively in Figma",
    claudeCodeNote: "No direct Figma access",
  },
  {
    category: "Design & Visual",
    feature: "Design token & style awareness",
    figmaMake: "yes",
    claudeCode: "partial",
    figmaMakeNote: "Reads Figma styles directly",
    claudeCodeNote: "Can read token files if provided",
  },
  {
    category: "Design & Visual",
    feature: "Real-time visual preview",
    figmaMake: "yes",
    claudeCode: "no",
    figmaMakeNote: "Live preview in browser",
    claudeCodeNote: "Requires separate dev server",
  },
  {
    category: "Design & Visual",
    feature: "Prototyping & mockups",
    figmaMake: "yes",
    claudeCode: "partial",
    figmaMakeNote: "Clickable React prototypes",
    claudeCodeNote: "Code-only, no visual canvas",
  },
  {
    category: "Design & Visual",
    feature: "Design system generation",
    figmaMake: "yes",
    claudeCode: "yes",
    figmaMakeNote: "From Figma components",
    claudeCodeNote: "Code-based component libraries",
  },
  {
    category: "Design & Visual",
    feature: "Responsive layout generation",
    figmaMake: "yes",
    claudeCode: "yes",
    figmaMakeNote: "Tailwind-based responsive code",
    claudeCodeNote: "Full responsive implementation",
  },
  // Code Generation
  {
    category: "Code Generation",
    feature: "React component generation",
    figmaMake: "yes",
    claudeCode: "yes",
    figmaMakeNote: "Tailwind + React from designs",
    claudeCodeNote: "Any React pattern or framework",
  },
  {
    category: "Code Generation",
    feature: "Multi-file project management",
    figmaMake: "partial",
    claudeCode: "yes",
    figmaMakeNote: "Within Figma Make scope",
    claudeCodeNote: "Full codebase traversal",
  },
  {
    category: "Code Generation",
    feature: "Codebase-wide refactoring",
    figmaMake: "no",
    claudeCode: "yes",
    figmaMakeNote: "Single project scope only",
    claudeCodeNote: "Finds and edits across all files",
  },
  {
    category: "Code Generation",
    feature: "Custom code editing",
    figmaMake: "partial",
    claudeCode: "yes",
    figmaMakeNote: "Via prompt iteration",
    claudeCodeNote: "Direct file-level editing",
  },
  // Engineering & Backend
  {
    category: "Engineering & Backend",
    feature: "Full-stack / backend development",
    figmaMake: "no",
    claudeCode: "yes",
    figmaMakeNote: "Frontend only",
    claudeCodeNote: "APIs, servers, databases",
  },
  {
    category: "Engineering & Backend",
    feature: "Terminal & CLI access",
    figmaMake: "no",
    claudeCode: "yes",
    figmaMakeNote: "Browser-based only",
    claudeCodeNote: "Runs shell commands natively",
  },
  {
    category: "Engineering & Backend",
    feature: "Database & API integration",
    figmaMake: "partial",
    claudeCode: "yes",
    figmaMakeNote: "Via Supabase connection",
    claudeCodeNote: "Any database or REST/GraphQL API",
  },
  {
    category: "Engineering & Backend",
    feature: "Version control / Git workflow",
    figmaMake: "no",
    claudeCode: "yes",
    figmaMakeNote: "No git support",
    claudeCodeNote: "Commits, branches, PRs",
  },
  {
    category: "Engineering & Backend",
    feature: "Testing & debugging",
    figmaMake: "no",
    claudeCode: "yes",
    figmaMakeNote: "No test generation",
    claudeCodeNote: "Unit, integration, e2e tests",
  },
  {
    category: "Engineering & Backend",
    feature: "CI/CD pipeline configuration",
    figmaMake: "no",
    claudeCode: "yes",
    figmaMakeNote: "Out of scope",
    claudeCodeNote: "GitHub Actions, pipelines, etc.",
  },
  // Accessibility & Quality
  {
    category: "Accessibility & Quality",
    feature: "Accessibility review",
    figmaMake: "partial",
    claudeCode: "yes",
    figmaMakeNote: "Basic semantic HTML output",
    claudeCodeNote: "ARIA, axe audits, full a11y",
  },
  {
    category: "Accessibility & Quality",
    feature: "Complex business logic",
    figmaMake: "no",
    claudeCode: "yes",
    figmaMakeNote: "UI interactions only",
    claudeCodeNote: "Algorithms, data processing",
  },
  // Workflow & Usability
  {
    category: "Workflow & Usability",
    feature: "Natural language prompting",
    figmaMake: "yes",
    claudeCode: "yes",
    figmaMakeNote: "Describe UI in plain language",
    claudeCodeNote: "Describe any code task",
  },
  {
    category: "Workflow & Usability",
    feature: "No-code / visual interface",
    figmaMake: "yes",
    claudeCode: "no",
    figmaMakeNote: "Fully visual, no terminal needed",
    claudeCodeNote: "Requires terminal comfort",
  },
  {
    category: "Workflow & Usability",
    feature: "Instant shareable prototype URL",
    figmaMake: "yes",
    claudeCode: "no",
    figmaMakeNote: "Live link from Figma Make",
    claudeCodeNote: "Requires deployment step",
  },
  {
    category: "Workflow & Usability",
    feature: "External package / library usage",
    figmaMake: "yes",
    claudeCode: "yes",
    figmaMakeNote: "npm packages via prompts",
    claudeCodeNote: "Full npm / package management",
  },
];

const recommendations: RecommendationCard[] = [
  {
    tool: "Figma Make",
    color: "from-violet-600 to-purple-700",
    accent: "violet",
    tagline: "The designer's superpower — from pixels to prototype in minutes.",
    personas: [
      {
        role: "UI / Visual Designers",
        reason:
          "Turn Figma frames into interactive prototypes without writing a line of code.",
      },
      {
        role: "UX Designers",
        reason:
          "Validate interaction flows quickly with real, clickable React apps.",
      },
      {
        role: "Design Leads",
        reason:
          "Present stakeholders with working demos instead of static mockups.",
      },
      {
        role: "Product Designers",
        reason:
          "Rapidly iterate on UI concepts and share live links in reviews.",
      },
    ],
    integrationTips: [
      "Use Figma Make as the default prototyping layer — replace Figma prototyping for complex flows.",
      "Establish a shared Figma Make workspace per squad so designers share component libraries.",
      "Run weekly 'Design to Demo' sessions where designers ship a working mini-feature.",
      "Use the shareable URL in Jira/Linear tickets to give engineers a functional reference.",
    ],
    populationPercent: 85,
    populationLabel: "~85% of the design team",
    populationReasoning:
      "Nearly every designer benefits immediately — no coding required. The remaining ~15% (design engineers) may prefer Claude Code for deeper integration into existing codebases.",
  },
  {
    tool: "Claude Code",
    color: "from-orange-500 to-amber-600",
    accent: "orange",
    tagline:
      "The design engineer's co-pilot — deep code changes, any file, any stack.",
    personas: [
      {
        role: "Design Engineers / Technologists",
        reason:
          "Refactor component libraries, build design tokens pipelines, or contribute to production code.",
      },
      {
        role: "Senior Designers (coding-literate)",
        reason:
          "Work inside real repos, create PR-ready components, and debug live implementations.",
      },
      {
        role: "Design System Leads",
        reason:
          "Build and maintain scalable component systems with full test coverage and documentation.",
      },
    ],
    integrationTips: [
      "Pair Claude Code with your design system repo — keep it open alongside your IDE.",
      "Use Claude Code for design token automation: extract from Figma API, generate CSS/JS outputs.",
      "Have design engineers use Claude Code to bridge handoff gaps — convert Figma Make prototypes into production-ready components.",
      "Run 'Claude Code' office hours for designers who want to level up their coding skills.",
    ],
    populationPercent: 25,
    populationLabel: "~25% of the design team",
    populationReasoning:
      "Primarily design engineers, design technologists, and coding-literate senior designers. Requires terminal comfort and familiarity with git workflows. High ceiling, but steeper learning curve for traditional designers.",
  },
];

const categoryColors: Record<string, string> = {
  "Design & Visual": "bg-violet-50 text-violet-700",
  "Code Generation": "bg-blue-50 text-blue-700",
  "Engineering & Backend": "bg-orange-50 text-orange-700",
  "Accessibility & Quality": "bg-green-50 text-green-700",
  "Workflow & Usability": "bg-rose-50 text-rose-700",
};

function StatusIcon({ status, note }: { status: Status; note?: string }) {
  const [hovered, setHovered] = useState(false);

  const icon =
    status === "yes" ? (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 text-sm select-none">
        ✓
      </span>
    ) : status === "partial" ? (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-100 text-amber-600 text-sm select-none">
        ◑
      </span>
    ) : (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-gray-100 text-gray-400 text-sm select-none">
        ✕
      </span>
    );

  return (
    <div className="relative flex flex-col items-center gap-1">
      <div
        className="cursor-default"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {icon}
      </div>
      {note && hovered && (
        <div className="absolute top-8 z-10 w-48 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-xl pointer-events-none leading-relaxed">
          {note}
          <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-gray-900 rotate-45" />
        </div>
      )}
      {note && (
        <p className="text-xs text-gray-500 text-center leading-tight max-w-[110px] hidden sm:block">
          {note}
        </p>
      )}
    </div>
  );
}

function PopulationBar({ percent, color }: { percent: number; color: string }) {
  return (
    <div className="mt-3 mb-1">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-gray-500 uppercase tracking-wide">
          Design Team Adoption
        </span>
        <span
          className={`text-sm font-semibold ${color === "violet" ? "text-violet-700" : "text-orange-600"}`}
        >
          {percent}%
        </span>
      </div>
      <div className="h-2.5 w-full bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${color === "violet" ? "bg-gradient-to-r from-violet-500 to-purple-600" : "bg-gradient-to-r from-orange-400 to-amber-500"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

export default function App() {
  const [activeFilter, setActiveFilter] = useState<string>("All");

  const categories = [
    "All",
    "Design & Visual",
    "Code Generation",
    "Engineering & Backend",
    "Accessibility & Quality",
    "Workflow & Usability",
  ];

  const grouped = capabilities.reduce<Record<string, Capability[]>>(
    (acc, cap) => {
      if (activeFilter !== "All" && cap.category !== activeFilter) return acc;
      if (!acc[cap.category]) acc[cap.category] = [];
      acc[cap.category].push(cap);
      return acc;
    },
    {}
  );

  const yesCount = (tool: "figmaMake" | "claudeCode") =>
    capabilities.filter((c) => c[tool] === "yes").length;
  const partialCount = (tool: "figmaMake" | "claudeCode") =>
    capabilities.filter((c) => c[tool] === "partial").length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-14 text-center">
          <div className="inline-flex items-center gap-2 bg-gray-100 rounded-full px-4 py-1.5 text-sm text-gray-600 mb-6">
            <span>Tool Comparison Report</span>
            <span className="text-gray-400">·</span>
            <span>For Design Teams</span>
          </div>
          <h1 className="text-4xl md:text-5xl text-gray-900 mb-4 tracking-tight">
            Figma Make{" "}
            <span className="text-gray-400 mx-3 font-light">vs</span> Claude
            Code
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
            A capability breakdown to help design teams understand which AI tool
            fits which role — and how to integrate both for maximum impact.
          </p>

          {/* Score Cards */}
          <div className="mt-10 grid grid-cols-2 gap-4 max-w-lg mx-auto">
            {[
              {
                tool: "Figma Make",
                key: "figmaMake" as const,
                color: "violet",
                border: "border-violet-200",
                bg: "bg-violet-50",
                text: "text-violet-700",
              },
              {
                tool: "Claude Code",
                key: "claudeCode" as const,
                color: "orange",
                border: "border-orange-200",
                bg: "bg-orange-50",
                text: "text-orange-700",
              },
            ].map((t) => (
              <div
                key={t.tool}
                className={`rounded-2xl border ${t.border} ${t.bg} p-5 text-left`}
              >
                <p className={`text-xs uppercase tracking-wider ${t.text} mb-3`}>
                  {t.tool}
                </p>
                <div className="flex items-end gap-3 flex-wrap">
                  <div>
                    <span className={`text-3xl ${t.text}`}>
                      {yesCount(t.key)}
                    </span>
                    <span className="text-xs text-gray-500 ml-1">full ✓</span>
                  </div>
                  <div>
                    <span className="text-3xl text-amber-500">
                      {partialCount(t.key)}
                    </span>
                    <span className="text-xs text-gray-500 ml-1">partial ◑</span>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  out of {capabilities.length} capabilities
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Legend */}
        <div className="flex flex-wrap items-center gap-5 mb-6 text-sm text-gray-600">
          <span className="font-medium text-gray-700">Legend:</span>
          <span className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-600 text-xs">
              ✓
            </span>
            Fully supported
          </span>
          <span className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-100 text-amber-600 text-xs">
              ◑
            </span>
            Partially supported
          </span>
          <span className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-400 text-xs">
              ✕
            </span>
            Not supported
          </span>
          <span className="text-gray-400 text-xs">
            Hover icons for details
          </span>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-2 mb-8">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveFilter(cat)}
              className={`px-4 py-1.5 rounded-full text-sm border transition-all ${
                activeFilter === cat
                  ? "bg-gray-900 text-white border-gray-900"
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Comparison Table */}
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm mb-16">
          {/* Table Header */}
          <div className="grid grid-cols-[1fr_140px_140px] sm:grid-cols-[1fr_180px_180px] border-b border-gray-200 bg-gray-50">
            <div className="px-6 py-4 text-sm text-gray-500 uppercase tracking-wide">
              Capability
            </div>
            <div className="px-4 py-4 text-center">
              <span className="text-sm text-violet-700 font-semibold">
                Figma Make
              </span>
            </div>
            <div className="px-4 py-4 text-center">
              <span className="text-sm text-orange-600 font-semibold">
                Claude Code
              </span>
            </div>
          </div>

          {Object.entries(grouped).map(([category, items]) => (
            <div key={category}>
              {/* Category Header */}
              <div className="grid grid-cols-[1fr_140px_140px] sm:grid-cols-[1fr_180px_180px] bg-gray-50 border-y border-gray-100">
                <div className="px-6 py-2.5 col-span-3">
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full ${categoryColors[category] || "bg-gray-100 text-gray-600"}`}
                  >
                    {category}
                  </span>
                </div>
              </div>

              {items.map((cap, i) => (
                <div
                  key={cap.feature}
                  className={`grid grid-cols-[1fr_140px_140px] sm:grid-cols-[1fr_180px_180px] items-center border-b border-gray-100 hover:bg-gray-50/50 transition-colors ${
                    i === items.length - 1 ? "border-b-0" : ""
                  }`}
                >
                  <div className="px-6 py-4">
                    <p className="text-sm text-gray-800">{cap.feature}</p>
                  </div>
                  <div className="px-4 py-4 flex justify-center items-start">
                    <StatusIcon
                      status={cap.figmaMake}
                      note={cap.figmaMakeNote}
                    />
                  </div>
                  <div className="px-4 py-4 flex justify-center items-start">
                    <StatusIcon
                      status={cap.claudeCode}
                      note={cap.claudeCodeNote}
                    />
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Recommendation Section */}
        <div className="mb-4">
          <h2 className="text-2xl text-gray-900 mb-2">
            Team Integration Recommendations
          </h2>
          <p className="text-gray-500 text-base">
            How to embed each tool into your design team's workflow, and who
            should use what.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-16">
          {recommendations.map((rec) => (
            <div
              key={rec.tool}
              className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm"
            >
              {/* Card Header */}
              <div className={`bg-gradient-to-br ${rec.color} p-6 text-white`}>
                <h3 className="text-xl mb-1">{rec.tool}</h3>
                <p className="text-sm opacity-85 leading-relaxed">
                  {rec.tagline}
                </p>
              </div>

              <div className="p-6 space-y-6">
                {/* Who Uses It */}
                <div>
                  <h4 className="text-sm uppercase tracking-wide text-gray-400 mb-3">
                    Who Benefits Most
                  </h4>
                  <div className="space-y-2.5">
                    {rec.personas.map((p) => (
                      <div
                        key={p.role}
                        className="flex gap-3 items-start"
                      >
                        <span
                          className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${rec.accent === "violet" ? "bg-violet-500" : "bg-orange-500"}`}
                        />
                        <div>
                          <span className="text-sm text-gray-800">
                            {p.role}
                          </span>
                          <p className="text-xs text-gray-500 leading-relaxed mt-0.5">
                            {p.reason}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Integration Tips */}
                <div>
                  <h4 className="text-sm uppercase tracking-wide text-gray-400 mb-3">
                    Integration Tips
                  </h4>
                  <ul className="space-y-2">
                    {rec.integrationTips.map((tip, i) => (
                      <li key={i} className="flex gap-2.5 items-start">
                        <span
                          className={`text-xs mt-0.5 flex-shrink-0 ${rec.accent === "violet" ? "text-violet-500" : "text-orange-500"}`}
                        >
                          {i + 1}.
                        </span>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          {tip}
                        </p>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Population */}
                <div
                  className={`rounded-xl p-4 ${rec.accent === "violet" ? "bg-violet-50 border border-violet-100" : "bg-orange-50 border border-orange-100"}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-gray-700">
                      Estimated team adoption
                    </p>
                    <span
                      className={`text-sm px-2.5 py-0.5 rounded-full ${rec.accent === "violet" ? "bg-violet-100 text-violet-700" : "bg-orange-100 text-orange-700"}`}
                    >
                      {rec.populationLabel}
                    </span>
                  </div>
                  <PopulationBar
                    percent={rec.populationPercent}
                    color={rec.accent}
                  />
                  <p className="text-xs text-gray-500 mt-3 leading-relaxed">
                    {rec.populationReasoning}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Overlap & Synergy Section */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 mb-16">
          <h2 className="text-2xl text-gray-900 mb-2">
            Where They Work Best Together
          </h2>
          <p className="text-gray-500 mb-8">
            The strongest teams will use both tools in a complementary pipeline
            — not as alternatives.
          </p>

          <div className="grid sm:grid-cols-3 gap-4">
            {[
              {
                step: "01",
                title: "Design → Prototype",
                desc: "Designers use Figma Make to turn frames into interactive React prototypes. No code required. Stakeholders get a working URL.",
                color: "border-violet-200 bg-violet-50",
                label: "text-violet-700",
                who: "All Designers",
                whoColor: "bg-violet-100 text-violet-700",
              },
              {
                step: "02",
                title: "Prototype → Production",
                desc: "Design engineers use Claude Code to refine, refactor, and integrate the prototype into the real codebase with tests and proper architecture.",
                color: "border-gray-200 bg-gray-50",
                label: "text-gray-600",
                who: "Design Engineers",
                whoColor: "bg-gray-200 text-gray-600",
              },
              {
                step: "03",
                title: "System → Scale",
                desc: "Claude Code maintains and evolves the design system in code. Figma Make pulls from it to keep new prototypes consistent with production.",
                color: "border-orange-200 bg-orange-50",
                label: "text-orange-700",
                who: "Design System Leads",
                whoColor: "bg-orange-100 text-orange-700",
              },
            ].map((s) => (
              <div
                key={s.step}
                className={`rounded-xl border p-5 ${s.color}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-2xl ${s.label}`}>{s.step}</span>
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full ${s.whoColor}`}
                  >
                    {s.who}
                  </span>
                </div>
                <h3 className="text-base text-gray-800 mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Summary */}
        <div className="grid sm:grid-cols-2 gap-4 mb-12">
          <div className="bg-violet-600 rounded-2xl p-6 text-white">
            <h3 className="text-lg mb-3">Figma Make in a sentence</h3>
            <p className="text-sm opacity-85 leading-relaxed">
              It's the fastest path from a Figma design to a shareable,
              interactive app — perfect for the entire design team with zero
              coding barrier. Use it for prototyping, stakeholder demos, and
              design system documentation.
            </p>
          </div>
          <div className="bg-amber-500 rounded-2xl p-6 text-white">
            <h3 className="text-lg mb-3">Claude Code in a sentence</h3>
            <p className="text-sm opacity-85 leading-relaxed">
              It's an agentic coding partner for the design team's technical
              members — capable of diving into real codebases, running tests,
              managing git, and building production-grade systems. Use it where
              Figma Make ends.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 pb-8">
          Analysis based on publicly available capabilities as of March 2026. 
          Capability ratings reflect typical design team use cases.
        </div>
      </div>
    </div>
  );
}
