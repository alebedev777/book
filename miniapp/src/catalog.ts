import type { Style, Theme } from "./api";

export const FALLBACK_STYLES: Style[] = [
  { id: "disney", title_ru: "Дисней" },
  { id: "anime", title_ru: "Аниме" },
  { id: "watercolor", title_ru: "Акварель" },
  { id: "flat_graphic", title_ru: "Плоская графика" },
  { id: "storybook_ink", title_ru: "Книжная гравюра" },
];

export const STYLE_FACE: Record<string, { mood: string; line: string }> = {
  disney: {
    mood: "Мультфильм",
    line: "Тёплый объёмный мир, как в большом кино",
  },
  anime: {
    mood: "Аниме",
    line: "Живописное лето, мягкий свет и природа",
  },
  watercolor: {
    mood: "Акварель",
    line: "Воздушные краски и нежные размытые края",
  },
  flat_graphic: {
    mood: "Графика",
    line: "Ясные формы и спокойный плакат",
  },
  storybook_ink: {
    mood: "Гравюра",
    line: "Старинный штрих, лес и тайна",
  },
};

export function styleFace(id: string): { mood: string; line: string } {
  return STYLE_FACE[id] ?? { mood: "Стиль", line: "Иллюстрации в этом характере" };
}

export const FALLBACK_THEMES: Theme[] = [
  {
    id: "responsibility",
    title_ru: "Ответственность",
    learning_goal: "",
    age_range: "4-8",
  },
  { id: "empathy", title_ru: "Сочувствие", learning_goal: "", age_range: "4-8" },
  { id: "patience", title_ru: "Терпение", learning_goal: "", age_range: "4-8" },
  { id: "honesty", title_ru: "Честность", learning_goal: "", age_range: "4-8" },
  { id: "courage", title_ru: "Смелость", learning_goal: "", age_range: "4-8" },
  { id: "friendship", title_ru: "Дружба", learning_goal: "", age_range: "4-8" },
  {
    id: "anger_management",
    title_ru: "Управление гневом",
    learning_goal: "",
    age_range: "4-8",
  },
  { id: "sharing", title_ru: "Делиться", learning_goal: "", age_range: "4-8" },
];

export const THEME_FACE: Record<string, { tint: string; line: string }> = {
  responsibility: { tint: "#f4e2cc", line: "Довести обещание до конца" },
  empathy: { tint: "#f8ddd4", line: "Заметить чувство другого" },
  patience: { tint: "#e4edd6", line: "Выдержать, когда хочется сразу" },
  honesty: { tint: "#e6e1f3", line: "Сказать правду и остаться собой" },
  courage: { tint: "#f8dfc8", line: "Идти вперёд вместе со страхом" },
  friendship: { tint: "#dcece4", line: "Быть рядом и оставаться собой" },
  anger_management: { tint: "#f8d8d0", line: "Понять злость и не разорвать связь" },
  sharing: { tint: "#f8e8c8", line: "Поделиться и стать ближе" },
};

export function themeFace(id: string): { tint: string; line: string } {
  return THEME_FACE[id] ?? { tint: "#f3e6d4", line: "История, которую выберете вы" };
}
