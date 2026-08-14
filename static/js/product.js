(() => {
  "use strict";

  const body = document.body;
  const path = window.location.pathname;
  const isMarketing = path === "/";
  const isAuth = ["/login", "/signup", "/onboarding"].includes(path);
  body.classList.add(isMarketing ? "marketing-page" : isAuth ? "product-auth" : "product-app");
  body.dataset.productPage = path.includes("path-view") ? "path-view"
    : path === "/dashboard" ? "dashboard"
    : isMarketing ? "marketing"
    : isAuth ? "auth"
    : "standard";
  body.dataset.productRoute = path.replace(/^\/+|\/+$/g, "").replace(/[^a-z0-9]+/gi, "-") || "home";

  const main = document.querySelector("main");
  if (main && !main.id) main.id = "main-content";
  if (main) {
    const skip = document.createElement("a");
    skip.className = "skip-link";
    skip.href = `#${main.id}`;
    skip.textContent = "Skip to main content";
    body.prepend(skip);
  }

  const normalizedPath = (value) => value.replace(/\/$/, "") || "/";
  document.querySelectorAll("header a[href]").forEach((link) => {
    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href === "/logout") return;
    const linkPath = normalizedPath(new URL(link.href, window.location.origin).pathname);
    const currentPath = normalizedPath(path);
    const exact = linkPath === currentPath;
    const sectionMatch = linkPath !== "/dashboard" && linkPath !== "/" && currentPath.startsWith(`${linkPath}/`);
    if (exact || sectionMatch) {
      link.setAttribute("aria-current", "page");
      link.classList.add("active");
    }
  });

  const header = document.querySelector("header");
  const desktopNav = header?.querySelector("nav");
  if (header && desktopNav && desktopNav.querySelectorAll("a").length > 1) {
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "mobile-nav-trigger";
    trigger.setAttribute("aria-label", "Open navigation");
    trigger.setAttribute("aria-expanded", "false");
    trigger.innerHTML = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg>';

    const panel = document.createElement("nav");
    panel.className = "mobile-nav-panel";
    panel.id = "mobile-navigation";
    panel.setAttribute("aria-label", "Mobile navigation");
    panel.dataset.open = "false";
    trigger.setAttribute("aria-controls", panel.id);

    const seen = new Set();
    const headerLinks = [...desktopNav.querySelectorAll("a"), ...header.querySelectorAll("a")];
    headerLinks.forEach((link) => {
      const href = link.getAttribute("href");
      if (!href || seen.has(href)) return;
      seen.add(href);
      const clone = link.cloneNode(true);
      clone.removeAttribute("class");
      panel.appendChild(clone);
    });

    const anchor = header.querySelector(":scope > div") || header;
    anchor.appendChild(trigger);
    header.after(panel);

    const close = () => {
      panel.dataset.open = "false";
      trigger.setAttribute("aria-expanded", "false");
      trigger.setAttribute("aria-label", "Open navigation");
    };
    trigger.addEventListener("click", () => {
      const willOpen = panel.dataset.open !== "true";
      panel.dataset.open = String(willOpen);
      trigger.setAttribute("aria-expanded", String(willOpen));
      trigger.setAttribute("aria-label", willOpen ? "Close navigation" : "Open navigation");
    });
    panel.addEventListener("click", (event) => {
      if (event.target.closest("a")) close();
    });
    document.addEventListener("click", (event) => {
      if (!panel.contains(event.target) && !trigger.contains(event.target)) close();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
  }

  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const wrapper = document.createElement("div");
    wrapper.className = "password-field";
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "password-toggle";
    toggle.textContent = "Show";
    toggle.setAttribute("aria-label", "Show password");
    toggle.addEventListener("click", () => {
      const visible = input.type === "text";
      input.type = visible ? "password" : "text";
      toggle.textContent = visible ? "Show" : "Hide";
      toggle.setAttribute("aria-label", visible ? "Show password" : "Hide password");
    });
    wrapper.appendChild(toggle);
  });

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", () => {
      if (!form.checkValidity() || form.dataset.noLoading === "true") return;
      const button = form.querySelector('button[type="submit"], input[type="submit"]');
      if (!button) return;
      button.classList.add("is-submitting");
      button.setAttribute("aria-busy", "true");
    });
  });

  document.querySelectorAll('a[target="_blank"]').forEach((link) => {
    const rel = new Set((link.getAttribute("rel") || "").split(/\s+/).filter(Boolean));
    rel.add("noopener");
    rel.add("noreferrer");
    link.setAttribute("rel", [...rel].join(" "));
  });

  const toastRegion = document.createElement("div");
  toastRegion.className = "product-toast-region";
  toastRegion.setAttribute("aria-live", "polite");
  toastRegion.setAttribute("aria-atomic", "true");
  body.appendChild(toastRegion);

  window.menticsToast = (message) => {
    if (!message) return;
    const toast = document.createElement("div");
    toast.className = "product-toast";
    toast.textContent = message;
    toastRegion.appendChild(toast);
    window.setTimeout(() => toast.remove(), 4200);
  };

  /* Progressive visual layer. These elements are decorative and never own app state. */
  const progress = document.createElement("div");
  progress.className = "mentics-scroll-progress";
  progress.setAttribute("aria-hidden", "true");
  body.appendChild(progress);

  const updateScrollProgress = () => {
    const available = document.documentElement.scrollHeight - window.innerHeight;
    const amount = available > 0 ? Math.min(window.scrollY / available, 1) : 0;
    progress.style.transform = `scaleX(${amount})`;
  };
  updateScrollProgress();
  window.addEventListener("scroll", updateScrollProgress, { passive: true });

  if (isMarketing) {
    const hero = main?.querySelector(":scope > section:first-child");
    if (hero) {
      hero.classList.add("mentics-landing-hero");
    }

    main?.querySelectorAll(":scope > section").forEach((section, index) => {
      section.style.setProperty("--section-index", index);
    });

    document.querySelectorAll(".glass-card, .dark-bento, details").forEach((element, index) => {
      element.style.setProperty("--card-index", index % 6);
    });

    const marketingHeader = document.querySelector("body.marketing-page > header");
    const updateHeader = () => marketingHeader?.classList.toggle("is-scrolled", window.scrollY > 24);
    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
  } else {
    const cardTones = ["paper", "lavender", "sky", "mint", "peach"];
    document.querySelectorAll(".card, .bento-card, .glass-card").forEach((card, index) => {
      card.style.setProperty("--card-index", index % 8);
      if (!card.classList.contains("hero-card")) card.dataset.cardTone = cardTones[index % cardTones.length];
    });

    if (body.dataset.productPage === "dashboard") {
      main?.querySelector(":scope > div:first-child")?.classList.add("mentics-dashboard-hero");
      main?.querySelector(":scope > .grid")?.classList.add("mentics-dashboard-grid");
    }

    if (body.dataset.productPage === "path-view") {
      const panels = main?.querySelectorAll(":scope > .grid > .card");
      panels?.[0]?.classList.add("mentics-chat-panel");
      panels?.[1]?.classList.add("mentics-path-panel");
    }
  }

})();
