// Server sends UTC ISO strings ending in "Z"; the browser shows them in the user's local timezone.
export const fmt = (iso) => (iso ? new Date(iso).toLocaleString() : "-");
export const bytes = (n) => (n > 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);
export const isPast = (iso) => new Date(iso) < new Date();
