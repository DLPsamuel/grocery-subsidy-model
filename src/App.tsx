import { useState } from "react";
import {
  H1, H2, H3,
  Stack, Row, Grid,
  Card, CardHeader, CardBody,
  Text, Code, Divider,
  Table, Pill, Callout, Stat,
  useHostTheme,
} from "./ui";

type Tab = "architecture" | "equations" | "data" | "implementation";

// ─── Equation block helper ──────────────────────────────────────────────────
function EqBlock({ label, eq, note }: { label: string; eq: string; note?: string }) {
  const theme = useHostTheme();
  return (
    <div style={{ marginBottom: 12 }}>
      <Text size="small" tone="secondary" weight="semibold" style={{ marginBottom: 4 }}>
        {label}
      </Text>
      <div
        style={{
          background: theme.fill.secondary,
          border: `1px solid ${theme.stroke.tertiary}`,
          borderRadius: 6,
          padding: "8px 14px",
          fontFamily: "monospace",
          fontSize: 13,
          color: theme.text.primary,
          lineHeight: 1.7,
          whiteSpace: "pre-wrap",
        }}
      >
        {eq}
      </div>
      {note && (
        <Text size="small" tone="tertiary" style={{ marginTop: 4 }}>
          {note}
        </Text>
      )}
    </div>
  );
}

// ─── Section label ───────────────────────────────────────────────────────────
function SectionLabel({ children }: { children: string }) {
  const theme = useHostTheme();
  return (
    <div
      style={{
        display: "inline-block",
        background: theme.accent.primary,
        color: theme.text.onAccent,
        borderRadius: 4,
        padding: "2px 8px",
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  );
}

// ─── Step list ───────────────────────────────────────────────────────────────
function StepList({ steps }: { steps: { n: number; title: string; detail: string }[] }) {
  const theme = useHostTheme();
  return (
    <Stack gap={10}>
      {steps.map((s) => (
        <div key={s.n} style={{ display: "contents" }}>
          <Row gap={12} align="start">
            <div
              style={{
                minWidth: 24,
                height: 24,
                borderRadius: "50%",
                background: theme.fill.tertiary,
                border: `1px solid ${theme.stroke.secondary}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 11,
                fontWeight: 700,
                color: theme.text.secondary,
                flexShrink: 0,
                marginTop: 1,
              }}
            >
              {s.n}
            </div>
            <Stack gap={2}>
              <Text weight="semibold">{s.title}</Text>
              <Text size="small" tone="secondary">{s.detail}</Text>
            </Stack>
          </Row>
        </div>
      ))}
    </Stack>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB: Architecture
// ═══════════════════════════════════════════════════════════════════════════
function ArchitectureTab() {
  return (
    <Stack gap={24}>
      <Stack gap={6}>
        <H2>Problem Architecture</H2>
        <Text tone="secondary">
          Three sequential goals, each building on the last. The model is <Text weight="semibold" as="span">static</Text> — a single-period snapshot with incumbent store attributes fixed as inputs.
        </Text>
      </Stack>

      {/* Three goals */}
      <Grid columns={3} gap={12}>
        {[
          {
            phase: "Goal 1",
            title: "Single-Store Subsidy Effect",
            q: "How much must the city spend to meaningfully lower prices and shift consumer behavior at one store?",
            type: "Threshold / Sensitivity",
          },
          {
            phase: "Goal 2",
            title: "Optimal Store Selection",
            q: "Which store should receive the subsidy? How do volume, cost structure, quality, and variety affect the city's welfare return?",
            type: "Combinatorial Optimization",
          },
          {
            phase: "Goal 3",
            title: "Cross-Store Spillovers",
            q: "At steady state (no rival reactions), how does subsidizing one store affect traffic and profit at surrounding stores?",
            type: "Comparative Statics",
          },
        ].map((g) => (
          <div key={g.phase} style={{ display: "contents" }}>
            <Card style={{ height: "100%" }}>
              <CardHeader trailing={<Pill size="sm">{g.type}</Pill>}>{g.phase}</CardHeader>
              <CardBody>
                <Stack gap={8}>
                  <Text weight="semibold">{g.title}</Text>
                  <Text size="small" tone="secondary">{g.q}</Text>
                </Stack>
              </CardBody>
            </Card>
          </div>
        ))}
      </Grid>

      <Divider />

      {/* Model actors */}
      <Stack gap={12}>
        <H3>Model Actors and Decisions</H3>
        <Grid columns={2} gap={12}>
          <Card>
            <CardHeader>Decision-Maker: City (NYCEDC / Mayor's Office)</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small" weight="semibold">Choice variables</Text>
                <Text size="small" tone="secondary">
                  Which store(s) to support, which instrument to use (tax break / rent subsidy / direct operation), and how large the subsidy.
                </Text>
                <Text size="small" weight="semibold" style={{ marginTop: 4 }}>Constraints</Text>
                <Text size="small" tone="secondary">
                  Total budget <Code>B</Code>; eligibility requirements (SNAP-authorized, location in target zone, store size, ownership type).
                </Text>
                <Text size="small" weight="semibold" style={{ marginTop: 4 }}>Objective</Text>
                <Text size="small" tone="secondary">
                  Maximize aggregate consumer welfare gain <Code>ΔCS</Code> (or target households-in-food-desert served), subject to budget and eligibility.
                </Text>
              </Stack>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>Agents: Stores and Consumers</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small" weight="semibold">Stores (passive incumbents)</Text>
                <Text size="small" tone="secondary">
                  Fixed attributes: quality <Code>q_j</Code>, variety <Code>v_j</Code>, cost structure <Code>(FC_j, VC_j)</Code>.
                  Respond to subsidy by adjusting price via a calibrated pass-through rate <Code>θ_j</Code>.
                </Text>
                <Text size="small" weight="semibold" style={{ marginTop: 4 }}>Consumers (heterogeneous)</Text>
                <Text size="small" tone="secondary">
                  Each consumer <Code>i</Code> has preference weights <Code>(β_q, β_v, β_p, β_d)</Code> drawn from a distribution.
                  They choose the store that maximizes their indirect utility (multinomial logit).
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Grid>
      </Stack>

      <Divider />

      {/* Key assumptions */}
      <Stack gap={8}>
        <H3>Key Modeling Assumptions</H3>
        <Table
          headers={["Assumption", "Rationale", "Sensitivity"]}
          striped
          rows={[
            ["Static single-period model", "Tractable; captures steady-state price effect without dynamic entry/exit", "Extend to dynamic if store entry is policy-relevant"],
            ["Incumbent store attributes are fixed inputs", "Quality and variety don't adjust to subsidy in short run", "Shift quality/variety parameters in sensitivity runs"],
            ["No Nash equilibrium / rival response", "Goal 3 is a partial-equilibrium shock, not a game", "Full Bertrand competition left for optional extension"],
            ["Multinomial logit (MNL) base model", "Standard in discrete choice demand estimation; closed-form shares", "Mixed logit adds preference heterogeneity; nested logit adds store-type correlation"],
            ["Pass-through rate θ is calibrated, not derived", "Requires industry data or empirical estimate; avoids needing full cost function curvature", "Vary θ ∈ [0.4, 0.9] in sensitivity analysis"],
            ["Market is a defined NYC geographic area", "Controls for out-of-area shopping and tractability", "One or more community districts / census tracts"],
          ]}
          columnAlign={["left", "left", "left"]}
        />
      </Stack>
    </Stack>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB: Equations
// ═══════════════════════════════════════════════════════════════════════════
function EquationsTab() {
  const [section, setSection] = useState<"consumer" | "store" | "subsidy" | "optimization">("consumer");

  return (
    <Stack gap={20}>
      <H2>Model Equations</H2>

      {/* Sub-navigation */}
      <Row gap={8} wrap>
        {(["consumer", "store", "subsidy", "optimization"] as const).map((s) => (
          <span key={s} style={{ display: "contents" }}>
            <Pill active={section === s} onClick={() => setSection(s)}>
              {s === "consumer" ? "Consumer Demand" : s === "store" ? "Store Cost & Pricing" : s === "subsidy" ? "Subsidy Pass-Through" : "Optimization Problems"}
            </Pill>
          </span>
        ))}
      </Row>

      {section === "consumer" && (
        <Stack gap={20}>
          <Stack gap={4}>
            <SectionLabel>Consumer Side</SectionLabel>
            <H3>Indirect Utility (Mixed Logit)</H3>
            <Text tone="secondary">
              Consumer <Code>i</Code> derives utility from store <Code>j</Code>. Preference weights are drawn from a population distribution, producing heterogeneous choice behavior.
            </Text>
          </Stack>

          <EqBlock
            label="Utility of consumer i at store j"
            eq={"U_ij = β_q_i · q_j  +  β_v_i · v_j  −  β_p_i · p_j  −  β_d_i · d_ij  +  ε_ij\n\nε_ij ~ Gumbel(0, 1)  (i.i.d. extreme value)"}
            note="q_j = quality index, v_j = variety index, p_j = price level, d_ij = travel distance/time from consumer i's census tract centroid to store j."
          />

          <EqBlock
            label="Preference heterogeneity (Random Coefficients)"
            eq={"β_i = (β_q_i, β_v_i, β_p_i, β_d_i)  ~  MVN(μ_β, Σ_β)\n\nμ_β estimated from ACS income data + Consumer Expenditure Survey.\nΣ_β captures correlation in preferences (e.g., price and distance sensitivity)."}
            note="Lower-income consumers receive higher β_p (price sensitivity) and potentially higher β_d (mobility constraints). This is identified from ACS income distribution."
          />

          <EqBlock
            label="Individual choice probability (conditional on β_i)"
            eq={"s_ij | β_i  =  exp(V_ij)  /  Σ_k exp(V_ik)\n\nV_ij = β_q_i · q_j + β_v_i · v_j − β_p_i · p_j − β_d_i · d_ij   (systematic part)"}
          />

          <EqBlock
            label="Aggregate market share of store j"
            eq={"S_j  =  (1/N) · Σ_i s_ij   ≈   ∫ s_ij(β) · f(β) dβ\n\nComputed via simulation: draw R vectors β^r, average s_ij(β^r) over r."}
            note="N = number of consumers in the study area (from ACS household count)."
          />

          <EqBlock
            label="Consumer welfare (logsum / expected maximum utility)"
            eq={"W_i  =  (1/β_p_i) · ln[ Σ_k exp(V_ik) ]   (Williams–Daly–Zachary formula)\n\nΔW_i (post subsidy)  =  (1/β_p_i) · [ ln Σ_k exp(V_ik_post)  −  ln Σ_k exp(V_ik_pre) ]\n\nΔCS  =  Σ_i ΔW_i  ·  income_weight_i"}
            note="The logsum is the log of the denominator of the MNL formula. It represents the expected utility of the best available option. Dividing by β_p_i converts utils to dollars. income_weight_i optionally weights low-income households more heavily in the social welfare function."
          />

          <Callout tone="info" title="Simplification path">
            Start with a <Text weight="semibold" as="span">standard MNL</Text> with fixed β estimated from the literature (e.g., Davis 2006, Allcott et al. 2019).
            Upgrade to <Text weight="semibold" as="span">Mixed Logit</Text> with simulated preference draws once the base model runs.
            This mirrors the project's phased approach.
          </Callout>
        </Stack>
      )}

      {section === "store" && (
        <Stack gap={20}>
          <Stack gap={4}>
            <SectionLabel>Store Side</SectionLabel>
            <H3>Cost Structure and Pricing</H3>
            <Text tone="secondary">
              Store <Code>j</Code>'s cost structure is calibrated from industry benchmarks (IBISWorld, Supermarket News). Price is set as a markup over variable cost.
            </Text>
          </Stack>

          <EqBlock
            label="Total cost"
            eq={"TC_j(Q_j)  =  FC_j  +  VC_j · Q_j\n\nFC_j  =  Rent_j + Labor_fixed_j + Other_fixed_j\nVC_j  =  COGS_per_unit_j  +  Labor_variable_per_unit_j"}
            note="Q_j = units sold (or revenue equivalent). FC_j and VC_j calibrated from chain-specific 10-K filings and industry gross margin benchmarks (~25–30% for conventional grocery, ~15% for discount)."
          />

          <EqBlock
            label="Profit"
            eq={"π_j  =  (p_j − VC_j) · Q_j  −  FC_j\n\n     =  margin_j · Q_j  −  FC_j"}
          />

          <EqBlock
            label="Baseline pricing rule (cost-plus)"
            eq={"p_j  =  (1 + μ_j) · VC_j\n\nμ_j = markup rate, calibrated per store type:\n  Large chain (Walmart, Costco):    μ ≈ 0.20–0.25\n  Mid-size (Key Food, C-Town):       μ ≈ 0.30–0.40\n  Small independent:                 μ ≈ 0.40–0.60"}
            note="Alternatively, use the Lerner condition: p_j = VC_j / (1 − 1/|ε_j|), where ε_j is the own-price elasticity estimated from the demand model."
          />

          <EqBlock
            label="Own-price elasticity from MNL"
            eq={"ε_jj  =  −β_p · p_j · (1 − S_j)\n\nFor mixed logit:\nε_jj  =  −p_j · (1/N) · Σ_i [ β_p_i · s_ij · (1 − s_ij) ]"}
            note="This is the standard MNL price elasticity formula. It feeds back into the Lerner pricing condition if you use the economic pricing rule rather than cost-plus."
          />

          <EqBlock
            label="Store volume (quantity demanded)"
            eq={"Q_j  =  S_j · M\n\nM = total market size in dollars or visits per period\n  (calibrated from: households × average weekly food spend from CES)\n\nAlternatively, use store-level revenue estimates from ReferenceUSA / Dun & Bradstreet\nand back out implied volume: Q_j = Revenue_j / p_j"}
          />
        </Stack>
      )}

      {section === "subsidy" && (
        <Stack gap={20}>
          <Stack gap={4}>
            <SectionLabel>Policy Instruments</SectionLabel>
            <H3>Subsidy Pass-Through to Consumer Prices</H3>
            <Text tone="secondary">
              The key behavioral link: how does a dollar of city subsidy translate into a price reduction at the store? This depends on the instrument and the store's cost structure.
            </Text>
          </Stack>

          <EqBlock
            label="General pass-through equation"
            eq={"Δp_j  =  −θ_j · g_j(s)\n\nθ_j ∈ [0, 1]  =  pass-through rate (empirical estimate)\ng_j(s)        =  per-unit price savings from subsidy s"}
            note="θ_j is the fraction of subsidy savings that the store passes to consumers as lower prices. Literature suggests 0.5–0.8 for competitive grocery markets."
          />

          <Grid columns={3} gap={12}>
            {[
              {
                name: "Instrument 1: Tax Break",
                formula: "Δ(effective tax) = −τ · Tax_j\n\nPer-unit saving:\ng_j = τ · Tax_j / Q_j\n\nPrice effect:\nΔp_j = −θ_j · τ · Tax_j / Q_j",
                note: "τ = fraction of tax liability forgiven. Tax data from NYC property records.",
              },
              {
                name: "Instrument 2: Rent Subsidy",
                formula: "ΔFC_j = −σ_rent\n\nPer-unit saving:\ng_j = σ_rent / Q_j\n\nPrice effect:\nΔp_j = −θ_j · σ_rent / Q_j",
                note: "σ_rent = annual dollar amount of rent covered. Rent from NYC ACRIS or estimated from sq-ft × market rate.",
              },
              {
                name: "Instrument 3: Direct Operation",
                formula: "City sets price directly:\np_j_post = VC_j  (zero markup)\n\nOr applies per-unit subsidy:\np_j_post = p_j − s_unit\n\nEquivalent: θ_j = 1, full pass-through",
                note: "This is the strongest instrument. Requires city to absorb FC_j − (p−VC)·Q_j as operating loss. Binding budget constraint is tighter.",
              },
            ].map((instr) => (
              <div key={instr.name} style={{ display: "contents" }}>
                <Card>
                  <CardHeader>{instr.name}</CardHeader>
                  <CardBody>
                    <div
                      style={{
                        fontFamily: "monospace",
                        fontSize: 12,
                        lineHeight: 1.7,
                        whiteSpace: "pre-wrap",
                        marginBottom: 8,
                      }}
                    >
                      {instr.formula}
                    </div>
                    <Text size="small" tone="tertiary">{instr.note}</Text>
                  </CardBody>
                </Card>
              </div>
            ))}
          </Grid>

          <EqBlock
            label="Post-subsidy utility and share (Goal 1 and 3 core update)"
            eq={"V_ij_post  =  V_ij_pre  +  β_p_i · |Δp_j|           (if store j is subsidized)\nV_ik_post  =  V_ik_pre                               (all other stores k ≠ j)\n\ns_ij_post  =  exp(V_ij_post)  /  Σ_l exp(V_il_post)\n\nΔCS        =  Σ_i (1/β_p_i) · Δ ln(Σ_l exp(V_il_post))"}
            note="This is the complete chain from subsidy → price reduction → utility update → share reallocation → welfare gain."
          />
        </Stack>
      )}

      {section === "optimization" && (
        <Stack gap={20}>
          <Stack gap={4}>
            <SectionLabel>Optimization</SectionLabel>
            <H3>Formal Problem Statements</H3>
          </Stack>

          <Card>
            <CardHeader trailing={<Pill size="sm">Goal 1</Pill>}>Minimum Effective Subsidy (Single Store)</CardHeader>
            <CardBody>
              <EqBlock
                label="Problem: find smallest s that achieves measurable welfare change"
                eq={"min   s\ns.t.  Δp_j(s) ≥ Δp_min           (price must fall by at least Δp_min, e.g. 5%)\n      ΔCS_j(s) ≥ ΔCS_min       (welfare gain threshold)\n      s ≤ B                    (budget)\n      s ≥ 0\n\nEquivalently: invert Δp_j(s) = −θ_j · g_j(s) to get s*(Δp_min)\nthen verify ΔCS_j(s*) ≥ ΔCS_min"}
                note="This is a single-variable inversion — not a hard optimization. Run over a grid of s values and plot ΔCS(s) to find the cost-effectiveness frontier."
              />
            </CardBody>
          </Card>

          <Card>
            <CardHeader trailing={<Pill size="sm">Goal 2</Pill>}>Optimal Store Selection</CardHeader>
            <CardBody>
              <Stack gap={12}>
                <EqBlock
                  label="Binary selection (choose exactly one store from J candidates)"
                  eq={"max_{x_j ∈ {0,1}}    Σ_j  x_j · ΔCS_j(s_j)\n\ns.t.   Σ_j  x_j · s_j  ≤  B          (total budget)\n       Σ_j  x_j  ≤  K               (at most K stores, e.g. K=1 or K=2)\n       x_j ≤ e_j  ∀j               (eligibility: e_j ∈ {0,1})\n       s_j ≥ s_j_min  ∀j           (min effective subsidy per store type)"}
                  note="With K=1 and |J| small (e.g. 5–15 candidate stores), this is solved by enumeration. For K>1 or large J, use integer programming (e.g. scipy.optimize.milp or PuLP)."
                />
                <EqBlock
                  label="Continuous allocation (split budget across stores)"
                  eq={"max_{s_j ≥ 0}    Σ_j  ΔCS_j(s_j)\n\ns.t.   Σ_j  s_j  ≤  B\n       e_j · s_j = s_j  ∀j    (zero subsidy to ineligible stores)\n\nΔCS_j(s_j) is concave in s_j (diminishing returns) → convex program → unique solution."}
                  note="If ΔCS_j is concave and differentiable, use KKT conditions: dΔCS_j/ds_j = λ for all active stores (equalize marginal welfare gain per dollar)."
                />
              </Stack>
            </CardBody>
          </Card>

          <Card>
            <CardHeader trailing={<Pill size="sm">Goal 3</Pill>}>Cross-Store Spillover (Comparative Statics)</CardHeader>
            <CardBody>
              <EqBlock
                label="Not an optimization — a shock propagation calculation"
                eq={"Given: optimal subsidy s* → price change Δp_j* at subsidized store j*\n\nFor all other stores k ≠ j*:\n  ΔQ_k  =  M · [ S_k_post  −  S_k_pre ]\n          = M · (1/N) · Σ_i [ s_ik_post − s_ik_pre ]\n\n  Δπ_k  =  (p_k − VC_k) · ΔQ_k\n\nAggregate displaced revenue:\n  ΔRev_displaced  =  Σ_{k ≠ j*}  p_k · ΔQ_k\n\nFraction captured by subsidized store:\n  ΔRev_j*  =  p_j* · ΔQ_j*"}
                note="No rival price response (static equilibrium). All share reallocation is driven by the utility improvement at store j*. Identify stores most at risk by ranking |ΔQ_k|."
              />
            </CardBody>
          </Card>

          <Callout tone="neutral" title="Model summary in one line">
            Subsidy <Code>s</Code> → price reduction <Code>Δp_j</Code> (via pass-through <Code>θ_j</Code>) → utility shift <Code>ΔV_ij</Code> → share reallocation <Code>Δs_ij</Code> → welfare gain <Code>ΔCS</Code> and spillovers <Code>ΔQ_k</Code>.
            City maximizes <Code>ΔCS</Code> over store choice and instrument.
          </Callout>
        </Stack>
      )}
    </Stack>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB: Data
// ═══════════════════════════════════════════════════════════════════════════
function DataTab() {
  const [layer, setLayer] = useState<"all" | "demand" | "supply" | "geo" | "policy">("all");

  const sources = [
    {
      layer: "demand",
      layerLabel: "Demand",
      source: "ACS 5-Year Estimates",
      provider: "U.S. Census Bureau",
      variables: "Household income, size, race/ethnicity, vehicle access — tract level",
      use: "Construct consumer income distribution; calibrate β_p (price sensitivity) by income quintile; set market size M",
      access: "census.gov API or tidycensus (R) / censusdataapi (Python)",
    },
    {
      layer: "demand",
      layerLabel: "Demand",
      source: "Consumer Expenditure Survey (CES/CEX)",
      provider: "BLS",
      variables: "Share of income spent on food at home, by income quintile",
      use: "Set per-household food expenditure; calibrate μ_β (mean preference weights)",
      access: "bls.gov/cex — public microdata",
    },
    {
      layer: "demand",
      layerLabel: "Demand",
      source: "Discrete Choice Literature",
      provider: "Academic (Davis 2006; Allcott et al. 2019; Handbury 2021)",
      variables: "Estimated β_p, β_d, β_q from grocery demand studies",
      use: "Prior / starting point for preference weights before local calibration",
      access: "Published papers; replication data if available",
    },
    {
      layer: "supply",
      layerLabel: "Supply",
      source: "IBISWorld / Supermarket News",
      provider: "Industry reports",
      variables: "Gross margin by chain type, operating cost breakdown (labor, rent, COGS)",
      use: "Calibrate FC_j, VC_j per store type; set baseline markup μ_j",
      access: "Paid; NYC library access or university subscription",
    },
    {
      layer: "supply",
      layerLabel: "Supply",
      source: "SEC 10-K Filings",
      provider: "Public companies (Walmart, Kroger, etc.)",
      variables: "Revenue, COGS, SG&A, occupancy costs at chain level",
      use: "Refine cost structure estimates for large-chain stores in the candidate set",
      access: "SEC EDGAR — free",
    },
    {
      layer: "supply",
      layerLabel: "Supply",
      source: "ReferenceUSA / Dun & Bradstreet",
      provider: "Commercial",
      variables: "Establishment-level revenue estimates, employee count",
      use: "Estimate store-level revenue Q_j · p_j; back out volume",
      access: "NYC Public Library (free with library card) or university access",
    },
    {
      layer: "geo",
      layerLabel: "Geography",
      source: "USDA SNAP Retailer Locator",
      provider: "USDA FNS",
      variables: "SNAP-authorized store name, address, type",
      use: "Identify candidate stores in the study area; eligibility filter",
      access: "usda.gov/snap-retailer — downloadable CSV",
    },
    {
      layer: "geo",
      layerLabel: "Geography",
      source: "NYC Open Data — Food Retail Establishments",
      provider: "NYC DOHMH",
      variables: "Store name, address, type (supermarket, bodega, etc.)",
      use: "Enrich candidate store list; classify by store type for quality/variety scoring",
      access: "data.cityofnewyork.us — free API",
    },
    {
      layer: "geo",
      layerLabel: "Geography",
      source: "Census TIGER / OpenStreetMap",
      provider: "U.S. Census / OSM contributors",
      variables: "Census tract boundaries, centroids, street network",
      use: "Compute d_ij (distance matrix from each tract centroid to each candidate store); define study area",
      access: "census.gov TIGER shapefiles; osmuf / osmnx Python library",
    },
    {
      layer: "policy",
      layerLabel: "Policy",
      source: "NYC ACRIS (property records)",
      provider: "NYC Dept. of Finance",
      variables: "Lease agreements, property sale prices, assessed values",
      use: "Estimate Rent_j for each store; basis for rent subsidy instrument (σ_rent)",
      access: "a836-acris.nyc.gov — free search",
    },
    {
      layer: "policy",
      layerLabel: "Supply",
      source: "NYC Property Tax Data (NYCDB)",
      provider: "NYC Dept. of Finance",
      variables: "Annual property tax bill by parcel",
      use: "Estimate current Tax_j for each store; basis for tax break instrument",
      access: "nycdb.info or data.cityofnewyork.us",
    },
    {
      layer: "policy",
      layerLabel: "Policy",
      source: "Pass-Through Rate Literature",
      provider: "Academic (Besanko et al. 2005; Nakamura & Zerom 2010)",
      variables: "Empirical θ estimates for food retail: range 0.5–0.85",
      use: "Calibrate θ_j; used as sensitivity parameter in Goal 1",
      access: "Published papers",
    },
  ];

  const filtered = layer === "all" ? sources : sources.filter((s) => s.layer === layer);

  return (
    <Stack gap={20}>
      <Stack gap={6}>
        <H2>Data Sources</H2>
        <Text tone="secondary">
          All data is publicly available or accessible via NYC library / university subscription. The table maps each source to the model parameter it informs.
        </Text>
      </Stack>

      <Row gap={8} wrap>
        {(["all", "demand", "supply", "geo", "policy"] as const).map((l) => (
          <span key={l} style={{ display: "contents" }}>
            <Pill active={layer === l} onClick={() => setLayer(l)}>
              {l === "all" ? "All Sources" : l === "demand" ? "Consumer Demand" : l === "supply" ? "Store Supply" : l === "geo" ? "Geography" : "Policy Instruments"}
            </Pill>
          </span>
        ))}
      </Row>

      <Table
        headers={["Source", "Provider", "Variables", "Model Use", "Access"]}
        striped
        stickyHeader
        rows={filtered.map((s) => [
          <Text weight="semibold" size="small" as="span">{s.source}</Text>,
          <Text size="small" tone="secondary" as="span">{s.provider}</Text>,
          <Text size="small" as="span">{s.variables}</Text>,
          <Text size="small" tone="secondary" as="span">{s.use}</Text>,
          <Text size="small" tone="secondary" as="span">{s.access}</Text>,
        ])}
        rowTone={filtered.map((s) =>
          s.layer === "demand" ? "info" :
          s.layer === "supply" ? "warning" :
          s.layer === "geo" ? "success" : "neutral"
        )}
      />

      <Divider />

      <Stack gap={12}>
        <H3>Data-to-Parameter Mapping</H3>
        <Grid columns={2} gap={12}>
          <Card>
            <CardHeader>Consumer-Side Parameters</CardHeader>
            <CardBody>
              <Stack gap={6}>
                {[
                  { param: "β_p_i (price sensitivity)", source: "ACS income + CES food share + literature priors" },
                  { param: "β_d_i (distance sensitivity)", source: "ACS vehicle access + literature; higher for low-income tracts" },
                  { param: "β_q, β_v (quality/variety weight)", source: "Literature (Handbury 2021); fixed input for now" },
                  { param: "M (market size, $)", source: "ACS households × CES mean food-at-home expenditure" },
                  { param: "d_ij (distance matrix)", source: "TIGER centroids + OSMnx travel time" },
                ].map((r) => (
                  <div key={r.param} style={{ display: "contents" }}>
                  <Row gap={8} align="start">
                    <div style={{ minWidth: 8, height: 8, borderRadius: "50%", background: "currentColor", opacity: 0.4, marginTop: 6, flexShrink: 0 }} />
                    <Stack gap={1}>
                      <Text size="small" weight="semibold"><Code>{r.param}</Code></Text>
                      <Text size="small" tone="tertiary">{r.source}</Text>
                    </Stack>
                  </Row>
                  </div>
                ))}
              </Stack>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>Store-Side Parameters</CardHeader>
            <CardBody>
              <Stack gap={6}>
                {[
                  { param: "FC_j (fixed costs)", source: "Rent from ACRIS + labor estimates from IBISWorld" },
                  { param: "VC_j (variable costs per unit)", source: "IBISWorld COGS benchmarks + 10-K filings by chain" },
                  { param: "p_j (baseline price)", source: "Back-calculated from Revenue_j / Q_j (ReferenceUSA)" },
                  { param: "q_j, v_j (quality, variety)", source: "Proxy: store type (DOHMH), sq footage, Yelp/Google reviews (ordinal)" },
                  { param: "θ_j (pass-through rate)", source: "Literature (Besanko et al. 2005); varied in sensitivity analysis" },
                  { param: "Tax_j / Rent_j", source: "NYCDB property tax + ACRIS lease data" },
                ].map((r) => (
                  <div key={r.param} style={{ display: "contents" }}>
                    <Row gap={8} align="start">
                      <div style={{ minWidth: 8, height: 8, borderRadius: "50%", background: "currentColor", opacity: 0.4, marginTop: 6, flexShrink: 0 }} />
                      <Stack gap={1}>
                        <Text size="small" weight="semibold"><Code>{r.param}</Code></Text>
                        <Text size="small" tone="tertiary">{r.source}</Text>
                      </Stack>
                    </Row>
                  </div>
                ))}
              </Stack>
            </CardBody>
          </Card>
        </Grid>
      </Stack>
    </Stack>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB: Implementation
// ═══════════════════════════════════════════════════════════════════════════
function ImplementationTab() {
  const theme = useHostTheme();

  const phases: {
    id: string;
    goal: string;
    title: string;
    output: string;
    color: string;
    steps: { n: number; title: string; detail: string }[];
  }[] = [
    {
      id: "phase0",
      goal: "Setup",
      title: "Phase 0 — Study Area and Data Assembly",
      output: "A clean dataset: candidate stores with attributes, consumer tracts with demographics, and a distance matrix.",
      color: theme.fill.tertiary,
      steps: [
        {
          n: 1,
          title: "Define geographic scope",
          detail: "Select 1–3 contiguous NYC community districts or ~10–20 census tracts that contain food deserts. Rationale: small enough for tractability, large enough for meaningful variation in store types.",
        },
        {
          n: 2,
          title: "Pull ACS household data",
          detail: "Download ACS 5-year tract-level data: median household income, income distribution, household size, vehicle access, population. Use tidycensus or Census API.",
        },
        {
          n: 3,
          title: "Build candidate store list",
          detail: "Query USDA SNAP retailer database + NYC DOHMH food retail data for the study area. Filter to SNAP-authorized stores. Classify by type (supermarket, discount, independent). Target 5–15 stores.",
        },
        {
          n: 4,
          title: "Compute distance matrix d_ij",
          detail: "Use tract centroids (TIGER) and store addresses (geocoded). Compute walking/transit time via OSMnx or Google Maps API. Produces an N_tracts × J_stores matrix.",
        },
        {
          n: 5,
          title: "Assign store attributes (q_j, v_j)",
          detail: "Score quality and variety as ordinal indices: store type (supermarket=3, discount=2, bodega=1), sq footage bins, and if available, health department inspection scores or product count proxies.",
        },
        {
          n: 6,
          title: "Calibrate cost structure",
          detail: "For each store, estimate FC_j (rent from ACRIS × sq ft, staff from employee count × avg wage) and VC_j (COGS per unit from IBISWorld gross margin benchmarks by store type). Pull revenue estimates from ReferenceUSA.",
        },
        {
          n: 7,
          title: "Set preference parameters",
          detail: "Use literature values for μ_β = (β_q, β_v, β_p, β_d). Scale β_p_i by income: lower-income consumers get higher price sensitivity. Use CES food-budget shares to anchor magnitudes.",
        },
      ],
    },
    {
      id: "phase1",
      goal: "Goal 1",
      title: "Phase 1 — Single-Store Subsidy Effect",
      output: "A cost-effectiveness curve: dollars of subsidy vs. price reduction and consumer welfare gain for one store.",
      color: theme.fill.tertiary,
      steps: [
        {
          n: 1,
          title: "Pick a representative store j*",
          detail: "Choose one store to analyze first (e.g., a mid-size independent in a food desert tract). Fix all other store prices at baseline.",
        },
        {
          n: 2,
          title: "Model price as a function of subsidy: p_j(s)",
          detail: "For each instrument: compute g_j(s) (per-unit savings), then Δp_j = −θ_j · g_j(s). Build a grid of s values from $0 to B_max in $10k increments.",
        },
        {
          n: 3,
          title: "Compute pre-subsidy baseline market shares",
          detail: "Evaluate V_ij_pre for all i, j. Compute s_ij_pre = softmax. Compute baseline logsum W_i_pre and aggregate consumer surplus CS_pre.",
        },
        {
          n: 4,
          title: "For each subsidy level s, compute ΔCS(s)",
          detail: "Update V_ij*_post = V_ij*_pre + β_p_i · |Δp_j*(s)|. Recompute market shares and logsum. ΔCS(s) = Σ_i (1/β_p_i) · Δlogsum_i.",
        },
        {
          n: 5,
          title: "Find threshold subsidy s*",
          detail: "Identify the smallest s where ΔCS(s) exceeds a meaningful threshold (e.g., $X per household, or Y% share shift). This is your 'minimum effective subsidy.'",
        },
        {
          n: 6,
          title: "Sensitivity analysis on θ_j and β_p",
          detail: "Vary pass-through rate θ_j ∈ {0.4, 0.6, 0.8} and income-price sensitivity scaling. Plot confidence band around the ΔCS(s) curve. Identify how robust the threshold s* is.",
        },
        {
          n: 7,
          title: "Repeat for each instrument",
          detail: "Compare tax break vs. rent subsidy vs. direct operation at equal subsidy levels. Rank by cost-effectiveness: ΔCS per dollar spent.",
        },
      ],
    },
    {
      id: "phase2",
      goal: "Goal 2",
      title: "Phase 2 — Optimal Store Selection",
      output: "A ranking of all candidate stores by welfare return per dollar, plus an optimal selection given budget B.",
      color: theme.fill.tertiary,
      steps: [
        {
          n: 1,
          title: "Run Phase 1 for every candidate store j",
          detail: "Apply the single-store subsidy model to all J stores. For a fixed budget B, compute ΔCS_j(B). Produces a J-vector of welfare returns.",
        },
        {
          n: 2,
          title: "Apply eligibility filters",
          detail: "Set e_j = 0 for ineligible stores (not SNAP-authorized, outside target zone, above size threshold, chain-owned if policy targets independents). This reduces the feasible set.",
        },
        {
          n: 3,
          title: "Enumerate store selection (K=1)",
          detail: "With a single store selection, simply pick argmax_j ΔCS_j(B) among eligible stores. No integer program needed.",
        },
        {
          n: 4,
          title: "Multi-store allocation (K>1 or continuous)",
          detail: "Solve the continuous allocation program: maximize Σ_j ΔCS_j(s_j) s.t. Σ_j s_j ≤ B. Use scipy.optimize (SLSQP) or KKT conditions (equalize marginal welfare per dollar across stores).",
        },
        {
          n: 5,
          title: "Decompose welfare gain by store type",
          detail: "Compare results across store types (large chain, mid-size, independent). Chart: subsidy per $ welfare gain vs. store volume, cost structure, and quality/variety score.",
        },
        {
          n: 6,
          title: "Instrument comparison at optimal store",
          detail: "For the winning store j*, compare all three instruments at equal total cost. Identify the most efficient delivery mechanism.",
        },
        {
          n: 7,
          title: "Distributional analysis",
          detail: "Break ΔCS down by income quintile. Does the optimal store selection disproportionately benefit low-income households? Compare to an equity-weighted objective.",
        },
      ],
    },
    {
      id: "phase3",
      goal: "Goal 3",
      title: "Phase 3 — Cross-Store Spillovers",
      output: "For each non-subsidized store k: change in traffic ΔQ_k, revenue ΔRev_k, and implied profit change Δπ_k at steady state.",
      color: theme.fill.tertiary,
      steps: [
        {
          n: 1,
          title: "Start from Phase 2 optimal solution",
          detail: "Use the optimal subsidy s* at the selected store j*. The post-subsidy price p_j*_post and updated utility V_ij*_post are already computed.",
        },
        {
          n: 2,
          title: "Recompute market shares for all stores",
          detail: "Hold all other store prices fixed (no rival response). Compute s_ik_post for all k using the updated logit denominator. ΔS_k = S_k_post − S_k_pre.",
        },
        {
          n: 3,
          title: "Compute quantity and revenue changes",
          detail: "ΔQ_k = M · ΔS_k for each k. ΔRev_k = p_k · ΔQ_k. Δπ_k = (p_k − VC_k) · ΔQ_k (only variable cost effect, since FC_k is unchanged).",
        },
        {
          n: 4,
          title: "Identify at-risk stores",
          detail: "Rank stores by |ΔQ_k|. Flag stores where Δπ_k pushes π_k < 0 (the subsidy would cause a rival to be unprofitable). These are 'collateral damage' candidates.",
        },
        {
          n: 5,
          title: "Geographic spillover map",
          detail: "Map ΔQ_k by store location. Identify spatial clusters of impact. Stores geographically closest to j* and serving overlapping census tracts will see largest spillovers.",
        },
        {
          n: 6,
          title: "Compute net social welfare",
          detail: "ΔW_total = ΔCS (consumer gain) + Δπ_j* (subsidized store profit change) + Σ_{k≠j*} Δπ_k (rival profit changes). This is the full social surplus change.",
        },
        {
          n: 7,
          title: "Sensitivity: vary subsidy size and store selection",
          detail: "Re-run spillover analysis for the second- and third-best store selections from Phase 2. Determine whether the optimal-welfare selection is also the least disruptive to rivals.",
        },
      ],
    },
  ];

  return (
    <Stack gap={24}>
      <Stack gap={6}>
        <H2>Step-by-Step Implementation</H2>
        <Text tone="secondary">
          Four phases: one setup phase and one phase per goal. Each phase produces a concrete deliverable that feeds the next.
        </Text>
      </Stack>

      <Row gap={16} wrap align="center">
        {phases.map((p, i) => (
          <div key={p.id} style={{ display: "contents" }}>
            <Row gap={8} align="center">
              <Pill active={p.goal !== "Setup"}>{p.goal}</Pill>
              {i < phases.length - 1 && (
                <Text tone="tertiary" size="small">→</Text>
              )}
            </Row>
          </div>
        ))}
      </Row>

      {phases.map((phase) => (
        <div key={phase.id} style={{ display: "contents" }}>
          <Card collapsible defaultOpen>
            <CardHeader trailing={<Pill size="sm">{phase.goal}</Pill>}>{phase.title}</CardHeader>
            <CardBody>
              <Stack gap={16}>
                <Callout tone="neutral">
                  <Text size="small" weight="semibold">Output: </Text>
                  <Text size="small" as="span" tone="secondary">{phase.output}</Text>
                </Callout>
                <StepList steps={phase.steps} />
              </Stack>
            </CardBody>
          </Card>
        </div>
      ))}

      <Divider />

      <Stack gap={12}>
        <H3>Suggested Tech Stack</H3>
        <Table
          headers={["Task", "Tool", "Notes"]}
          striped
          rows={[
            ["Data assembly & cleaning", "Python (pandas, geopandas)", "ACS via censusdataapi; TIGER shapefiles via geopandas"],
            ["Distance matrix", "OSMnx or Google Maps API", "OSMnx is free; Google Maps for transit travel time"],
            ["MNL / Mixed Logit estimation", "Python (xlogit, pylogit) or R (mlogit)", "xlogit supports GPU-accelerated mixed logit"],
            ["Optimization (Goal 2)", "scipy.optimize.minimize (SLSQP) or PuLP", "SLSQP for continuous; PuLP for integer program"],
            ["Visualization", "matplotlib / seaborn + folium (maps)", "folium for choropleth spillover maps"],
            ["Sensitivity analysis", "Parallel runs with itertools.product", "Grid over θ and β_p scaling; store results in DataFrame"],
          ]}
          columnAlign={["left", "left", "left"]}
        />
      </Stack>
    </Stack>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// ROOT COMPONENT
// ═══════════════════════════════════════════════════════════════════════════
export default function GrocerySubsidyModel() {
  const [tab, setTab] = useState<Tab>("architecture");
  const theme = useHostTheme();

  const tabs: { id: Tab; label: string }[] = [
    { id: "architecture", label: "Problem Architecture" },
    { id: "equations", label: "Equations" },
    { id: "data", label: "Data Sources" },
    { id: "implementation", label: "Implementation" },
  ];

  return (
    <div
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "32px 24px 64px",
        color: theme.text.primary,
      }}
    >
      <Stack gap={28}>
        {/* Header */}
        <Stack gap={8}>
          <Row gap={10} align="center">
            <H1>NYC Municipal Grocery Subsidy — Model Design</H1>
          </Row>
          <Text tone="secondary">
            Optimization framework for allocating a city subsidy across candidate retail food stores in a defined NYC region.
            Decision-maker: NYCEDC / Mayor's Office. Instrument: tax break, rent subsidy, or direct operation.
          </Text>
          <Row gap={16}>
            <Stat value="3" label="Model goals" />
            <Stat value="3" label="Subsidy instruments" />
            <Stat value="MNL" label="Choice model" />
            <Stat value="Static" label="Model type" />
          </Row>
        </Stack>

        <Divider />

        {/* Nav */}
        <Row gap={8} wrap>
          {tabs.map((t) => (
            <span key={t.id} style={{ display: "contents" }}>
              <Pill active={tab === t.id} onClick={() => setTab(t.id)}>
                {t.label}
              </Pill>
            </span>
          ))}
        </Row>

        {/* Content */}
        {tab === "architecture" && <ArchitectureTab />}
        {tab === "equations" && <EquationsTab />}
        {tab === "data" && <DataTab />}
        {tab === "implementation" && <ImplementationTab />}
      </Stack>
    </div>
  );
}
