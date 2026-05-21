export default function Card({
  title,
  items,
  active,
  onPick
}) {

  return (
    <div className="card">

      <h3>{title}</h3>

      {items.map((item) => (

        <button
          key={item}
          className={
            active === item
              ? "cardBtn active"
              : "cardBtn"
          }
          onClick={() => onPick(item)}
        >
          {item}
        </button>

      ))}

    </div>
  );
}