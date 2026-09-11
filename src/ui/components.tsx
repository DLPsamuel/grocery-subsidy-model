import {
  createContext,
  useContext,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { useHostTheme } from "./theme";

export function mergeStyle(
  base: CSSProperties,
  override?: CSSProperties,
): CSSProperties {
  return { ...base, ...override };
}

export function Stack({
  children,
  gap = 0,
  style,
}: {
  children?: ReactNode;
  gap?: number;
  style?: CSSProperties;
}) {
  return (
    <div
      style={mergeStyle(
        { display: "flex", flexDirection: "column", gap },
        style,
      )}
    >
      {children}
    </div>
  );
}

export function Row({
  children,
  gap = 0,
  align = "stretch",
  justify = "start",
  wrap = false,
  style,
}: {
  children?: ReactNode;
  gap?: number;
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "space-between";
  wrap?: boolean;
  style?: CSSProperties;
}) {
  const alignMap = {
    start: "flex-start",
    center: "center",
    end: "flex-end",
    stretch: "stretch",
  } as const;
  const justifyMap = {
    start: "flex-start",
    center: "center",
    end: "flex-end",
    "space-between": "space-between",
  } as const;
  return (
    <div
      style={mergeStyle(
        {
          display: "flex",
          flexDirection: "row",
          gap,
          alignItems: alignMap[align],
          justifyContent: justifyMap[justify],
          flexWrap: wrap ? "wrap" : "nowrap",
        },
        style,
      )}
    >
      {children}
    </div>
  );
}

export function Grid({
  children,
  columns,
  gap = 0,
  align = "stretch",
  style,
}: {
  children?: ReactNode;
  columns: number | string;
  gap?: number;
  align?: "start" | "center" | "end" | "stretch";
  style?: CSSProperties;
}) {
  const alignMap = {
    start: "start",
    center: "center",
    end: "end",
    stretch: "stretch",
  } as const;
  return (
    <div
      style={mergeStyle(
        {
          display: "grid",
          gridTemplateColumns:
            typeof columns === "number"
              ? `repeat(${columns}, minmax(0, 1fr))`
              : columns,
          gap,
          alignItems: alignMap[align],
        },
        style,
      )}
    >
      {children}
    </div>
  );
}

export function Divider({ style }: { style?: CSSProperties }) {
  const theme = useHostTheme();
  return (
    <hr
      style={mergeStyle(
        {
          border: "none",
          borderTop: `1px solid ${theme.stroke.tertiary}`,
          margin: 0,
          width: "100%",
        },
        style,
      )}
    />
  );
}

export function Spacer() {
  return <div style={{ flex: 1 }} />;
}

export function H1({
  children,
  style,
}: {
  children?: ReactNode;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  return (
    <h1
      style={mergeStyle(
        {
          margin: 0,
          fontSize: 24,
          lineHeight: "30px",
          fontWeight: 600,
          color: theme.text.primary,
        },
        style,
      )}
    >
      {children}
    </h1>
  );
}

export function H2({
  children,
  style,
}: {
  children?: ReactNode;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  return (
    <h2
      style={mergeStyle(
        {
          margin: 0,
          fontSize: 18,
          lineHeight: "24px",
          fontWeight: 600,
          color: theme.text.primary,
        },
        style,
      )}
    >
      {children}
    </h2>
  );
}

export function H3({
  children,
  style,
}: {
  children?: ReactNode;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  return (
    <h3
      style={mergeStyle(
        {
          margin: 0,
          fontSize: 16,
          lineHeight: "22px",
          fontWeight: 600,
          color: theme.text.primary,
        },
        style,
      )}
    >
      {children}
    </h3>
  );
}

const weightMap = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export function Text({
  children,
  tone = "primary",
  size = "body",
  as,
  weight = "normal",
  italic,
  style,
}: {
  children?: ReactNode;
  tone?: "primary" | "secondary" | "tertiary" | "quaternary";
  size?: "body" | "small";
  as?: "p" | "span";
  weight?: "normal" | "medium" | "semibold" | "bold";
  italic?: boolean;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  const Tag = as ?? "p";
  return (
    <Tag
      style={mergeStyle(
        {
          margin: 0,
          fontSize: size === "small" ? 12 : 14,
          lineHeight: size === "small" ? "16px" : "20px",
          fontWeight: weightMap[weight],
          fontStyle: italic ? "italic" : undefined,
          color: theme.text[tone],
        },
        style,
      )}
    >
      {children}
    </Tag>
  );
}

export function Code({
  children,
  style,
}: {
  children?: ReactNode;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  return (
    <code
      style={mergeStyle(
        {
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          fontSize: "0.92em",
          background: theme.fill.secondary,
          border: `1px solid ${theme.stroke.tertiary}`,
          borderRadius: 4,
          padding: "1px 5px",
          color: theme.text.primary,
        },
        style,
      )}
    >
      {children}
    </code>
  );
}

type CardContextValue = {
  collapsible: boolean;
  open: boolean;
  toggle: () => void;
  size: "base" | "lg";
};

const CardContext = createContext<CardContextValue | null>(null);

export function Card({
  children,
  variant = "default",
  size = "base",
  collapsible = false,
  defaultOpen = true,
  open: openProp,
  onOpenChange,
  style,
}: {
  children?: ReactNode;
  variant?: "default" | "borderless";
  size?: "base" | "lg";
  stickyHeader?: boolean;
  collapsible?: boolean;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen);
  const open = openProp ?? uncontrolledOpen;
  const toggle = () => {
    const next = !open;
    if (openProp === undefined) setUncontrolledOpen(next);
    onOpenChange?.(next);
  };

  return (
    <CardContext.Provider value={{ collapsible, open, toggle, size }}>
      <div
        style={mergeStyle(
          {
            background: theme.bg.elevated,
            border:
              variant === "borderless"
                ? "none"
                : `1px solid ${theme.stroke.tertiary}`,
            borderRadius: variant === "borderless" ? 0 : 8,
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
            height: "100%",
          },
          style,
        )}
      >
        {children}
      </div>
    </CardContext.Provider>
  );
}

export function CardHeader({
  children,
  trailing,
  style,
}: {
  children?: ReactNode;
  trailing?: ReactNode;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  const ctx = useContext(CardContext);
  const height = ctx?.size === "lg" ? 32 : 28;

  const content = (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
        {ctx?.collapsible && (
          <span
            style={{
              display: "inline-flex",
              transform: ctx.open ? "rotate(90deg)" : "rotate(0deg)",
              transition: "transform 0.15s ease",
              fontSize: 10,
              color: theme.text.tertiary,
            }}
            aria-hidden
          >
            ▸
          </span>
        )}
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: theme.text.primary,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {children}
        </span>
      </div>
      {trailing && <div style={{ flexShrink: 0 }}>{trailing}</div>}
    </>
  );

  if (ctx?.collapsible) {
    return (
      <button
        type="button"
        onClick={ctx.toggle}
        style={mergeStyle(
          {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 8,
            height,
            padding: "0 12px",
            background: theme.fill.tertiary,
            border: "none",
            borderBottom: ctx.open
              ? `1px solid ${theme.stroke.tertiary}`
              : "none",
            cursor: "pointer",
            width: "100%",
            textAlign: "left",
            fontFamily: "inherit",
          },
          style,
        )}
      >
        {content}
      </button>
    );
  }

  return (
    <div
      style={mergeStyle(
        {
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          height,
          padding: "0 12px",
          background: theme.fill.tertiary,
          borderBottom: `1px solid ${theme.stroke.tertiary}`,
        },
        style,
      )}
    >
      {content}
    </div>
  );
}

export function CardBody({
  children,
  style,
}: {
  children?: ReactNode;
  style?: CSSProperties;
}) {
  const ctx = useContext(CardContext);
  if (ctx?.collapsible && !ctx.open) return null;
  return (
    <div style={mergeStyle({ padding: 12 }, style)}>{children}</div>
  );
}

export function Pill({
  children,
  active = false,
  size = "md",
  disabled,
  title,
  style,
  onClick,
}: {
  children?: ReactNode;
  active?: boolean;
  tone?: string;
  size?: "sm" | "md";
  leadingContent?: ReactNode;
  keyboardHint?: string;
  disabled?: boolean;
  title?: string;
  style?: CSSProperties;
  onClick?: () => void;
}) {
  const theme = useHostTheme();
  const isButton = Boolean(onClick);
  const Tag = isButton ? "button" : "span";
  const sm = size === "sm";

  return (
    <Tag
      type={isButton ? "button" : undefined}
      title={title}
      disabled={disabled}
      onClick={onClick}
      style={mergeStyle(
        {
          display: "inline-flex",
          alignItems: "center",
          gap: 4,
          borderRadius: 9999,
          border: sm
            ? "none"
            : `1px solid ${active ? theme.accent.primary : theme.stroke.secondary}`,
          background: active ? theme.accent.primary : theme.fill.tertiary,
          color: active ? theme.text.onAccent : theme.text.secondary,
          fontSize: sm ? 11 : 12,
          fontWeight: 500,
          lineHeight: 1,
          padding: sm ? "2px 6px" : "6px 12px",
          cursor: isButton && !disabled ? "pointer" : "default",
          fontFamily: "inherit",
          opacity: disabled ? 0.5 : 1,
        },
        style,
      )}
    >
      {children}
    </Tag>
  );
}

export function Stat({
  value,
  label,
  tone,
  style,
}: {
  value: ReactNode;
  label: string;
  tone?: "success" | "danger" | "warning" | "info";
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  const toneColor =
    tone === "success"
      ? theme.diff.added
      : tone === "danger"
        ? theme.diff.removed
        : tone === "warning"
          ? theme.diff.modified
          : tone === "info"
            ? theme.accent.primary
            : theme.text.primary;

  return (
    <div style={mergeStyle({ display: "flex", flexDirection: "column", gap: 2 }, style)}>
      <div style={{ fontSize: 20, fontWeight: 600, color: toneColor, lineHeight: 1.2 }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: theme.text.tertiary }}>{label}</div>
    </div>
  );
}

export function Callout({
  children,
  tone = "neutral",
  title,
  style,
}: {
  children?: ReactNode;
  tone?: "info" | "success" | "warning" | "danger" | "neutral";
  title?: ReactNode;
  icon?: ReactNode;
  style?: CSSProperties;
}) {
  const theme = useHostTheme();
  const borderColor =
    tone === "info"
      ? theme.accent.primary
      : tone === "success"
        ? theme.diff.added
        : tone === "warning"
          ? theme.diff.modified
          : tone === "danger"
            ? theme.diff.removed
            : theme.stroke.secondary;

  return (
    <div
      style={mergeStyle(
        {
          border: `1px solid ${theme.stroke.tertiary}`,
          borderLeft: `3px solid ${borderColor}`,
          borderRadius: 6,
          background: theme.fill.tertiary,
          padding: "10px 12px",
        },
        style,
      )}
    >
      {title && (
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: theme.text.primary,
            marginBottom: 4,
          }}
        >
          {title}
        </div>
      )}
      <div style={{ fontSize: 13, color: theme.text.secondary, lineHeight: 1.45 }}>
        {children}
      </div>
    </div>
  );
}

const rowToneColors: Record<string, string> = {
  success: "#1e8e3e",
  danger: "#d93025",
  warning: "#e37400",
  info: "#0b57d0",
  neutral: "#8a8a8a",
};

export function Table({
  headers,
  rows,
  columnAlign,
  rowTone,
  framed = true,
  striped,
  stickyHeader,
  style,
  emptyMessage,
}: {
  headers: ReactNode[];
  rows: ReactNode[][];
  columnAlign?: Array<"left" | "center" | "right" | undefined>;
  rowTone?: Array<"success" | "danger" | "warning" | "info" | "neutral" | undefined>;
  framed?: boolean;
  striped?: boolean;
  stickyHeader?: boolean;
  style?: CSSProperties;
  emptyMessage?: ReactNode;
}) {
  const theme = useHostTheme();

  return (
    <div
      style={mergeStyle(
        {
          border: framed ? `1px solid ${theme.stroke.tertiary}` : "none",
          borderRadius: framed ? 8 : 0,
          overflow: "auto",
          width: "100%",
        },
        style,
      )}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 13,
        }}
      >
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th
                key={i}
                style={{
                  textAlign: columnAlign?.[i] ?? "left",
                  padding: "8px 10px",
                  fontWeight: 600,
                  fontSize: 12,
                  color: theme.text.secondary,
                  background: theme.fill.tertiary,
                  borderBottom: `1px solid ${theme.stroke.tertiary}`,
                  position: stickyHeader ? "sticky" : undefined,
                  top: stickyHeader ? 0 : undefined,
                  zIndex: stickyHeader ? 1 : undefined,
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={headers.length}
                style={{ padding: 12, color: theme.text.tertiary }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row, ri) => (
              <tr
                key={ri}
                style={{
                  background:
                    striped && ri % 2 === 1 ? theme.fill.quaternary : undefined,
                }}
              >
                {headers.map((_, ci) => {
                  const cell = row[ci] ?? null;
                  const tone = rowTone?.[ri];
                  return (
                    <td
                      key={ci}
                      style={{
                        textAlign: columnAlign?.[ci] ?? "left",
                        padding: "8px 10px",
                        borderBottom: `1px solid ${theme.stroke.tertiary}`,
                        color: theme.text.primary,
                        verticalAlign: "top",
                      }}
                    >
                      {ci === 0 && tone ? (
                        <span style={{ display: "inline-flex", gap: 8, alignItems: "flex-start" }}>
                          <span
                            style={{
                              width: 7,
                              height: 7,
                              borderRadius: "50%",
                              background: rowToneColors[tone],
                              marginTop: 5,
                              flexShrink: 0,
                            }}
                          />
                          <span>{cell}</span>
                        </span>
                      ) : (
                        cell
                      )}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
