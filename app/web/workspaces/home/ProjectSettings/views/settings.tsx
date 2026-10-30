import { SettingsPanel, type SettingsPanelProps } from '../../SettingsPanel/module';

/** Existing advanced-settings frame and explicit mounted composition slots. */
export function ProjectSettings(props: SettingsPanelProps) {
  return <div className="sqd-fullsettings">
    <div className="sqd-advanced-title">Advanced settings</div>
    <SettingsPanel {...props} />
  </div>;
}
