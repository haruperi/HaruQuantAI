export interface LogMessage {
  time: string;
  category: string;
  message: string;
}

export interface LogFilter {
  category: string;
  text: string;
}

export class DebugLogBuffer {
  public text: string = '';
  public filter: LogFilter = { category: 'all', text: '' };

  clear(): void {
    this.text = '';
  }

  accepts(log: LogMessage): boolean {
    if (this.filter.category !== 'all' && this.filter.category !== log.category) {
      return false;
    }
    return log.message.includes(this.filter.text);
  }

  receive(batch: readonly LogMessage[]): void {
    for (const log of batch) {
      if (!this.accepts(log)) {
        return;
      }
      this.text = `${log.time} ${log.category} - ${log.message}</br>${this.text.substring(0, 10000)}`;
    }
  }
}
