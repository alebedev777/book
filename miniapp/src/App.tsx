import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createOrder,
  fetchStyles,
  fetchThemes,
  getOrder,
  type Order,
  type Style,
  type Theme,
} from "./api";
import { FALLBACK_STYLES, FALLBACK_THEMES, themeFace } from "./catalog";
import { ConsentCheckbox } from "./legal/consent";
import { stylePreview } from "./previews";
import { StyleGallery } from "./StyleGallery";
import { getInitData, ready } from "./telegram";
import { ThemeGlyph } from "./ThemeGlyph";

type Step = "theme" | "style" | "child" | "photo" | "confirm" | "wait";

const FLOW: Step[] = ["theme", "style", "child", "photo", "confirm"];
const AGES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"];

const STEP_COPY: Record<Exclude<Step, "wait">, { kicker: string; title: string; lede: string }> = {
  theme: {
    kicker: "Шаг 1 из 5",
    title: "О чём сказка?",
    lede: "Выберите урок, который хотите обсудить с ребёнком. Или опишите свою ситуацию.",
  },
  style: {
    kicker: "Шаг 2 из 5",
    title: "В каком мире?",
    lede: "Листайте. В центре каждого мира стоит ребёнок — в книге на его месте будет ваш.",
  },
  child: {
    kicker: "Шаг 3 из 5",
    title: "Кто герой?",
    lede: "Имя прозвучит в сказке. Возраст помогает подобрать слова.",
  },
  photo: {
    kicker: "Шаг 4 из 5",
    title: "Поставьте ребёнка в кадр",
    lede: "Мир уже выбран. Фото нужно, чтобы герой был похож.",
  },
  confirm: {
    kicker: "Шаг 5 из 5",
    title: "Вот книга",
    lede: "Проверьте обложку. Если что-то не то — вернитесь на шаг назад.",
  },
};

async function compressImage(file: File, maxSide = 1280): Promise<Blob> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale);
  const h = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return file;
  ctx.drawImage(bitmap, 0, 0, w, h);
  return new Promise((resolve, reject) => {
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("blob"))), "image/jpeg", 0.85);
  });
}

function explain(error: unknown): string {
  if (error instanceof Error) {
    if (error.message === "Failed to fetch" || error.message.includes("NetworkError")) {
      return "Не получилось связаться с сервером. Запустите API и попробуйте ещё раз.";
    }
    return error.message;
  }
  return "Ошибка заказа";
}

export function App() {
  const [step, setStep] = useState<Step>("theme");
  const [themes, setThemes] = useState<Theme[]>(FALLBACK_THEMES);
  const [styles, setStyles] = useState<Style[]>(FALLBACK_STYLES);
  const [themeId, setThemeId] = useState<string | null>(null);
  const [customTheme, setCustomTheme] = useState("");
  const [styleId, setStyleId] = useState<string | null>(FALLBACK_STYLES[0]?.id ?? null);
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offlineCatalog, setOfflineCatalog] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);

  const initData = useMemo(() => getInitData(), []);

  useEffect(() => {
    ready();
    Promise.all([fetchThemes(), fetchStyles()])
      .then(([nextThemes, nextStyles]) => {
        if (nextThemes.length) setThemes(nextThemes);
        if (nextStyles.length) setStyles(nextStyles);
        setOfflineCatalog(false);
      })
      .catch(() => setOfflineCatalog(true));
  }, []);

  useEffect(() => {
    if (!photo) {
      setPhotoUrl(null);
      return;
    }
    const url = URL.createObjectURL(photo);
    setPhotoUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  const pollOrder = useCallback(
    (id: string) => {
      const timer = setInterval(async () => {
        try {
          const next = await getOrder(id, initData);
          setOrder(next);
          if (next.status === "done" || next.status === "failed") clearInterval(timer);
        } catch {
          /* retry */
        }
      }, 2500);
      return () => clearInterval(timer);
    },
    [initData]
  );

  useEffect(() => {
    if (!order?.id || order.status === "done" || order.status === "failed") return;
    return pollOrder(order.id);
  }, [order?.id, order?.status, pollOrder]);

  const themeTitle = themeId
    ? themes.find((theme) => theme.id === themeId)?.title_ru
    : customTheme.trim();
  const styleTitle = styles.find((style) => style.id === styleId)?.title_ru;
  const preview = styleId ? stylePreview(styleId) : undefined;

  const canThemeNext = themeId !== null || customTheme.trim().length >= 3;
  const canStyleNext = styleId !== null;
  const canChildNext = childName.trim().length >= 2;
  const canPhotoNext = photo !== null && consent;
  const canAdvance =
    (step === "theme" && canThemeNext) ||
    (step === "style" && canStyleNext) ||
    (step === "child" && canChildNext) ||
    (step === "photo" && canPhotoNext) ||
    step === "confirm";

  function choosePhoto(file: File | null) {
    setPhoto(file);
  }

  function goBack() {
    const index = FLOW.indexOf(step);
    if (index > 0) setStep(FLOW[index - 1]);
    setError(null);
  }

  async function submit() {
    if (!styleId || !photo || !consent) return;
    if (!initData) {
      setError("Откройте приложение из Telegram или задайте VITE_DEV_INIT_DATA для разработки.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const compressed = await compressImage(photo);
      const form = new FormData();
      form.append("init_data", initData);
      form.append("style_id", styleId);
      form.append("child_name", childName.trim());
      if (childAge) form.append("child_age", childAge);
      if (themeId) form.append("theme_id", themeId);
      if (customTheme.trim()) form.append("custom_theme", customTheme.trim());
      form.append("consent", consent ? "true" : "false");
      form.append("photo", compressed, "photo.jpg");

      const created = await createOrder(form);
      setStep("wait");
      setOrder({
        id: created.id,
        status: created.status,
        progress_percent: 0,
      });
    } catch (e) {
      setError(explain(e));
    } finally {
      setLoading(false);
    }
  }

  function goNext() {
    if (step === "confirm") {
      void submit();
      return;
    }
    const index = FLOW.indexOf(step);
    if (index >= 0 && canAdvance) setStep(FLOW[index + 1]);
  }

  const copy = step === "wait" ? null : STEP_COPY[step];

  return (
    <div className="app">
      <header className="top">
        <p className="brand">Книжка</p>
        {copy && (
          <>
            <p className="step-label">{copy.kicker}</p>
            <h1>{copy.title}</h1>
            <p className="lede">{copy.lede}</p>
            <div className="meter" aria-hidden="true">
              {FLOW.map((id) => (
                <span
                  key={id}
                  className={
                    FLOW.indexOf(id) < FLOW.indexOf(step)
                      ? "done"
                      : id === step
                        ? "now"
                        : ""
                  }
                />
              ))}
            </div>
          </>
        )}
        {step === "wait" && (
          <>
            <p className="step-label">Создание</p>
            <h1>{order?.status === "done" ? "Книга готова" : "Книга собирается"}</h1>
            <p className="lede">
              {order?.status === "done"
                ? "Страницы можно посмотреть здесь, PDF также придёт в чат с ботом."
                : "Можно закрыть приложение — готовый PDF придёт в чат с ботом."}
            </p>
          </>
        )}
      </header>

      <main className="stage" key={step}>
        {step === "theme" && (
          <div className="themes">
            {themes.map((theme) => {
              const face = themeFace(theme.id);
              const selected = themeId === theme.id;
              return (
                <button
                  type="button"
                  key={theme.id}
                  className={`theme-card ${selected ? "on" : ""}`}
                  onClick={() => {
                    setThemeId(theme.id);
                    setCustomTheme("");
                  }}
                >
                  <span className="theme-mark" style={{ background: face.tint }}>
                    <ThemeGlyph id={theme.id} />
                  </span>
                  <span className="theme-text">
                    <strong>{theme.title_ru}</strong>
                    <em>{face.line}</em>
                  </span>
                </button>
              );
            })}
            <div className={`own ${customTheme.trim() && !themeId ? "on" : ""}`}>
              <div className="own-head">
                <span className="theme-mark" style={{ background: "#efe4d4" }}>
                  <ThemeGlyph id="custom" />
                </span>
                <span className="theme-text">
                  <strong>Своя тема</strong>
                  <em>Ситуация своими словами</em>
                </span>
              </div>
              <textarea
                placeholder="Например: первый день в садике"
                value={customTheme}
                onChange={(e) => {
                  setCustomTheme(e.target.value);
                  setThemeId(null);
                }}
                rows={3}
                maxLength={400}
              />
            </div>
          </div>
        )}

        {step === "style" && (
          <StyleGallery styles={styles} styleId={styleId} onSelect={setStyleId} />
        )}

        {step === "child" && (
          <div className="child">
            <label className="name-label" htmlFor="child-name">
              Имя
            </label>
            <input
              id="child-name"
              className="name-input"
              value={childName}
              placeholder="Имя"
              onChange={(e) => setChildName(e.target.value)}
              maxLength={80}
              autoComplete="off"
            />
            <p className="field-label">
              Сколько лет <span>можно пропустить</span>
            </p>
            <div className="ages">
              {AGES.map((age) => (
                <button
                  type="button"
                  key={age}
                  className={`age ${childAge === age ? "on" : ""}`}
                  onClick={() => setChildAge((current) => (current === age ? "" : age))}
                >
                  {age}
                </button>
              ))}
            </div>
          </div>
        )}

        {step === "photo" && (
          <div className="photo-step">
            <div className="photo-stage">
              {preview ? (
                <img className="photo-world" src={preview} alt="" />
              ) : (
                <div className="art-fallback" />
              )}
              {photoUrl && (
                <div className="photo-hero">
                  <img src={photoUrl} alt="Фото ребёнка" />
                </div>
              )}
              <div className="photo-bar">
                <label className="photo-btn">
                  {photoUrl ? "Заменить фото" : "Добавить фото"}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => choosePhoto(e.target.files?.[0] ?? null)}
                  />
                </label>
                <p>Лицо крупно, при дневном свете, без фильтров</p>
              </div>
            </div>
            <ConsentCheckbox checked={consent} onChange={setConsent} />
          </div>
        )}

        {step === "confirm" && (
          <div className="confirm">
            <BookCover
              image={preview}
              name={childName.trim()}
              subtitle={themeTitle || "Своя история"}
              photo={photoUrl}
            />
            <ul className="facts">
              <li>
                <span>Герой</span>
                <strong>
                  {childName.trim()}
                  {childAge ? `, ${childAge}` : ""}
                </strong>
              </li>
              <li>
                <span>Тема</span>
                <strong>{themeTitle}</strong>
              </li>
              <li>
                <span>Стиль</span>
                <strong>{styleTitle}</strong>
              </li>
            </ul>
            {offlineCatalog && (
              <p className="note">
                Каталог открыт локально. Чтобы отправить заказ, нужен запущенный сервер.
              </p>
            )}
          </div>
        )}

        {step === "wait" && order && (
          <div className="wait">
            <BookCover
              image={preview}
              name={childName.trim()}
              subtitle={styleTitle}
              photo={photoUrl}
              working={order.status !== "done" && order.status !== "failed"}
            />
            <div className="progress" aria-hidden="true">
              <span style={{ width: `${order.progress_percent}%` }} />
            </div>
            <p className="wait-status">
              {order.progress_percent}% · {statusLabel(order.status)}
            </p>
            <ol className="phases">
              {PHASES.map((phase) => (
                <li key={phase.id} data-state={phaseState(order.status, phase.id)}>
                  <i />
                  {phase.label}
                </li>
              ))}
            </ol>
            {order.status === "done" && (
              <div className="preview">
                {order.preview_urls?.map((url) => (
                  <img key={url} src={url} alt="Превью страницы" />
                ))}
                {order.pdf_url && (
                  <a className="primary link" href={order.pdf_url} target="_blank" rel="noreferrer">
                    Скачать PDF
                  </a>
                )}
              </div>
            )}
            {order.status === "failed" && <p className="error">{order.error_message}</p>}
          </div>
        )}
      </main>

      {error && <p className="error banner">{error}</p>}

      {step !== "wait" && (
        <footer className="dock">
          {step !== "theme" && (
            <button type="button" className="back" onClick={goBack}>
              Назад
            </button>
          )}
          <button type="button" className="primary" disabled={!canAdvance || loading} onClick={goNext}>
            {step === "confirm" ? (loading ? "Отправляем…" : "Создать книгу") : "Дальше"}
          </button>
        </footer>
      )}
    </div>
  );
}

function BookCover({
  image,
  name,
  subtitle,
  photo,
  working = false,
}: {
  image?: string;
  name: string;
  subtitle?: string;
  photo: string | null;
  working?: boolean;
}) {
  return (
    <div className={`cover ${working ? "working" : ""}`}>
      <div className="cover-art">
        {image ? <img src={image} alt="" /> : <div className="art-fallback" />}
        <div className="cover-shade" />
        {photo && (
          <div className="cover-photo">
            <img src={photo} alt="" />
          </div>
        )}
        <div className="cover-copy">
          <span>сказка про</span>
          <strong>{name || "героя"}</strong>
          {subtitle && <em>{subtitle}</em>}
        </div>
      </div>
    </div>
  );
}

const PHASES = [
  { id: "text", label: "Пишем сказку" },
  { id: "images", label: "Рисуем иллюстрации" },
  { id: "pdf", label: "Собираем книгу" },
] as const;

function phaseState(status: Order["status"], id: (typeof PHASES)[number]["id"]): "done" | "now" | "todo" {
  const rank: Record<Order["status"], number> = {
    pending: 0,
    generating_text: 0,
    generating_images: 1,
    building_pdf: 2,
    done: 3,
    failed: -1,
  };
  const index = id === "text" ? 0 : id === "images" ? 1 : 2;
  const current = rank[status];
  if (current < 0) return "todo";
  if (current > index) return "done";
  if (current === index) return "now";
  return "todo";
}

function statusLabel(status: Order["status"]): string {
  const map: Record<Order["status"], string> = {
    pending: "В очереди",
    generating_text: "Пишем сказку",
    generating_images: "Рисуем иллюстрации",
    building_pdf: "Собираем PDF",
    done: "Готово",
    failed: "Ошибка",
  };
  return map[status];
}
