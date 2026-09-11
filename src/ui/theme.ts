export type CanvasTokens = {
  text: {
    primary: string;
    secondary: string;
    tertiary: string;
    quaternary: string;
    link: string;
    onAccent: string;
  };
  bg: {
    editor: string;
    chrome: string;
    elevated: string;
  };
  fill: {
    primary: string;
    secondary: string;
    tertiary: string;
    quaternary: string;
  };
  stroke: {
    primary: string;
    secondary: string;
    tertiary: string;
  };
  accent: {
    primary: string;
    control: string;
  };
  diff: {
    added: string;
    removed: string;
    modified: string;
  };
};

export type CanvasPalette = Record<string, string>;

export type CanvasHostTheme = CanvasTokens & {
  kind: string;
  tokens: CanvasTokens;
  palette: CanvasPalette;
};

const lightTokens: CanvasTokens = {
  text: {
    primary: "#1a1a1a",
    secondary: "#5c5c5c",
    tertiary: "#8a8a8a",
    quaternary: "#a8a8a8",
    link: "#0b57d0",
    onAccent: "#ffffff",
  },
  bg: {
    editor: "#ffffff",
    chrome: "#f5f5f5",
    elevated: "#ffffff",
  },
  fill: {
    primary: "#e8e8e8",
    secondary: "#f0f0f0",
    tertiary: "#f7f7f7",
    quaternary: "#fafafa",
  },
  stroke: {
    primary: "#b0b0b0",
    secondary: "#d0d0d0",
    tertiary: "#e5e5e5",
  },
  accent: {
    primary: "#0b57d0",
    control: "#0b57d0",
  },
  diff: {
    added: "#1e8e3e",
    removed: "#d93025",
    modified: "#e37400",
  },
};

export function useHostTheme(): CanvasHostTheme {
  return {
    kind: "light",
    ...lightTokens,
    tokens: lightTokens,
    palette: {},
  };
}
