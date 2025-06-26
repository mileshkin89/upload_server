window.addEventListener("DOMContentLoaded", () => {
  // Пример: /images/abc123.jpg → извлечь "abc123.jpg"
  const parts = window.location.pathname.split("/images/");
  const filename = parts.length > 1 ? parts[1] : null;

  if (!filename) {
    console.error("Filename not found in URL");
    return;
  }

  const imgElement = document.getElementById("dynamic-image");
  if (imgElement) {
    imgElement.src = `/images_repo/${encodeURIComponent(filename)}`;
  }
});