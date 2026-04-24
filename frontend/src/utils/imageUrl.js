const BACKEND_BASE = "http://127.0.0.1:5000";

export function resolveImageUrl(imageUrl, fallbackText = "Product") {
  if (!imageUrl) {
    return `https://placehold.co/800x600?text=${encodeURIComponent(fallbackText)}`;
  }
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }
  if (imageUrl.startsWith("/")) {
    return `${BACKEND_BASE}${imageUrl}`;
  }
  return imageUrl;
}
