export class DatabankDefaults {
  static reset_value(column_type: string): '' | 0 {
    switch (column_type) {
      case 'text':
      case 'dateTime':
      case 'filterResult':
        return '';
      default:
        return 0;
    }
  }
}
