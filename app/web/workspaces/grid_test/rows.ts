export type GridTestRow = readonly [number, number, string];

export interface TimedRow {
  row: GridTestRow;
  next_counter: number;
  change_count: 0;
}

export interface TimerPeriods {
  add: 20;
  remove: 30;
  change: 40;
  count: 50;
}

export class GridTestRows {
  static manual_batch(): GridTestRow[] {
    const rows: GridTestRow[] = [];
    for (let i = 0; i < 100; i += 1) {
      rows.push([i, i * 2, `${i}-text`]);
    }
    return rows;
  }

  static timed_row(counter: number): TimedRow {
    return {
      row: [counter, counter * 2, `${counter}-text`],
      next_counter: counter + 1,
      change_count: 0,
    };
  }

  static intervals_ms(): TimerPeriods {
    return {
      add: 20,
      remove: 30,
      change: 40,
      count: 50,
    };
  }
}
