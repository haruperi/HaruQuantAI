export class ThemeProjection {
  static for_home(skin_name: string): 'dark' | 'light' {
    return skin_name === 'Dark skin' ? 'dark' : 'light';
  }
}
