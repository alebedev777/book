type Props = { id: string };

export function ThemeGlyph({ id }: Props) {
  return (
    <svg viewBox="0 0 24 24" className="glyph" aria-hidden="true">
      {glyph(id)}
    </svg>
  );
}

function glyph(id: string) {
  switch (id) {
    case "responsibility":
      return (
        <>
          <circle cx="12" cy="12" r="7.25" />
          <path d="M8.8 12.2 11 14.4 15.4 9.8" />
        </>
      );
    case "empathy":
      return (
        <path d="M12 18.6s-6.2-3.8-6.2-7.6a3.4 3.4 0 0 1 6.2-1.9 3.4 3.4 0 0 1 6.2 1.9c0 3.8-6.2 7.6-6.2 7.6z" />
      );
    case "patience":
      return (
        <>
          <path d="M12 19.5V10" />
          <path d="M12 12.2c.2-3.4 2.6-5.4 5.6-5.6-1.2 3.2-3 5-5.6 5.6z" />
          <path d="M12 14.4c-.2-2.6-2.4-4.4-5.2-4.6 1 2.6 2.6 4.2 5.2 4.6z" />
        </>
      );
    case "honesty":
      return (
        <>
          <path d="M12 3.8 19.2 12 12 20.2 4.8 12 12 3.8z" />
          <path d="M12 9.2v3.2" />
          <path d="M12 15.6h.01" />
        </>
      );
    case "courage":
      return <path d="M3.8 18.2 9.2 9.4l3.1 4.2 2.2-3.1 5.7 7.7H3.8z" />;
    case "friendship":
      return (
        <>
          <circle cx="9" cy="12" r="4.2" />
          <circle cx="15" cy="12" r="4.2" />
        </>
      );
    case "anger_management":
      return (
        <path d="M12 19.4c3.3 0 5.4-2.2 5.4-5 0-3.2-2.2-4.2-2.2-6.8-1.6 1.8-1.8 2.8-2.6 4.4-.8-1.8-.9-3.4-1-4.2-1.7 2.4-4.4 4-4.4 6.6 0 2.8 2 5 5 5z" />
      );
    case "sharing":
      return (
        <>
          <path d="M5.5 10.2h13v8.2h-13z" />
          <path d="M12 10.2v8.2" />
          <path d="M12 10.2c-1.6-2.6-4.4-2.2-4.6 0" />
          <path d="M12 10.2c1.6-2.6 4.4-2.2 4.6 0" />
        </>
      );
    default:
      return (
        <>
          <path d="M5 18.5 6.2 14 16.2 4.2 19.8 7.8 9.8 17.6 5 18.5z" />
          <path d="M14.2 6.2 17.8 9.8" />
        </>
      );
  }
}
