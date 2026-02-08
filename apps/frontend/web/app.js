const GENRES = [
  "Drama", "Comedy", "Documentary", "Romance", "Action", "Crime",
  "Thriller", "Horror", "Adventure", "Mystery", "Family", "Biography",
  "Fantasy", "History", "Music", "Sci-Fi", "Musical", "War",
  "Animation", "Western", "Sport", "Adult"
];

function escapeHtml(text) {
  return $("<div>").text(text || "").html();
}

function setTab(tab) {
  const normalized = ["predict", "similar", "model"].includes(tab) ? tab : "predict";
  const isPredict = normalized === "predict";
  const isSimilar = normalized === "similar";
  const isModel = normalized === "model";

  $("#tab-predict").toggleClass("active", isPredict).attr("aria-selected", String(isPredict));
  $("#tab-similar").toggleClass("active", isSimilar).attr("aria-selected", String(isSimilar));
  $("#tab-model").toggleClass("active", isModel).attr("aria-selected", String(isModel));

  $("#page-predict").toggleClass("active", isPredict);
  $("#page-similar").toggleClass("active", isSimilar);
  $("#page-model").toggleClass("active", isModel);

  const url = new URL(window.location.href);
  url.searchParams.set("tab", normalized);
  window.history.replaceState({}, "", url);
}

function showError(fieldId, message) {
  $(`#error-${fieldId}`).text(message || "");
}

function clearPredictErrors() {
  showError("startYear", "");
  showError("runtimeMinutes", "");
  showError("budget", "");
  showError("genres", "");
  showError("overview", "");
}

function validatePredictForm() {
  clearPredictErrors();
  const errors = [];
  const year = Number($("#startYear").val());
  const runtime = Number($("#runtimeMinutes").val());
  const budget = Number($("#budget").val() || 0);
  const genres = $("#genres").val() || [];
  const overview = ($("#overview").val() || "").trim();

  if (!Number.isFinite(year) || year < 1900 || year > 2030) {
    showError("startYear", "Enter a valid year between 1900 and 2030.");
    errors.push("#startYear");
  }
  if (!Number.isFinite(runtime) || runtime < 1 || runtime > 500) {
    showError("runtimeMinutes", "Enter a runtime between 1 and 500.");
    errors.push("#runtimeMinutes");
  }
  if (!Number.isFinite(budget) || budget < 0) {
    showError("budget", "Budget cannot be negative.");
    errors.push("#budget");
  }
  if (genres.length === 0) {
    showError("genres", "Select at least one genre.");
    errors.push("#genres");
  }
  if (!overview) {
    showError("overview", "Plot overview is required.");
    errors.push("#overview");
  }
  return errors;
}

function renderCards(targetId, results) {
  const target = $(targetId);
  target.empty();
  if (!results || results.length === 0) {
    target.append("<p class='lede'>No results found.</p>");
    return;
  }
  results.forEach((m) => {
    const imdbUrl = m.imdb_id ? `https://www.imdb.com/title/${m.imdb_id}/` : null;
    const title = escapeHtml(m.title || "Unknown");
    const genres = Array.isArray(m.genres) ? m.genres.join(", ") : (m.genres || "");
    const score = Number(m.vote_average || 0).toFixed(1);
    const overview = escapeHtml((m.overview || "").slice(0, 180));
    target.append(`
      <article class="card">
        <h4>${imdbUrl ? `<a href="${imdbUrl}" target="_blank" rel="noreferrer noopener">${title}</a>` : title}</h4>
        <p class="meta">IMDb: ${score} | ${escapeHtml(genres)}</p>
        <p class="overview">${overview}</p>
      </article>
    `);
  });
}

async function updateHealth() {
  const healthText = $("#health-text");
  if (!healthText.length) return;
  try {
    await $.getJSON("/health");
    healthText.text("API status: online.");
  } catch (_err) {
    healthText.text("API status: unavailable. Please retry in a moment.");
  }
}

async function runPrediction(event) {
  event.preventDefault();
  const errors = validatePredictForm();
  if (errors.length) {
    $(errors[0]).trigger("focus");
    return;
  }

  const btn = $("#predict-btn");
  btn.prop("disabled", true).text("Predicting…");
  try {
    const params = {
      startYear: $("#startYear").val(),
      runtimeMinutes: $("#runtimeMinutes").val(),
      genres: ($("#genres").val() || []).join(","),
      overview: ($("#overview").val() || "").trim(),
      isAdult: $("#isAdult").is(":checked") ? 1 : 0
    };
    const budget = Number($("#budget").val() || 0);
    if (budget > 0) params.budget = budget;

    const prediction = await $.getJSON("/predict", params);
    $("#rating").text(`${Number(prediction.predicted_rating).toFixed(2)} / 10`);
    $("#results").removeClass("hidden");

    try {
      const similar = await $.getJSON("/similar-film", { query: params.overview, k: 4 });
      renderCards("#similar-grid", similar.results);
    } catch (_err) {
      renderCards("#similar-grid", []);
    }
  } catch (err) {
    const message = err?.responseJSON?.detail || "Prediction failed. Please try again.";
    showError("overview", message);
    $("#overview").trigger("focus");
  } finally {
    btn.prop("disabled", false).text("Predict Rating");
  }
}

async function runSimilarOnly() {
  const query = ($("#similar-query").val() || "").trim();
  showError("similar-query", "");
  if (!query) {
    showError("similar-query", "Enter a query before searching.");
    $("#similar-query").trigger("focus");
    return;
  }

  const btn = $("#similar-btn");
  btn.prop("disabled", true).text("Searching…");
  try {
    const similar = await $.getJSON("/similar-film", { query, k: 8 });
    renderCards("#similar-only-grid", similar.results);
  } catch (err) {
    const message = err?.responseJSON?.detail || "Search failed. Please try again.";
    showError("similar-query", message);
  } finally {
    btn.prop("disabled", false).text("Find Similar Films");
  }
}

const EXAMPLES = [
  {
    startYear: 1997, budget: 200000000, runtimeMinutes: 195, isAdult: false,
    genres: ["Drama", "Romance"],
    overview: "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic."
  },
  {
    startYear: 1999, budget: 63000000, runtimeMinutes: 136, isAdult: false,
    genres: ["Action", "Sci-Fi"],
    overview: "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers."
  },
  {
    startYear: 2008, budget: 180000000, runtimeMinutes: 98, isAdult: false,
    genres: ["Animation", "Adventure", "Family", "Sci-Fi"],
    overview: "In the distant future, a small waste-collecting robot inadvertently embarks on a space journey that will ultimately decide the fate of mankind."
  }
];

function applyExample(ex) {
  $("#startYear").val(ex.startYear);
  $("#budget").val(ex.budget);
  $("#runtimeMinutes").val(ex.runtimeMinutes);
  $("#isAdult").prop("checked", ex.isAdult);
  $("#genres").val(ex.genres).trigger("change");
  $("#overview").val(ex.overview);
}

$(function () {
  GENRES.forEach((genre) => $("#genres").append(`<option value="${genre}">${genre}</option>`));
  $("#genres").select2({
    placeholder: "Select genres",
    width: "100%",
    closeOnSelect: false,
    dropdownParent: $("body")
  });

  applyExample(EXAMPLES[Math.floor(Math.random() * EXAMPLES.length)]);

  $("#tab-predict").on("click", () => setTab("predict"));
  $("#tab-similar").on("click", () => setTab("similar"));
  $("#tab-model").on("click", () => setTab("model"));

  $("#predict-form").on("submit", runPrediction);
  $("#similar-btn").on("click", runSimilarOnly);

  $(".step").on("click", function () {
    const target = $($(this).data("target"));
    const step = Number($(this).data("step")) || 1;
    const min = Number(target.attr("min"));
    const max = Number(target.attr("max"));
    let next = Number(target.val() || 0) + step;
    if (!Number.isNaN(min)) next = Math.max(min, next);
    if (!Number.isNaN(max)) next = Math.min(max, next);
    target.val(next);
  });

  const tabFromUrl = new URL(window.location.href).searchParams.get("tab");
  setTab(tabFromUrl || "predict");
  updateHealth();
});
