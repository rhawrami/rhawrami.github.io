const content = window.SITE_CONTENT;

function renderProjects(id, projects, descriptionMode = null) {
  const list = document.getElementById(id);
  if (!list) return;

  projects.forEach((project) => {
    const item = document.createElement("li");
    const link = document.createElement("a");

    link.href = project.url;
    link.textContent = "[link]";
    item.append(`${project.title} `, link);

    if (descriptionMode) {
      const description = document.createElement("p");
      let summaryComplete = false;
      description.className = "project-description";

      project.description.forEach((part) => {
        if (summaryComplete) return;

        if (typeof part === "string") {
          if (descriptionMode === "summary") {
            const boundary = part.search(/[.;]/);
            if (boundary !== -1) {
              description.append(`${part.slice(0, boundary).trimEnd()}.`);
              summaryComplete = true;
              return;
            }
          }

          description.append(part);
          return;
        }

        const inlineLink = document.createElement("a");
        inlineLink.href = part.url;
        inlineLink.textContent = part.text;
        description.append(inlineLink);
      });

      item.append(description);
    }

    list.append(item);
  });
}

function renderMediaList(id, items) {
  const list = document.getElementById(id);
  if (!list) return;

  items.forEach((item) => {
    const listItem = document.createElement("li");

    if (typeof item === "string") {
      listItem.textContent = item;
      list.append(listItem);
      return;
    }

    const link = document.createElement("a");
    const preview = document.createElement("div");

    listItem.className = "media-item";
    link.href = item.url;
    link.textContent = "[link]";
    preview.className = `media-preview media-preview--${item.preview.type}`;

    if (item.preview.type === "book") {
      const image = document.createElement("img");
      const description = document.createElement("p");

      image.src = item.preview.image;
      image.alt = `Cover of ${item.title.replaceAll("`", "")}`;
      image.loading = "lazy";
      description.textContent = item.preview.description;
      preview.append(image, description);
    }

    if (item.preview.type === "spotify") {
      const iframe = document.createElement("iframe");

      iframe.src = item.preview.embedUrl;
      iframe.title = `Spotify embed for ${item.title.replaceAll("`", "")}`;
      iframe.allow = "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture";
      iframe.loading = "lazy";
      iframe.allowFullscreen = true;
      preview.append(iframe);
    }

    link.addEventListener("click", (event) => {
      if (window.matchMedia("(hover: none)").matches && !listItem.classList.contains("preview-open")) {
        event.preventDefault();
        document.querySelectorAll(".media-item.preview-open").forEach((openItem) => {
          openItem.classList.remove("preview-open");
        });
        listItem.classList.add("preview-open");
      }
    });

    listItem.append(`${item.title} by ${item.creator} `, link, preview);
    list.append(listItem);
  });
}

function renderPublications(id, publications) {
  const list = document.getElementById(id);
  if (!list) return;

  publications.forEach((publication) => {
    const listItem = document.createElement("li");
    const link = document.createElement("a");
    const date = document.createElement("time");

    link.href = publication.url;
    link.textContent = "[link]";
    date.className = "publication-date";
    date.textContent = publication.date;

    listItem.append(`${publication.title} `, link, date);
    list.append(listItem);
  });
}

function setupItemToggle(containerId, buttonId, visibleCount) {
  const list = document.getElementById(containerId);
  const button = document.getElementById(buttonId);
  if (!list || !button || list.children.length <= visibleCount) return;

  const additionalItems = [...list.children].slice(visibleCount);
  additionalItems.forEach((item) => {
    item.hidden = true;
  });
  button.hidden = false;

  button.addEventListener("click", () => {
    const isExpanded = button.getAttribute("aria-expanded") === "true";
    additionalItems.forEach((item) => {
      item.hidden = isExpanded;
    });
    button.setAttribute("aria-expanded", String(!isExpanded));
    button.textContent = isExpanded ? "See all" : "Show less";
  });
}

function renderCitations(id, citations) {
  const container = document.getElementById(id);
  if (!container) return;

  const groups = new Map();
  citations.forEach((citation) => {
    citation.cites.forEach((work) => {
      if (!groups.has(work.title)) groups.set(work.title, { work, citations: [] });
      groups.get(work.title).citations.push(citation);
    });
  });

  groups.forEach(({ work, citations: citingWorks }) => {
    const group = document.createElement("section");
    const heading = document.createElement("h3");
    const workLink = document.createElement("a");
    const list = document.createElement("ul");

    group.className = "citation-group";
    workLink.href = work.url;
    workLink.textContent = "[link]";
    heading.append(`${work.title} `, workLink);
    list.className = "citation-list";

    citingWorks.forEach((citation) => {
      const item = document.createElement("li");
      const title = document.createElement("cite");
      const link = document.createElement("a");
      const source = document.createElement("span");

      title.textContent = citation.title;
      link.href = citation.url;
      link.textContent = "[link]";
      source.className = "citation-source";
      source.textContent =
        citation.authors === citation.publisher
          ? citation.publisher
          : `${citation.authors} · ${citation.publisher}`;
      item.append(title, " ", link, source);
      list.append(item);
    });

    group.append(heading, list);
    container.append(group);
  });
}

function renderRandomVisualization() {
  const title = document.getElementById("visualization-title");
  const frame = document.getElementById("visualization-frame");
  if (!title || !frame) return;

  const figures = window.FIGURE_DATA?.figures;
  if (!Array.isArray(figures) || figures.length === 0) {
    title.textContent = "Unable to load a figure.";
    frame.hidden = true;
    return;
  }

  const figure = figures[Math.floor(Math.random() * figures.length)];
  const link = document.createElement("a");
  const isDatawrapper = figure.fig_link.startsWith("https://datawrapper");
  const usesLightTheme =
    isDatawrapper ||
    figure.fig_link.startsWith("https://aibmen") ||
    figure.fig_link.startsWith("https://flo.uri") ||
    figure.fig_link.split(/[?#]/)[0].toLowerCase().endsWith(".svg");

  link.href = figure.fig_article_link;
  link.textContent = "[link]";
  title.append(`From \`${figure.fig_name}\` `, link);
  frame.src = figure.fig_link;
  frame.title = `Figure from ${figure.fig_name}`;

  if (usesLightTheme) {
    document.documentElement.classList.add("light-visualization");
    document.querySelector(".site-logo").src = "./skeleton_dark.png";
  }

  if (isDatawrapper) {
    frame.setAttribute("scrolling", "no");

    window.addEventListener("message", (event) => {
      if (event.source !== frame.contentWindow || typeof event.data !== "object") return;

      const heights = event.data?.["datawrapper-height"];
      if (!heights || typeof heights !== "object") return;

      const chartId = Object.keys(heights).find((id) => frame.src.includes(`/${id}/`));
      const height = Number(heights[chartId]);
      if (Number.isFinite(height) && height > 0) frame.style.height = `${height}px`;
    });
  }
}

function markExternalLinks() {
  document.querySelectorAll("a[href]").forEach((link) => {
    const url = new URL(link.href);
    const isExternal =
      (url.protocol === "http:" || url.protocol === "https:") &&
      url.origin !== window.location.origin;

    if (isExternal) {
      link.target = "_blank";
      link.rel = "noopener";
    }
  });
}

const summary = document.getElementById("summary");
if (summary) summary.textContent = content.summary;

renderProjects("recent-projects", content.projects.slice(0, 3), "summary");
renderProjects("all-projects", content.projects, true);
renderMediaList("reading", content.reading);
renderMediaList("listening", content.listening);
renderPublications("recent-publications", content.publications.slice(0, 3));
renderPublications("all-publications", content.publications);
setupItemToggle("all-publications", "publications-toggle", 6);
renderCitations("citations", content.citations ?? []);
setupItemToggle("citations", "citations-toggle", 6);
renderRandomVisualization();
markExternalLinks();

document.addEventListener("click", (event) => {
  document.querySelectorAll(".media-item.preview-open").forEach((item) => {
    if (!item.contains(event.target)) item.classList.remove("preview-open");
  });
});
