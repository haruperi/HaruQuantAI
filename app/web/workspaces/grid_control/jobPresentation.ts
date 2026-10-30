export class GridJobPresentation {
  static kind(blocking: boolean): 'Continuous' | 'One time' {
    return blocking ? 'Continuous' : 'One time';
  }

  static state(waiting: boolean): 'Waiting' | 'Running' {
    return waiting ? 'Waiting' : 'Running';
  }

  static progress(value: number): string {
    return value === -1 ? 'N/A' : `${value}%`;
  }

  static can_refresh(active_app: string): boolean {
    return active_app === 'GRIDCONTROL';
  }

  static interval_ms(): 3000 {
    return 3000;
  }
}
