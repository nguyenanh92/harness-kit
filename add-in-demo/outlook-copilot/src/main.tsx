import "./index.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./app";
import { OfficeProvider } from "./office-context";

/* Office.js must initialise before any Office API call.
   Rendering is deferred until the host signals readiness. */
Office.onReady(() => {
  const root = document.getElementById("root")!;
  createRoot(root).render(
    <StrictMode>
      <OfficeProvider>
        <App />
      </OfficeProvider>
    </StrictMode>
  );
});
