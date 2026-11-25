type Props = {
  checked: boolean;
  onChange: (v: boolean) => void;
};

export function ConsentCheckbox({ checked, onChange }: Props) {
  return (
    <label className="consent">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      Я — родитель или законный представитель и даю согласие на обработку фото ребёнка только для
      генерации иллюстраций. Фото удаляется через 30 дней. Данные не передаются третьим лицам, кроме
      API генерации по вашему запросу.
    </label>
  );
}