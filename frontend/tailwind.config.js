export default {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                surface: {
                    0: "rgb(var(--surface-0) / <alpha-value>)",
                    1: "rgb(var(--surface-1) / <alpha-value>)",
                    2: "rgb(var(--surface-2) / <alpha-value>)",
                },
                ink: {
                    1: "rgb(var(--ink-1) / <alpha-value>)",
                    2: "rgb(var(--ink-2) / <alpha-value>)",
                    3: "rgb(var(--ink-3) / <alpha-value>)",
                },
                accent: {
                    DEFAULT: "rgb(var(--accent) / <alpha-value>)",
                    soft: "rgb(var(--accent-soft) / <alpha-value>)",
                },
                success: "rgb(var(--success) / <alpha-value>)",
                warning: "rgb(var(--warning) / <alpha-value>)",
                danger: "rgb(var(--danger) / <alpha-value>)",
            },
            borderRadius: {
                panel: "var(--radius-panel)",
            },
            boxShadow: {
                panel: "0 12px 30px rgba(15, 23, 42, 0.08)",
            },
        },
    },
    plugins: [],
};
