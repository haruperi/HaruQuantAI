import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { examples } from "./algoWizardFixtures";
export function ExampleChart({ index }: { index: number }) {
  const points = Array.from({ length: 36 }, (_, i) => {
    const y = 100 - i * 1.65 - Math.sin(i * 0.8 + index) * 14;
    return { x: 8 + i * 7, y };
  });
  return (
    <svg
      className="aw-example-chart"
      viewBox="0 0 264 136"
      role="img"
      aria-label={`${examples[index]?.name ?? "Equity"} illustrative chart`}
    >
      <rect width="264" height="136" fill="#000" />
      {index === 2
        ? points
            .filter((_, i) => i % 5 === 0)
            .map((p, i) => (
              <rect
                key={i}
                x={p.x}
                y={110 - i * 12}
                width="3"
                height={i * 12 + 5}
                fill="#00ee00"
              />
            ))
        : points.map((p, i) => (
            <g key={i} stroke="#00ed00" strokeWidth=".7">
              <path d={`M${p.x} ${p.y - 8}V${p.y + 9}`} />
              <rect
                x={p.x - 2}
                y={p.y - 3}
                width="4"
                height={(i % 3) + 4}
                fill={i % 3 ? "#000" : "#fff"}
              />
            </g>
          ))}
      {index === 0 && (
        <>
          <path
            d="M0 114 Q70 103 130 77 T264 37"
            fill="none"
            stroke="#ff0000"
            strokeWidth="2"
          />
          <path
            d="M0 122 Q70 118 140 98 T264 58"
            fill="none"
            stroke="#f000ff"
            strokeWidth="2"
          />
        </>
      )}
      {(index === 1 || index === 3) && (
        <>
          <path d="M20 30H210 M20 118H210" stroke="red" />
          <path d="M20 80H210" stroke="blue" />
        </>
      )}
      {index === 4 && (
        <path
          d="M140 45L170 65 M140 120L170 106"
          stroke="yellow"
          strokeWidth="3"
        />
      )}
      {index > 4 && (
        <path d="M12 119L225 54" stroke="#306aff" strokeDasharray="3 3" />
      )}
    </svg>
  );
}
export function AlgoWizardHome({
  onNew,
  onLoad,
  onResource,
  onExample,
}: {
  onNew: () => void;
  onLoad: () => void;
  onResource: (type: string) => void;
  onExample: (i: number) => void;
}) {
  const carousel = useRef<HTMLDivElement>(null);
  return (
    <div className="aw-home">
      <div className="aw-home-start">
        <h1>No strategies loaded</h1>
        <div className="aw-home-buttons">
          <button className="aw-old" onClick={onNew}>
            New Strategy
          </button>
          <button className="aw-old" onClick={onLoad}>
            Load from file
          </button>
        </div>
        <div className="aw-home-resources">
          <button onClick={() => onResource("Random groups")}>
            Random groups
          </button>
          <button onClick={() => onResource("Custom blocks")}>
            Custom blocks
          </button>
        </div>
      </div>
      <div className="aw-carousel-shell">
        <div className="aw-carousel" ref={carousel}>
          {examples.map((e, i) => (
            <article key={e.file}>
              <h3>{e.name}</h3>
              <small>
                {e.cloud ? "STOCKPICKER" : "STANDARD"} STRATEGY EXAMPLE
              </small>
              <div className="aw-example-description">
                <p>{e.description}</p>
                {e.rules && (
                  <p>
                    Rules:
                    <br />
                    {e.rules.split("\n").map((r) => (
                      <span key={r}>
                        - {r}
                        <br />
                      </span>
                    ))}
                  </p>
                )}
              </div>
              <ExampleChart index={i} />
              <button
                className="aw-primary"
                aria-label={`Open ${e.name}`}
                onClick={() => onExample(i)}
              >
                Open
              </button>
            </article>
          ))}
        </div>
        <button
          className="aw-carousel-prev"
          aria-label="Previous examples"
          onClick={() =>
            carousel.current?.scrollBy({ left: -296, behavior: "smooth" })
          }
        >
          <ChevronLeft />
        </button>
        <button
          className="aw-carousel-next"
          aria-label="Next examples"
          onClick={() =>
            carousel.current?.scrollBy({ left: 296, behavior: "smooth" })
          }
        >
          <ChevronRight />
        </button>
      </div>
    </div>
  );
}
