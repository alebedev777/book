import { useEffect, useRef } from "react";
import type { Style } from "./api";
import { styleFace } from "./catalog";
import { stylePreview } from "./previews";

type Props = {
  styles: Style[];
  styleId: string | null;
  onSelect: (id: string) => void;
};

export function StyleGallery({ styles, styleId, onSelect }: Props) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const fromUserScroll = useRef(false);
  const programmatic = useRef(false);

  useEffect(() => {
    const root = scrollerRef.current;
    if (!root || !styleId) return;
    if (fromUserScroll.current) {
      fromUserScroll.current = false;
      return;
    }
    const el = root.querySelector<HTMLElement>(`[data-id="${CSS.escape(styleId)}"]`);
    if (!el) return;
    const left = el.offsetLeft - (root.clientWidth - el.offsetWidth) / 2;
    if (Math.abs(root.scrollLeft - left) < 2) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    programmatic.current = true;
    root.scrollTo({ left, behavior: reduce ? "auto" : "smooth" });
    const done = () => {
      programmatic.current = false;
    };
    root.addEventListener("scrollend", done, { once: true });
    const timer = window.setTimeout(done, reduce ? 0 : 480);
    return () => {
      root.removeEventListener("scrollend", done);
      window.clearTimeout(timer);
    };
  }, [styleId, styles]);

  useEffect(() => {
    const root = scrollerRef.current;
    if (!root) return;
    let frame = 0;
    const release = () => {
      programmatic.current = false;
    };
    const onScroll = () => {
      if (programmatic.current) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const mid = root.scrollLeft + root.clientWidth / 2;
        let bestId: string | null = null;
        let best = Infinity;
        root.querySelectorAll<HTMLElement>(".spread").forEach((el) => {
          const center = el.offsetLeft + el.offsetWidth / 2;
          const dist = Math.abs(center - mid);
          if (dist < best) {
            best = dist;
            bestId = el.dataset.id ?? null;
          }
        });
        if (bestId && bestId !== styleId) {
          fromUserScroll.current = true;
          onSelect(bestId);
        }
      });
    };
    root.addEventListener("pointerdown", release);
    root.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      root.removeEventListener("pointerdown", release);
      root.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, [onSelect, styleId]);

  const current = styles.find((style) => style.id === styleId) ?? styles[0];
  const face = current ? styleFace(current.id) : null;

  return (
    <div className="gallery">
      <div className="snap" ref={scrollerRef}>
        {styles.map((style) => {
          const preview = stylePreview(style.id);
          const selected = style.id === styleId;
          return (
            <article
              key={style.id}
              className={`spread ${selected ? "on" : ""}`}
              data-id={style.id}
            >
              <div className="spread-art">
                {preview ? (
                  <img src={preview} alt="" draggable={false} />
                ) : (
                  <div className="art-fallback" />
                )}
              </div>
            </article>
          );
        })}
      </div>
      {current && face && (
        <div className="style-caption" key={current.id}>
          <span className="mood">{face.mood}</span>
          <h2>{current.title_ru}</h2>
          <p>{face.line}</p>
        </div>
      )}

      <div className="rail" role="listbox" aria-label="Все стили">
        {styles.map((style) => {
          const preview = stylePreview(style.id);
          const selected = style.id === styleId;
          return (
            <button
              key={style.id}
              type="button"
              role="option"
              aria-selected={selected}
              className={`thumb ${selected ? "on" : ""}`}
              onClick={() => onSelect(style.id)}
            >
              <span className="thumb-art">
                {preview ? <img src={preview} alt="" draggable={false} /> : null}
              </span>
              <span className="thumb-name">{style.title_ru}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
