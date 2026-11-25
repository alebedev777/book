import { mockTelegramEnv } from "@telegram-apps/sdk-react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

if (import.meta.env.DEV && !window.Telegram?.WebApp?.initData) {
  mockTelegramEnv({
  themeParams: {
    bgColor: "#17212b",
    textColor: "#f5f5f5",
    hintColor: "#708499",
    linkColor: "#6ab3f3",
    buttonColor: "#5288c1",
    buttonTextColor: "#ffffff",
    secondaryBgColor: "#232e3c",
  },
  initData: {
    user: {
      id: 900001,
      firstName: "Dev",
      lastName: "User",
      username: "devuser",
    },
    authDate: new Date(),
    hash: "dev-local-preview",
    signature: "dev-local-preview",
  },
  version: "8.0",
  platform: "tdesktop",
});
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);