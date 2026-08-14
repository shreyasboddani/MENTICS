(() => {
  "use strict";

  const blockedTags = new Set([
    "SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED", "FORM", "INPUT",
    "BUTTON", "TEXTAREA", "SELECT", "OPTION", "SVG", "MATH", "META",
    "LINK", "BASE"
  ]);

  const escapeHtml = (value) => {
    const node = document.createElement("div");
    node.textContent = String(value ?? "");
    return node.innerHTML;
  };

  window.renderMenticsMarkdown = (source) => {
    const value = String(source ?? "");
    const rawHtml = window.marked?.parse ? window.marked.parse(value) : escapeHtml(value);
    const template = document.createElement("template");
    template.innerHTML = rawHtml;

    [...template.content.querySelectorAll("*")].forEach((element) => {
      if (blockedTags.has(element.tagName)) {
        element.remove();
        return;
      }

      [...element.attributes].forEach((attribute) => {
        const name = attribute.name.toLowerCase();
        const value = attribute.value.trim();
        if (name.startsWith("on") || name === "style" || name === "srcdoc") {
          element.removeAttribute(attribute.name);
          return;
        }
        if (["href", "src", "xlink:href"].includes(name)) {
          try {
            const parsed = new URL(value, window.location.origin);
            if (!["http:", "https:", "mailto:"].includes(parsed.protocol)) {
              element.removeAttribute(attribute.name);
            }
          } catch {
            element.removeAttribute(attribute.name);
          }
        }
      });

      if (element.tagName === "A") {
        element.target = "_blank";
        element.rel = "noopener noreferrer";
      }
    });

    return template.innerHTML;
  };
})();
