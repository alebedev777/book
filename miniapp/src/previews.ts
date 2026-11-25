const modules = import.meta.glob("../data/*.jpeg", {
  eager: true,
  import: "default",
}) as Record<string, string>;

const byId = new Map<string, string>();
for (const [path, url] of Object.entries(modules)) {
  const id = path.split("/").pop()?.replace(/\.jpeg$/, "");
  if (id) byId.set(id, url);
}

export function stylePreview(id: string): string | undefined {
  return byId.get(id);
}
